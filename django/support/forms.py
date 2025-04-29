from django import forms
from .models import Message
from django.utils.translation import gettext_lazy as _


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"placeholder": _("Write your message..."), "name": "content"}
            )
        }
        labels = {
            "content": _("Content")
        }
