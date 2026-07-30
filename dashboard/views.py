from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.contrib import messages
from django.core.paginator import Paginator

from customers.models import Customer
from payments.models import Order
from plans.models import InternetPlan


@staff_member_required
def admin_dashboard(request):

    customers = Customer.objects.count()

    total_orders = Order.objects.count()

    paid_orders = Order.objects.filter(status="Paid").count()

    pending_orders = Order.objects.filter(status="Pending").count()

    active_customers = Customer.objects.filter(
        active_plan=True
    ).count()

    revenue = (
        Order.objects.filter(status="Paid")
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    recent_orders = (
        Order.objects.select_related(
            "user",
            "plan",
        )
        .order_by("-created_at")[:10]
    )

    return render(
        request,
        "dashboard/admin_dashboard.html",
        {
            "customers": customers,
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "pending_orders": pending_orders,
            "active_customers": active_customers,
            "revenue": revenue,
            "recent_orders": recent_orders,
        },
    )


@staff_member_required
def customer_management(request):

    query = request.GET.get("q", "")

    customers = Customer.objects.select_related("user")

    if query:

        customers = customers.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
            | Q(phone__icontains=query)
            | Q(state__icontains=query)
            | Q(city__icontains=query)
        )

    paginator = Paginator(
        customers.order_by("user__first_name"),
        10,
    )

    page = request.GET.get("page")

    customers = paginator.get_page(page)

    return render(
        request,
        "dashboard/customer_management.html",
        {
            "customers": customers,
            "query": query,
        },
    )


@staff_member_required
def order_management(request):

    orders = (
        Order.objects.select_related(
            "user",
            "plan",
        )
        .order_by("-created_at")
    )

    paginator = Paginator(
        orders,
        10,
    )

    page = request.GET.get("page")

    orders = paginator.get_page(page)

    return render(
        request,
        "dashboard/order_management.html",
        {
            "orders": orders,
        },
    )


@staff_member_required
def plan_management(request):

    plans = InternetPlan.objects.order_by(
        "plan_type",
        "price",
    )

    paginator = Paginator(
        plans,
        10,
    )

    page = request.GET.get("page")

    plans = paginator.get_page(page)

    return render(
        request,
        "dashboard/plan_management.html",
        {
            "plans": plans,
        },
    )


@staff_member_required
def add_plan(request):

    if request.method == "POST":

        InternetPlan.objects.create(
            name=request.POST["name"],
            plan_type=request.POST["plan_type"],
            data=request.POST["data"],
            validity=request.POST["validity"],
            price=request.POST["price"],
            description=request.POST["description"],
            active=True,
        )

        messages.success(
            request,
            "Internet plan created successfully.",
        )

        return redirect("plan_management")

    return render(
        request,
        "dashboard/add_plan.html",
    )


@staff_member_required
def edit_plan(request, plan_id):

    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
    )

    if request.method == "POST":

        plan.name = request.POST["name"]
        plan.plan_type = request.POST["plan_type"]
        plan.data = request.POST["data"]
        plan.validity = request.POST["validity"]
        plan.price = request.POST["price"]
        plan.description = request.POST["description"]

        plan.save()

        messages.success(
            request,
            "Plan updated successfully.",
        )

        return redirect("plan_management")

    return render(
        request,
        "dashboard/edit_plan.html",
        {
            "plan": plan,
        },
    )


@staff_member_required
def toggle_plan_status(request, plan_id):

    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
    )

    plan.active = not plan.active

    plan.save()

    messages.success(
        request,
        "Plan status updated successfully.",
    )

    return redirect("plan_management")


@staff_member_required
def delete_plan(request, plan_id):

    plan = get_object_or_404(
        InternetPlan,
        id=plan_id,
    )

    if request.method == "POST":

        plan.delete()

        messages.success(
            request,
            "Plan deleted successfully.",
        )

        return redirect("plan_management")

    return render(
        request,
        "dashboard/delete_plan.html",
        {
            "plan": plan,
        },
    )


@staff_member_required
def reports(request):

    paid_orders = Order.objects.filter(
        status="Paid"
    )

    total_revenue = (
        paid_orders.aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    total_paid = paid_orders.count()

    pending_orders = Order.objects.filter(
        status="Pending"
    ).count()

    customers = Customer.objects.count()

    return render(
        request,
        "dashboard/reports.html",
        {
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "pending_orders": pending_orders,
            "customers": customers,
        },
    )