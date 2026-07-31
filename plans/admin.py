from django.contrib import admin
from .models import InternetPlan


@admin.register(InternetPlan)
class InternetPlanAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "display_order",
        "plan_type",
        "data",
        "validity",
        "price",
        "popular",
        "active",
    )

    list_display_links = (
        "name",
    )

    list_editable = (
        "display_order",
        "popular",
        "active",
    )

    list_filter = (
        "plan_type",
        "popular",
        "active",
    )

    search_fields = (
        "name",
        "data",
        "description",
    )

    ordering = (
        "display_order",
        "price",
    )