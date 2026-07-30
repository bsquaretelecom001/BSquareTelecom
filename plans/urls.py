from django.urls import path
from . import views

urlpatterns = [
    path("", views.plans, name="plans"),
    path("buy/<int:plan_id>/", views.buy_plan, name="buy_plan"),
]