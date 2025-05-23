from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from reviews.models import Review
from stats.views import stats

# Create your views here.


def home(request):
    recent_reviews = Review.objects.all().order_by("-created_at")[:6]

    context = {
        "recent_reviews": recent_reviews,
    }
    context.update(stats(request))
    return render(request, "home.html", context)


def contacts(request):
    return render(request, "contacts.html")

def about(request):
    return render(request, "about.html")


@csrf_exempt
def save_location(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request.session["user_latitude"] = data.get("latitude")
        request.session["user_longitude"] = data.get("longitude")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)
