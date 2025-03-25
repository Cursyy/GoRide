from django.urls import path
from .views import booking_page, rent_vehicle, buy_subscription, top_up_balance, success

app_name = "booking"

urlpatterns = [
    path("<str:subject>/", booking_page, name="booking_page"),
    path("<str:subject>/<int:vehicle_id>/", booking_page, name="booking_page_with_vehicle"),
    path("rent/process/", rent_vehicle, name="process_rent"),
    path("subscription/process/", buy_subscription, name="process_subscription"),
    path("balance/process/", top_up_balance, name="process_topup"),
    path("success/", success, name="success"),
]
