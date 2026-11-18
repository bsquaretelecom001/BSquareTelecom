from django.contrib import admin
from .models import ContactInfo, Announcement, CoverageArea


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "phone",
        "updated_at",
    )


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "display_type",
        "priority",
        "is_published",
        "starts_at",
        "ends_at",
    )

    list_filter = (
        "is_published",
        "display_type",
        "priority",
    )

    search_fields = (
        "title",
        "message",
    )

    list_editable = (
        "is_published",
        "priority",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(CoverageArea)
class CoverageAreaAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "location",
        "status",
        "is_active",
        "display_order",
    )

    list_filter = (
        "status",
        "is_active",
    )

    search_fields = (
        "name",
        "location",
    )

    list_editable = (
        "status",
        "is_active",
        "display_order",
    )