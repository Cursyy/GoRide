from django.urls import path
from . import views

urlpatterns = [
    path('payment/<int:vehicle_id>/stripe/', views.stripe_payment, name='stripe_payment'),
    path('payment/<int:vehicle_id>/paypal/', views.paypal_payment, name='paypal_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
]