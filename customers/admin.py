from django.contrib import admin
from .models import Customer, Device


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "phone",
        "state",
        "city",
        "active_plan",
        "telegram_username",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "phone",
    )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):

    list_display = (
        "device_name",
        "customer",
        "voucher",
        "mac_address",
        "connected",
        "last_seen",
    )

    search_fields = (
        "device_name",
        "mac_address",
        "customer__user__username",
    )

    list_filter = (
        "connected",
    )