import uuid

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from customers.models import Customer
from customers.utils import (
    check_customer_subscription,
    get_days_remaining,
)

from payments.models import Order
from vouchers.models import Voucher


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
            "Account created successfully.",
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


@login_required
def dashboard(request):

    customer, created = Customer.objects.get_or_create(
        user=request.user
    )

    check_customer_subscription(customer)

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

    devices = customer.devices.all()

    connected_devices = devices.filter(
        connected=True
    ).count()

    latest_voucher = None

    latest_order = orders.filter(
        status="Paid"
    ).first()

    if latest_order and hasattr(latest_order, "voucher"):
        latest_voucher = latest_order.voucher

    voucher = Voucher.objects.filter(
        customer=customer,
        status="Active",
    ).first()

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "customer": customer,
            "orders": orders,
            "voucher": voucher,
            "latest_voucher": latest_voucher,
            "devices": devices,
            "connected_devices": connected_devices,
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "pending_orders": pending_orders,
            "days_remaining": days_remaining,
        },
    )


@login_required
def profile(request):

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


@login_required
def generate_telegram_code(request):

    customer = Customer.objects.get(
        user=request.user
    )

    customer.telegram_code = uuid.uuid4()

    customer.save()

    messages.success(
        request,
        "Telegram link code generated successfully."
    )

    return redirect("dashboard")


@login_required
def my_vouchers(request):

    customer = Customer.objects.get(
        user=request.user
    )

    vouchers = Voucher.objects.filter(
        customer=customer
    ).order_by("-created_at")

    return render(
        request,
        "dashboard/vouchers.html",
        {
            "vouchers": vouchers,
        },
    )