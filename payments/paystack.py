import requests
from django.conf import settings


def initialize_payment(email, amount, reference):
    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    callback_url = settings.PAYSTACK_CALLBACK_URL

    data = {
        "email": email,
        "amount": int(amount * 100),
        "reference": str(reference),
        "callback_url": callback_url,
    }

    response = requests.post(
        url,
        json=data,
        headers=headers,
        timeout=30,
    )

    return response.json()


def verify_payment(reference):
    url = (
        f"https://api.paystack.co/"
        f"transaction/verify/{reference}"
    )

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    return response.json()