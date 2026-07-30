import requests
from django.conf import settings


def initialize_payment(email, amount, reference):
    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    data = {
        "email": email,
        "amount": int(amount * 100),
        "reference": str(reference),
        "callback_url": "http://127.0.0.1:8000/payment/verify/",
    }

    response = requests.post(
        url,
        json=data,
        headers=headers,
    )

    return response.json()


def verify_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    response = requests.get(
        url,
        headers=headers,
    )

    return response.json()