from urllib.parse import urlencode

from django.core import signing
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction

from plans.models import InternetPlan
from .models import Order, VoucherAccessOTP, PaystackPaymentAttempt
from .paystack import initialize_payment, verify_payment
from .tasks import generate_voucher_for_order

import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.utils import timezone



RECEIPT_SALT = "payments.guest.receipt"
CHECKOUT_SALT = "payments.guest.checkout"


def payment_page(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related("plan"),
        id=order_id,
    )

    # Registered-user orders remain restricted to their owner.
    if order.user_id:
        if (
            not request.user.is_authenticated
            or order.user_id != request.user.id
        ):
            return redirect("plans")

    # Guest orders require a valid signed checkout token.
    if not order.user_id:
        token = request.GET.get("token", "")

        try:
            token_order_id = signing.loads(
                token,
                salt=CHECKOUT_SALT,
                max_age=60 * 60,
            )
        except signing.BadSignature:
            return redirect("plans")

        if token_order_id != order.id:
            return redirect("plans")

    if order.status == "Paid":
        if order.user_id:
            return redirect("receipt", order_id=order.id)

        return redirect("plans")

    error = ""
    details_saved = False
    whatsapp_url = ""

    if request.method == "POST":
        name = request.POST.get("customer_name", "").strip()
        email = request.POST.get("customer_email", "").strip()
        phone = request.POST.get("customer_phone", "").strip()

        if not name or not email or not phone:
            error = (
                "Please enter your name, email address, and phone number."
            )

        elif order.status != "Pending":
            error = (
                "This order can no longer be paid. "
                "Please select a plan again."
            )

        else:
            order.customer_name = name
            order.customer_email = email
            order.customer_phone = phone

            if order.user_id and not order.user.email:
                order.user.email = email
                order.user.save(update_fields=["email"])

            order.save(
                update_fields=[
                    "customer_name",
                    "customer_email",
                    "customer_phone",
                ]
            )
            # Reuse an existing pending Paystack checkout if available.
            payment_attempt = (
                PaystackPaymentAttempt.objects
                .filter(
                    order=order,
                    status="Pending",
                )
                .exclude(authorization_url="")
                .order_by("-created_at")
                .first()
            )

            if payment_attempt:
                return redirect(payment_attempt.authorization_url)

            # Create a fresh attempt if no active checkout exists.
            payment_attempt = PaystackPaymentAttempt.objects.create(
                order=order,
                amount=order.amount,
            )

            paystack_response = initialize_payment(
                email=order.customer_email,
                amount=payment_attempt.amount,
                reference=str(payment_attempt.reference),
            )

            authorization_url = (
                paystack_response.get("data", {}).get("authorization_url")
                if paystack_response.get("status")
                else None
            )

            if authorization_url:
                payment_attempt.authorization_url = authorization_url
                payment_attempt.save(update_fields=["authorization_url"])

                return redirect(authorization_url)

            payment_attempt.status = "Failed"
            payment_attempt.save(update_fields=["status"])
            whatsapp_message = (
                "Hello B Square Telecom!\n\n"
                "I have made a bank transfer for my internet plan.\n\n"
                f"Name: {order.customer_name}\n"
                f"Phone: {order.customer_phone}\n"
                f"Email: {order.customer_email}\n"
                f"Plan: {order.plan.name}\n"
                f"Data: {order.plan.data}\n"
                f"Validity: {order.plan.validity}\n"
                f"Amount: NGN {order.amount}\n"
                f"Order Reference: {order.reference}\n\n"
                "I have attached a screenshot of my bank transfer receipt.\n"
                "Please verify my payment. Thank you!"
            )

            whatsapp_url = (
                "https://wa.me/2349113724631?"
                + urlencode({"text": whatsapp_message})
            )

            details_saved = True

    return render(
        request,
        "payments/payment.html",
        {
            "order": order,
            "error": error,
            "details_saved": details_saved,
            "whatsapp_url": whatsapp_url,
        },
    )


