from datetime import date

from django.utils import timezone

from .models import Customer


def deactivate_expired_subscriptions():
    """
    Deactivate every expired customer subscription.
    Returns the number of customers updated.
    """

    now = timezone.now()

    expired_customers = Customer.objects.filter(
        active_plan=True,
        plan_expiry__isnull=False,
        plan_expiry__lte=now,
    )

    count = expired_customers.count()

    expired_customers.update(
        active_plan=False
    )

    return count


def check_customer_subscription(customer):
    """
    Check one customer's subscription
    and deactivate it if expired.
    """

    if (
        customer.active_plan
        and customer.plan_expiry
        and customer.plan_expiry <= timezone.now()
    ):

        customer.active_plan = False
        customer.save()

    return customer


def get_days_remaining(customer):
    """
    Returns remaining subscription days.
    """

    if not customer.plan_expiry:
        return None

    days = (
        customer.plan_expiry.date()
        - date.today()
    ).days

    return max(days, 0)