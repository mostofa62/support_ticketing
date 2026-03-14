from django.db import models
from django.conf import settings
from django.forms import ValidationError

from .validators import validate_file_size,validate_mime_type
from .choices import STATUS_CHOICES, PRIORITY_CHOICES, TicketStatus, TicketPriority

from django.core.validators import FileExtensionValidator

def attachment_upload_path(instance, filename):
    return f"{settings.TICKET_ATTACHMENT_PATH}{instance.ticket.id}/{filename}"

# -------------------
# Category & Subcategory
# -------------------
class IssueCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class IssueSubcategory(models.Model):
    category = models.ForeignKey(IssueCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} -> {self.name}"

# -------------------
# Ticket
# -------------------
class Ticket(models.Model):
    

    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_tickets')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    category = models.ForeignKey(IssueCategory, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(IssueSubcategory, on_delete=models.PROTECT)
    #priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    priority = models.CharField(
        max_length=20,
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM
    )
    #status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_resolved = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.category.name} - {self.status}"

# -------------------
# Attachments
# -------------------
class Attachment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to=attachment_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
            ),
            validate_file_size,
            validate_mime_type
        ]
        
    )
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # return filename if exists, else fallback string
        if self.file:
            return self.file.name
        return f"Attachment #{self.pk}"
    
from solo.models import SingletonModel
class PasswordResetConfig(SingletonModel):
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_app = models.BooleanField(default=False)

    def clean(self):
        """Ensure at least one method is enabled."""
        if not (self.enable_email or self.enable_sms or self.enable_app):
            raise ValidationError(
                "At least one password reset method (Email, SMS, App) must be enabled."
            )

    def __str__(self):
        return "Password Reset Configuration"