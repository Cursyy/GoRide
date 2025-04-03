from django.urls import path
from .views import get_places, get_route, map_view, get_address_marker, get_search

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
]
