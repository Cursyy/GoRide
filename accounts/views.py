from .models import CustomUser
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.

class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("main:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        customer_group, created = Group.objects.get_or_create(name="Customer")
        self.object.groups.add(customer_group)
        login(self.request, self.object)
        return response


@login_required
def profile_view(request):
    return render(request, "profile.html", {"user": request.user})

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
