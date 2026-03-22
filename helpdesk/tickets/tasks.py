from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import TempAttachment
from django.conf import settings

@shared_task
def cleanup_temp_attachments():
    threshold = timezone.now() - timedelta(
        minutes=settings.TEMP_ATTACHMENT_THRESHOLD_MINUTES
    )

    print(f"Threshold: {threshold}")

    old_files = TempAttachment.objects.filter(uploaded_at__lt=threshold)

    print(f"Found {old_files.count()} files")

    for temp in old_files:
        print("FILE PATH:", temp.file.path)

        if temp.file:
            try:
                temp.file.delete(save=False)
                print("Deleted file")
            except Exception as e:
                print("File delete failed:", e)

        temp.delete()