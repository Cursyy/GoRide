import json
import requests
from decouple import config
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from find_transport.views import get_address

GEOAPIFY_API_KEY = config("GEOAPIFY_API_KEY")


def get_places(request, lat, lon, category):
    url = f"https://api.geoapify.com/v2/places?apiKey={GEOAPIFY_API_KEY}"

    params = {
        "lat": lat,
        "lon": lon,
        "categories": category if category else None,
        "radius": 5000,
        "limit": 20,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return JsonResponse(
            {"error": "API request failed", "details": response.text},
            status=response.status_code,
        )
    response = response.json()
    return JsonResponse(response, safe=False)


@csrf_exempt
def get_route(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            waypoints = data.get("waypoints", [])
            if not waypoints or len(waypoints) < 2:
                return JsonResponse({"error": "Invalid waypoints"}, status=400)
            url = "https://api.geoapify.com/v1/routing"
            params = {
                "apiKey": GEOAPIFY_API_KEY,
                "waypoints": "|".join([f"{lat},{lon}" for lat, lon in waypoints]),
                "mode": "bicycle",
                "details": "route_details",
            }
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return JsonResponse(
                    {"error": "API request failed", "details": response.text},
                    status=response.status_code,
                )

            return JsonResponse(response.json(), safe=False)

        except Exception as e:
            return JsonResponse(
                {"error": "Invalid request", "details": str(e)}, status=400
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)


def get_address_marker(request, lat, lon):
    response = get_address(lat, lon)
    return HttpResponse(f"Address: {response}")


def map_view(request):
    return render(request, "get_direction/get_direction.html")
