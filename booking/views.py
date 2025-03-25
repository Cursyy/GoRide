from django.shortcuts import render, get_object_or_404
from find_transport.models import Vehicle
from django.contrib.auth.decorators import login_required
from .models import Booking
from vouchers.models import Voucher
from django.shortcuts import redirect

@login_required
def booking_page(request, subject, vehicle_id=None):
    context = {"subject": subject}

    if subject == "Rent" and vehicle_id:
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        context["vehicle"] = vehicle
    elif subject == "Subscription":
        context["subscription_price"] = 20.00 
    elif subject == "Balance":
        pass

    return render(request, "booking.html", context)


@login_required
def rent_vehicle(request):
    if request.method == "POST":
        vehicle_id = request.POST.get("vehicle_id")
        hours = int(request.POST.get("hours", 1))
        payment_type = request.POST.get("payment_type")
        voucher_code = request.POST.get("voucher", "").strip()

        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        
        # Перевіряємо ваучер
        discount = 0
        if voucher_code:
            try:
                voucher = Voucher.objects.get(code=voucher_code, is_active=True)
                discount = voucher.discount_amount
            except Voucher.DoesNotExist:
                return render(request, "booking.html", {
                    "vehicle": vehicle,
                    "error": "Invalid voucher code."
                })

        total_price = (vehicle.price_per_hour * hours) - discount
        total_price = max(total_price, 0)

        # payment_success = process_payment(request.user, total_price, payment_type)
        # if not payment_success:
        #     return render(request, "booking.html", {"vehicle": vehicle, "error": "Payment failed."})

        booking = Booking.objects.create(
            user=request.user,
            vehicle=vehicle,
            hours=hours,
            amount=total_price,
            payment_type=payment_type,
            subject="Rent",
            status="Paid"
        )

        return redirect("booking:success")

    return redirect("main:home")

@login_required
def success(request):
    return render(request, "success.html")

@login_required
def buy_subscription(request):
    if request.method == "POST":
        payment_type = request.POST.get("payment_type")
        plan_price = 20.00

        # payment_success = process_payment(request.user, plan_price, payment_type)
        # if not payment_success:
        #     return render(request, "subscription.html", {"error": "Payment failed."})

        booking = Booking.objects.create(
            user=request.user,
            amount=plan_price,
            payment_type=payment_type,
            subject="Subscription",
            status="Paid"
        )

        return redirect("subscription:success")

    return redirect("home")

@login_required
def top_up_balance(request):
    if request.method == "POST":
        amount = float(request.POST.get("amount"))
        payment_type = request.POST.get("payment_type")

        # payment_success = process_payment(request.user, amount, payment_type)
        # if not payment_success:
        #     return render(request, "topup.html", {"error": "Payment failed."})

        booking = Booking.objects.create(
            user=request.user,
            amount=amount,
            payment_type=payment_type,
            subject="Balance",
            status="Paid"
        )

        # Додаємо баланс користувачу
        request.user.profile.balance += amount
        request.user.profile.save()

        return redirect("account:success")

    return redirect("home")
