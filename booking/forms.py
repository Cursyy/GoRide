from django import forms
from .models import Booking

class RentalBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['hours', 'payment_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hours'].widget.attrs.update({'min': 1, 'id': 'id_hours'})

class SubscriptionBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['payment_type', 'voucher']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_type'].choices = [
            (k, v) for k, v in Booking.PAYMENT_TYPE if k != 'Subscription'
        ]
        self.fields['payment_type'].initial = 'Stripe'