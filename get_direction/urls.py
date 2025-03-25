from django.urls import path
from .views import get_places, get_route, map_view

app_name = "get_direction"

urlpatterns = [
    path(
        "api/places/<str:category>/<str:lat>/<str:lon>/", get_places, name="get_places"
    ),
    path("api/route", get_route, name="get_route"),
    path("", map_view, name="map"),
]
