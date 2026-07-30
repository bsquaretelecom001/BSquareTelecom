from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("coverage/", views.coverage, name="coverage"),
    path("contact/", views.contact, name="contact"),
]