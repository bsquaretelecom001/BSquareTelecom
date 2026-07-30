import requests

from django.conf import settings


class OmadaAPI:
    def __init__(self):
        self.base_url = settings.OMADA_BASE_URL
        self.username = settings.OMADA_USERNAME
        self.password = settings.OMADA_PASSWORD
        self.site = settings.OMADA_SITE

        self.session = requests.Session()

    def login(self):
        """
        Login to Omada Controller.

        This will be completed when the
        controller is installed.
        """

        if not self.base_url:
            return False

        return True

    def create_voucher(
        self,
        username,
        duration,
        download_limit=None,
        upload_limit=None,
    ):
        """
        Placeholder.

        Will generate hotspot vouchers later.
        """

        return {
            "status": True,
            "username": username,
            "duration": duration,
            "download_limit": download_limit,
            "upload_limit": upload_limit,
        }

    def activate_customer(
        self,
        customer,
        plan,
    ):
        """
        Placeholder.

        Later this will activate internet
        automatically after payment.
        """

        return {
            "status": True,
            "customer": customer.user.username,
            "plan": plan.name,
        }