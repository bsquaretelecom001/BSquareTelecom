from django.urls import path
from . import views

urlpatterns = [
    path("<int:order_id>/", views.payment_page, name="payment"),
    path("verify/", views.verify, name="verify"),
    path("receipt/<int:order_id>/", views.receipt, name="receipt"),
    path("telegram/<int:plan_id>/", views.telegram_payment, name="telegram_payment"),

    # Customer voucher access
    path("my-vouchers/", views.my_vouchers, name="my_vouchers"),
    path("verify-voucher-otp/", views.verify_voucher_otp, name="verify_voucher_otp"),
    path("voucher-history/", views.voucher_history, name="voucher_history"),
]