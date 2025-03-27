from django.urls import path
from . import views

app_name = "vouchers"

urlpatterns = [
    path("apply/", views.voucher_apply, name="voucher_apply"),
]
