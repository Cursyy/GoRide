from django.contrib import admin
from .models import Vehicle, EVStation


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "battery_percentage", "status", "station")
    list_filter = ["type", "status"]
    list_editable = ["status"]
    list_per_page = 10
    list_max_show_all = 100

    actions = ["mark_as_available", "mark_as_unavailable"]

    @admin.action(description="Mark selected vehicles as available")
    def mark_as_available(self, request, queryset):
        queryset.update(status=True)

    @admin.action(description="Mark selected vehicles as unavailable")
    def mark_as_unavailable(self, request, queryset):
        queryset.update(status=False)


@admin.register(EVStation)
class EVStationAdmin(admin.ModelAdmin):
    list_display = ("latitude", "longitude", "max_spaces")
    list_filter = ["max_spaces"]
    list_per_page = 10
    list_max_show_all = 100
