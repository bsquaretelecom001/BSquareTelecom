from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse

from customers.models import Customer
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
        # Voucher is intentionally NOT generated automatically.
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

        receipt_url = request.build_absolute_uri(
            reverse(
                "receipt",
                args=[order.id],
            )
        )

        whatsapp_message = (
            "Hello B Square Telecom 👋\n\n"
            "I just made a payment for an internet plan.\n\n"
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

    return render(
        request,
        "payments/receipt.html",
        {
            "order": order,
            "customer": customer,
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