from decimal import Decimal
from django.utils import timezone
import json
import requests
from decouple import config
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from find_transport.views import get_address
from .models import Trip
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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


def get_search(request, searchInput):
    url = f"https://api.geoapify.com/v1/geocode/search?text={searchInput}&format=json&filter=countrycode:ie&apiKey={GEOAPIFY_API_KEY}"

    response = requests.get(url)

    print(response)
    if response.status_code != 200:
        return JsonResponse(
            {"error": "API request failed", "details": response.text},
            status=response.status_code,
        )
    response = response.json()
    return JsonResponse(response, safe=False)


def map_view(request):
    return render(request, "get_direction/get_direction.html")


@login_required
def start_trip(request):
    user = request.user
    trip = Trip.objects.filter(user=user, status="not_started").first()
    notify_trip_status(user)
    if not trip:
        return JsonResponse({"error": "No trip to start"}, status=400)

    trip.status = "active"
    trip.started_at = timezone.now()
    trip.save()
    return JsonResponse({"trip_id": trip.id, "started_at": trip.started_at})


@login_required
def pause_trip(request):
    user = request.user
    trip = Trip.objects.filter(user=user, status="active").first()
    notify_trip_status(user)
    if trip:
        trip.status = "paused"
        trip.paused_at = timezone.now()
        trip.total_travel_time += timezone.now() - trip.started_at
        trip.save()
        return JsonResponse({"status": "paused", "trip_id": trip.id})
    else:
        return JsonResponse({"error": "No active trip found"}, status=404)


@login_required
def resume_trip(request):
    user = request.user
    trip = Trip.objects.filter(user=user, status="paused").first()
    notify_trip_status(user)
    if trip:
        trip.status = "active"
        trip.started_at = timezone.now()
        trip.paused_at = None
        trip.save()
        return JsonResponse({"status": "resumed", "trip_id": trip.id})
    else:
        return JsonResponse({"error": "No paused trip found"}, status=404)


@login_required
def end_trip(request):
    user = request.user
    trip = Trip.objects.filter(user=user, status="active").first()
    notify_trip_status(user)
    if trip:
        trip.status = "finished"
        trip.ended_at = timezone.now()
        trip.total_travel_time += timezone.now() - trip.started_at
        total_minutes = trip.total_travel_time.total_seconds() / 60
        trip.total_amount = Decimal(total_minutes) * trip.cost_per_minute
        trip.save()
        return JsonResponse(
            {"status": "ended", "trip_id": trip.id, "total_cost": trip.total_amount}
        )
    else:
        return JsonResponse({"error": "No active trip found"}, status=404)


def notify_trip_status(user):
    channel_layer = get_channel_layer()
    trip = Trip.objects.filter(user=user, status__in=["active", "paused"]).first()
    data = (
        {
            "status": trip.status,
            "started_at": trip.started_at.isoformat(),
            "paused_at": trip.paused_at.isoformat() if trip.paused_at else None,
            "total_travel_time": trip.total_travel_time.total_seconds(),
        }
        if trip
        else {"status": "none"}
    )

    async_to_sync(channel_layer.group_send)(
        f"user_{user.user_id}", {"type": "trip_status_update", "data": data}
    )
