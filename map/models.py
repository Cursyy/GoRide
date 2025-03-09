from django.db import models


class EVStation(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    max_spaces = models.IntegerField()

    def __str__(self):
        return super().__str__() + f" ({self.latitude}, {self.longitude})"
