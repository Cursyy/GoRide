from django import views
from django.urls import path
from .views import find_transport, checkout

app_name = "find_transport"

urlpatterns = [
    path("", find_transport, name="find_transport"),
    path("", checkout, name='checkout'),
]
