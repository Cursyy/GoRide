from datetime import timedelta
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from booking.models import Booking
from wallet.models import Wallet
from find_transport.models import Vehicle
from subscriptions.models import SubscriptionPlan, UserSubscription, UserStatistics
from successful_booking import send_transaction_email
from vouchers.models import Voucher
from get_direction.models import Trip
from get_direction.views import end_active_trip, start_trip
from wallet.models import Wallet
from django.contrib.auth.decorators import login_required

@login_required
def top_up_wallet(request):
    if request.method == "POST":
        amount = float(request.POST.get("amount", 0))
        payment_type = request.POST.get("payment_type")
        voucher_code = request.POST.get("voucher_code", None)

        total_amount = Decimal(str(amount))

        booking = Booking.objects.create(
            user=request.user,
            payment_type=payment_type,
            subject="Balance",
            amount=total_amount,
            status="Pending",
            created_at=timezone.now(),
            voucher=voucher_code if voucher_code else None,
        )

        if payment_type == "Stripe":
            return redirect("payments:process_stripe_payment", booking_id=booking.booking_id)
        elif payment_type == "Paypal":
            return redirect("payments:process_paypal_payment", booking_id=booking.booking_id)

    return render(request, "top_up_wallet.html")

@login_required
def rent_vehicle(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    trip = Trip.objects.filter(user=request.user, status="active").first()

    if not vehicle.status:
        return redirect("find_transport:find_transport")
    
    if trip:
        return redirect("get_direction:map")

    subscription = None
    try:
        user_subscription = UserSubscription.objects.get(user=request.user)
        if user_subscription.is_active() and user_subscription.can_use_vehicle(vehicle):
            subscription = user_subscription
    except UserSubscription.DoesNotExist:
        pass

    wallet = None
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        pass

    if request.method == "POST":
        hours = int(request.POST.get("hours", 0))
        payment_type = request.POST.get("payment_type")
        voucher_code = request.POST.get("voucher_code", None)

        total_amount = Decimal(str(vehicle.price_per_hour * hours))

        if voucher_code:
            try:
                voucher = Voucher.objects.get(code=voucher_code, active=True)
                if voucher.valid_from <= timezone.now() <= voucher.valid_to and (voucher.used or 0) < (voucher.max_use or float("inf")):
                    total_amount -= total_amount * Decimal(str(voucher.discount)) / 100
                    voucher.used = (voucher.used or 0) + 1
                    voucher.save()
                    if payment_type == "Subscription":
                        payment_type = "Stripe"
            except Voucher.DoesNotExist:
                return redirect("booking:rent_vehicle", vehicle_id=vehicle_id)

        booking = Booking.objects.create(
            user=request.user,
            vehicle=vehicle,
            payment_type=payment_type,
            subject="Rent",
            amount=total_amount,
            hours=hours,
            status="Pending",
            created_at=timezone.now(),
            voucher=voucher_code if voucher_code else None,
        )

        if payment_type == "Stripe":
            return redirect("payments:process_stripe_payment", booking_id=booking.booking_id)
        elif payment_type == "Paypal":
            return redirect("payments:process_paypal_payment", booking_id=booking.booking_id)
        elif payment_type == "Subscription" and not voucher_code:
            if subscription:
                if subscription.remaining_rides is None or subscription.remaining_rides >= hours:
                    total_amount = Decimal("0")
                    subscription.remaining_rides = (subscription.remaining_rides or 0) - hours
                    subscription.save()
                else:
                    booking.status = "Cancelled"
                    booking.save()
                    return redirect("booking:rent_vehicle", vehicle_id=vehicle_id)
            else:
                booking.status = "Cancelled"
                booking.save()
                return redirect("booking:rent_vehicle", vehicle_id=vehicle_id)
        elif payment_type == "AppBalance":
            if wallet and wallet.balance >= total_amount:
                wallet.withdraw(total_amount)
            else:
                booking.status = "Cancelled"
                booking.save()
                return redirect("booking:rent_vehicle", vehicle_id=vehicle_id)

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

                send_transaction_email(request, request.user, request.user.email, transaction_data)

                booking.status = "Paid"
                booking.save()
                return render(request, "booking_success.html")
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

    return render(request, "rental_booking.html", {"vehicle": vehicle, "subscription": subscription})

@login_required
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

        total_amount = Decimal(str(plan.price))

        if voucher_code:
            try:
                voucher = Voucher.objects.get(code=voucher_code, active=True)
                if voucher.valid_from <= timezone.now() <= voucher.valid_to and (voucher.used or 0) < (voucher.max_use or float("inf")):
                    total_amount -= total_amount * Decimal(str(voucher.discount)) / 100
                    voucher.used = (voucher.used or 0) + 1
                    voucher.save()
            except Voucher.DoesNotExist:
                return redirect("booking:subscribe", plan_id=plan_id)

        booking = Booking.objects.create(
            user=request.user,
            payment_type=payment_type,
            subject="Subscription",
            amount=total_amount,
            status="Pending",
            created_at=timezone.now(),
            voucher=voucher_code if voucher_code else None,
            plan_id=plan_id,
        )

        if payment_type == "Stripe":
            return redirect("payments:process_stripe_payment", booking_id=booking.booking_id)
        elif payment_type == "Paypal":
            return redirect("payments:process_paypal_payment", booking_id=booking.booking_id)
        elif payment_type == "AppBalance":
            try:
                wallet = Wallet.objects.get(user=request.user)
                if wallet.balance >= total_amount:
                    wallet.withdraw(total_amount)
                else:
                    booking.status = "Cancelled"
                    booking.save()
                    return redirect("booking:subscribe", plan_id=plan_id)
            except Wallet.DoesNotExist:
                booking.status = "Cancelled"
                booking.save()
                return redirect("booking:subscribe", plan_id=plan_id)

        user_subscription, created = UserSubscription.objects.get_or_create(user=request.user)
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
        send_transaction_email(request, request.user, request.user.email, transaction_data)
        booking.status = "Paid"
        booking.save()
        return redirect("subscriptions:subscription_success")

    return render(request, "subscription_booking.html", {"plan": plan_id})

@login_required
def booking_success(request, booking_id):
    booking = Booking.objects.get(booking_id=booking_id)
    booking.status = "Paid"
    booking.save()

    if booking.subject == "Balance":
        wallet = Wallet.objects.get(user=request.user)
        wallet.top_up(booking.amount)
        transaction_data = {
            "transaction_id": booking.booking_id,
            "date": booking.booking_date,
            "time": booking.created_at,
            "amount": booking.amount,
            "payment_method": booking.payment_type,
            "payment_subject": booking.subject,
        }
        send_transaction_email(request, request.user, request.user.email, transaction_data)
        return render(request, "booking_success.html")

    elif booking.subject == "Rent":
        vehicle = booking.vehicle
        vehicle.status = False
        vehicle.save()
        try:
            stats = UserStatistics.objects.get(user=request.user)
        except UserStatistics.DoesNotExist:
            stats = UserStatistics.objects.create(user=request.user)
        stats.update_stats(booking.hours, booking.amount, vehicle.type)
        transaction_data = {
            "transaction_id": booking.booking_id,
            "date": booking.booking_date,
            "time": booking.created_at,
            "amount": booking.amount,
            "payment_method": booking.payment_type,
            "payment_subject": booking.subject,
            "rental_item": vehicle.type,
            "duration": booking.hours,
        }
        minutes_paid = booking.hours * 60
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

                send_transaction_email(request, request.user, request.user.email, transaction_data)
                return render(request, "booking_success.html")
            else:
                print(f"Error during auto-start for newly created trip {new_trip.id}. Response: {start_response.content}")
                error_message = start_data.get("error", "Failed to auto-start the trip after creation.")
                return JsonResponse( {"error": error_message}, status=start_response.status_code or 400)
            

        except Exception as e:
            print(f"Error creating trip for user {request.user}: {e}")
            return JsonResponse({"error": "Failed to create the trip."}, status=500)

    elif booking.subject == "Subscription":
        plan = SubscriptionPlan.objects.get(id=booking.plan_id)
        user_subscription, created = UserSubscription.objects.get_or_create(user=request.user)
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
        send_transaction_email(request, request.user, request.user.email, transaction_data)
        return redirect("subscriptions:subscription_success")