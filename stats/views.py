from django.shortcuts import render
from django.conf import settings
from get_direction.models import Trip
from reviews.models import Review
from django.db.models import Count, Avg
from accounts.models import CustomUser


def stats(request):
    total_users = CustomUser.objects.filter(is_active=True).count()
    total_trips = Trip.objects.filter(status='finished').count()
    average_rating = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 1)

    return {
        'total_users': total_users,
        'total_trips': total_trips,
        'average_rating': average_rating,
    }