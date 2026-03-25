import os
import tempfile
import uuid
from pathlib import Path

from google.cloud import storage as gcs

from app.core.config import settings


def _generate_path(filename: str, prefix: str = "originals") -> str:
    """Generate a storage path that is unique to avoid collisions"""
    unique = uuid.uuid4().hex[:12]
    return f"{prefix}/{unique}_{filename}"


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


def store_file(
    file_bytes: bytes, filename: str, content_type: str, prefix: str = "originals"
) -> str:
    """Helper to store a file, tries to use gcs but fallsback to localstorage.
       Returns storage path"""
    destination = _generate_path(filename, prefix=prefix)
    if settings.use_local_storage:
        return upload_to_local(file_bytes, destination)
    return upload_to_gcs(file_bytes, destination, content_type)


def download_file(storage_path: str) -> str:
    """Download a file to a local temp path and return that path.

    For local storage the file is already on disk, so this returns the
    existing path directly.  For GCS (gs:// URIs) the blob is downloaded
    to a temporary file.
    """
    if storage_path.startswith("gs://"):
        without_scheme = storage_path[len("gs://"):]
        bucket_name, blob_name = without_scheme.split("/", 1)
        client = gcs.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        suffix = Path(blob_name).suffix or ".bin"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        # The file descriptor from mkstemp must be closed before ffmpeg reads it.
        # This avoids leaks and cross-platform locking issues.
        try:
            os.close(fd)
            blob.download_to_filename(tmp_path)
            return tmp_path
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    # Local storage — the path is already on disk
    return storage_path
