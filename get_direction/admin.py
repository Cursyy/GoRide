from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "user")
    list_filter = ["user", "status"]
    list_editable = ["status"]
    list_per_page = 50

    actions = ["mark_as_finished", "mark_as_started", "mark_as_paused"]

    @admin.action(description="Mark selected trips as started")
    def mark_as_available(self, request, queryset):
        queryset.update(status="active")

    @admin.action(description="Mark selected trips as paused")
    def mark_as_available(self, request, queryset):
        queryset.update(status="paused")

    @admin.action(description="Mark selected trips as ended")
    def mark_as_available(self, request, queryset):
        queryset.update(status="ended")
