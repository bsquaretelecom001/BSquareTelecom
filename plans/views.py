from django.shortcuts import render, get_object_or_404, redirect

from .models import InternetPlan
from payments.models import Order


def plans(request):

    # Save Omada captive-portal information in the
    # customer's session so it survives the purchase
    # and login process.

    omada_fields = [
        "clientMac",
        "clientIp",
        "apMac",
        "gatewayMac",
        "ssidName",
        "radioId",
        "site",
        "redirectUrl",
    ]

    for field in omada_fields:
        value = request.GET.get(field)

        if value:
            request.session[f"omada_{field}"] = value

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

    return render(
        request,
        "plans/plans.html",
        {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
        },
    )


def buy_plan(request, plan_id):

    if not request.user.is_authenticated:
        return redirect("login")

    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
    )

    # Always create a new order with a new unique reference
    order = Order.objects.create(
        user=request.user,
        plan=plan,
        amount=plan.price,
    )

    return redirect(
        "payment",
        order_id=order.id,
    )

