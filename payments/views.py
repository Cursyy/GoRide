from payments.forms import PaymentForm
from django.utils import timezone
import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Payment
from find_transport.models import Vehicle
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY



def payment_view(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    hours = int(request.GET.get('hours', 1))
    total_amount = vehicle.price_per_hour * hours

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.vehicle = vehicle
            payment.amount = total_amount
            payment.save()
            vehicle.status = False
            vehicle.save()
            return redirect('payment_success')
    else:
        form = PaymentForm(initial={'vehicle': vehicle, 'amount': total_amount})
    return render(request, 'payments/payment.html', {'form': form, 'vehicle': vehicle, 'total_amount': total_amount})

def payment_success(request):
    return render(request, 'payments/payment_success.html')

def stripe_payment(request, vehicle_id):
 
    vehicle = Vehicle.objects.get(id=vehicle_id)
    hours = int(request.GET.get('hours', 1))
    total_amount = int(vehicle.price_per_hour * hours * 100)  
    description = f'Rent for {vehicle.type}'

    if request.method == 'POST':
        try:
           
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'Rent for {vehicle.type}',
                        },
                        'unit_amount': total_amount,  
                    },
                    'quantity': 1,
                }],
                mode='payment',
                billing_address_collection='required',  
                shipping_address_collection={},  
                payment_intent_data={'description': description},
                success_url=request.build_absolute_uri(reverse('payment_success')),  
                cancel_url=request.build_absolute_uri(reverse('find_transport:find_transport')),  
            )
            payment = Payment.objects.create(
                vehicle=vehicle,
                amount=total_amount / 100,  
                payment_method="Stripe",
            )

            
            vehicle.status = False
            vehicle.save()
            
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return render(request, 'payments/stripe_payment.html', {
                'error': str(e),
                'vehicle': vehicle,
                'total_amount': total_amount / 100,  
            })

  
    return render(request, 'payments/stripe_payment.html', {
        'vehicle': vehicle,
        'total_amount': total_amount / 100,  
        })

def paypal_payment(request, vehicle_id):

    vehicle = Vehicle.objects.get(id=vehicle_id)
    hours = int(request.GET.get('hours', 1))
    total_amount = vehicle.price_per_hour * hours

    return render(request, 'payments/paypal_payment.html', {
        'vehicle': vehicle,
        'total_amount': total_amount,
    })