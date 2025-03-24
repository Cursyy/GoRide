from django.urls import path
from . import views

urlpatterns = [
    path('booking/<int:vehicle_id>/', views.booking_view, name='booking'),
    path('payment/success/', views.payment_success, name='payment_success'),
]