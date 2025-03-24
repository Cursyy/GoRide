import json
from django.utils import timezone
from django.http import JsonResponse

# from django.views.decorators.http import require_POST
from .models import Voucher
from find_transport.models import Vehicle
from subscriptions.models import SubscriptionPlan


def voucher_apply(request):
    print(request)
    if request.method == "POST":
        data = json.loads(request.body)
        print("Request body:", data)
        vehicle_id = data.get("vehicle_id") or None
        code = data.get("code")
        user = request.user.user_id
        now = timezone.now()
        type = data.get("type")
        subscription_id = data.get("subscription") or None
        try:
            voucher = Voucher.objects.get(code=code)
            if voucher.valid_from <= now <= voucher.valid_to:
                if not type or voucher.voucher_type != type:
                    return JsonResponse({"error": "Invalid voucher type."}, status=400)
                elif type == "vehicle":
                    if vehicle_id is not None:
                        price = get_vehicle_price(vehicle_id, voucher.discount)
                        voucher.used = (voucher.used or 0) + 1
                        voucher.save()
                        return JsonResponse({"price": price}, status=200)
                elif type == "subscription":
                    if user is not None:
                        price = get_subscription_price(
                            subscription_id, voucher.discount
                        )
                        voucher.used = (voucher.used or 0) + 1
                        voucher.save()
                        return JsonResponse({"price": price}, status=200)
            else:
                return JsonResponse(
                    {"error": "Voucher expired or invalid."}, status=400
                )
        except Voucher.DoesNotExist:
            return JsonResponse({"error": "Invalid voucher code."}, status=400)
    return JsonResponse({"error": "Invalid request."}, status=400)


def get_vehicle_price(vehicle_id, discount):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    price = vehicle.price_per_hour
    price = price - (price * discount / 100)
    return price


def get_subscription_price(subscription_id, discount):
    subscription = SubscriptionPlan.objects.get(id=subscription_id)
    price = subscription.price
    price = price - (price * discount / 100)
    return price
