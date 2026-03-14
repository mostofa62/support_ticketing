from ..models import Notification
from ..tasks import send_notification

def create_notification(user, event_type, channel, data):
    notification = Notification.objects.create(
        recipient=user,
        event_type=event_type,
        channel=channel,
        data=data
    )

    send_notification.delay(notification.id)