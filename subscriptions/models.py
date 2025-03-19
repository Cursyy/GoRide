from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from find_transport.models import Vehicle

class SubscriptionPlan(models.Model):
    TYPE_CHOICES = [
        ("Daily", _('Daily Subscription')),
        ("Weekly", _('Weekly Subscription')),
        ("Monthly", _('Monthly Subscription')),
        ("Student", _('Student')),
        ("Athlete", _('Athlete')),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, unique=True, null=True, blank=True)
    duration_days = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    max_ride_hours = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.type

class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True)
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

    def activate(self, plan):
        self.plan = plan
        self.start_date = now()
        self.end_date = now() + timedelta(days=self.plan.duration_days)
        self.remaining_rides = self.plan.max_ride_hours if self.plan.max_ride_hours else None
        self.is_paid = True
        self.save()
