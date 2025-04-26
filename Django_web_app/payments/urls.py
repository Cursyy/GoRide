from django.urls import path
from . import views

app_name = 'payments'

# urlpatterns = [
#     path('booking/<int:vehicle_id>/', views.booking_view, name='booking'),
#     path('stripe_payment/<int:vehicle_id>/', views.stripe_payment, name='stripe_payment'),
#     path('payment/success/', views.payment_success, name='payment_success'),
# ]

urlpatterns = [
    path('stripe/<str:booking_id>/', views.process_stripe_payment, name='process_stripe_payment'),
    path('paypal/<str:booking_id>/', views.process_paypal_payment, name='process_paypal_payment'),
    path('paypal-execute/<str:booking_id>/', views.paypal_execute, name='paypal_execute'),
]