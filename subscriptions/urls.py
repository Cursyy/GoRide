from django.urls import path
from .views import subscription_plans, subscribe_user, subscription_success

urlpatterns = [
    path('plans/', subscription_plans, name='subscription_plans'),
    path('subscribe/<int:plan_id>/', subscribe_user, name='subscribe_user'),
    path('success/', subscription_success, name='subscription_success'),
]
