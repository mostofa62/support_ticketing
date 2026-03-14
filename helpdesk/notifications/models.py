from django.db import models
from django.conf import settings
# Create your models here.
# -------------------
# Notifications
# -------------------
class Notification(models.Model):

    EVENT_TYPES = [
        ("ticket_created", "Ticket Created"),
        ("ticket_assigned", "Ticket Assigned"),
        ("ticket_resolved", "Ticket Resolved"),
        ("password_reset", "Password Reset"),
        ("password_reset_sms", "Password Reset using SMS"),
        ("user_registered", "User Registered"),
    ]

    CHANNEL_TYPES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("portal", "Portal"),
        ("push", "Push Notification"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPES
    )

    # optional reference for ticket related events
    ticket = models.ForeignKey(
        "ict_support.Ticket",  # full app_label.ModelName
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    # celery processing status
    is_sent = models.BooleanField(default=False)

    # portal notification read status
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    sent_at = models.DateTimeField(null=True, blank=True)

    data = models.JSONField(default=dict, blank=True)
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} -> {self.recipient}"
