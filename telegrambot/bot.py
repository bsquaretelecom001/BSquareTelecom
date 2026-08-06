from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from customers.models import Customer
from customers.utils import get_days_remaining


BOT_TOKEN = "8862627544:AAGYJXH9uJsuWlJ3iaYVQmKPv5mTt4bSbiw"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to B Square Telecom!\n\n"
        "Commands:\n"
        "/link YOUR_CODE - Link your account\n"
        "/me - View your account\n"
        "/usage - View your current usage"
    )


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/link YOUR_CODE"
        )
        return

    code = context.args[0].strip()

    try:
        customer = await sync_to_async(
            Customer.objects.get
        )(telegram_code=code)

        customer.telegram_id = update.effective_user.id
        customer.telegram_username = (
            update.effective_user.username or ""
        )

        customer.telegram_code = None

        await sync_to_async(customer.save)()

        await update.message.reply_text(
            "✅ Telegram account linked successfully!"
        )

    except Customer.DoesNotExist:

        await update.message.reply_text(
            "❌ Invalid or expired code."
        )


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        customer = await sync_to_async(
            Customer.objects.select_related("user").get
        )(
            telegram_id=update.effective_user.id
        )

    except Customer.DoesNotExist:

        await update.message.reply_text(
            "❌ Your Telegram account is not linked.\n\n"
            "Use /link YOUR_CODE first."
        )
        return

    days_remaining = get_days_remaining(customer)

    devices = await sync_to_async(
        lambda: customer.devices.count()
    )()

    status = "✅ Active" if customer.active_plan else "❌ Inactive"

    name = customer.user.get_full_name() or customer.user.username

    message = f"""
👤 *B Square Telecom*

👨 Name: {name}

📞 Phone: {customer.phone}

📡 Plan Status: {status}

📅 Expiry:
{customer.plan_expiry if customer.plan_expiry else "No Active Plan"}

⏳ Days Remaining:
{days_remaining}

📶 Data Balance:
{customer.data_balance}

💻 Connected Devices:
{devices}
"""

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        customer = await sync_to_async(
            Customer.objects.select_related("user").get
        )(
            telegram_id=update.effective_user.id
        )

    except Customer.DoesNotExist:

        await update.message.reply_text(
            "❌ Please link your account first."
        )
        return

    devices = await sync_to_async(
        lambda: list(customer.devices.all())
    )()

    if not devices:

        await update.message.reply_text(
            "No connected device found."
        )
        return

    text = "📊 *Current Device Usage*\n\n"

    for device in devices:

        text += (
            f"💻 {device.device_name}\n"
            f"MAC: `{device.mac_address}`\n"
            f"IP: {device.ip_address}\n"
            f"Used: {device.data_used}\n"
        )

        if device.connected:
            text += "Status: 🟢 Online\n\n"
        else:
            text += "Status: 🔴 Offline\n\n"

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
    )


def build_bot():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("usage", usage))

    return app