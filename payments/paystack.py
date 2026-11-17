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

        result = response.json()

        if not result.get("status"):
            print(
                "PAYSTACK INITIALIZATION REJECTED:",
                result.get("message"),
                "| Reference:",
                reference,
            )

        elif not result.get("data", {}).get("authorization_url"):
            print(
                "PAYSTACK RESPONSE MISSING AUTHORIZATION URL:",
                result,
            )

        return result

    except requests.HTTPError as e:
        response = e.response

        print(
            "PAYSTACK HTTP ERROR:",
            response.status_code if response is not None else "Unknown",
            response.text[:1000] if response is not None else str(e),
        )

    except requests.Timeout:
        print(
            "PAYSTACK TIMEOUT: Payment initialization exceeded 20 seconds.",
            "| Reference:",
            reference,
        )

    except requests.RequestException as e:
        print(
            "PAYSTACK CONNECTION ERROR:",
            str(e),
            "| Reference:",
            reference,
        )

    except ValueError as e:
        print(
            "PAYSTACK INVALID RESPONSE:",
            str(e),
            "| Reference:",
            reference,
        )

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

    except (requests.RequestException, ValueError) as e:
        print(f"Paystack verification error: {e}")
        return {
            "status": False,
            "message": "Unable to verify payment with Paystack.",
        }