from django.urls import path
from .views import RentalBookingCreateView, SubscriptionBookingCreateView
from django.shortcuts import render

app_name = 'booking'

urlpatterns = [
    path('rent/<int:vehicle_id>/', RentalBookingCreateView.as_view(), name='rent_vehicle'),
    path('subscribe/<int:plan_id>/', SubscriptionBookingCreateView.as_view(), name='subscribe_plan'),
    path('success/', lambda request: render(request, 'booking/success.html'), name='booking_success'),
]