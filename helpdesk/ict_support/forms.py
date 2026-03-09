from django.contrib.auth.forms import AuthenticationForm
from django import forms

class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username / Email",
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "Enter username or email"
        })
    )

