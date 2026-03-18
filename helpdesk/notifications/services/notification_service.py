from ..models import Notification
from ..tasks import send_notification
from django.db import transaction

def create_notification(user, event_type, channel, data):
    notification = Notification.objects.create(
        recipient=user,
        event_type=event_type,
        channel=channel,
        data=data,
        is_sent=False,
        retry_count=0,
    )

    def enqueue():
        try:
            send_notification.apply_async(
                args=[notification.id],
                ignore_result=True,
                queue="notifications",  # optional, good for later scaling
            )
            print(f"Notification {notification.id} enqueued successfully")
        except Exception as e:
            # ❗ Never break user request
            print(f"Celery enqueue failed for notification {notification.id}: {e}")

    transaction.on_commit(enqueue)

    return notification