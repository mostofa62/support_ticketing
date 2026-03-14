from celery import shared_task
from django.utils import timezone

from .services.sms_service import ShortMessageHelper
from .models import Notification

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

@shared_task(bind=True, max_retries=3)
def send_notification(self, notification_id):

    notification = Notification.objects.get(id=notification_id)
    event = notification.event_type
    try:
        # Example logic depending on channel
        if notification.channel == "email":
            # Template paths
            subject_template = f"notifications/email/{event}_subject.txt"
            body_template = f"notifications/email/{event}_body.html"
            # Render templates with notification.data
            subject = render_to_string(subject_template, notification.data).strip()
            body_html = render_to_string(body_template, notification.data)
            # Send HTML email
            email = EmailMultiAlternatives(
                subject=subject,
                body=body_html,  # fallback for plain text
                from_email="no-reply@example.com",
                to=[notification.data.get("email")],
            )
            email.attach_alternative(body_html, "text/html")
            if email.send():
                # mark as sent
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save()
                print(f"Email sent for event: {event}")

        elif notification.channel == "sms":
            phone = notification.data.get("phone")
            sms_template = f"notifications/sms/{event}.txt"
            print(f"Sending SMS to {phone} for event: {event}")
            message = render_to_string(sms_template, notification.data).strip()
            print(f"SMS content: {message}")
            sent = ShortMessageHelper.send_sms_via_robi(
                message=message,
                phone=phone
            )
            if sent:
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save()
                print("SMS sent successfully")
            else:
                print("Failed to send SMS")

        elif notification.channel == "app":
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save()
            print("App notification saved")

        

    except Exception as exc:
        # Update retry info
        notification.retry_count = self.request.retries + 1
        notification.error_message = str(exc)
        notification.save(update_fields=["retry_count", "error_message"])

        raise self.retry(exc=exc, countdown=60)