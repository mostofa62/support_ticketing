import uuid
from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator

from ict_support.validators import validate_file_size, validate_mime_type

def temp_upload_path(instance, filename):
    return f"temp/{uuid.uuid4()}_{filename}"

class TempAttachment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=temp_upload_path,
        validators=[
            FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']),
            validate_file_size,
            validate_mime_type
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
