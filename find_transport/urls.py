from django.urls import path
from .views import find_transport

urlpatterns = [
    path("", find_transport, name="find_transport"),
]
