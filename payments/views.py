from payments.forms import PaymentForm
from paypal.standard.forms import PayPalPaymentsForm
from django.utils import timezone
import stripe
from django.conf import settings
from django.shortcuts import render, redirect , get_object_or_404
from django.urls import reverse 
from .models import Payment
from find_transport.models import Vehicle



stripe.api_key = settings.STRIPE_SECRET_KEY



def payment_view(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
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
 
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
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
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    hours = int(request.GET.get('hours', 1))
    total_amount = vehicle.price_per_hour * hours

    # Get the host from the request
    host = request.get_host()

    # PayPal payment details
    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': total_amount,
        'item_name': f'Rent for {vehicle.type}',
        'invoice': f'invoice-{vehicle.id}-{timezone.now().timestamp()}',
        'currency_code': 'EUR',
        'notify_url': f'http://{host}{reverse("paypal-ipn")}',
        'return_url': request.build_absolute_uri(reverse('payment_success')),
        'cancel_return': request.build_absolute_uri(reverse('find_transport:find_transport')),
    }

    # Create the PayPal form
    paypal_form = PayPalPaymentsForm(initial=paypal_dict)

    return render(request, 'payments/paypal_payment.html', {
        'vehicle': vehicle,
        'total_amount': total_amount,
        'form': paypal_form,
    })