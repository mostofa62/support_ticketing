from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.contrib.auth.forms import UserCreationForm


class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username / Email",
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "Enter username or email"
        })
    )

from django.db import transaction, DatabaseError

class CustomUserCreationForm(UserCreationForm):
    username = forms.EmailField(
        label="Email",
        error_messages={
            "required": "Email is required",
            "invalid": "Enter a valid email address"
        }
    )
    phone_number = forms.RegexField(
        label="Phone Number", 
        regex=r'^(?:015|016|013|019|018|017|014)\d{8}$',
        error_messages={
            "required": "Phone number is required",
            'invalid': 'Enter a valid phone number starting with 015/016/013/019/018/017/014 followed by 8 digits.'
        },
        required=True)
    
    first_name = forms.CharField(
        required=True,
        error_messages={
            "required": "First name is required",
        })
    last_name = forms.CharField(
        required=True,
        error_messages={
            "required": "Last name is required",
        }
    )
    
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Groups",
        error_messages={
            "required": "At least one group must be selected.",
        }
    )

    is_staff = forms.BooleanField(required=False, label="Staff Status")

    address = forms.CharField(
        widget=forms.Textarea, 
        required=True,
        error_messages={
            'required': 'Address is required.'
        }
                              
    )

    password1 = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Password is required'
        }
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Confirm Password is required',
            "invalid": "Passwords do not match"
        }
    )

    class Meta:
        model = User
        fields = ("username", "groups")

    def clean_username(self):
        email = self.cleaned_data.get("username")

        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("This email is already registered.")

        return email
    
    def clean_groups(self):
        groups = self.cleaned_data.get("groups")

        if not groups or groups.count() == 0:
            raise forms.ValidationError("At least one group must be selected.")

        return groups

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            # attach error to password2 field
            self.add_error("password2", "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        try:
            with transaction.atomic():  # everything in one DB transaction
                user = super().save(commit=False)

                email = self.cleaned_data["username"]
                user.username = email
                user.email = email
                user.set_password(self.cleaned_data["password1"])

                groups = self.cleaned_data["groups"]
                # auto is_staff if Staff group selected
                user.is_staff = groups.filter(name__in=["Staff", "Operation"]).exists()

                phone_number = self.cleaned_data.get("phone_number")
                address = self.cleaned_data.get("address")
                is_email_verified = True if email.endswith('@cu.ac.bd') else False
                

                user.phone_number = phone_number
                user.address = address
                user.is_email_verified = is_email_verified

                if commit:
                    # 1️⃣ Save the user first so it has a PK
                    user.save()
                    user.groups.set(groups)

                    

                return user
        except DatabaseError as db_err:
            print(db_err)
            raise forms.ValidationError("An error occurred while saving the user. Please try again.")
        
        except Exception as e:
            print(e)
            raise forms.ValidationError("An unexpected error occurred. Please contact support.")
        



class CustomUserChangeForm(forms.ModelForm):
    username = forms.EmailField(
        label="Email",
        error_messages={
            "required": "Email is required",
            "invalid": "Enter a valid email address"
        }
    )

    password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput,
        required=False
    )

    password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = User
        fields = '__all__'

    def clean_username(self):
        email = self.cleaned_data.get("username")

        qs = User.objects.filter(username=email)

        # exclude current user when editing
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("This email is already registered.")

        return email
    
    def clean(self):
        cleaned_data = super().clean()

        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Passwords do not match")

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get("password1")

        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user




