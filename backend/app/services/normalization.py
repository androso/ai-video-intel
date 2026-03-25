import logging
import os
import tempfile

from sqlalchemy.orm import Session

from app.integrations.storage import download_file, store_file
from app.models.models import ProcessingJob, VideoAsset
from app.services.ffmpeg import generate_thumbnail, probe_media, transcode_to_standard

logger = logging.getLogger(__name__)


def execute_normalization(
    db: Session, asset: VideoAsset, job: ProcessingJob
) -> None:
    """Run the full normalization pipeline for a single asset.

    1. Download the original file to a local temp directory
    2. Probe media metadata
    3. Transcode to H.264/AAC MP4 (or stream-copy if already normalized)
    4. Generate a thumbnail at 25% of duration
    5. Upload normalized file and thumbnail to storage
    6. Update the asset record with paths and metadata
    """
    tmp_dir = tempfile.mkdtemp(prefix="normalize_")
    downloaded_path: str | None = None

    try:
        # 1. Download original to local filesystem
        local_input = download_file(asset.original_storage_path)
        # Track GCS downloads for cleanup (local paths shouldn't be deleted)
        if local_input != asset.original_storage_path:
            downloaded_path = local_input

        # 2. Probe
        media_info = probe_media(local_input)

        # 3. Transcode
        normalized_filename = f"{asset.id}_normalized.mp4"
        local_normalized = os.path.join(tmp_dir, normalized_filename)
        transcode_to_standard(local_input, local_normalized, media_info)

        # 4. Thumbnail at 25% of duration (fall back to 0 for very short videos)
        thumb_filename = f"{asset.id}_thumb.jpg"
        local_thumb = os.path.join(tmp_dir, thumb_filename)
        thumb_ts = media_info.duration_seconds * 0.25 if media_info.duration_seconds > 1 else 0.0
        generate_thumbnail(local_normalized, local_thumb, timestamp=thumb_ts)

        # 5. Upload results
        with open(local_normalized, "rb") as f:
            normalized_bytes = f.read()
        normalized_path = store_file(
            normalized_bytes, normalized_filename, "video/mp4", prefix="normalized"
        )

        with open(local_thumb, "rb") as f:
            thumb_bytes = f.read()
        thumbnail_path = store_file(
            thumb_bytes, thumb_filename, "image/jpeg", prefix="thumbnails"
        )

        # 6. Update asset record
        asset.normalized_storage_path = normalized_path
        asset.thumbnail_path = thumbnail_path
        asset.duration_seconds = media_info.duration_seconds
        asset.technical_metadata = media_info.to_dict()
        db.commit()

        logger.info("Normalization complete for asset %s", asset.id)

    finally:
        # Cleanup temp files
        for path in [
            os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir)
        ]:
            _safe_remove(path)
        _safe_remove(tmp_dir, is_dir=True)
        if downloaded_path:
            _safe_remove(downloaded_path)


def _safe_remove(path: str, is_dir: bool = False) -> None:
    """Remove a file or directory, logging but not raising on failure"""
    try:
        if is_dir:
            os.rmdir(path)
        else:
            os.remove(path)
    except OSError:
        logger.debug("Could not remove temp path: %s", path)
