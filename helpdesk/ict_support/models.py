from django.db import models
from django.conf import settings

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
# Staff Members (optional)
# -------------------
class StaffMember(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

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


# -------------------
# Notifications
# -------------------
class Notification(models.Model):
    EVENT_TYPES = [
        ('ticket_created', 'Ticket Created'),
        ('ticket_assigned', 'Ticket Assigned'),
        ('ticket_resolved', 'Ticket Resolved'),
    ]
    MESSAGE_TYPES = [
        ('email', 'Email'),
        ('in_app', 'In App'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='notifications')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPES)
    status = models.BooleanField(default=False)
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification {self.id} -> {self.recipient.username}"
