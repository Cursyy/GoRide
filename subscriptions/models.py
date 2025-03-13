from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        (1, _('Daily Subscription')),
        (7, _('Weekly Subscription')),
        (30, _('Monthly Subscription')),
    ]

    duration_days = models.IntegerField(choices=DURATION_CHOICES, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    max_rides = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.get_duration_days_display()

class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField(null=True, blank=True)
    remaining_rides = models.IntegerField(null=True, blank=True)

    def is_active(self):
        return self.end_date >= now()

    def renew(self):
        if self.plan:
            self.start_date = now()
            self.end_date = now() + timedelta(days=self.plan.duration_days)
            self.remaining_rides = self.plan.max_rides
            self.save()
