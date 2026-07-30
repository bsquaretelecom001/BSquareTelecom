from django.db import models


class InternetPlan(models.Model):

    PLAN_TYPES = (
        ("Daily", "Daily"),
        ("Weekly", "Weekly"),
        ("Monthly", "Monthly"),
    )

    name = models.CharField(max_length=100)

    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        default="Monthly",
    )

    data = models.CharField(max_length=30)

    validity = models.CharField(max_length=30)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    description = models.TextField(blank=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.plan_type})"