from django.urls import path
from .views import find_transport, get_vehicles, get_station, get_direction

app_name = "find_transport"

urlpatterns = [
    path("", find_transport, name="find_transport"),
    path("api/vehicles", get_vehicles, name="get_vehicles"),
    path("api/stations", get_station, name="get_station"),
    path(
        "api/get_direction/<int:station_id>/<str:lon>/<str:lat>/",
        get_direction,
        name="get_direction",
    ),
]
