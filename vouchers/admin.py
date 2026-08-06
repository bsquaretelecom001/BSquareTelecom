from django.contrib import admin

from .models import Voucher


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):

    list_display = (
        "voucher_code",
        "customer",
        "plan_name",
        "data",
        "status",
        "device_limit",
        "expires_at",
    )

    search_fields = (
        "voucher_code",
        "customer__user__username",
    )

    list_filter = (
        "status",
    )
