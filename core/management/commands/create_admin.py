from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = "Create default admin user"

    def handle(self, *args, **kwargs):

        username = "bigt"
        password = "Admin12345"

        if User.objects.filter(username=username).exists():

            self.stdout.write(
                "Admin already exists"
            )

        else:

            User.objects.create_superuser(
                username=username,
                password=password,
                email="admin@bsquaretelecom.com"
            )

            self.stdout.write(
                "Admin created successfully"
            )