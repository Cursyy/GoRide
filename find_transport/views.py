from django.shortcuts import render
from .models import Vehicle
from django.http import JsonResponse


def find_transport(request):
    vehicles = Vehicle.objects.filter(status=True)
    vehicle_type = request.GET.get("type")
    min_battery = request.GET.get("min_battery")

    if vehicle_type:
        vehicles = vehicles.filter(type=vehicle_type)
    if min_battery:
        try:
            min_battery = int(min_battery)
            vehicles = vehicles.filter(battery_percentage__gte=min_battery)
        except ValueError:
            return JsonResponse({"error": "Invalid battery percentage"}, status=400)

    return render(request, "find_transport.html", {"vehicles": vehicles})
