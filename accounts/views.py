from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic import CreateView
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from subscriptions.models import UserStatistics, UserSubscription
from booking.models import Booking
from avatar.models import UserAvatar, AvatarItem
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from accounts.tasks import send_email_task


class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:email_sent")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            request.session.flush()
            return redirect("accounts:signup")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        if CustomUser.objects.filter(email=email).exists():
            form.add_error("email", "A user with this email already exists.")
            return self.form_invalid(form)

        user = form.save(commit=False)
        user.is_active = False
        user.save()
        domain = self.request.get_host()
        send_email_task.delay(user.user_id, domain)
        return super().form_valid(form)


def confirm_email(request, token):
    try:
        uid = force_str(urlsafe_base64_decode(token))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None:
        if user.is_active:
            return redirect("accounts:login")

        user.is_active = True
        user.save()

        user.refresh_from_db()
        if not user.is_active:
            return redirect("main:home")

        customer_group, created = Group.objects.get_or_create(name="Customer")
        user.groups.add(customer_group)
        UserStatistics.objects.create(user=user)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        return redirect("main:home")
    else:
        return redirect("main:home")


@cache_page(60 * 15)
def email_sent(request):
    return render(request, "registration/email_sent.html")


@login_required
def profile_view(request):
    subscription = UserSubscription.objects.filter(user=request.user).first()
    statistics = UserStatistics.objects.filter(user=request.user).first()
    bookings = Booking.objects.filter(user=request.user)
    avatar, _ = UserAvatar.objects.get_or_create(user=request.user)
    all_items = AvatarItem.objects.all()

    unlocked_items = list(avatar.unlocked_items.values_list("id", flat=True))

    print("Unlocked items:", unlocked_items)


    context = {
        "user": request.user,
        "subscription": subscription,
        "statistics": statistics,
        "bookings": bookings,
        "userAvatar": avatar,
        "all_items": all_items,
        "unlocked_items": unlocked_items,
        "base_avatar_url": "/static/images/avatar/avatar.png",
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
