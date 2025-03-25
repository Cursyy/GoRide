from django.views.generic import CreateView
from .forms import RentalBookingForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

from .models import Booking
from find_transport.models import Vehicle
from subscriptions.models import UserSubscription, SubscriptionPlan
from .forms import SubscriptionBookingForm

class RentalBookingCreateView(CreateView):
    model = Booking
    form_class = RentalBookingForm
    template_name = 'rental_booking.html'

    def get_subscription_details(self):
        try:
            subscription = self.request.user.usersubscription
            if subscription.is_active():
                return {
                    'type': subscription.plan.type,
                    'remaining_hours': subscription.remaining_rides
                }
        except UserSubscription.DoesNotExist:
            return None
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle = get_object_or_404(Vehicle, id=self.kwargs['vehicle_id'])
        context['vehicle'] = vehicle
        context['price_per_hour'] = vehicle.price_per_hour
        context['subscription'] = self.get_subscription_details()
        return context

    def form_valid(self, form):
        vehicle = get_object_or_404(Vehicle, id=self.kwargs['vehicle_id'])
        form.instance.user = self.request.user
        form.instance.vehicle = vehicle
        hours = form.cleaned_data['hours']
        payment_type = form.cleaned_data['payment_type']
        subscription = self.get_subscription_details()

        if payment_type == 'Subscription':
            if not subscription or subscription['remaining_hours'] < hours:
                form.add_error('payment_type', "Not enough subscription hours.")
                return self.form_invalid(form)
            form.instance.amount = 0  # No additional cost
            subscription_obj = self.request.user.usersubscription
            subscription_obj.remaining_rides -= hours
            subscription_obj.save()  # Decrease hours in DB
        else:
            form.instance.amount = vehicle.price_per_hour * hours
            # Process other payment methods (e.g., Stripe) here

        vehicle.status = False  # Mark vehicle as rented
        vehicle.save()
        return super().form_valid(form)


class SubscriptionBookingCreateView(CreateView):
    model = Booking
    form_class = SubscriptionBookingForm
    template_name = 'subscription_booking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = get_object_or_404(SubscriptionPlan, id=self.kwargs['plan_id'])
        context['plan'] = plan
        context['amount'] = plan.price
        return context

    def form_valid(self, form):
        plan = get_object_or_404(SubscriptionPlan, id=self.kwargs['plan_id'])
        form.instance.user = self.request.user
        form.instance.subject = 'Subscription'
        form.instance.amount = plan.price
        payment_type = form.cleaned_data['payment_type']

        # if not process_payment(payment_type, form.instance.amount):
        #     form.add_error(None, "Payment failed.")
        #     return self.form_invalid(form)

        form.instance.status = 'Paid'
        # Activate subscription logic here
        UserSubscription.objects.create(user=self.request.user, plan=plan)
        return super().form_valid(form)
    