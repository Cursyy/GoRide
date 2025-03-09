from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


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
    battery_percentage = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    price_per_hour = models.FloatField()

    def clean(self):
        if self.type == "Bike":
            self.battery_percentage = None
        elif self.battery_percentage is None:
            raise ValidationError(
                "Battery percentage is required for E-Bike and E-Scooter"
            )
        elif not (0 <= self.battery_percentage <= 100):
            raise ValidationError("Battery percentage must be between 0 and 100")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return super().__str__()


class EVStation(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    max_spaces = models.IntegerField()

    def __str__(self):
        return super().__str__() + f" ({self.latitude}, {self.longitude})"
