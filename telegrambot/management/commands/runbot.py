from django.core.management.base import BaseCommand
from telegrambot.bot import build_bot


class Command(BaseCommand):
    help = "Run Telegram Bot"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Telegram Bot...")

        app = build_bot()
        app.run_polling()