from django import forms


class VoucherApplyForm(forms.Form):
    code = forms.CharField()
