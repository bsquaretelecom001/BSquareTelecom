from asgiref.sync import sync_to_async

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from payments.models import Order
from payments.paystack import initialize_payment

from plans.models import InternetPlan
from customers.models import Customer
from customers.utils import get_days_remaining
from vouchers.models import Voucher

from django.conf import settings

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
def main_menu():

    keyboard = [
        [KeyboardButton("📦 Buy Data")],
        [KeyboardButton("🎟 My Voucher"), KeyboardButton("📊 Usage")],
        [KeyboardButton("👤 My Account"), KeyboardButton("📜 Orders")],
        [KeyboardButton("🔄 Renew"), KeyboardButton("☎ Contact Support")],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Welcome to *B Square Telecom*\n\n"
        "Choose an option below.",
        reply_markup=main_menu(),
        parse_mode="Markdown",
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

from vouchers.models import Voucher


async def voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        customer = await sync_to_async(
            Customer.objects.get
        )(
            telegram_id=update.effective_user.id
        )

    except Customer.DoesNotExist:

        await update.message.reply_text(
            "❌ Link your account first.\n\nUse /link YOUR_CODE"
        )

        return

    try:

        latest_voucher = await sync_to_async(
            lambda: Voucher.objects.filter(
                customer=customer,
                status="Active"
            ).latest("created_at")
        )()

    except Voucher.DoesNotExist:

        await update.message.reply_text(
            "❌ You don't have any active voucher."
        )

        return

    message = f"""
🎟 *Current Voucher*

Voucher:
`{latest_voucher.voucher_code}`

Plan:
{latest_voucher.plan_name}

Data:
{latest_voucher.data}

Status:
{latest_voucher.status}

Expiry:
{latest_voucher.expires_at.strftime("%d %B %Y")}
"""

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )
async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        customer = await sync_to_async(
            Customer.objects.get
        )(
            telegram_id=update.effective_user.id
        )

    except Customer.DoesNotExist:

        await update.message.reply_text(
            "❌ Link your account first.\n\nUse /link YOUR_CODE"
        )

        return

    orders = await sync_to_async(
        lambda: list(
            Order.objects.filter(
                user=customer.user
            ).order_by("-created_at")[:5]
        )
    )()

    if not orders:

        await update.message.reply_text(
            "You have no orders yet."
        )

        return

    message = "🧾 *Your Recent Orders*\n\n"

    for order in orders:

        message += (
            f"📦 {order.plan.name}\n"
            f"💰 ₦{order.amount}\n"
            f"📅 {order.created_at.strftime('%d %b %Y')}\n"
            f"📌 {order.status}\n\n"
        )

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
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📦 Buy Data":
        await plans(update, context)

    elif text == "🎟 My Voucher":
        await voucher(update, context)

    elif text == "📊 Usage":
        await usage(update, context)

    elif text == "👤 My Account":
        await me(update, context)

    elif text == "📜 Orders":
        await orders(update, context)

    elif text == "🔄 Renew":
        await plans(update, context)

    elif text == "☎ Contact Support":

        await update.message.reply_text(

            "📞 *B Square Telecom Support*\n\n"

            "Phone:\n"
            "+234 XXX XXX XXXX\n\n"

            "WhatsApp:\n"
            "+234 XXX XXX XXXX\n\n"

            "Email:\n"
            "support@bsquaretelecom.com\n\n"

            "We're available 24/7.",

            parse_mode="Markdown",

        )
async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    plans = await sync_to_async(
        lambda: list(
            InternetPlan.objects.filter(active=True)
        )
    )()

    if not plans:

        await update.message.reply_text(
            "No plans available."
        )

        return

    message = "📡 *B Square Telecom Available Plans*\n\n"

    for plan in plans:
        message += (
            f"🆔 *ID:* {plan.id}\n"
            f"🟢 *{plan.name}*\n"
            f"💾 Data: {plan.data}\n"
            f"💰 Price: ₦{plan.price}\n"
            f"🗓 Validity: {plan.validity}\n\n"
        )

    message += (
    "\n━━━━━━━━━━━━━━\n"
    "To purchase a plan, send:\n"
    "`/buy PLAN_ID`\n\n"
    "Example:\n"
    "`/buy 3`"
)
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Usage:\n\n/buy PLAN_ID"
        )

        return

    try:

        plan_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "Invalid Plan ID."
        )

        return

    try:

        customer = await sync_to_async(
            Customer.objects.select_related("user").get
        )(
            telegram_id=update.effective_user.id
        )

    except Customer.DoesNotExist:

        await update.message.reply_text(
            "❌ Please link your account first.\n\nUse /link YOUR_CODE"
        )

        return

    try:

        plan = await sync_to_async(
            InternetPlan.objects.get
        )(
            id=plan_id,
            active=True,
        )

    except InternetPlan.DoesNotExist:

        await update.message.reply_text(
            "Plan not found."
        )

        return

    order = await sync_to_async(
        Order.objects.create
    )(
        user=customer.user,
        plan=plan,
        amount=plan.price,
    )

    response = initialize_payment(
        email=customer.user.email,
        amount=order.amount,
        reference=str(order.reference),
    )

    if response["status"]:

        payment_url = response["data"]["authorization_url"]

        await update.message.reply_text(
            f"""
✅ Order Created

Plan:
{plan.name}

Amount:
₦{plan.price}

Click below to pay:

{payment_url}
"""
        )

    else:

        await update.message.reply_text(
            "Unable to initialize payment."
        )
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Example:\n/buy 3"
        )
        return

    try:
        plan_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "Invalid plan."
        )
        return

    customer = await sync_to_async(
        Customer.objects.get
    )(
        telegram_id=str(update.effective_user.id)
    )

    plan = await sync_to_async(
        InternetPlan.objects.get
    )(
        id=plan_id
    )

    order = await sync_to_async(
        Order.objects.create
    )(
        user=customer.user,
        plan=plan,
        amount=plan.price,
    )

    response = initialize_payment(
        email=customer.user.email,
        amount=order.amount,
        reference=str(order.reference),
    )

    if response["status"]:

        await update.message.reply_text(
            f"""
✅ Order Created

Plan:
{plan.name}

Amount:
₦{plan.price}

Click below to pay:

{response["data"]["authorization_url"]}
"""
        )

    else:

        await update.message.reply_text(
            "Payment initialization failed."
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
def build_bot():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("plans", plans))
    app.add_handler(
    CommandHandler("buy", buy)
)
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("usage", usage))
    app.add_handler(CommandHandler("voucher", voucher))
    app.add_handler(
    CommandHandler("orders", orders)
)

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            button_handler,
        )
    )
    return app