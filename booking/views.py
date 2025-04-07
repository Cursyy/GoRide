from datetime import timedelta
import json
from django.shortcuts import render, redirect
from .models import Booking
from subscriptions.models import UserSubscription, SubscriptionPlan, UserStatistics
from find_transport.models import Vehicle
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from successful_booking import send_transaction_email
from vouchers.models import Voucher
from get_direction.models import Trip
from get_direction.views import end_active_trip, start_trip


def rent_vehicle(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)

    if not vehicle.status:
        return redirect("find_transport:find_transport")

    subscription = None
    try:
        user_subscription = UserSubscription.objects.get(user=request.user)
        if user_subscription.is_active() and user_subscription.can_use_vehicle(vehicle):
            subscription = user_subscription
    except UserSubscription.DoesNotExist:
        pass

    if request.method == "POST":
        hours = int(request.POST.get("hours", 0))
        payment_type = request.POST.get("payment_type")
        voucher_code = request.POST.get("voucher_code", None)

        total_amount = vehicle.price_per_hour * hours

        if voucher_code:
            try:
                voucher = Voucher.objects.get(code=voucher_code, active=True)
                if voucher.valid_from <= timezone.now() <= voucher.valid_to and (
                    voucher.used or 0
                ) < (voucher.max_use or float("inf")):
                    total_amount -= total_amount * voucher.discount / 100
                    voucher.used = (voucher.used or 0) + 1
                    voucher.save()
                    if payment_type == "Subscription":
                        payment_type = "Stripe"
            except Voucher.DoesNotExist:
                return redirect("rent_vehicle", vehicle_id=vehicle_id)

            if payment_type == "Subscription" and not voucher_code:
                if subscription:
                    if subscription.remaining_rides is None:
                        total_amount = 0
                    elif subscription.remaining_rides == 0:
                        return redirect("rent_vehicle", vehicle_id=vehicle_id)
                    elif subscription.remaining_rides < hours:
                        return redirect("rent_vehicle", vehicle_id=vehicle_id)
                    else:
                        total_amount = 0
                        subscription.remaining_rides -= hours
                        subscription.save()
                else:
                    return redirect("rent_vehicle", vehicle_id=vehicle_id)
                total_amount = 0

        payment_success = True
        if payment_success:
            booking = Booking.objects.create(
                user=request.user,
                vehicle=vehicle,
                payment_type=payment_type,
                subject="Rent",
                amount=Decimal(str(total_amount)),
                hours=hours,
                status="Paid",
                created_at=timezone.now(),
                voucher=voucher_code if voucher_code else None,
            )

            if payment_type == "Subscription":
                subscription.remaining_rides -= hours
                subscription.save()

            vehicle.status = False
            vehicle.save()

            try:
                stats = UserStatistics.objects.get(user=request.user)
            except UserStatistics.DoesNotExist:
                stats = UserStatistics.objects.create(user=request.user)
            stats.update_stats(hours, total_amount, vehicle.type)

            transaction_data = {
                "transaction_id": booking.booking_id,
                "date": booking.booking_date,
                "time": booking.created_at,
                "amount": booking.amount,
                "payment_method": booking.payment_type,
                "payment_subject": booking.subject,
                "rental_item": booking.vehicle.type if booking.vehicle else None,
                "duration": booking.hours,
            }
            minutes_paid = hours * 60
            end_active_trip(request.user)
            print(f"Previous trip ended (if any) for user: {request.user}")
            try:
                new_trip = Trip.objects.create(
                    user=request.user,
                    prepaid_minutes=minutes_paid,
                    cost_per_minute=Decimal(vehicle.price_per_hour) / 60,
                    status="not_started",
                    total_travel_time=timedelta(seconds=0),
                )
                print(
                    f"New trip created (id: {new_trip.id}) for user: {request.user}. Attempting auto-start..."
                )

                start_response = start_trip(request)

                try:
                    start_data = json.loads(start_response.content)
                except json.JSONDecodeError:
                    start_data = {}

                if start_response.status_code == 200 and "trip_id" in start_data:
                    print(
                        f"Auto-start successful for trip id: {start_data.get('trip_id')}"
                    )

                    send_transaction_email(
                        request, request.user, request.user.email, transaction_data
                    )
                    return redirect("booking:booking_success")
                else:
                    print(
                        f"Error during auto-start for newly created trip {new_trip.id}. Response: {start_response.content}"
                    )

                    error_message = start_data.get(
                        "error", "Failed to auto-start the trip after creation."
                    )

                    return JsonResponse(
                        {"error": error_message},
                        status=start_response.status_code or 400,
                    )

            except Exception as e:
                print(f"Error creating trip for user {request.user}: {e}")
                return JsonResponse({"error": "Failed to create the trip."}, status=500)

    return render(
        request,
        "rental_booking.html",
        {"vehicle": vehicle, "subscription": subscription},
    )


def subscribe(request, plan_id):
    plan = SubscriptionPlan.objects.get(id=plan_id)
    try:
        user_subscription = UserSubscription.objects.get(user=request.user)
        if user_subscription.is_active():
            return redirect("main:home")
    except UserSubscription.DoesNotExist:
        pass

    if request.method == "POST":
        payment_type = request.POST.get("payment_type")
        voucher_code = request.POST.get("voucher", "")

        total_amount = plan.price

        if voucher_code:
            try:
                voucher = Voucher.objects.get(code=voucher_code, active=True)
                if voucher.valid_from <= timezone.now() <= voucher.valid_to and (
                    voucher.used or 0
                ) < (voucher.max_use or float("inf")):
                    total_amount -= total_amount * voucher.discount / 100
                    voucher.used = (voucher.used or 0) + 1
                    voucher.save()
            except Voucher.DoesNotExist:
                return redirect("subscribe", plan_id=plan_id)

        payment_success = True
        if payment_success:
            booking = Booking.objects.create(
                user=request.user,
                payment_type=payment_type,
                subject="Subscription",
                amount=plan.price,
                status="Paid",
                created_at=timezone.now(),
                voucher=voucher_code if voucher_code else None,
            )

            try:
                user_subscription = UserSubscription.objects.get(user=request.user)
                user_subscription.activate(plan)
            except UserSubscription.DoesNotExist:
                user_subscription = UserSubscription(user=request.user)
                user_subscription.activate(plan)
            transaction_data = {
                "transaction_id": booking.booking_id,
                "date": booking.booking_date,
                "time": booking.created_at,
                "amount": booking.amount,
                "payment_method": booking.payment_type,
                "payment_subject": booking.subject,
                "subscription_type": plan.type,
                "subscription_duration": plan.duration_days,
            }
            send_transaction_email(
                request, request.user, request.user.email, transaction_data
            )
            return redirect("subscriptions:subscription_success")

    return render(
        request,
        "subscription_booking.html",
        {
            "plan": plan,
        },
    )


def booking_success(request):
    return render(request, "booking_success.html")
