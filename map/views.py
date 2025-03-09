from django.shortcuts import render
from .models import EVStation


# Create your views here.
def index(request):
    stations = list(EVStation.objects.values("latitude", "longitude", "max_spaces"))
    context = {"stations": stations}
    return render(request, "map.html", context)
