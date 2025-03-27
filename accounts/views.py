from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import CreateView
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from subscriptions.models import UserStatistics, UserSubscription


class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:email_sent")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            request.session.flush()
            return redirect('accounts:signup')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            form.add_error('email', 'A user with this email already exists.')
            return self.form_invalid(form)

        user = form.save(commit=False)
        user.is_active = False 
        user.save()

        token = urlsafe_base64_encode(force_bytes(user.pk))
        domain = self.request.get_host()
        confirm_url = f"http://{domain}/accounts/confirm/{token}/"

        subject = "Confirm Your Email Address"
        message = f"Hi {user.username},\n\nPlease confirm your email by clicking the link below:\n{confirm_url}\n\nIf you did not sign up, please ignore this email.\n\nThanks,\nThe GoRide Team"
        html_message = render_to_string('registration/confirmation_email.html', {
            'user': user,
            'confirm_url': confirm_url,
        })
        send_mail(
            subject,
            message,
            'tud.goride@gmail.com',
            [user.email],
            fail_silently=False,
            html_message=html_message,
        )

        return super().form_valid(form)


def confirm_email(request, token):
    try:
        uid = force_str(urlsafe_base64_decode(token))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None:
        if user.is_active:
            return redirect('accounts:login')

        user.is_active = True
        user.save()

        user.refresh_from_db()
        if not user.is_active:
            return redirect('main:home')

        customer_group, created = Group.objects.get_or_create(name="Customer")
        user.groups.add(customer_group)

        UserStatistics.objects.create(user=user)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        return redirect('main:home')
    else:
        return redirect('main:home')
    
def email_sent(request):
    return render(request, "registration/email_sent.html")

@login_required
def profile_view(request):
    subscription = UserSubscription.objects.filter(user=request.user).first()
    statistics = UserStatistics.objects.filter(user=request.user).first()
    
    context = {
        "user": request.user,
        "subscription": subscription,
        "statistics": statistics,
    }
    
    if subscription:
        context["subscription_progress"] = subscription.progress_remaining()
    
    return render(request, "profile.html", context)


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile")
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, "profile_edit.html", {"form": form})
