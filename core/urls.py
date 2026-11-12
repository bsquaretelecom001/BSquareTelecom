from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("coverage/", views.coverage, name="coverage"),
    path("contact/", views.contact, name="contact"),

    # Website Policies
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms_and_conditions, name="terms"),
    path("refund-policy/", views.refund_policy, name="refund_policy"),
]