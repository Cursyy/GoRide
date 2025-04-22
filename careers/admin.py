from django.contrib import admin
from .models import JobApplication

class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone", "position", "submitted_at")

admin.site.register(JobApplication, JobApplicationAdmin)