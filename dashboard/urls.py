from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.admin_dashboard,
        name="admin_dashboard",
    ),

    path(
        "customers/",
        views.customer_management,
        name="customer_management",
    ),

    path(
        "orders/",
        views.order_management,
        name="order_management",
    ),

    path(
        "plans/",
        views.plan_management,
        name="plan_management",
    ),

    path(
        "plans/add/",
        views.add_plan,
        name="add_plan",
    ),

    path(
        "plans/<int:plan_id>/edit/",
        views.edit_plan,
        name="edit_plan",
    ),

    path(
        "plans/<int:plan_id>/toggle/",
        views.toggle_plan_status,
        name="toggle_plan_status",
    ),

    path(
        "plans/<int:plan_id>/delete/",
        views.delete_plan,
        name="delete_plan",
    ),

    path(
        "reports/",
        views.reports,
        name="reports",
    ),

]