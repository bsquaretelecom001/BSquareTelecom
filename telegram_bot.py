import os
import django

from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from plans.models import InternetPlan

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


keyboard = [
    ["🌐 Buy Internet"],
    ["👤 My Account"],
    ["📞 Contact Support"],
    ["🌍 Visit Website"],
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Welcome to B Square Telecom\n\n"
        "Connecting You Without Limits.\n\n"
        "Choose an option below.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        ),
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🌐 Buy Internet":

        plans = await sync_to_async(
            lambda: list(
                InternetPlan.objects.filter(active=True)
            )
        )()

        if not plans:
            await update.message.reply_text(
                "❌ No internet plans are available at the moment."
            )
            return

        message = "🌐 *Available Internet Plans*\n\n"

        for plan in plans:
            message += (
                f"📦 {plan.name}\n"
                f"💾 Data: {plan.data}\n"
                f"💰 Price: ₦{plan.price}\n"
                f"⏳ Validity: {plan.validity}\n"
                "----------------------\n"
            )

        message += (
            "\nTo purchase a plan, visit:\n"
            "http://127.0.0.1:8000/plans/"
        )

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
        )

    elif text == "👤 My Account":

        await update.message.reply_text(
            f"👤 Username: {update.effective_user.username}\n\n"
            "Account lookup from the website will be added soon."
        )

    elif text == "📞 Contact Support":

        await update.message.reply_text(
            "📞 Support\n\n"
            "Call/WhatsApp:\n"
            "08032556433"
        )

    elif text == "🌍 Visit Website":

        await update.message.reply_text(
            "🌍 Website\n\n"
            "http://127.0.0.1:8000/"
        )

    else:

        await update.message.reply_text(
            "Please choose one of the buttons below."
        )


def main():

    app = Application.builder().token(
        settings.TELEGRAM_BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons,
        )
    )

    print("Telegram Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()