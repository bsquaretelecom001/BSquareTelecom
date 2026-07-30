from django.contrib import admin
from .models import InternetPlan


@admin.register(InternetPlan)
class InternetPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "data",
        "validity",
        "price",
        "active",
    )

    list_filter = (
        "active",
    )

    search_fields = (
        "name",
        "data",
    )