def verify(request):

    reference = request.GET.get("reference")

    if not reference:
        return redirect("plans")

    # First, check whether this is a new payment attempt.
    payment_attempt = (
        PaystackPaymentAttempt.objects
        .filter(reference=reference)
        .select_related("order__plan")
        .first()
    )

    if payment_attempt:
        order = payment_attempt.order
        payment_reference = str(payment_attempt.reference)
        expected_amount = int(payment_attempt.amount * 100)

    else:
        # Preserve compatibility with existing Telegram payments.
        order = get_object_or_404(
            Order.objects.select_related("plan"),
            reference=reference,
        )

        payment_reference = str(order.reference)
        expected_amount = int(order.amount * 100)

    # Verify the transaction directly with Paystack.
    try:
        response = verify_payment(payment_reference)

    except Exception:
        return render(
            request,
            "payments/failed.html",
            {
                "error": (
                    "We couldn't verify your payment. "
                    "Please contact support."
                )
            },
        )

    payment_data = (
        response.get("data", {})
        if response.get("status")
        else {}
    )

    if (
        payment_data.get("status") != "success"
        or str(payment_data.get("reference")) != payment_reference
    ):
        return render(
            request,
            "payments/failed.html",
            {"error": "Your payment could not be verified."},
        )

    # Verify the original amount requested from Paystack.
    paid_requested_amount = int(
        payment_data.get("requested_amount")
        or payment_data.get("amount")
        or 0
    )

    if paid_requested_amount != expected_amount:
        return render(
            request,
            "payments/failed.html",
            {
                "error": (
                    "The payment amount could not be confirmed. "
                    "Please contact support."
                )
            },
        )

    # Verify payment currency.
    if payment_data.get("currency") != "NGN":
        return render(
            request,
            "payments/failed.html",
            {
                "error": (
                    "The payment currency could not be confirmed. "
                    "Please contact support."
                )
            },
        )

    # Record successful payment and update the order safely.
    with transaction.atomic():

        order = (
            Order.objects
            .select_for_update()
            .select_related("plan")
            .get(id=order.id)
        )

        if payment_attempt:
            payment_attempt = (
                PaystackPaymentAttempt.objects
                .select_for_update()
                .get(id=payment_attempt.id)
            )

            payment_attempt.status = "Paid"
            payment_attempt.save(update_fields=["status"])

        if order.status != "Paid":

            order.status = "Paid"
            order.voucher_status = "Pending"
            order.voucher_error = ""

            order.save(
                update_fields=[
                    "status",
                    "voucher_status",
                    "voucher_error",
                ]
            )

    # Automatically allocate an imported Omada voucher.
    # Existing protection against duplicate voucher generation is preserved.
    generate_voucher_for_order(order)

    order.refresh_from_db()

    receipt_token = signing.dumps(
        order.id,
        salt=RECEIPT_SALT,
    )

    receipt_path = reverse(
        "receipt",
        args=[order.id],
    )

    receipt_url = request.build_absolute_uri(
        f"{receipt_path}?{urlencode({'token': receipt_token})}"
    )

    voucher = (
        Order.objects
        .filter(pk=order.pk)
        .select_related("voucher")
        .first()
    )

    voucher_code = ""

    if voucher:
        try:
            voucher_code = voucher.voucher.voucher_code
        except Order.voucher.RelatedObjectDoesNotExist:
            voucher_code = ""

    whatsapp_message = (
        "Hello B Square Telecom 👋\n\n"
        "I just made a payment for an internet plan.\n\n"
        f"👤 Name: {order.customer_name}\n"
        f"📞 Phone: {order.customer_phone}\n"
        f"📦 Plan: {order.plan.name}\n"
        f"📶 Data: {order.plan.data}\n"
        f"📅 Validity: {order.plan.validity}\n"
        f"💰 Amount Paid: ₦{order.amount}\n"
        f"🔖 Reference: {order.reference}\n\n"
    )

    if voucher_code:
        whatsapp_message += (
            f"🎟️ Your Internet Voucher Code: {voucher_code}\n\n"
        )
    else:
        whatsapp_message += (
            "Your payment has been confirmed. "
            "Your voucher is being processed.\n\n"
        )

    whatsapp_message += (
        "🧾 Payment receipt:\n"
        f"{receipt_url}\n\n"
        "Thank you for choosing B Square Telecom."
    )

    return render(
        request,
        "payments/success.html",
        {
            "order": order,
            "receipt_url": receipt_url,
            "whatsapp_message": whatsapp_message,
            "voucher_code": voucher_code,
        },
    )


