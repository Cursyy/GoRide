from django.shortcuts import render
from .models import Vehicle


def find_transport(request):
    vehicle_type = request.GET.get("type")
    min_battery = request.GET.get("min_battery")

    vehicles = Vehicle.objects.all()
    if vehicle_type:
        vehicles = vehicles.filter(type=vehicle_type)
    if min_battery:
        vehicles = vehicles.filter(battery_percentage__gte=min_battery)

    return render(request, "find_transport.html", {"vehicles": vehicles})
