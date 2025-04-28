from django.urls import path
from .views import events_page, get_default_events, search_events_near_location

app_name = "events"
urlpatterns = [
    path("", events_page, name="events_page"),  # Сторінка HTML
    path(
        "api/search/default/", get_default_events, name="get_default_events_api"
    ),  # API для дефолтних подій
    path(
        "api/search/nearby/",
        search_events_near_location,
        name="search_nearby_events_api",
    ),  # API для пошуку за локацією
]
