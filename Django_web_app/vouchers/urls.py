from django.urls import path
from .views import voucher_apply

app_name = "vouchers"

urlpatterns = [
    path("apply/", voucher_apply, name="voucher_apply"),
]
