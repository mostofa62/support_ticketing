# users/models.py
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Bangladesh phone number validator
    phone_regex = RegexValidator(
        regex=r'^\+?88\d{10}$',
        message="Phone number must be entered in the format: '+8801XXXXXXXXX'"
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=14, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_active_submitter = models.BooleanField(default=True)  # toggle in admin

    def save(self, *args, **kwargs):
        if self.user.email.endswith('@cu.ac.bd'):
            self.is_email_verified = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username
