from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, timedelta
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .models import SubscriptionPlan, UserSubscription
from django.contrib import messages

@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'plans.html', {'plans': plans})

@login_required
def subscribe_user(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    subscription, created = UserSubscription.objects.get_or_create(user=request.user)

    if not created:
        messages.error(request, _("You already have an active subscription."))
        return redirect('subscriptions:subscription_plans')

    subscription.plan = plan
    subscription.start_date = now()
    subscription.end_date = now() + timedelta(days=plan.duration_days)
    subscription.remaining_rides = plan.max_ride_hours
    subscription.save()

    return redirect('subscriptions:subscription_success')

@login_required
def subscription_success(request):
    return render(request, 'success.html')