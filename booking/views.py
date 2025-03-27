from django.shortcuts import render, redirect
from .models import Booking
from subscriptions.models import UserSubscription, SubscriptionPlan, UserStatistics
from find_transport.models import Vehicle
from django.utils import timezone
from django.contrib import messages
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage


def sendEmail(request, user, to_email, booking):
    print(user.email)
    mail_subject = "Transaction Successful."
    message = render_to_string(
        "payment_success_email.html",
        {
            "user": user.username,
            "transaction_status": "Successful",
            "transaction_id": booking.booking_id,
            # transaction_id is a variable that holds the transaction id
            "amount": booking.amount,
            # amount is a variable that holds the amount of the transaction
            "date": booking.booking_date,
            # date is a variable that holds the date of the transaction
            "time": booking.created_at,
            # time is a variable that holds the time of the transaction
            "payment_subject": booking.subject,
            # payment_subject is a variable that holds the subject of the payment "Rent","Subscription","Wallet"
            "rental_item": booking.vehicle or None,
            # rental_item is a variable that holds the item rented "Bike","E-Scooter","E-Bike"
            "payment_method": booking.payment_type,
            # payment_method is a variable that holds the payment method used "PayPal","Stripe"
            "duration": booking.hours or None,
            # duration is a variable that holds the duration of the rental if the payment_subject is "Rent"
            # 'wallet_top_up_amount': wallet_top_up_amount,
            # wallet_top_up_amount is a variable that holds the amount of the wallet top-up if the payment_subject is "Wallet Top-up"
            # 'wallet_balance': wallet_balance,
            "domain": get_current_site(request).domain,
            "protocol": "https" if request.is_secure() else "http",
        },
    )
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(
            request,
            f"Dear <b>{user}</b>Your transaction was successful!\
                          Please check your<b>{to_email}</b>  for the details. Thank you for using our rental service!",
        )
    else:
        messages.error(
            request,
            f"Problem sending email to {to_email}, check if you typed it correctly.",
        )


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
                amount=total_amount,
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

            return redirect("booking:booking_success", booking_id=booking.booking_id)

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

            return redirect(
                "subscriptions:subscription_success", booking_id=booking.booking_id
            )

    return render(
        request,
        "subscription_booking.html",
        {
            "plan": plan,
        },
    )


def booking_success(request, booking_id):
    booking = Booking.objects.get(booking_id=booking_id)
    user = request.user
    sendEmail(request, user, user.email, booking)
    return render(request, "booking_success.html")
