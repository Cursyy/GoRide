# vouchers/views.py
import json
from django.utils import timezone
from django.http import JsonResponse
from .models import Voucher
from find_transport.models import Vehicle
from subscriptions.models import SubscriptionPlan

def voucher_apply(request):
    print(f"Request method: {request.method}, Body: {request.body}")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Parsed data:", data)
            vehicle_id = data.get("vehicle_id")
            code = data.get("code")
            now = timezone.now()
            type = data.get("type")
            subscription_id = data.get("subscription")

            voucher = Voucher.objects.get(code=code, active=True)
            if voucher.valid_from <= now <= voucher.valid_to and (voucher.used or 0) < (voucher.max_use or float('inf')):
                if type == "vehicle" and vehicle_id:
                    price = get_vehicle_price(vehicle_id, voucher.discount)
                    return JsonResponse({"price": price, "discount": voucher.discount}, status=200)
                elif type == "subscription" and subscription_id:
                    price = get_subscription_price(subscription_id, voucher.discount)
                    return JsonResponse({"price": price, "discount": voucher.discount}, status=200)
                else:
                    return JsonResponse({"error": "Invalid voucher type."}, status=400)
            else:
                return JsonResponse({"error": "Voucher expired or usage limit reached."}, status=400)
        except Voucher.DoesNotExist:
            return JsonResponse({"error": "Invalid voucher code."}, status=400)
        except Exception as e:
            print(f"Error in voucher_apply: {str(e)}")
            return JsonResponse({"error": "Server error."}, status=500)
    return JsonResponse({"error": "Invalid request."}, status=400)

def get_vehicle_price(vehicle_id, discount):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    return vehicle.price_per_hour - (vehicle.price_per_hour * discount / 100)

def get_subscription_price(subscription_id, discount):
    subscription = SubscriptionPlan.objects.get(id=subscription_id)
    return subscription.price - (subscription.price * discount / 100)