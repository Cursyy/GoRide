from decimal import Decimal
from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class SubscriptionPlan(models.Model):
    TYPE_CHOICES = [
        ("Daily", _("Daily Subscription")),
        ("Weekly", _("Weekly Subscription")),
        ("Monthly", _("Monthly Subscription")),
        ("Student", _("Student")),
        ("Athlete", _("Athlete")),
    ]
    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, unique=True, null=True, blank=True
    )
    duration_days = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    max_ride_hours = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.type


class UserSubscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField(null=True, blank=True)
    remaining_rides = models.IntegerField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def is_active(self):
        return self.is_paid and self.end_date >= now()

    def can_use_vehicle(self, vehicle):
        if self.plan and self.plan.type == "Athlete" and vehicle.type != "Bike":
            return False
        return True

    def has_time(self):
        if self.plan and self.remaining_rides > 0:
            return True
        return False

    def progress_remaining(self):
        if not self.end_date:
            return 0
        total_hours = (self.end_date - self.start_date).total_seconds() / 3600
        elapsed_hours = (now() - self.start_date).total_seconds() / 3600
        if total_hours <= 0:
            return 0
        percentage = ((total_hours - elapsed_hours) / total_hours) * 100
        return max(0, min(percentage, 100))

    def activate(self, plan):
        self.plan = plan
        self.start_date = now()
        self.end_date = now() + timedelta(days=self.plan.duration_days)
        self.remaining_rides = (
            self.plan.max_ride_hours if self.plan.max_ride_hours else None
        )
        self.is_paid = True
        self.save()


class UserStatistics(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True
    )
    total_rides = models.IntegerField(default=0)
    total_hours = models.FloatField(default=0.0)
    total_spent = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    bike_rides = models.IntegerField(default=0)
    scooter_rides = models.IntegerField(default=0)
    ebike_rides = models.IntegerField(default=0)
    most_used_vehicle = models.CharField(max_length=10, null=True, blank=True)

    def update_stats(self, duration_hours, cost, vehicle_type):
        self.total_rides += 1
        self.total_hours += duration_hours
        self.total_spent += (
            Decimal(cost) if isinstance(cost, str) else Decimal(str(cost))
        )
        if vehicle_type == "Bike":
            self.bike_rides += 1
        elif vehicle_type == "E-Scooter":
            self.scooter_rides += 1
        else:
            self.ebike_rides += 1
        most_used = max(self.bike_rides, self.scooter_rides, self.ebike_rides)
        if most_used == self.bike_rides:
            self.most_used_vehicle = "Bike"
        elif most_used == self.scooter_rides:
            self.most_used_vehicle = "E-Scooter"
        else:
            self.most_used_vehicle = "E-Bike"

        self.save()

    def get_badges(self):
        badges = []
        if self.total_rides >= 1:
            badges.append(
                {"name": "Beginner", "src": "/static/images/badges/beginner.png"}
            )
        if self.bike_rides + self.ebike_rides >= 20:
            badges.append(
                {"name": "Bike Lover", "src": "/static/images/badges/bike_lover.png"}
            )
        if self.scooter_rides >= 30:
            badges.append(
                {
                    "name": "Scooter Enthusiast",
                    "src": "/static/images/badges/scooter_ent.png",
                }
            )
        if self.total_hours >= 100:
            badges.append(
                {
                    "name": "Marathon Rider",
                    "src": "/static/images/badges/marathon_rider.png",
                }
            )
        if self.total_spent >= 200:
            badges.append(
                {"name": "Big Spender", "src": "/static/images/badges/big_spender.png"}
            )
        if self.total_rides >= 50 and self.most_used_vehicle == "Bike":
            badges.append(
                {"name": "Eco Warrior", "src": "/static/images/badges/eco_warrior.png"}
            )

        return badges

    def __str__(self):
        return f"Stats for {self.user.username}"
