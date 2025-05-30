from celery import shared_task
from stats.models import UserStatistics
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage


@shared_task
def update_stats(hours, total_amount, vehicle, user):
    try:
        stats = UserStatistics.objects.get(user=user)
    except UserStatistics.DoesNotExist:
        stats = UserStatistics.objects.create(user=user)
    stats.update_stats(hours, total_amount, vehicle.type)


@shared_task
def send_transaction_email(request, user, email, transaction_data):
    template = "payment_success_email.html"

    """
    transaction_data: dict with next keys
        - transaction_id
        - date
        - time
        - amount
        - payment_method
        - payment_subject (Rent, Subscription, Wallet)
        - rental_item (для Rent)
        - duration (для Rent)
        - subscription_type (для Subscription)
        - subscription_duration (для Subscription)
    """
    mail_subject = "Transaction Successful."
    context = {
        "user": user.username,
        "transaction_id": transaction_data.get("transaction_id"),
        "date": transaction_data.get("date"),
        "time": transaction_data.get("time"),
        "amount": transaction_data.get("amount"),
        "payment_method": transaction_data.get("payment_method"),
        "payment_subject": transaction_data.get("payment_subject"),
        "rental_item": transaction_data.get("rental_item"),
        "duration": transaction_data.get("duration"),
        "subscription_type": transaction_data.get("subscription_type"),
        "subscription_duration": transaction_data.get("subscription_duration"),
        "domain": get_current_site(request).domain,
        "protocol": "https" if request.is_secure() else "http",
    }
    message = render_to_string(template, context)
    email = EmailMessage(mail_subject, message, to=[email])
    email.content_subtype = "html"
    if email.send():
        return True
    else:
        return False
