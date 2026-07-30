from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from customers.utils import (
    check_customer_subscription,
    get_days_remaining,
)

from .models import Customer


def register(request):
    if request.method == "POST":

        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        username = request.POST["username"]
        email = request.POST["email"]
        phone = request.POST["phone"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        Customer.objects.create(
            user=user,
            phone=phone,
        )

        messages.success(
            request,
            "Account created successfully."
        )

        return redirect("login")

    return render(
        request,
        "accounts/register.html",
    )


def login_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user:

            login(request, user)

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "accounts/login.html",
    )


def logout_view(request):

    logout(request)

    return redirect("home")


def dashboard(request):

    if not request.user.is_authenticated:
        return redirect("login")

    customer, created = Customer.objects.get_or_create(
        user=request.user
    )

    check_customer_subscription(customer)

    from payments.models import Order

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    total_orders = orders.count()

    paid_orders = orders.filter(
        status="Paid"
    ).count()

    pending_orders = orders.filter(
        status="Pending"
    ).count()

    days_remaining = get_days_remaining(customer)

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "customer": customer,
            "orders": orders,
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "pending_orders": pending_orders,
            "days_remaining": days_remaining,
        },
    )


def profile(request):

    if not request.user.is_authenticated:
        return redirect("login")

    customer, created = Customer.objects.get_or_create(
        user=request.user
    )

    check_customer_subscription(customer)

    if request.method == "POST":

        request.user.first_name = request.POST["first_name"]
        request.user.last_name = request.POST["last_name"]
        request.user.save()

        customer.phone = request.POST["phone"]
        customer.state = request.POST["state"]
        customer.city = request.POST["city"]
        customer.address = request.POST["address"]
        customer.save()

        messages.success(
            request,
            "Profile updated successfully.",
        )

        return redirect("profile")

    return render(
        request,
        "customers/profile.html",
        {
            "customer": customer,
        },
    )