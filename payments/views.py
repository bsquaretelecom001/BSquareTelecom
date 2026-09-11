from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings

try:
    from telegram import Bot
except ImportError:
    Bot = None

from customers.models import Customer
from vouchers.models import Voucher
from plans.models import InternetPlan

from .models import Order
from .paystack import initialize_payment, verify_payment
from .tasks import generate_voucher_for_order


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

        if response.get("status"):
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


def verify(request):

    reference = request.GET.get("reference")

    if not reference:
        return redirect("plans")

    response = verify_payment(reference)

    if (
        response.get("status")
        and response.get("data", {}).get("status") == "success"
    ):

        order = get_object_or_404(
            Order,
            reference=reference,
        )

        # Payment has been successfully confirmed.
        # Record the payment BEFORE attempting Omada.
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

        # Try to generate the Omada voucher.
        voucher_created = generate_voucher_for_order(
            order
        )

        order.refresh_from_db()

        voucher = Voucher.objects.filter(
            order=order
        ).first()

        # ---------------------------------------------
        # VOUCHER SUCCESSFULLY CREATED
        # ---------------------------------------------

        if voucher_created and voucher:

            try:

                customer = Customer.objects.get(
                    user=order.user
                )

                if customer.telegram_id and Bot is not None:

                    bot = Bot(
                        token=settings.TELEGRAM_BOT_TOKEN
                    )

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

                print(
                    "Telegram Error:",
                    e
                )

            return render(
                request,
                "payments/success.html",
                {
                    "order": order,
                    "voucher": voucher,
                },
            )

        # ---------------------------------------------
        # PAYMENT SUCCESSFUL
        # BUT VOUCHER NOT YET AVAILABLE
        # ---------------------------------------------

        return render(
            request,
            "payments/pending_voucher.html",
            {
                "order": order,
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

    if not request.user.is_authenticated:

        return JsonResponse(
            {
                "status": False,
                "error": "authentication_required",
            },
            status=401,
        )

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

    if response.get("status"):

        return JsonResponse(
            {
                "status": True,
                "url": response["data"]["authorization_url"],
            }
        )

    return JsonResponse(
        {
            "status": False,
        }
    )