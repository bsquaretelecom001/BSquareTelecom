import resend

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)

        resend.api_key = settings.RESEND_API_KEY

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent_count = 0

        for email_message in email_messages:
            try:
                params = {
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": list(email_message.to),
                    "subject": email_message.subject,
                    "text": email_message.body,
                }
                print(
    "RESEND EMAIL:",
    params["to"],
    params["subject"],
)

                resend.Emails.send(params)

                sent_count += 1

            except Exception:
                if not self.fail_silently:
                    raise

        return sent_count