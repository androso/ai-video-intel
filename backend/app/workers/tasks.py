import logging
from datetime import datetime, timezone
from uuid import UUID

from app.db.session import SessionLocal
from app.models.enums import AssetStatus, JobStatus, StepName, StepStatus
from app.models.models import ProcessingJob, VideoAsset
from app.services.normalization import execute_normalization
from app.services.step_runner import run_step
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_video", bind=True, max_retries=3)
def process_video(self, asset_id: str, job_id: str) -> dict:
    logger.info("Starting pipeline for asset=%s job=%s", asset_id, job_id)

    db = SessionLocal()
    try:
        asset = db.get(VideoAsset, UUID(asset_id))
        job = db.get(ProcessingJob, UUID(job_id))

        if asset is None or job is None:
            logger.error("Asset or job not found: asset=%s job=%s", asset_id, job_id)
            return {"asset_id": asset_id, "job_id": job_id, "status": "not_found"}

        # Mark job and asset as processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        asset.status = AssetStatus.PROCESSING
        db.commit()

        # Step 1: Normalization
        norm_status = run_step(
            db, job.id, StepName.NORMALIZATION,
            lambda: execute_normalization(db, asset, job),
        )

        if norm_status == StepStatus.FAILED:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            asset.status = AssetStatus.FAILED
            db.commit()
            logger.error("Pipeline failed at normalization for asset=%s", asset_id)
            return {"asset_id": asset_id, "job_id": job_id, "status": "failed"}

        # TODO: Steps 2-4
        # 2. audio_extraction
        # 3. transcription
        # 4. ai_enrichment

        # All steps complete
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        asset.status = AssetStatus.READY
        db.commit()

        logger.info("Pipeline complete for asset=%s job=%s", asset_id, job_id)
        return {"asset_id": asset_id, "job_id": job_id, "status": "completed"}

    except Exception as exc:
        logger.exception("Unhandled error in pipeline for asset=%s job=%s", asset_id, job_id)
        try:
            if "job" in locals() and job is not None:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
            if "asset" in locals() and asset is not None:
                asset.status = AssetStatus.FAILED
            db.commit()
        except Exception:
            logger.exception("Failed to persist failure state for asset=%s job=%s", asset_id, job_id)
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()