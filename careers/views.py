from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import JobApplicationForm

def careers_view(request):
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for your application! We'll get back to you soon.")
            return redirect('careers:thank_you')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobApplicationForm()

    return render(request, 'careers.html', {'form': form})

def careers_thank_you_view(request):
    return render(request, 'careers_thank_you.html')