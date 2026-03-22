from fastapi import UploadFile

from app.core.config import settings

class ValidationError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail

async def validate_upload(file: UploadFile) -> bytes:
    """Validate mime type and file size. Returns the raw bytes if valid."""
 
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Unsupported file type '{file.content_type}'. "
            f"Allowed: {', '.join(sorted(settings.ALLOWED_MIME_TYPES))}"
        )
 
    contents = await file.read()
    if len(contents) > settings.max_upload_size_bytes:
        size_mb = len(contents) / (1024 * 1024)
        raise ValidationError(
            f"File size {size_mb:.1f} MB exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit."
        )
 
    if len(contents) == 0:
        raise ValidationError("Uploaded file is empty.")
 
    return contents