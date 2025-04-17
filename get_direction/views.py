from datetime import timedelta
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
from wallet.models import Wallet
from django.core.cache import cache
from avatar.models import UserAvatar
from stats.models import UserStatistics


GEOAPIFY_API_KEY = config("GEOAPIFY_API_KEY")


def get_places(request, lat, lon, category):
    cache_key = f"address_{lat}_{lon}_{category}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data, safe=False)

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
    cache.set(cache_key, response, timeout=60 * 60 * 24)  # one day cache
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

            cache_key = f"route_{json.dumps(waypoints)}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return JsonResponse(cached_data, safe=False)

            response = requests.get(url, params=params)
            if response.status_code != 200:
                return JsonResponse(
                    {"error": "API request failed", "details": response.text},
                    status=response.status_code,
                )
            response = response.json()
            cache.set(cache_key, response, timeout=60 * 60 * 24)
            return JsonResponse(response, safe=False)

        except Exception as e:
            return JsonResponse(
                {"error": "Invalid request", "details": str(e)}, status=400
            )

    return JsonResponse({"error": "Method not allowed"}, status=405)


def get_address_marker(request, lat, lon):
    response = get_address(lat, lon)
    return HttpResponse(f"Address: {response}")


def get_search(request, searchInput):
    cache_key = f"search_{searchInput}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data, safe=False)
    url = f"https://api.geoapify.com/v1/geocode/search?text={searchInput}&format=json&filter=countrycode:ie&apiKey={GEOAPIFY_API_KEY}"

    response = requests.get(url)

    print(response)
    if response.status_code != 200:
        return JsonResponse(
            {"error": "API request failed", "details": response.text},
            status=response.status_code,
        )
    response = response.json()
    cache.set(cache_key, response, timeout=60 * 60 * 24)
    return JsonResponse(response, safe=False)


def map_view(request):
    return render(request, "get_direction/get_direction.html")


@login_required
def start_trip(request):
    user = request.user
    print(f"API: start_trip called for user: {user}")
    trip = Trip.objects.filter(user=user, status="not_started").order_by("-id").first()
    if not trip:
        print("API start_trip: No trip with status 'not_started' found to start")
        active_trip = Trip.objects.filter(user=user, status="active").first()
        if active_trip:
            print(f"API start_trip: User already has an active trip: {active_trip.id}")
            notify_trip_status(user)
            return JsonResponse(
                {"error": "An active trip is already in progress"}, status=400
            )
        return JsonResponse({"error": "No suitable trip found to start"}, status=404)

    trip.status = "active"
    trip.started_at = timezone.now()
    trip.total_travel_time = timedelta(seconds=0)
    trip.save()

    notify_trip_status(user)

    print(f"API start_trip: Trip started successfully: {trip.id}")
    return JsonResponse(
        {
            "trip_id": trip.id,
            "started_at": trip.started_at.isoformat(),
            "status": "active",
        },
        status=200,
    )


@login_required
def pause_trip(request):
    user = request.user
    print(f"Pausing trip for user: {user}")
    trip = Trip.objects.filter(user=user, status="active").first()
    if trip:
        trip.status = "paused"
        trip.paused_at = timezone.now()

        if trip.started_at:
            trip.total_travel_time += trip.paused_at - trip.started_at

        trip.started_at = None
        trip.save()
        notify_trip_status(user)
        print(f"Trip paused: {trip.id}")
        return JsonResponse({"status": "paused", "trip_id": trip.id})
    else:
        print("No active trip found to pause")
        return JsonResponse({"error": "No active trip found"}, status=404)


@login_required
def resume_trip(request):
    user = request.user
    print(f"Resuming trip for user: {user}")
    trip = Trip.objects.filter(user=user, status="paused").first()
    if trip:
        trip.status = "active"
        trip.started_at = timezone.now()
        pause_delta = timezone.now() - trip.paused_at
        pause_minutes = Decimal(pause_delta.total_seconds() / 60)
        trip.pause_duration += pause_minutes
        trip.paused_at = None
        trip.save()
        notify_trip_status(user)
        print(f"Trip resumed: {trip.id}")
        return JsonResponse({"status": "resumed", "trip_id": trip.id})
    else:
        print("No paused trip found to resume")
        return JsonResponse({"error": "No paused trip found"}, status=404)


