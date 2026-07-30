from django.shortcuts import render, get_object_or_404, redirect

from .models import InternetPlan
from payments.models import Order


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
    