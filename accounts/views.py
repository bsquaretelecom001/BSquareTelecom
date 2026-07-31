import uuid
from datetime import date

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from customers.models import Customer, Device


print("LOADED ACCOUNTS VIEWS.PY")


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

        login(request, user)

        return redirect("/dashboard/")

    return render(request, "accounts/register.html")


def login_view(request):

    from django.contrib.auth.models import User

    print("========== USERS ==========")
    print("TOTAL USERS:", User.objects.count())

    for u in User.objects.all():
        print(
            f"Username={u.username}, "
            f"Superuser={u.is_superuser}, "
            f"Staff={u.is_staff}"
        )

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        print("LOGIN RESULT:", user)

        if user:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")

def logout_view(request):
    logout(request)
    return redirect("home")


def dashboard(request):

    print("DASHBOARD OPENED")
    print("Authenticated:", request.user.is_authenticated)
    print("Current User:", request.user)

    if not request.user.is_authenticated:
        return redirect("login")

    customer, created = Customer.objects.get_or_create(
        user=request.user
    )

    if (
        customer.active_plan
        and customer.plan_expiry
        and customer.plan_expiry <= timezone.now()
    ):
        customer.active_plan = False
        customer.save()

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

    days_remaining = None

    if customer.plan_expiry:
        days_remaining = (
            customer.plan_expiry.date() - date.today()
        ).days

        if days_remaining < 0:
            days_remaining = 0

    # ===============================
    # Devices
    # ===============================

    devices = Device.objects.filter(
        customer=customer
    )

    connected_devices = devices.filter(
        connected=True
    ).count()

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

            "devices": devices,
            "connected_devices": connected_devices,
        },
    )


def profile(request):

    if not request.user.is_authenticated:
        return redirect("login")

    customer, created = Customer.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        request.user.first_name = request.POST["first_name"]
        request.user.last_name = request.POST["last_name"]
        request.user.email = request.POST["email"]
        request.user.save()

        customer.phone = request.POST["phone"]
        customer.state = request.POST["state"]
        customer.city = request.POST["city"]
        customer.address = request.POST["address"]
        customer.save()

        messages.success(
            request,
            "Profile updated successfully."
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
        f"Your Telegram Link Code is:\n\n{customer.telegram_code}"
    )

    return redirect("dashboard")