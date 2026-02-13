# users/forms.py
from django import forms
import re
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django import forms

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    phone_number = forms.RegexField(
        regex=r'^(?:015|016|013|019|018|017|014)\d{8}$',
        error_messages={
            'invalid': 'Enter a valid phone number starting with 015/016/013/019/018/017/014 followed by 8 digits.'
        },
        required=True,
    )
    address = forms.CharField(widget=forms.Textarea, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit)
        
        # Save user profile
        profile = UserProfile(
            user=user,
            phone_number=self.cleaned_data['phone_number'],
            address=self.cleaned_data.get('address', ''),
        )
        profile.save()
        
        # Auto-create group "Submitter" if it doesn't exist
        group, created = Group.objects.get_or_create(name='Submitter')
        user.groups.add(group)
        
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes and placeholders
        field_map = {
            'username': 'Username',
            'email': 'Email',
            'password1': 'Password',
            'password2': 'Confirm password',
            'first_name': 'First name',
            'last_name': 'Last name',
            'phone_number': 'Phone number',
            'address': 'Address',
        }
        for name, label in field_map.items():
            if name in self.fields:
                widget = self.fields[name].widget
                css = widget.attrs.get('class', '')
                widget.attrs.update({
                    'class': (css + ' form-control').strip(),
                    'placeholder': label,
                })
        # textarea should keep rows
        if 'address' in self.fields:
            self.fields['address'].widget.attrs.update({'rows': 3})

    def clean_phone_number(self):
        """Normalize phone number by removing non-digit characters then validate pattern."""
        raw = self.cleaned_data.get('phone_number', '')
        digits = re.sub(r'\D+', '', str(raw))
        # Ensure it matches the required pattern after cleaning
        pattern = re.compile(r'^(?:015|016|013|019|018|017|014)\d{8}$')
        if not pattern.match(digits):
            raise forms.ValidationError('Enter a valid phone number starting with 015/016/013/019/018/017/014 followed by 8 digits.')
        return digits


class LoginForm(AuthenticationForm):
    """Custom AuthenticationForm that adds Bootstrap classes to widgets and an optional remember_me field."""
    remember_me = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes and placeholders to widgets
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
            'id': 'id_username',
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'id_password',
            'autocomplete': 'current-password',
        })

