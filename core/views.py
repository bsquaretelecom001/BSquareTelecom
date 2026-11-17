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


# PRIVACY POLICY
def privacy_policy(request):
    return render(request, "policies/privacy_policy.html")


# TERMS AND CONDITIONS
def terms_and_conditions(request):
    return render(request, "policies/terms_and_conditions.html")


# REFUND POLICY
def refund_policy(request):
    return render(request, "policies/refund_policy.html")

def csrf_failure(request, reason=""):
    return render(
        request,
        "403_csrf.html",
        status=403,
    )