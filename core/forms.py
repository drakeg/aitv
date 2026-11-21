from django import forms

from .models import SystemSettings


class AccountProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, label='First name')
    last_name = forms.CharField(max_length=150, required=False, label='Last name')
    email = forms.EmailField(required=False, label='Email address')


class OperatorGuestSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = (
            'site_name',
            'welcome_message',
            'default_region',
            'show_guest_account_links',
        )
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'default_region': forms.Select(attrs={'class': 'form-select'}),
            'show_guest_account_links': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
