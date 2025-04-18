from django.urls import path

# from django.shortcuts import render
from . import views

app_name = "booking"

urlpatterns = [
    path("rent/<int:vehicle_id>/", views.rent_vehicle, name="rent_vehicle"),
    path("subscribe/<int:plan_id>/", views.subscribe, name="subscribe_plan"),
    path("topup/", views.top_up_wallet, name="topup"),
    path("success/<str:booking_id>/", views.booking_success, name="booking_success"),
]
