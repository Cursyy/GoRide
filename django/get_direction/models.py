from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Route(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="routes")
    name = models.CharField(max_length=255)
    points = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Trip(models.Model):
    STATUS_CHOICES = (
        ("not_started", "Not started"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("finished", "Finished"),
    )
    booking_id = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_started"
    )
    prepaid_minutes = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    total_travel_time = models.DurationField(default=timedelta(0))
    ended_at = models.DateTimeField(null=True, blank=True)
    cost_per_minute = models.DecimalField(
        null=True, blank=True, max_digits=4, decimal_places=2
    )
    total_amount = models.DecimalField(
        null=True, blank=True, max_digits=10, decimal_places=2
    )
    pause_duration = models.DecimalField(
        default=0, blank=True, max_digits=10, decimal_places=2
    )

    def __str__(self):
        return f"Trip #{self.id} by {self.user}"

    @property
    def trip_current_time(self):
        if self.status == "active" and self.started_at:
            current_time = self.total_travel_time + (timezone.now() - self.started_at)
            print("Trip current time:", current_time)
            return current_time
        return self.total_travel_time
