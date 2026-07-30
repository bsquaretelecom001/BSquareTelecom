from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Main Website
    path("", include("core.urls")),

    # Accounts
    path("", include("accounts.urls")),

    # Customers
    path("", include("customers.urls")),

    # Plans & Payments
    path("plans/", include("plans.urls")),
    path("payment/", include("payments.urls")),

    # Django Authentication (Password Reset)
    path("accounts/", include("django.contrib.auth.urls")),

    # Admin Dashboard
    path("dashboard-admin/", include("dashboard.urls")),
]