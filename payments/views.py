from payments.forms import PaymentForm
from paypal.standard.forms import PayPalPaymentsForm
from django.utils import timezone
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Payment
from find_transport.models import Vehicle
from django.contrib import messages
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.views.decorators.csrf import csrf_exempt


stripe.api_key = settings.STRIPE_SECRET_KEY


def sendEmail(request, user, to_email):
    print(user.email)
    mail_subject = "Transaction Successful."
    message = render_to_string(
        "payment_success_email.html",
        {
            "user": user.username,
            # 'transaction_status': transaction_status,
            #  # transaction_status is a variable that holds the status of the transaction success or failed
            # 'transaction_id': transaction_id,
            #  # transaction_id is a variable that holds the transaction id
            # 'amount': amount,
            #  # amount is a variable that holds the amount of the transaction
            # 'date': date,
            #  # date is a variable that holds the date of the transaction
            # 'time': time,
            #  # time is a variable that holds the time of the transaction
            # 'payment_subject': payment_subject,
            # # payment_subject is a variable that holds the subject of the payment "Rent","Subscription","Wallet"
            # 'rental_item': rental_item,
            #  # rental_item is a variable that holds the item rented "Bike","E-Scooter","E-Bike"
            # 'payment_method': payment_method,
            #  # payment_method is a variable that holds the payment method used "PayPal","Stripe"
            # 'duration': duration,
            #  # duration is a variable that holds the duration of the rental if the payment_subject is "Rent"
            # 'subscription_type': subscription_type,
            # # subscription_type is a variable that holds the type of subscription if the payment_subject is "Subscription"
            # 'subscription_duration': subscription_duration,
            #  # subscription_duration is a variable that holds the duration of the subscription if the payment_subject is "Subscription"
            # 'wallet_top_up_amount': wallet_top_up_amount,
            #  # wallet_top_up_amount is a variable that holds the amount of the wallet top-up if the payment_subject is "Wallet Top-up"
            # 'wallet_balance': wallet_balance,
            #  # wallet_balance is a variable that holds the balance of the wallet after the wallet top-up if the payment_subject is "Wallet Top-up"
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


def booking_view(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    hours = int(request.GET.get("hours", 1))
    total_amount = vehicle.price_per_hour * hours

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.vehicle = vehicle
            payment.amount = total_amount
            payment.save()
            vehicle.status = False
            vehicle.save()
            return redirect("payment_success")
    else:
        form = PaymentForm(initial={"vehicle": vehicle, "amount": total_amount})
    return render(
        request,
        "payments/payment.html",
        {"form": form, "vehicle": vehicle, "total_amount": total_amount},
    )


def payment_success(request):
    user = request.user
    sendEmail(request, user, user.email)
    return render(request, "payments/payment_success.html")


def stripe_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    hours = int(request.GET.get("hours", 1))
    total_amount = int(vehicle.price_per_hour * hours * 100)
    description = f"Rent for {vehicle.type}"

    if request.method == "POST":
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "eur",
                            "product_data": {
                                "name": f"Rent for {vehicle.type}",
                            },
                            "unit_amount": total_amount,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                billing_address_collection="required",
                shipping_address_collection={},
                payment_intent_data={"description": description},
                success_url=request.build_absolute_uri(reverse("payments:payment_success")),
                cancel_url=request.build_absolute_uri(
                    reverse("find_transport:find_transport")
                ),
            )
            customer_details = checkout_session.customer_details
            customer_name = customer_details.name
            customer_email = customer_details.email
            customer_address = f"{customer_details.address.line1}, {customer_details.address.city},{customer_details.address.postal_code}, {customer_details.address.country}"

            payment = Payment.objects.create(
                vehicle=vehicle,
                amount=total_amount / 100,
                payment_method="Stripe",
                transaction_id=checkout_session.payment_intent,
                status="Completed",
                customer_name=customer_name,
                customer_email=customer_email,
                customer_address=customer_address,
            )

            vehicle.status = False
            vehicle.save()

            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return render(
                request,
                "payments/stripe_payment.html",
                {
                    "error": str(e),
                    "vehicle": vehicle,
                    "total_amount": total_amount / 100,
                },
            )

    return render(
        request,
        "payments/stripe_payment.html",
        {
            "vehicle": vehicle,
            "total_amount": total_amount / 100,
        },
    )


def paypal_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    hours = int(request.GET.get("hours", 1))
    total_amount = vehicle.price_per_hour * hours

    host = request.get_host()

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": total_amount,
        "item_name": f"Rent for {vehicle.type}",
        "invoice": f"invoice-{vehicle.id}-{timezone.now().timestamp()}",
        "currency_code": "EUR",
        "notify_url": f'http://{host}{reverse("paypal-ipn")}',
        "return_url": request.build_absolute_uri(reverse("payment_success")),
        "cancel_return": request.build_absolute_uri(
            reverse("find_transport:find_transport")
        ),
    }
    paypal_form = PayPalPaymentsForm(initial=paypal_dict)

    # payment = Payment.objects.create(
    #     vehicle=vehicle, amount=total_amount, payment_method="PayPal", status="Pending"
    # )

    return render(
        request,
        "payments/paypal_payment.html",
        {
            "vehicle": vehicle,
            "total_amount": total_amount,
            "form": paypal_form,
        },
    )

    return render(
        request,
        "payments/paypal_payment.html",
        {
            "vehicle": vehicle,
            "total_amount": total_amount,
            "form": paypal_form,
        },
    )


@csrf_exempt
def paypal_ipn(request):
    if request.method == "POST":
        pass
    return HttpResponse(status=200)


def update_payment_status(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == ST_PP_COMPLETED:
        payment = Payment.objects.get(invoice=ipn_obj.invoice)
        payment.status = "Completed"
        payment.transaction_id = ipn_obj.txn_id
        payment.customer_name = ipn_obj.first_name + " " + ipn_obj.last_name
        payment.customer_email = ipn_obj.payer_email
        payment.customer_address = f"{ipn_obj.address_street}, {ipn_obj.address_city}, {ipn_obj.address_zip}, {ipn_obj.address_country}"
        payment.save()


valid_ipn_received.connect(update_payment_status)
