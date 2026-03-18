from celery import shared_task
from django.utils import timezone

from .services.sms_service import ShortMessageHelper
from .models import Notification

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import transaction
# -----------------------------
# Main notification sender
# -----------------------------
@shared_task(bind=True, max_retries=3)
def send_notification(self, notification_id):
    try:
        with transaction.atomic():
            notification = Notification.objects.select_for_update().get(id=notification_id)
            print('notification',notification)
            # ❗ Idempotency check
            if notification.is_sent:
                print(f"[Skip] Notification {notification.id} already sent")
                return
            event = notification.event_type
    
            if notification.channel == "email":
                subject_template = f"notifications/email/{event}_subject.txt"
                body_template = f"notifications/email/{event}_body.html"
                subject = render_to_string(subject_template, notification.data).strip()
                body_html = render_to_string(body_template, notification.data)
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=body_html,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[notification.data.get("email")],
                )
                email.attach_alternative(body_html, "text/html")
                if email.send():
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
        print('Execption',exec)
        notification.retry_count = self.request.retries + 1
        notification.error_message = str(exc)
        notification.save(update_fields=["retry_count", "error_message"])
        raise self.retry(exc=exc, countdown=60)


# -----------------------------
# Periodic retry task (Beat)
# -----------------------------
@shared_task
def retry_unsent_notifications():
    """
    Find all unsent notifications and enqueue them to be sent again.
    """
    pending_notifications = Notification.objects.filter(is_sent=False)

    for notification in pending_notifications:
        try:
            send_notification.apply_async(
                args=[notification.id],
                ignore_result=True,
                queue="notifications",
            )
            print(f"[Retry] Notification {notification.id} re-enqueued successfully")
        except Exception as e:
            print(f"[Retry] Failed to enqueue notification {notification.id}: {e}")