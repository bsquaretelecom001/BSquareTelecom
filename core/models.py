from django.db import models
from django.utils import timezone


class ContactInfo(models.Model):
    company_name = models.CharField(max_length=100, default="B Square Telecom")
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=254)
    address = models.TextField(blank=True)

    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    telegram = models.URLField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class Announcement(models.Model):

    DISPLAY_CHOICES = [
        ("popup", "Popup"),
        ("banner", "Website Banner"),
    ]

    PRIORITY_CHOICES = [
        ("normal", "Normal"),
        ("important", "Important"),
        ("urgent", "Urgent"),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()

    display_type = models.CharField(
        max_length=10,
        choices=DISPLAY_CHOICES,
        default="popup",
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="normal",
    )

    is_published = models.BooleanField(default=False)

    starts_at = models.DateTimeField(
        default=timezone.now,
    )

    ends_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()

        return (
            self.is_published
            and self.starts_at <= now
            and (self.ends_at is None or self.ends_at >= now)
        )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Customer Announcement"
        verbose_name_plural = "Customer Announcements"


class CoverageArea(models.Model):

    STATUS_CHOICES = [
        ("available", "Currently Available"),
        ("coming_soon", "Coming Soon"),
    ]

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
    )

    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Coverage Area"
        verbose_name_plural = "Coverage Areas"

    def __str__(self):
        return f"{self.name} - {self.location}"