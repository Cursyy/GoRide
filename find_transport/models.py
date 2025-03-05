from django.db import models


class Vehicle(models.Model):
    TYPE_VEHICLE = [
        ("Bike", "Bike"),
        ("E-Bike", "E-Bike"),
        ("E-Scooter", "E-Scooter"),
    ]

    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=TYPE_VEHICLE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.BooleanField(default=True)
    battery_percentage = models.IntegerField()
    price_per_hour = models.FloatField()

    def __str__(self):
        return super().__str__()

class Booking(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    total_price =models.FloatField()
    hours = models.PositiveIntegerField()
    ordered_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.hours * self.vehicle.price_per_hour
        super().save(*args, **kwargs)

    def __str__(self):
        return f"renting  {self.vehicle.type}"    