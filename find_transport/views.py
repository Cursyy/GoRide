from django.shortcuts import render
from .models import Vehicle, Booking
from .forms import BookingForm
import stripe
from django.conf import settings


def find_transport(request):
    vehicle_type = request.GET.get("type")
    min_battery = request.GET.get("min_battery")

    vehicles = Vehicle.objects.all()
    if vehicle_type:
        vehicles = vehicles.filter(type=vehicle_type)
    if min_battery:
        vehicles = vehicles.filter(battery_percentage__gte=min_battery)

    return render(request, "find_transport.html", {"vehicles": vehicles})

def checkout(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.vehicle = vehicle
            booking.save() 

            intent = stripe.PaymentIntent.create(
                    amount=int(booking.total_price * 100),  
                    currency='eur',
                    metadata={'booking_id': booking.id},
            )
            return render(request, 'payment.html', {'client_secret': intent.client_secret}) 
    else:
        form = BookingForm()
    return render(request, 'checkout.html', {'form': form, 'vehicle': vehicle})