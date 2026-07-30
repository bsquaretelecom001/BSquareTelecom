import uuid

from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    active_plan = models.BooleanField(
        default=False
    )

    plan_start = models.DateTimeField(
        null=True,
        blank=True
    )

    plan_expiry = models.DateTimeField(
        null=True,
        blank=True
    )

    data_balance = models.CharField(
        max_length=30,
        default="0 GB"
    )

    # Hotspot Login
    hotspot_username = models.CharField(
        max_length=50,
        blank=True
    )

    hotspot_password = models.CharField(
        max_length=50,
        blank=True
    )

    # Telegram Integration
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
    )

    telegram_username = models.CharField(
        max_length=100,
        blank=True,
    )

    telegram_code = models.UUIDField(
        null=True,
        blank=True,
        default=uuid.uuid4,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username


class Device(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    device_name = models.CharField(
        max_length=100
    )

    mac_address = models.CharField(
        max_length=50,
        unique=True,
    )

    ip_address = models.CharField(
        max_length=50,
        blank=True,
    )

    connected = models.BooleanField(
        default=False,
    )

    data_used = models.CharField(
        max_length=30,
        default="0 GB",
    )

    last_seen = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.device_name