def receipt(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related("plan"),
        id=order_id,
    )

    # Existing account orders require their owner to be logged in.
    if order.user_id:
        if (
            not request.user.is_authenticated
            or order.user_id != request.user.id
        ):
            return redirect("plans")

    # Guest receipts require a valid signed token.
    token = request.GET.get("token", "")

    if not order.user_id:

        if not token:
            return redirect("plans")

        try:
            token_order_id = signing.loads(
                token,
                salt=RECEIPT_SALT,
                max_age=60 * 60 * 24 * 30,
            )

        except signing.BadSignature:
            return redirect("plans")

        if token_order_id != order.id:
            return redirect("plans")

    if order.status != "Paid":
        return redirect("plans")

    return render(
        request,
        "payments/receipt.html",
        {
            "order": order,
            "customer": None,
            "guest_receipt": not bool(order.user_id),
        },
    )


def telegram_payment(request, plan_id):

    # Keep the existing Telegram/account flow separate.
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": False,
                "error": "authentication_required",
            },
            status=401,
        )

    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
        active=True,
    )

    order = Order.objects.create(
        user=request.user,
        customer_name=request.user.get_full_name(),
        customer_email=request.user.email,
        plan=plan,
        amount=plan.price,
    )

    response = initialize_payment(
        email=request.user.email,
        amount=order.amount,
        reference=str(order.reference),
    )

    if response.get("status"):
        return JsonResponse(
            {
                "status": True,
                "url": response["data"]["authorization_url"],
            }
        )

    return JsonResponse({"status": False})
def my_vouchers(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        if not email:
            return render(
                request,
                "payments/my_vouchers.html",
                {"error": "Please enter your email address."},
            )

        latest_otp = VoucherAccessOTP.objects.filter(
            email__iexact=email,
            created_at__gte=timezone.now() - timedelta(seconds=60),
        ).exists()

        if latest_otp:
            return render(
                request,
                "payments/my_vouchers.html",
                {"error": "Please wait one minute before requesting another code."},
            )

        code = f"{secrets.randbelow(1000000):06d}"

        VoucherAccessOTP.objects.filter(
            email__iexact=email,
            is_used=False,
        ).update(is_used=True)

        VoucherAccessOTP.objects.create(
            email=email,
            code_hash=make_password(code),
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        try:
            send_mail(
                subject="Your B Square Telecom verification code",
                message=(
                    f"Your verification code is: {code}\n\n"
                    "This code expires in 10 minutes.\n"
                    "Do not share it with anyone."
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            VoucherAccessOTP.objects.filter(
                email__iexact=email,
                is_used=False,
            ).update(is_used=True)

            return render(
                request,
                "payments/my_vouchers.html",
                {"error": "We could not send your code. Please try again later."},
            )

        request.session["voucher_otp_email"] = email

        return redirect("verify_voucher_otp")

    return render(request, "payments/my_vouchers.html")


def verify_voucher_otp(request):
    email = request.session.get("voucher_otp_email")

    if not email:
        return redirect("my_vouchers")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        otp = VoucherAccessOTP.objects.filter(
            email__iexact=email,
            is_used=False,
            expires_at__gt=timezone.now(),
        ).order_by("-created_at").first()

        if not otp or otp.attempts >= 5:
            return render(
                request,
                "payments/verify_voucher_otp.html",
                {"error": "Your code has expired. Please request another one."},
            )

        otp.attempts += 1

        if check_password(code, otp.code_hash):
            otp.is_used = True
            otp.save(update_fields=["attempts", "is_used"])

            request.session["verified_voucher_email"] = email
            request.session.set_expiry(15 * 60)

            return redirect("voucher_history")

        otp.save(update_fields=["attempts"])

        return render(
            request,
            "payments/verify_voucher_otp.html",
            {"error": "Invalid verification code. Please try again."},
        )

    return render(request, "payments/verify_voucher_otp.html")


def voucher_history(request):
    email = request.session.get("verified_voucher_email")

    if not email:
        return redirect("my_vouchers")

    orders = (
        Order.objects.filter(
            customer_email__iexact=email,
            status="Paid",
        )
        .select_related("plan", "voucher")
        .order_by("-created_at")
    )

    return render(
        request,
        "payments/voucher_history.html",
        {"orders": orders},
    )