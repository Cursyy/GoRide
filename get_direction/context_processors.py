from .models import Trip


def active_trip(request):
    if request.user.is_authenticated:
        trip = Trip.objects.filter(user=request.user, status="active").first()
        return {"active_trip": trip}
    return {"active_trip": None}
