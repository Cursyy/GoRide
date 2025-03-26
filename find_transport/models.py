from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class EVStation(models.Model):
    id = models.AutoField(primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    max_spaces = models.IntegerField()

    def __str__(self):
        return f"EVStation {self.id}"


class Vehicle(models.Model):
    TYPE_VEHICLE = [
        ("Bike", _("Bike")),
        ("E-Bike", _("E-Bike")),
        ("E-Scooter", _("E-Scooter")),
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
    station = models.ForeignKey(
        EVStation, on_delete=models.SET_NULL, blank=True, null=True, default=""
    )

    def clean(self):
        if self.type == "Bike":
            self.battery_percentage = None
        elif self.battery_percentage is None:
            raise ValidationError(
                "Battery percentage is required for E-Bike and E-Scooter"
            )
        elif not (0 <= self.battery_percentage <= 100):
            raise ValidationError("Battery percentage must be between 0 and 100")
        if (
            self.station
            and Vehicle.objects.filter(station=self.station).count()
            >= self.station.max_spaces
        ):
            raise ValidationError("Cannot add new vehicle. The station is full")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return super().__str__()