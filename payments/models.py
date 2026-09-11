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

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    plan = models.ForeignKey(
        InternetPlan,
        on_delete=models.CASCADE,
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

    notification_sent = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return str(self.reference)