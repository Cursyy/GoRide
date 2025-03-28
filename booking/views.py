from django.shortcuts import render, redirect
from .models import Booking
from subscriptions.models import UserSubscription, SubscriptionPlan, UserStatistics
from find_transport.models import Vehicle
from django.utils import timezone
from decimal import Decimal
from successful_booking import send_transaction_email

# from vouchers.models import Voucher


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

        total_amount = vehicle.price_per_hour * hours

        if payment_type == "Subscription":
            if (
                not subscription
                or subscription.remaining_rides is None
                or subscription.remaining_rides < hours
            ):
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

            send_transaction_email(
                request, request.user, request.user.email, transaction_data
            )
            return redirect("booking:booking_success")

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

        payment_success = True
        if payment_success:
            booking = Booking.objects.create(
                user=request.user,
                payment_type=payment_type,
                subject="Subscription",
                amount=plan.price,
                status="Paid",
                created_at=timezone.now(),
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
