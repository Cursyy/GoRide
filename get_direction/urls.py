from django.urls import path
from .views import (
    get_places,
    get_route,
    map_view,
    get_address_marker,
    get_search,
    start_trip,
    pause_trip,
    resume_trip,
    end_trip,
    trip_status,
)

app_name = "get_direction"

urlpatterns = [
    path(
        "api/places/<str:category>/<str:lat>/<str:lon>/", get_places, name="get_places"
    ),
    path("api/route/", get_route, name="get_route"),
    path("", map_view, name="map"),
    path(
        "api/get_address_marker/<str:lat>/<str:lon>/",
        get_address_marker,
        name="get_address_marker",
    ),
    path("api/search/<str:searchInput>/", get_search, name="get_search"),
    path("api/start_trip/", start_trip, name="start_trip"),
    path("api/pause_trip/", pause_trip, name="pause_trip"),
    path("api/resume_trip/", resume_trip, name="resume_trip"),
    path("api/end_trip/", end_trip, name="end_trip"),
    path("api/trip_status/", trip_status, name="trip_status"),
]
