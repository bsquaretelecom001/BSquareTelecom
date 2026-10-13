from django.shortcuts import render, get_object_or_404, redirect
from django.core import signing

from .models import InternetPlan
from payments.models import Order

from django.urls import reverse
from urllib.parse import urlencode

CHECKOUT_SALT = "payments.guest.checkout"


def plans(request):
    daily = InternetPlan.objects.filter(
        active=True,
        plan_type="Daily",
    )

    weekly = InternetPlan.objects.filter(
        active=True,
        plan_type="Weekly",
    )

    monthly = InternetPlan.objects.filter(
        active=True,
        plan_type="Monthly",
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
    checkout_url = reverse("payment", kwargs={"order_id": order.id})
    return redirect(f"{checkout_url}?{urlencode({'token': token})}")