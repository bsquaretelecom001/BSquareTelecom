from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from telegram import Bot
from django.conf import settings
from vouchers.models import Voucher
from vouchers.utils import generate_voucher
from customers.models import Customer
from hotspot.omada import OmadaAPI
from plans.models import InternetPlan

from .models import Order
from .paystack import initialize_payment, verify_payment


@login_required
def payment_page(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    if request.method == "POST":

        response = initialize_payment(
            email=request.user.email,
            amount=order.amount,
            reference=order.reference,
        )

        print("PAYSTACK RESPONSE:")
        print(response)

        if response["status"]:
            return redirect(
                response["data"]["authorization_url"]
            )

        print("PAYSTACK FAILED")

    return render(
        request,
        "payments/payment.html",
        {
            "order": order,
        },
    )


@login_required
def verify(request):

    reference = request.GET.get("reference")

    if not reference:
        return redirect("plans")

    response = verify_payment(reference)

    if (
        response["status"]
        and response["data"]["status"] == "success"
    ):

        order = get_object_or_404(
            Order,
            reference=reference,
        )

        if order.status != "Paid":

            order.status = "Paid"
            order.save()

            customer = Customer.objects.get(
                user=order.user
            )

            now = timezone.now()

            if (
                customer.active_plan
                and customer.plan_expiry
                and customer.plan_expiry > now
            ):
                start_date = customer.plan_expiry
            else:
                start_date = now

            validity = order.plan.validity.lower()

            if "daily" in validity:
                expiry = start_date + timedelta(days=1)

            elif "week" in validity:
                expiry = start_date + timedelta(days=7)

            else:
                expiry = start_date + timedelta(days=30)

            customer.active_plan = True
            customer.plan_start = now
            customer.plan_expiry = expiry
            customer.save()

            # Generate voucher
            voucher_code = generate_voucher()

            while Voucher.objects.filter(
                voucher_code=voucher_code
            ).exists():
                voucher_code = generate_voucher()

            voucher = Voucher.objects.create(
                customer=customer,
                order=order,
                voucher_code=voucher_code,
                plan_name=order.plan.name,
                data=order.plan.data,
                expires_at=customer.plan_expiry,
            )

            # ==========================
            # TELEGRAM NOTIFICATION
            # ==========================
            try:

                if customer.telegram_id:

                    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

                    bot.send_message(
                        chat_id=customer.telegram_id,
                        text=(
                            "✅ PAYMENT SUCCESSFUL\n\n"
                            f"📦 Plan: {order.plan.name}\n"
                            f"📶 Data: {order.plan.data}\n"
                            f"💰 Amount: ₦{order.amount}\n\n"
                            f"🎟 Voucher:\n"
                            f"{voucher.voucher_code}\n\n"
                            f"📅 Expires:\n"
                            f"{customer.plan_expiry.strftime('%d %B %Y')}"
                        ),
                    )

            except Exception as e:
                print("Telegram Error:", e)

            # ==========================
            # ACTIVATE CUSTOMER ON OMADA
            # ==========================
            try:

                omada = OmadaAPI()

                omada.activate_customer(
                    customer,
                    order.plan,
                )

            except Exception as e:
                print("OMADA ERROR:", e)

            # ==========================
            # SEND EMAIL
            # ==========================
            send_mail(
                subject="Payment Successful - B Square Telecom",
                message=f"""
Hello {order.user.first_name or order.user.username},

Your payment was successful.

Plan: {order.plan.name}
Data: {order.plan.data}
Amount: ₦{order.amount}

Reference:
{order.reference}

Start Date:
{customer.plan_start.strftime('%d %B %Y %I:%M %p')}

Expiry Date:
{customer.plan_expiry.strftime('%d %B %Y %I:%M %p')}

Thank you for choosing B Square Telecom.

Enjoy your internet service!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=True,
            )

        return render(
            request,
            "payments/success.html",
            {
                "order": order,
                "voucher": voucher,
            },
        )

    return render(
        request,
        "payments/failed.html",
    )

@login_required
def receipt(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    customer = Customer.objects.get(
        user=request.user,
    )

    voucher = Voucher.objects.filter(
        order=order
    ).first()

    return render(
        request,
        "payments/receipt.html",
        {
            "order": order,
            "customer": customer,
            "voucher": voucher,
        },
    )


def telegram_payment(request, plan_id):

    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
    )

    # Ensure only authenticated users can create orders
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "error": "authentication_required"}, status=401)

    order = Order.objects.create(
        user=request.user,
        plan=plan,
        amount=plan.price,
    )

    response = initialize_payment(
        email=request.user.email,
        amount=order.amount,
        reference=str(order.reference),
    )

    if response["status"]:

        return JsonResponse({
            "status": True,
            "url": response["data"]["authorization_url"],
        })

    return JsonResponse({
        "status": False,
    })