from django.urls import path
from . import views
from events_near_me import views as events_views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("contacts/", views.contacts, name="contacts"),
    path("about/", views.about, name="about"),
    path("api/save_location/", views.save_location, name="save_location"),
    path("events_page/", events_views.events_page, name="events_page"),
]
