from django.db import models


class ContactInfo(models.Model):
    company_name = models.CharField(max_length=100, default="B Square Telecom")
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    address = models.TextField(blank=True)

    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    telegram = models.URLField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name