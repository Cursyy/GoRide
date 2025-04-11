from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .models import CustomUser


@shared_task
def send_email_task(user_id, domain):
    try:
        user = CustomUser.objects.get(user_id=user_id)
        token = urlsafe_base64_encode(force_bytes(user.pk))
        confirm_url = f"http://{domain}/accounts/confirm/{token}/"

        subject = "Confirm Your Email Address"
        message = (
            f"Hi {user.username},\n\n"
            f"Please confirm your email by clicking the link below:\n"
            f"{confirm_url}\n\n"
            f"If you did not sign up, please ignore this email.\n\n"
            f"Thanks,\nThe GoRide Team"
        )
        html_message = render_to_string(
            "registration/confirmation_email.html",
            {
                "user": user,
                "confirm_url": confirm_url,
            },
        )

        send_mail(
            subject,
            message,
            "tud.goride@gmail.com",
            [user.email],
            fail_silently=False,
            html_message=html_message,
        )
        return f"Email sent successfully to user {user.email}"
    except CustomUser.DoesNotExist:
        return f"User with ID {user_id} not found"
    except Exception as e:
        return f"Error sending email to user ID {user_id}: {e}"
