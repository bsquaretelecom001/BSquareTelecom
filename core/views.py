from django.shortcuts import render
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

from .models import ContactInfo


def home(request):
    return render(request, "home.html")


def coverage(request):
    return render(request, "coverage.html")


def contact(request):

    contact_info = ContactInfo.objects.first()

    if request.method == "POST":

        name = request.POST["name"]
        email = request.POST["email"]
        message = request.POST["message"]

        send_mail(
            subject=f"New Contact Message from {name}",
            message=f"""
Name: {name}

Email: {email}

Message:

{message}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[
                settings.DEFAULT_FROM_EMAIL,
            ],
            fail_silently=True,
        )

        messages.success(
            request,
            "Your message has been sent successfully."
        )

    return render(
        request,
        "contact.html",
        {
            "contact_info": contact_info,
        },
    )