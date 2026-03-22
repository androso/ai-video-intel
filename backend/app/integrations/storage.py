import uuid
from google.cloud import storage as gcs
from app.core.config import settings
from pathlib import Path


def _generate_path(filename: str) -> str:
    """Generate a storage path that is unique to avoid collisions"""
    unique = uuid.uuid4().hex[:12]
    return f"originals/{unique}_{filename}"


def upload_to_gcs(file_bytes: bytes, destination: str, content_type: str) -> str:
    """Upload bytes to google cloud storage, returning the gs:// URI"""
    client = gcs.Client()
    bucket = client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(destination)
    blob.upload_from_string(file_bytes, content_type=content_type)
    return f"gs://{settings.GCS_BUCKET}/{destination}"


def upload_to_local(file_bytes: bytes, destination: str) -> str:
    """Writes bytes to the local storage directory and returns the file path"""
    path = Path(settings.LOCAL_STORAGE_DIR) / destination
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(file_bytes)
    return str(path)


def store_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Helper to store a file, tries to use gcs but fallsback to localstorage. Returns storage path"""
    destination = _generate_path(filename)
    if settings.use_local_storage:
        return upload_to_local(file_bytes, destination)
    return upload_to_gcs(file_bytes, destination, content_type)
