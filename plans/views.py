from django.shortcuts import render, get_object_or_404, redirect
from django.core import signing
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib import messages
from urllib.parse import urlencode

from .models import InternetPlan
from payments.models import Order
from vouchers.models import VoucherInventory


CHECKOUT_SALT = "payments.guest.checkout"


def plans(request):
    daily = InternetPlan.objects.filter(
        active=True,
        plan_type="Daily",
    ).annotate(
        available_vouchers=Count(
            "voucher_inventory",
            filter=Q(voucher_inventory__status="Available"),
        )
    )

    weekly = InternetPlan.objects.filter(
        active=True,
        plan_type="Weekly",
    ).annotate(
        available_vouchers=Count(
            "voucher_inventory",
            filter=Q(voucher_inventory__status="Available"),
        )
    )

    monthly = InternetPlan.objects.filter(
        active=True,
        plan_type="Monthly",
    ).annotate(
        available_vouchers=Count(
            "voucher_inventory",
            filter=Q(voucher_inventory__status="Available"),
        )
    )

    plan_groups = [
        (daily, "Daily Plans"),
        (weekly, "Weekly Plans"),
        (monthly, "Monthly Plans"),
    ]

    return render(
        request,
        "plans/plans.html",
        {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "plan_groups": plan_groups,
        },
    )


def buy_plan(request, plan_id):
    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
        active=True,
    )

    # Check available Omada voucher stock.
    available_stock = VoucherInventory.objects.filter(
        plan=plan,
        status="Available",
    ).count()

    if available_stock < 1:
        messages.error(
            request,
            f"Sorry, {plan.name} is temporarily unavailable. "
            "Please check back later.",
        )
        return redirect("plans")

    # Create an unpaid guest order.
    order = Order.objects.create(
        plan=plan,
        amount=plan.price,
    )

    # Generate a signed token tied to this order.
    token = signing.dumps(
        order.id,
        salt=CHECKOUT_SALT,
    )

    # Redirect to checkout with the signed token.
    checkout_url = reverse(
        "payment",
        kwargs={"order_id": order.id},
    )

    return redirect(
        f"{checkout_url}?{urlencode({'token': token})}"
    )