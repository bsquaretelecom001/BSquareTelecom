from datetime import timedelta
from vouchers.models import Voucher
from vouchers.utils import generate_voucher
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

from customers.models import Customer
from hotspot.omada import OmadaAPI

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

            # Generate a unique voucher
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

            # Activate customer on Omada
            try:
                omada = OmadaAPI()

                omada.activate_customer(
                    customer,
                    order.plan,
                )

            except Exception as e:
                print("OMADA ERROR:", e)

            # Send payment confirmation email
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
from django.http import JsonResponse
from plans.models import InternetPlan


def telegram_payment(request, plan_id):

    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
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

    if response["status"]:

        return JsonResponse({
            "status": True,
            "url": response["data"]["authorization_url"],
        })

    return JsonResponse({
        "status": False,
    })