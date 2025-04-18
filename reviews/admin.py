from django.contrib import admin
from .models import Review

class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "rating", "created_at")

admin.site.register(Review, ReviewAdmin)