import uuid

from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    active_plan = models.BooleanField(
        default=False,
    )

    plan_start = models.DateTimeField(
        null=True,
        blank=True,
    )

    plan_expiry = models.DateTimeField(
        null=True,
        blank=True,
    )

    data_balance = models.CharField(
        max_length=30,
        default="0 GB",
    )

    hotspot_username = models.CharField(
        max_length=50,
        blank=True,
    )

    hotspot_password = models.CharField(
        max_length=50,
        blank=True,
    )

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
        default=uuid.uuid4,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.user.username


class Device(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    voucher = models.ForeignKey(
        "vouchers.Voucher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    device_name = models.CharField(
        max_length=100,
        default="Unknown Device",
        blank=True,
    )

    mac_address = models.CharField(
        max_length=20,
        unique=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    connected = models.BooleanField(
        default=True,
    )

    data_used = models.CharField(
        max_length=30,
        default="0 MB",
    )

    first_connected = models.DateTimeField(
        auto_now_add=True,
    )

    last_seen = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.device_name} ({self.mac_address})"


class DeviceSession(models.Model):

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    voucher = models.ForeignKey(
        "vouchers.Voucher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    login_time = models.DateTimeField(
        auto_now_add=True,
    )

    logout_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    data_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.device} - {self.login_time}"