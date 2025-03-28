from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('booking/<int:vehicle_id>/', views.booking_view, name='booking'),
    path('stripe_payment/<int:vehicle_id>/', views.stripe_payment, name='stripe_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
]