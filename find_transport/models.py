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
