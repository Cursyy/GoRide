from django.urls import path
from . import views

app_name = "careers"

urlpatterns = [
    path("", views.careers_view, name="apply"),
    path("thank-you/", views.careers_thank_you_view, name="thank_you"),
]