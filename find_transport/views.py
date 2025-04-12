from django.shortcuts import render
from .models import Vehicle, EVStation
from django.http import JsonResponse
import requests
from django.db.models import Count
from django.forms.models import model_to_dict
from decouple import config
from vouchers.views import voucher_apply
from django.contrib.auth.decorators import login_required
from django.core.cache import cache


def get_address(lat, lon):
    cache_key = f"address_{lat}_{lon}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return " ".join(cached_data)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML,like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36 GoRide/1.0 "
        "(san4ez.4otkuy@gmail.com)"
    }

    response = requests.get(
        f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}",
        headers=headers,
    )

    if response.status_code == 200:
        data = response.json()
        content = (
            data.get("address", {}).get("road")
            + ", "
            + data.get("address", {}).get("postcode"),
        )
        cache.set(cache_key, content, timeout=60 * 60 * 24 * 30)  # one month cache
        print(f"Response from API: {content}")
        return " ".join(content)
    else:
        print(f"Error {response.status_code}: {response.text}")
        return "Address fetch failed"


@login_required
def find_transport(request):
    return render(request, "find_transport.html")


def get_vehicles(request):
    vehicle_type = request.GET.get("type")
    min_battery = request.GET.get("min_battery")
    vehicles = Vehicle.objects.filter(status=True)
    if vehicle_type:
        vehicles = vehicles.filter(type=vehicle_type)
    if min_battery:
        try:
            min_battery = int(min_battery)
            vehicles = vehicles.filter(battery_percentage__gte=min_battery)
        except ValueError:
            return JsonResponse({"error": "Invalid battery percentage"}, status=400)
    return JsonResponse(
        list(
            vehicles.values(
                "id", "type", "battery_percentage", "price_per_hour", "station_id"
            )
        ),
        safe=False,
    )


def get_station(request):
    station_id = request.GET.get("id")
    cache_key = f"station_{station_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse({"station": model_to_dict(cached_data)})

    if station_id and not station_id.isdigit():
        return JsonResponse({"error": "Invalid ID"}, status=404)

    if station_id:
        station = EVStation.objects.filter(id=station_id).first()
        if station:
            cache.set(cache_key, station, timeout=60 * 10)
            return JsonResponse({"station": model_to_dict(station)})
        return JsonResponse({"error": "Station not found"}, status=404)
    cache_key = f"stations"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data, safe=False)
    stations = EVStation.objects.annotate(vehicle_count=Count("vehicle"))

    stations_data = [
        {
            "id": station.id,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "max_spaces": station.max_spaces,
            "free_spaces": station.max_spaces - station.vehicle_count,
            "address": get_address(station.latitude, station.longitude),
        }
        for station in stations
    ]
    cache.set(cache_key, stations_data, timeout=60 * 10)
    return JsonResponse(stations_data, safe=False)


def get_direction(request, station_id, lon, lat):
    cache_key = f"direction_{lat}_{lon}_{station_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)
    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
    }
    api_key = config("OPENROUTE_API_KEY")

    station = EVStation.objects.filter(id=station_id).first()
    start = f"{lon},{lat}"
    end = f"{station.longitude},{station.latitude}"
    url = f"https://api.openrouteservice.org/v2/directions/foot-walking?api_key={api_key}&start={start}&end={end}"
    if station_id and lon and lat:
        call = requests.get(f"{url}", headers=headers)
        if call.is_redirect or call.status_code == 301:
            call = request.get(call.headers["Location"], headers=headers)
        if call.status_code != 200:
            return JsonResponse(
                {"error": "API request failed", "details": call.text},
                status=call.status_code,
            )

        response = call.json()
        cache.set(cache_key, response, timeout=60 * 60 * 24)  # one day cache
        return JsonResponse(response, safe=False)


def get_voucher(request):
    print("Request body:", request.body)
    return voucher_apply(request)
