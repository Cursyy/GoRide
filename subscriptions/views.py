from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, timedelta
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .models import SubscriptionPlan, UserSubscription

@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'plans.html', {'plans': plans})

@login_required
def subscribe_user(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    subscription, created = UserSubscription.objects.get_or_create(user=request.user)

    if subscription.is_active():
        return redirect('subscriptions:subscription_plans')

    subscription.activate(plan)
    return redirect('subscriptions:subscription_success')


@login_required
def subscription_success(request):
    return render(request, 'success.html')