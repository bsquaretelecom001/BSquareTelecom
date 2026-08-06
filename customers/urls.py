from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile, name="profile"),
path(
    "disconnect-device/<int:device_id>/",
    views.disconnect_device,
    name="disconnect_device",
),
]