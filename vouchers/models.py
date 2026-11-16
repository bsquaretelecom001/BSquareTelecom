from django.db import models

from customers.models import Customer
from payments.models import Order
from plans.models import InternetPlan


class Voucher(models.Model):

    STATUS_CHOICES = (
        ("Active", "Active"),
        ("Used", "Used"),
        ("Expired", "Expired"),
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="vouchers",
        null=True,
        blank=True,
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="voucher",
    )

    voucher_code = models.CharField(
        max_length=50,
        unique=True,
    )

    plan_name = models.CharField(
        max_length=100,
    )

    data = models.CharField(
        max_length=50,
    )

    device_limit = models.PositiveIntegerField(
        default=2,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Active",
    )

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.voucher_code


class VoucherInventory(models.Model):

    STATUS_CHOICES = (
        ("Available", "Available"),
        ("Issued", "Issued"),
    )

    plan = models.ForeignKey(
        InternetPlan,
        on_delete=models.PROTECT,
        related_name="voucher_inventory",
    )

    voucher_code = models.CharField(
        max_length=50,
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Available",
    )

    assigned_order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_voucher",
    )

    imported_at = models.DateTimeField(
        auto_now_add=True,
    )

    issued_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.voucher_code} - {self.plan.name}"


class VoucherStockAlert(models.Model):

    ALERT_LEVELS = (
        ("Normal", "Normal"),
        ("Low", "Low"),
        ("Critical", "Critical"),
        ("Out", "Out of Stock"),
    )

    plan = models.OneToOneField(
        InternetPlan,
        on_delete=models.CASCADE,
        related_name="stock_alert",
    )

    last_alert_level = models.CharField(
        max_length=20,
        choices=ALERT_LEVELS,
        default="Normal",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.plan.name} - {self.last_alert_level}"