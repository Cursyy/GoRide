from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

# Create your views here.


def home(request):
    return render(request, "home.html")


def contacts(request):
    return render(request, "contacts.html")


@csrf_exempt
def save_location(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request.session["user_latitude"] = data.get("latitude")
        request.session["user_longitude"] = data.get("longitude")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)
