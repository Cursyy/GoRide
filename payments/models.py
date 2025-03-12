from django.db import models
from find_transport.models import Vehicle

class Payment(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_method = models.CharField(max_length=50, choices=[("Stripe", "Stripe"), ("PayPal", "PayPal")])
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.vehicle.type} on {self.payment_date}"