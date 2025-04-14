from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("contacts/", views.contacts, name="contacts"),
    path("api/save_location/", views.save_location, name="save_location"),
]
