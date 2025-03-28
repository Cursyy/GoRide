from django.contrib import admin

# Register your models here.
from .models import Booking

class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id','user','amount','status','created_at']
admin.site.register(Booking, BookingAdmin)