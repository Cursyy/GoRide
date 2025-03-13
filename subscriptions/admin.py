from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('duration_days', 'price', 'max_rides')

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription)
