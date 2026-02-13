# ict_support/signals.py
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Attachment  # your model

@receiver(post_delete, sender=Attachment)
def delete_file_on_delete(sender, instance, **kwargs):
    """Delete file from storage when Attachment is deleted."""
    if instance.file:
        instance.file.delete(False)

@receiver(pre_save, sender=Attachment)
def delete_old_file_on_change(sender, instance, **kwargs):
    """Delete old file from storage when Attachment is updated with a new file."""
    if not instance.pk:
        return  # new object, nothing to delete

    try:
        old_file = sender.objects.get(pk=instance.pk).file
    except sender.DoesNotExist:
        return

    new_file = instance.file
    if old_file and old_file != new_file:
        old_file.delete(False)
