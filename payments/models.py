import uuid

from django.db import models
from django.contrib.auth.models import User

from plans.models import InternetPlan


class Order(models.Model):
    STATUS = (
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Cancelled", "Cancelled"),
    )

    VOUCHER_STATUS = (
        ("Pending", "Pending"),
        ("Created", "Created"),
        ("Failed", "Failed"),
    )

    # Existing registered customers remain supported.
    # New guest customers do not need an account.
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Contact details for guest checkout and payment follow-up.
    customer_name = models.CharField(max_length=150, blank=True, default="")
    customer_email = models.EmailField(blank=True, default="")
    customer_phone = models.CharField(max_length=30, blank=True, default="")

    plan = models.ForeignKey(
        InternetPlan,
        on_delete=models.PROTECT,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Pending",
    )

    voucher_status = models.CharField(
        max_length=20,
        choices=VOUCHER_STATUS,
        default="Pending",
    )

    voucher_error = models.TextField(
        blank=True,
        default="",
    )

    notification_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.reference)


class VoucherAccessOTP(models.Model):
    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voucher access OTP for {self.email}"


class PaystackPaymentAttempt(models.Model):

    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Failed", "Failed"),
        ("Paid", "Paid"),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payment_attempts",
    )

    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    authorization_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.reference)