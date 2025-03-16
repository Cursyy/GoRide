from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('type','duration_days', 'price', 'max_ride_hours')

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription)
