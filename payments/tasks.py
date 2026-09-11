from datetime import timedelta

from django.utils import timezone

from customers.models import Customer
from vouchers.models import Voucher
from hotspot.omada import OmadaAPI

from .models import Order

def generate_voucher_for_order(order):
    """
    Try to generate an Omada voucher for a paid order.
    """

    # Don't create another voucher if one already exists.
    existing_voucher = Voucher.objects.filter(
        order=order
    ).first()

    if existing_voucher:

        if order.voucher_status != "Created":
            order.voucher_status = "Created"
            order.voucher_error = ""

            order.save(
                update_fields=[
                    "voucher_status",
                    "voucher_error",
                ]
            )

        return True

    try:

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

        if "daily" in validity or "day" in validity:
            expiry = start_date + timedelta(days=1)

        elif "week" in validity:
            expiry = start_date + timedelta(days=7)

        else:
            expiry = start_date + timedelta(days=30)

        omada = OmadaAPI()

        omada_result = omada.activate_customer(
            customer,
            order.plan,
        )

        if not omada_result.get("status"):
            raise Exception(
                "Omada did not return a successful voucher result."
            )

        voucher_code = omada_result.get(
            "voucher_code"
        )

        if not voucher_code:
            raise Exception(
                "Omada created no voucher code."
            )

        Voucher.objects.create(
            customer=customer,
            order=order,
            voucher_code=voucher_code,
            plan_name=order.plan.name,
            data=order.plan.data,
            device_limit=20,
            expires_at=expiry,
        )

        customer.active_plan = True
        customer.plan_start = now
        customer.plan_expiry = expiry
        customer.data_balance = order.plan.data

        customer.save()

        order.voucher_status = "Created"
        order.voucher_error = ""

        order.save(
            update_fields=[
                "voucher_status",
                "voucher_error",
            ]
        )

        print(
            f"Voucher successfully generated for order "
            f"{order.reference}: {voucher_code}"
        )

        return True

    except Exception as e:

        print(
            f"Voucher generation failed for order "
            f"{order.reference}: {e}"
        )

        order.voucher_status = "Failed"
        order.voucher_error = str(e)

        order.save(
            update_fields=[
                "voucher_status",
                "voucher_error",
            ]
        )

        return False


def retry_failed_vouchers():
    """
    Retry voucher generation for payments that succeeded
    but whose Omada voucher could not be created.
    """

    failed_orders = Order.objects.filter(
        status="Paid",
        voucher_status="Failed",
    )

    results = {
        "attempted": 0,
        "successful": 0,
        "failed": 0,
    }

    for order in failed_orders:

        results["attempted"] += 1

        success = generate_voucher_for_order(
            order
        )

        if success:
            results["successful"] += 1
        else:
            results["failed"] += 1

    return results