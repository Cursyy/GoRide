from django.shortcuts import render
from .models import Vehicle, EVStation
from django.http import JsonResponse
import requests
from cache_manager import load_from_cache, save_to_cache


def get_address(lat, lon):
    cached_content = load_from_cache(lat, lon)
    if cached_content:
        return cached_content

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
        save_to_cache(lat, lon, content)
        print(f"Response from API: {content}")
        return content
    else:
        print(f"Error {response.status_code}: {response.text}")
        return "Address fetch failed"


def find_transport(request):
    return render(request, "find_transport.html")


def get_vehicles(request):
    vehicle_type = request.GET.get("type")
    min_battery = request.GET.get("min_battery")
    vehicles = Vehicle.objects.all()
    if vehicle_type:
        vehicles = vehicles.filter(type=vehicle_type)
    if min_battery:
        try:
            min_battery = int(min_battery)
            vehicles = vehicles.filter(battery_percentage__gte=min_battery)
        except ValueError:
            return JsonResponse({"error": "Invalid battery percentage"}, status=400)
    return JsonResponse(
        list(vehicles.values("id", "type", "battery_percentage", "price_per_hour")),
        safe=False,
    )


def get_station(request):
    stations_data = []
    for station in EVStation.objects.all():
        station_vehicle_count = Vehicle.objects.filter(station=station).count()
        stations_data.append(
            {
                "latitude": station.latitude,
                "longitude": station.longitude,
                "max_spaces": station.max_spaces,
                "free_spaces": station.max_spaces - station_vehicle_count,
                "address": get_address(station.latitude, station.longitude),
            }
        )
    return JsonResponse(list(stations_data), safe=False)
