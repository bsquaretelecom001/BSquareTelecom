import requests
import urllib3

from django.conf import settings


class OmadaAPI:
    def __init__(self):
        self.base_url = settings.OMADA_BASE_URL.rstrip("/")
        self.omadac_id = settings.OMADA_ID
        self.client_id = settings.OMADA_CLIENT_ID
        self.client_secret = settings.OMADA_CLIENT_SECRET
        self.site_id = settings.OMADA_SITE_ID

        self.session = requests.Session()

        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning
        )

    def get_access_token(self):
        url = (
            f"{self.base_url}"
            "/openapi/authorize/token"
            "?grant_type=client_credentials"
        )

        body = {
            "omadacId": self.omadac_id,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = self.session.post(
            url,
            json=body,
            verify=False,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("errorCode") != 0:
            raise Exception(
                f"Omada authentication failed: {data.get('msg')}"
            )

        return data["result"]["accessToken"]

    def _headers(self):
        token = self.get_access_token()

        return {
            "Authorization": f"AccessToken={token}",
            "Content-Type": "application/json",
        }

    def get_sites(self):
        url = (
            f"{self.base_url}"
            f"/openapi/v1/{self.omadac_id}/sites"
            "?pageSize=10&page=1"
        )

        response = self.session.get(
            url,
            headers=self._headers(),
            verify=False,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    def create_voucher(
        self,
        username,
        duration,
        download_limit=None,
        upload_limit=None,
        traffic_limit=None,
    ):
        url = (
            f"{self.base_url}"
            f"/openapi/v1/{self.omadac_id}"
            f"/sites/{self.site_id}"
            "/hotspot/voucher-groups"
        )

        rate_limit = {
            "mode": 0,
            "rateLimitProfileId": "",
            "customRateLimit": {
                "downLimitEnable": download_limit is not None,
                "downLimit": download_limit or 0,
                "upLimitEnable": upload_limit is not None,
                "upLimit": upload_limit or 0,
            },
        }

        payload = {
            "name": f"B-Square-{username}-{int(__import__('time').time())}",
            "amount": 1,
            "codeLength": 6,
            "codeForm": [0],
            "limitType": 2,
            "limitNum": 20,
            "durationType": 1,
            "duration": duration,
            "timingType": 0,
            "rateLimit": rate_limit,
            "trafficLimitEnable": traffic_limit is not None,
            "trafficLimit": traffic_limit or 0,
            "trafficLimitFrequency": 0,
            "unitPrice": 1,
            "currency": "USD",
            "applyToAllPortals": True,
            "portals": [],
            "logout": True,
            "description": f"B Square Telecom - {username}",
            "printComments": "",
        }

        response = self.session.post(
            url,
            headers=self._headers(),
            json=payload,
            verify=False,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("errorCode") != 0:
            raise Exception(
                f"Omada voucher creation failed: {data.get('msg')}"
            )

        group_id = data["result"]["id"]

        voucher_url = f"{url}/{group_id}"

        voucher_response = self.session.get(
            voucher_url,
            headers=self._headers(),
            params={
                "page": 1,
                "pageSize": 10,
            },
            verify=False,
            timeout=15,
        )

        voucher_response.raise_for_status()

        voucher_data = voucher_response.json()

        if voucher_data.get("errorCode") != 0:
            raise Exception(
                f"Could not retrieve Omada voucher: "
                f"{voucher_data.get('msg')}"
            )

        vouchers = voucher_data.get("result", {}).get("data", [])

        if not vouchers:
            raise Exception(
                "Omada created the voucher group "
                "but returned no voucher code."
            )

        voucher = vouchers[0]

        return {
            "status": True,
            "voucher_code": voucher["code"],
            "voucher_id": voucher["id"],
            "group_id": group_id,
            "duration": duration,
            "traffic_limit": traffic_limit,
        }

    def activate_customer(self, customer, plan):
        traffic_limit = None

        data = plan.data.upper().replace(" ", "")

        if data.endswith("GB"):
            gb = float(data.replace("GB", ""))
            traffic_limit = int(gb * 1024)

        elif data.endswith("MB"):
            mb = float(data.replace("MB", ""))
            traffic_limit = int(mb)

        validity = plan.validity.lower()

        if (
            "30 day" in validity
            or "monthly" in validity
            or "month" in validity
        ):
            duration = 43200

        elif "week" in validity:
            duration = 10080

        elif "daily" in validity or "day" in validity:
            duration = 1440

        else:
            duration = 43200

        result = self.create_voucher(
            username=customer.user.username,
            duration=duration,
            traffic_limit=traffic_limit,
        )

        return result