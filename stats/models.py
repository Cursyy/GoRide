from django.db import models
from django.conf import settings
from decimal import Decimal

class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='badges/', blank=True, null=True)
    condition = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

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
    earned_badges = models.ManyToManyField(Badge, blank=True)

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

    def get_all_badges(self):
        return self.earned_badges.all()

    def get_badges(self):
        old_badges = set(self.earned_badges.values_list('name', flat=True))

        all_badges = Badge.objects.all()
        new_badges = []

        for badge in all_badges:
            if badge.name in old_badges:
                continue

            condition = badge.condition.split("__")
            if len(condition) != 2:
                print(f"Invalid condition format for badge {badge.name}")
                continue

            condition_type, condition_value = condition[0], int(condition[1])
            condition_met = False

            if condition_type == "total_rides" and self.total_rides >= condition_value:
                condition_met = True
            elif condition_type == "all_bikes_rides" and self.bike_rides + self.ebike_rides >= condition_value:
                condition_met = True
            elif condition_type == "scooter_rides" and self.scooter_rides >= condition_value:
                condition_met = True
            elif condition_type == "total_hours" and self.total_hours >= condition_value:
                condition_met = True
            elif condition_type == "total_spent" and self.total_spent >= condition_value:
                condition_met = True
            elif condition_type == "most_used_vehicle_bike" and self.most_used_vehicle == "Bike" and self.total_rides >= condition_value:
                condition_met = True

            if condition_met:
                self.earned_badges.add(badge)
                new_badges.append(badge)

        self.save()
        return new_badges

    def __str__(self):
        return f"Stats for {self.user.username}"