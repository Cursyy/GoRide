from django.contrib import admin
from .models import Vehicle, EVStation


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("type", "battery_percentage", "status")
    list_filter = ["type", "status"]
    list_editable = ["status"]
    list_per_page = 10
    list_max_show_all = 100


@admin.register(EVStation)
class EVStationAdmin(admin.ModelAdmin):
    list_display = ("latitude", "longitude", "max_spaces")
    list_filter = ["max_spaces"]
    list_per_page = 10
    list_max_show_all = 100
