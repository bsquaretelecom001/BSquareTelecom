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

from hotspot.omada import OmadaAPI

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

        # -------------------------------------------------
        # Retrieve the device that started the Omada
        # captive portal session.
        # -------------------------------------------------

        omada_client_mac = request.session.get(
            "omada_clientMac"
        )

        omada_client_ip = request.session.get(
            "omada_clientIp"
        )

        omada_redirect_url = request.session.get(
            "omada_redirectUrl"
        )

        print(
            "OMADA CLIENT MAC:",
            omada_client_mac
        )

        print(
            "OMADA CLIENT IP:",
            omada_client_ip
        )

        print(
            "OMADA REDIRECT URL:",
            omada_redirect_url
        )

        # -------------------------------------------------
        # Mark payment as successful BEFORE attempting
        # any network authorization.
        # -------------------------------------------------

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

        # -------------------------------------------------
        # NEW:
        # Attempt direct authorization of the device.
        # -------------------------------------------------

        device_authorized = False
        device_authorization_error = ""

        if omada_client_mac and omada_client_ip:

            try:

                omada = OmadaAPI()

                authorization = (
                    omada.authorize_customer_device(
                        client_mac=omada_client_mac,
                        client_ip=omada_client_ip,
                        redirect_url=omada_redirect_url,
                        plan=order.plan,
                    )
                )

                if authorization.get("status"):

                    device_authorized = True

                    print(
                        "OMADA DEVICE AUTHORIZED:",
                        omada_client_mac,
                    )

            except Exception as e:

                device_authorization_error = str(e)

                print(
                    "OMADA DEVICE AUTHORIZATION ERROR:",
                    e,
                )

        else:

            device_authorization_error = (
                "Omada client information was not "
                "available in the session."
            )

            print(
                "OMADA DEVICE AUTHORIZATION SKIPPED:",
                device_authorization_error,
            )

        # -------------------------------------------------
        # EXISTING VOUCHER SYSTEM
        #
        # We keep this for now as the fallback.
        # -------------------------------------------------

        voucher_created = False

        try:

            voucher_created = (
                generate_voucher_for_order(
                    order
                )
            )

        except Exception as e:

            print(
                "VOUCHER GENERATION ERROR:",
                e,
            )

            order.refresh_from_db()

        order.refresh_from_db()

        voucher = Voucher.objects.filter(
            order=order
        ).first()

        # -------------------------------------------------
        # DIRECT DEVICE AUTHORIZATION SUCCESS
        # -------------------------------------------------

        if device_authorized:

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
                            "🌐 Your device has been "
                            "authorized automatically.\n\n"
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
                    "device_authorized": True,
                    "omada_client_mac": omada_client_mac,
                    "omada_client_ip": omada_client_ip,
                },
            )

        # -------------------------------------------------
        # VOUCHER SUCCESSFULLY CREATED
        # -------------------------------------------------

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
                    "device_authorized": False,
                    "omada_client_mac": omada_client_mac,
                    "omada_client_ip": omada_client_ip,
                },
            )

        # -------------------------------------------------
        # PAYMENT SUCCESSFUL
        # BUT NETWORK ACCESS IS NOT AVAILABLE YET
        # -------------------------------------------------

        return render(
            request,
            "payments/pending_voucher.html",
            {
                "order": order,
                "device_authorized": False,
                "omada_client_mac": omada_client_mac,
                "omada_client_ip": omada_client_ip,
                "device_authorization_error":
                    device_authorization_error,
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

    return JsonResponse({
        "status": False,
    })

