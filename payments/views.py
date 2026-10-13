from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.db import transaction

from plans.models import InternetPlan
from .models import Order
from .paystack import initialize_payment, verify_payment


RECEIPT_SALT = "payments.guest.receipt"
CHECKOUT_SALT = "payments.guest.checkout"


def payment_page(request, order_id):

    order = get_object_or_404(
        Order.objects.select_related("plan", "user"),
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
                salt="payments.guest.checkout",
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

    if request.method == "POST":
        name = request.POST.get("customer_name", "").strip()
        email = request.POST.get("customer_email", "").strip()
        phone = request.POST.get("customer_phone", "").strip()

        if not name or not email or not phone:
            error = "Please enter your name, email address, and phone number."
        elif order.status != "Pending":
            error = "This order can no longer be paid. Please select a plan again."
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

            try:
                response = initialize_payment(
                    email=email,
                    amount=order.amount,
                    reference=order.reference,
                )
            except Exception:
                response = {}

            if response.get("status") and response.get("data", {}).get(
                "authorization_url"
            ):
                return redirect(response["data"]["authorization_url"])

            error = (
                "We couldn't start your payment. Please try again. "
                "If the problem continues, contact B Square Telecom."
            )

    return render(
        request,
        "payments/payment.html",
        {
            "order": order,
            "error": error,
        },
    )


def verify(request):
    reference = request.GET.get("reference")

    if not reference:
        return redirect("plans")

    order = get_object_or_404(
        Order.objects.select_related("plan"),
        reference=reference,
    )

    # Do not trust the browser's callback alone.
    # Confirm the transaction directly with Paystack.
    try:
        response = verify_payment(str(order.reference))
    except Exception:
        return render(
            request,
            "payments/failed.html",
            {"error": "We couldn't verify your payment. Please contact support."},
        )

    payment_data = response.get("data", {}) if response.get("status") else {}

    if (
        payment_data.get("status") != "success"
        or str(payment_data.get("reference")) != str(order.reference)
    ):
        return render(
            request,
            "payments/failed.html",
            {"error": "Your payment could not be verified."},
        )

    # Check the transaction amount and currency before marking it paid.
    expected_amount = int(order.amount * 100)
    if payment_data.get("amount") != expected_amount:
        return render(
            request,
            "payments/failed.html",
            {"error": "The payment amount could not be confirmed. Please contact support."},
        )

    if payment_data.get("currency") != "NGN":
        return render(
            request,
            "payments/failed.html",
            {"error": "The payment currency could not be confirmed. Please contact support."},
        )

    with transaction.atomic():
        order = Order.objects.select_for_update().select_related("plan").get(
            id=order.id
        )

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

    receipt_token = signing.dumps(
        order.id,
        salt=RECEIPT_SALT,
    )

    receipt_path = reverse("receipt", args=[order.id])

    receipt_url = request.build_absolute_uri(
        f"{receipt_path}?{urlencode({'token': receipt_token})}"
    )

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
        "🧾 Payment receipt:\n"
        f"{receipt_url}\n\n"
        "Please activate my internet voucher. Thank you."
    )

    return render(
        request,
        "payments/success.html",
        {
            "order": order,
            "receipt_url": receipt_url,
            "whatsapp_message": whatsapp_message,
        },
    )


def receipt(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("plan", "user"),
        id=order_id,
    )

    # Existing account orders require their owner to be logged in.
    if order.user_id:
        if (
            not request.user.is_authenticated
            or order.user_id != request.user.id
        ):
            return redirect("plans")

    # Guest receipts use a signed token so sequential order IDs alone
    # do not grant access to another customer's receipt.
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
    # Keep the existing Telegram/account flow separate from guest checkout.
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