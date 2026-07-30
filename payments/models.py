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

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    plan = models.ForeignKey(
        InternetPlan,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return str(self.reference)