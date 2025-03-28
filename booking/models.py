from django.db import models
from django.conf import settings
from find_transport.models import Vehicle

class Booking(models.Model):
    PAYMENT_TYPE = [
        ('Stripe', 'Stripe'),
        ('Paypal', 'Paypal'),
        ('AppBalance', 'AppBalance'),
        ('Subscription', 'Subscription')
    ]

    SUBJECT = [
        ('Rent', 'Rent'),
        ('Subscription', 'Subscription'),
        ('Balance', 'Balance')
    ]

    STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled')
    ]

    booking_id = models.AutoField(primary_key=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, blank=True, null=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE)
    subject = models.CharField(max_length=20, choices=SUBJECT)
    voucher = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    hours = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.booking_id} - {self.subject} - {self.user.username}"
