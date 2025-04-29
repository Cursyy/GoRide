from django.db import models
from find_transport.models import Vehicle
import uuid

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_method = models.CharField(max_length=50, choices=[("Stripe", "Stripe"), ("PayPal", "PayPal")])
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending', choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')])
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.vehicle.type} on {self.payment_date}"