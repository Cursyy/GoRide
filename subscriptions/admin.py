from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('type','duration_days', 'price')

class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date')

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
