import requests
from decouple import config
from django.http import JsonResponse
from django.shortcuts import render

GEOAPIFY_API_KEY = config("GEOAPIFY_API_KEY")


def get_places(request, lat, lon, category):
    # lat = request.GET.get("lat")
    # lon = request.GET.get("lon")
    # query = request.GET.get("query")
    # category = request.GET.get("category")

    url = f"https://api.geoapify.com/v2/places?apiKey={GEOAPIFY_API_KEY}"

    params = {
        "lat": lat,
        "lon": lon,
        "categories": category if category else None,
        # "text": query if query else None,
        "radius": 5000,
        "limit": 20,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return JsonResponse(
            {"error": "API request failed", "details": response.text},
            status=response.status_code,
        )
    if response.status_code != 200:
        return JsonResponse(
            {"error": "API request failed", "details": response.text},
            status=response.status_code,
        )
    response = response.json()
    return JsonResponse(response, safe=False)


def get_route(request):
    waypoinst = request.GET.get("waypoints")
    units = request.GET.get("units")

    url = f"https://api.geoapify.com/v2/places?apiKey={GEOAPIFY_API_KEY}"

    params = {
        "waypoinst": "|".join(waypoinst),
        "mode": "bicyle",
        "units": units if units else "metric",
        "details": "route_details",
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return JsonResponse(
            {"error": "API request failed", "details": response.text},
            status=response.status_code,
        )
    return JsonResponse(response.json(), safe=False)


def map_view(request):
    return render(request, "get_direction/get_direction.html")
