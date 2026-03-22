from sqlalchemy.orm import Session
from app.models.models import JobStep, VideoAsset, ProcessingJob
from app.models.enums import AssetStatus, JobStatus, StepStatus

# Ordered pipeline stages
PIPELINE_STEPS = [
    (1, "normalization"),
    (2, "audio_extraction"),
    (3, "transcription"),
    (4, "ai_enrichment"),
]


def create_asset_with_job(
    db: Session,
    *,
    filename: str,
    storage_path: str,
    mime_type: str,
    file_size_bytes: int
) -> tuple[VideoAsset, ProcessingJob]:
    """Create a VideoAsset and a ProcessingJob with all step records in a single transaction"""

    asset = VideoAsset(
        filename=filename,
        original_storage_path=storage_path,
        status=AssetStatus.UPLOADED,
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
    )
    db.add(asset)
    db.flush()

    job = ProcessingJob(asset_id=asset.id, status=JobStatus.QUEUED)

    db.add(job)
    db.flush()

    for order, name in PIPELINE_STEPS:
        step = JobStep(
            job_id=job.id,
            step_name=name,
            step_order=order,
            status=StepStatus.PENDING,
            attempts=0,
            max_attempts=3
        )
        db.add(step)
    db.commit()
    db.refresh(asset)
    db.refresh(job)

    return asset, job

