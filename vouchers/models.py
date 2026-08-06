import uuid

from django.db import models

from customers.models import Customer
from payments.models import Order


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