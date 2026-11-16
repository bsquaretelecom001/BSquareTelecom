from django.conf import settings
from django.core.mail import send_mail

from plans.models import InternetPlan
from .models import VoucherInventory, VoucherStockAlert


ALERT_EMAIL = "bsquaretelecom@gmail.com"


def check_voucher_stock(plan):
    available = VoucherInventory.objects.filter(
        plan=plan,
        status="Available",
    ).count()

    if available == 0:
        level = "Out"
        subject = f"OUT OF STOCK: {plan.name}"
        message = (
            f"B Square Telecom stock alert\n\n"
            f"Plan: {plan.name}\n"
            f"Available vouchers: 0\n\n"
            f"This plan has run out of available Omada vouchers. "
            f"Please import more vouchers."
        )

    elif available <= 3:
        level = "Critical"
        subject = f"CRITICAL STOCK: {plan.name}"
        message = (
            f"B Square Telecom stock alert\n\n"
            f"Plan: {plan.name}\n"
            f"Available vouchers: {available}\n\n"
            f"Stock is critically low. Please import more vouchers."
        )

    elif available <= 5:
        level = "Low"
        subject = f"LOW STOCK WARNING: {plan.name}"
        message = (
            f"B Square Telecom stock alert\n\n"
            f"Plan: {plan.name}\n"
            f"Available vouchers: {available}\n\n"
            f"Please prepare more Omada vouchers."
        )

    else:
        level = "Normal"
        subject = ""
        message = ""

    alert, created = VoucherStockAlert.objects.get_or_create(
        plan=plan,
        defaults={"last_alert_level": "Normal"},
    )

    if level == "Normal":
        if alert.last_alert_level != "Normal":
            alert.last_alert_level = "Normal"
            alert.save(update_fields=["last_alert_level", "updated_at"])
        return

    if alert.last_alert_level == level:
        return

    sender = settings.DEFAULT_FROM_EMAIL

    if not sender:
        print("Stock alert email skipped: DEFAULT_FROM_EMAIL is not configured.")
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=sender,
            recipient_list=[ALERT_EMAIL],
            fail_silently=False,
        )

        alert.last_alert_level = level
        alert.save(update_fields=["last_alert_level", "updated_at"])

        print(
            f"Stock alert sent for {plan.name}: "
            f"{level} ({available} available)"
        )

    except Exception as error:
        print(f"Stock alert email failed for {plan.name}: {error}")


def check_all_voucher_stocks():
    for plan in InternetPlan.objects.filter(active=True):
        check_voucher_stock(plan)