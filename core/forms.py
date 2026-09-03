from django import forms


class AccountProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, label='First name')
    last_name = forms.CharField(max_length=150, required=False, label='Last name')
    email = forms.EmailField(required=False, label='Email address')
