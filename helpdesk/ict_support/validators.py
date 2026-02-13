from django.core.exceptions import ValidationError
from django.conf import settings

def validate_file_size(value):
    max_size = settings.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024

    if value.size > max_size:
        raise ValidationError(
            f"File size must be under {settings.MAX_ATTACHMENT_SIZE_MB}MB."
        )


import magic

def validate_mime_type(value):
    mime = magic.from_buffer(value.read(1024), mime=True)
    value.seek(0)

    allowed_mimes = [
        'application/pdf',
        'image/jpeg',
        'image/png',
    ]

    if mime not in allowed_mimes:
        raise ValidationError("Unsupported file type.")
