from django.contrib import admin

# Register your models here.

from .models import Badge, UserStatistics

class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'condition')

admin.site.register(Badge, BadgeAdmin)
admin.site.register(UserStatistics)