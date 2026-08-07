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

        # Temporary until SMTP is configured
        print("========== CONTACT MESSAGE ==========")
        print("Name:", name)
        print("Email:", email)
        print("Message:", message)
        print("=====================================")

        messages.success(
            request,
            "Your message has been received successfully. We will contact you soon."
        )

    return render(
        request,
        "contact.html",
        {
            "contact_info": contact_info,
        },
    )