import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from vouchers.models import Voucher, VoucherInventory

from .models import Order
from vouchers.notifications import check_voucher_stock


def get_plan_duration(validity):
    validity = str(validity).strip().lower()

    match = re.search(r"(\d+)\s*(days?|weeks?|months?)\b", validity)

    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        if unit.startswith("week"):
            return amount * 7

        if unit.startswith("month"):
            return amount * 30

        return amount

    if "week" in validity:
        return 7

    if "month" in validity:
        return 30

    if "day" in validity or "daily" in validity:
        return 1

    return 30


def generate_voucher_for_order(order):
    try:
        with transaction.atomic():

            locked_order = (
                Order.objects
                .select_for_update()
                .select_related("plan")
                .get(pk=order.pk)
            )

            if locked_order.status != "Paid":
                raise Exception("Order has not been paid.")

            existing_voucher = Voucher.objects.filter(
                order=locked_order
            ).first()

            if existing_voucher:
                locked_order.voucher_status = "Created"
                locked_order.voucher_error = ""
                locked_order.save(
                    update_fields=["voucher_status", "voucher_error"]
                )
                transaction.on_commit(
    lambda: check_voucher_stock(locked_order.plan)
)
                return True

            inventory_voucher = VoucherInventory.objects.filter(
                assigned_order=locked_order
            ).first()

            if not inventory_voucher:
                inventory_voucher = (
                    VoucherInventory.objects
                    .select_for_update()
                    .filter(
                        plan=locked_order.plan,
                        status="Available"
                    )
                    .order_by("imported_at", "id")
                    .first()
                )

            if not inventory_voucher:
                raise Exception(
                    f"No available vouchers for {locked_order.plan.name}."
                )

            now = timezone.now()
            customer = None

            if locked_order.user_id:
                customer = Customer.objects.filter(
                    user_id=locked_order.user_id
                ).first()

            start_date = now

            if (
                customer
                and customer.active_plan
                and customer.plan_expiry
                and customer.plan_expiry > now
            ):
                start_date = customer.plan_expiry

            duration_days = get_plan_duration(
                locked_order.plan.validity
            )

            expiry = start_date + timedelta(days=duration_days)

            inventory_voucher.status = "Issued"
            inventory_voucher.assigned_order = locked_order
            inventory_voucher.issued_at = now
            inventory_voucher.save(
                update_fields=[
                    "status",
                    "assigned_order",
                    "issued_at"
                ]
            )

            Voucher.objects.create(
                customer=customer,
                order=locked_order,
                voucher_code=inventory_voucher.voucher_code,
                plan_name=locked_order.plan.name,
                data=locked_order.plan.data,
                device_limit=20,
                expires_at=expiry,
            )

            if customer:
                customer.active_plan = True
                customer.plan_start = now
                customer.plan_expiry = expiry
                customer.data_balance = locked_order.plan.data
                customer.save()

            locked_order.voucher_status = "Created"
            locked_order.voucher_error = ""
            locked_order.save(
                update_fields=["voucher_status", "voucher_error"]
            )

            print(
                f"Voucher assigned to order {locked_order.reference}: "
                f"{inventory_voucher.voucher_code}"
            )

            return True

    except Exception as e:
        print(
            f"Voucher allocation failed for order "
            f"{order.reference}: {e}"
        )

        Order.objects.filter(pk=order.pk).update(
            voucher_status="Failed",
            voucher_error=str(e),
        )

        return False


def retry_failed_vouchers():
    failed_orders = Order.objects.filter(
        status="Paid",
        voucher_status="Failed"
    )

    results = {
        "attempted": 0,
        "successful": 0,
        "failed": 0
    }

    for order in failed_orders:
        results["attempted"] += 1

        success = generate_voucher_for_order(order)

        if success:
            results["successful"] += 1
        else:
            results["failed"] += 1

    return results