import requests
from django.conf import settings


PAYSTACK_BASE_URL = "https://api.paystack.co"


def initialize_payment(email, amount, reference):
    url = f"{PAYSTACK_BASE_URL}/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    callback_url = getattr(
        settings,
        "PAYSTACK_CALLBACK_URL",
        "https://bsquaretelecom.vercel.app/payment/verify/",
    )

    data = {
        "email": email,
        "amount": int(amount * 100),
        "reference": str(reference),
        "callback_url": callback_url,
    }

    try:
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    except (requests.RequestException, ValueError):
        return {
            "status": False,
            "message": "Unable to initialize payment with Paystack.",
        }


def verify_payment(reference):
    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    except (requests.RequestException, ValueError):
        return {
            "status": False,
            "message": "Unable to verify payment with Paystack.",
        }