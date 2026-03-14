# users/models.py
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator
# Bangladesh phone number validator
phone_regex = RegexValidator(
    regex=r'^\+?88\d{10}$',
    message="Phone number must be entered in the format: '+8801XXXXXXXXX'"
)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    
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
    
from django.utils import timezone
from datetime import timedelta
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(validators=[phone_regex], max_length=14, blank=True, null=True)
    otp = models.CharField(max_length=6,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expired_at:
            self.expired_at = timezone.now() + timedelta(minutes=2)  # default 2 min expiry
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expired_at

    def __str__(self):
        return f"{self.user.username} - {self.otp} ({'used' if self.used else 'active'})"
