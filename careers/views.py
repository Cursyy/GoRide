from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .forms import JobApplicationForm

def careers_view(request):
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()

            user_subject = "Thank You for Applying to GoRide!"
            user_html_content = render_to_string('emails/user_application_thank_you.html', {
                'first_name': application.first_name,
                'last_name': application.last_name,
                'home_url': request.build_absolute_uri('/'),
            })
            user_text_content = "Thank you for applying to GoRide! We'll get back to you soon."
            user_email = EmailMultiAlternatives(
                user_subject,
                user_text_content,
                settings.DEFAULT_FROM_EMAIL,
                [application.email],
            )
            user_email.attach_alternative(user_html_content, "text/html")
            user_email.send()

            return redirect('careers:thank_you')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobApplicationForm()

    return render(request, 'careers.html', {'form': form})

def careers_thank_you_view(request):
    return render(request, 'careers_thank_you.html')