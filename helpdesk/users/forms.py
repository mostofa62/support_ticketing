# users/forms.py


from django import forms
import re
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class ProfileUpdateForm(forms.ModelForm):
    username = forms.EmailField(
        label="Email",
        disabled=True
    )

    phone_number = forms.RegexField(
        regex=r'^(?:015|016|013|019|018|017|014)\d{8}$',
        required=True,
        error_messages={
            'invalid': 'Enter a valid phone number starting with 015/016/013/019/018/017/014 followed by 8 digits.'
        }
    )

    address = forms.CharField(
        widget=forms.Textarea, 
        required=True,
        error_messages={
            'required': 'Address is required.'
        }
                              
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")  # keep reference to current user
        super().__init__(*args, **kwargs)

        profile = self.user.userprofile
        self.fields["phone_number"].initial = profile.phone_number
        self.fields["address"].initial = profile.address
        self.fields["username"].initial = self.user.username

        # Bootstrap styling
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
        self.fields["address"].widget.attrs.update({"rows": 3})

    # ---------------------------
    # Validation
    # ---------------------------
    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip()
        if not first_name:
            raise forms.ValidationError("First name cannot be empty.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()
        if not last_name:
            raise forms.ValidationError("Last name cannot be empty.")
        return last_name

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        digits = re.sub(r'\D', '', phone)
        pattern = re.compile(r'^(?:015|016|013|019|018|017|014)\d{8}$')
        if not pattern.match(digits):
            raise forms.ValidationError(
                "Enter a valid phone number starting with 015/016/013/019/018/017/014 followed by 8 digits."
            )

        # Ensure phone is unique (optional)
        if UserProfile.objects.filter(phone_number=digits).exclude(user=self.user).exists():
            raise forms.ValidationError("This phone number is already used by another user.")

        return digits

    # ---------------------------
    # Save method updates both User + UserProfile
    # ---------------------------
    def save(self, commit=True):
        user = self.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()

            profile = user.userprofile
            profile.phone_number = self.cleaned_data["phone_number"]
            profile.address = self.cleaned_data["address"]
            profile.save()

        return user

class RegisterForm(UserCreationForm):
    username = forms.EmailField(
        label="Email",
        error_messages={
            "required": "Email is required",
            "invalid": "Enter a valid email address"
        }
    )
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
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name']
        error_messages = {
            'username': {
                'unique': "This email is already registered.",
            }
        }

    def clean_username(self):
        email = self.cleaned_data.get('username')

        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("This email is already registered.")

        return email    

    def save(self, commit=True):
        user = super().save(commit=False)

        # username is email → copy to email field
        user.email = user.username

        if commit:
            user.save()

            # create profile
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data.get('address', ''),
            )

            # assign group
            group, _ = Group.objects.get_or_create(name='Client')
            user.groups.add(group)

        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes and placeholders
        field_map = {
            'username': 'Email',
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

from django.contrib.auth import authenticate

class LoginForm(AuthenticationForm):
    """Custom AuthenticationForm that allows login with username or email."""
    remember_me = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Email"   # change label
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email',
            'id': 'id_username',
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'id_password',
            'autocomplete': 'current-password',
        })
        self.error_messages['invalid_login'] = "Invalid email or password."


class CustomPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


from django.contrib.auth.forms import SetPasswordForm

class CustomSetPasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Your Email",
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No user is registered with this email address")
        return email
    
class SetNewPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('new_password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
    

from ict_support.models import PasswordResetConfig

def get_password_reset_choices():
    config = PasswordResetConfig.get_solo()
    choices = []
    if config.enable_email:
        choices.append(('email', 'Email'))
    if config.enable_sms:
        choices.append(('sms', 'SMS'))
    if config.enable_app:
        choices.append(('app', 'App'))
    return choices

class PasswordResetChoiceForm(forms.Form):
    email_or_phone = forms.CharField(
        label="Email or Phone",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email or phone'})
    )
    method = forms.ChoiceField(
        choices=[],  # empty here
        widget=forms.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dynamically set choices every time the form is created
        self.fields['method'].choices = get_password_reset_choices()

       

        # Dynamically adjust label and placeholder based on enabled methods
        choices = [c[0] for c in get_password_reset_choices()]

         # Expose enabled methods to template/JS
        self.enabled_methods = choices
        
        label_parts = []
        placeholder_parts = []

        if 'email' in choices:
            label_parts.append("Email")
            placeholder_parts.append("email")
        if 'sms' in choices:
            label_parts.append("Phone")
            placeholder_parts.append("phone number")

        label_text = " or ".join(label_parts) if label_parts else "Email or Phone"
        placeholder_text = " or ".join(placeholder_parts) if placeholder_parts else "Enter your email or phone"

        self.fields['email_or_phone'].label = label_text
        self.fields['email_or_phone'].widget.attrs['placeholder'] = placeholder_text

    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get('email_or_phone')

        if not value:
            return cleaned_data

        if '@' in value:
            if not User.objects.filter(email=value).exists():
                self.add_error('email_or_phone', "No user with this email.")
        else:
            if not User.objects.filter(userprofile__phone_number=value).exists():
                self.add_error('email_or_phone', "No user with this phone number.")

        return cleaned_data