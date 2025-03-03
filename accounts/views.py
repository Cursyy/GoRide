from .models import CustomUser
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth import login

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
