from django.contrib import admin
from django.urls import path, include

urlpatterns = [
	# Django Admin — keep access for the site owner
	path("admin/", admin.site.urls),

	# Main Website
	path("", include("core.urls")),

	# Plans & Guest Checkout
	path("plans/", include("plans.urls")),
	path("payment/", include("payments.urls")),

	# Admin Dashboard
	path("dashboard-admin/", include("dashboard.urls")),
]