@login_required
def end_trip(request):
    user = request.user
    print(f"Ending trip for user: {user}")
    trip = Trip.objects.filter(user=user, status="active").first()
    if trip:
        trip.status = "finished"
        trip.ended_at = timezone.now()

        if trip.started_at:
            trip.total_travel_time += trip.ended_at - trip.started_at

        total_minutes = trip.total_travel_time.total_seconds() / 60
        trip.total_amount = (Decimal(total_minutes) * trip.cost_per_minute) + (
            trip.pause_duration * trip.cost_per_minute / 2
        )
        charge = trip.prepaid_minutes * trip.cost_per_minute - trip.total_amount
        wallet = Wallet.objects.get(user=user)
        print(wallet.balance)
        wallet.top_up(charge)
        print(wallet.balance)
        trip.save()

        try:
            stats = UserStatistics.objects.get(user=user)
        except UserStatistics.DoesNotExist:
            stats = UserStatistics.objects.create(user=user)

        duration_hours = total_minutes / 60
        vehicle_type = trip.booking.vehicle.type if trip.booking and trip.booking.vehicle else "E-Scooter"
        stats.update_stats(duration_hours, trip.total_amount, vehicle_type)

        new_badges = stats.get_badges()

        try:
            avatar = UserAvatar.objects.get(user=user)
        except UserAvatar.DoesNotExist:
            avatar = UserAvatar.objects.create(user=user)
        new_items = avatar.check_and_unlock_items()

        if new_badges or new_items:
            notifications = []
            for badge in new_badges:
                notifications.append({
                    'type': 'badge',
                    'name': badge.name,
                    'image': badge.image.url if badge.image else '', 
                })
            for item in new_items:
                notifications.append({
                    'type': 'item',
                    'name': item.name,
                    'image': item.image.url,
                })

            channel_layer = get_channel_layer()
            group_name = f"user_{user.user_id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "rewards_notification",
                    "data": notifications,
                }
            )

        notify_trip_status(user)
        print(f"Trip ended: {trip.id}, Total cost: {trip.total_amount}")
        return JsonResponse(
            {
                "status": "finished",
                "trip_id": trip.id,
                "total_cost": str(trip.total_amount),
                "show_review_popup": True,
            }
        )

    else:
        print("No active trip found to end")
        return JsonResponse({"error": "No active trip found"}, status=404)


def notify_trip_status(user):
    channel_layer = get_channel_layer()
    trip = (
        Trip.objects.filter(user=user, status__in=["active", "paused"])
        .order_by("-id")
        .first()
    )

    if trip:
        current_server_time_seconds = 0
        if trip.status == "active" and trip.started_at:
            if hasattr(trip, "trip_current_time"):
                current_server_time_seconds = trip.trip_current_time.total_seconds()
            else:
                current_server_time_seconds = (
                    trip.total_travel_time.total_seconds()
                    + (timezone.now() - trip.started_at).total_seconds()
                )
        else:
            current_server_time_seconds = trip.total_travel_time.total_seconds()

        data = {
            "status": trip.status,
            "started_at": trip.started_at.isoformat() if trip.started_at else None,
            "paused_at": trip.paused_at.isoformat() if trip.paused_at else None,
            "total_travel_time": trip.total_travel_time.total_seconds(),
            "server_time": current_server_time_seconds,
            "trip_id": trip.id,
        }
        print(f"Notify: Preparing status update for trip {trip.id}: {data}")
    else:
        last_finished = (
            Trip.objects.filter(user=user, status="finished")
            .order_by("-ended_at", "-id")
            .first()
        )
        if last_finished:
            data = {
                "status": "finished",
                "trip_id": last_finished.id,
                "ended_at": last_finished.ended_at.isoformat()
                if last_finished.ended_at
                else None,
                "total_travel_time": last_finished.total_travel_time.total_seconds(),
                "total_cost": str(last_finished.total_amount)
                if last_finished.total_amount is not None
                else None,
                "show_review_popup": True,
            }
            print(
                f"Notify: No active/paused trip found for user {user.user_id}, sending last finished."
            )
        else:
            data = {"status": "none", "message": "No relevant trip found."}
            print(f"Notify: No active/paused/finished trip found for user {user.id}")

    group_name = f"user_{user.pk}"
    print(f"Notify: Sending to group: {group_name} data: {data}")

    try:
        async_to_sync(channel_layer.group_send)(
            group_name, {"type": "trip_status_update", "data": data}
        )
        print(f"Notify: Message sent successfully to group {group_name}")
    except Exception as e:
        print(f"ERROR: Could not send message to group {group_name}: {e}")


def end_active_trip(user):
    active_trip = Trip.objects.filter(user=user).exclude(status="finished").last()
    if active_trip:
        if active_trip.status == "active" and active_trip.started_at:
            active_trip.total_travel_time += timezone.now() - active_trip.started_at
        active_trip.status = "finished"
        active_trip.ended_at = timezone.now()
        active_trip.save()
