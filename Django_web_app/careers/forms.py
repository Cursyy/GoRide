from django import forms
from .models import JobApplication

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['first_name', 'last_name', 'email', 'phone', 'position', 'message', 'resume']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name', 'required': True}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name', 'required': True}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address', 'required': True}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'position': forms.TextInput(attrs={'placeholder': 'Desired Position'}),
            'message': forms.Textarea(attrs={'placeholder': 'Tell us about yourself', 'rows': 5, 'required': True}),
            'resume': forms.FileInput(),
        }