import logging

from app.workers.celery_app import celery_app
logger = logging.getLogger(__name__)


@celery_app.task(name="process_video", bind=True, max_retries=3)
def process_video(self, asset_id, job_id: str) -> dict:
    logger.info("Starting pipeline for asset=%s job=%s", asset_id, job_id)

    # TODO: implement each stage
    # 1. normalize_video
    # 2. extract_audio
    # 3. transcribe
    # 4. enrich

    logger.info("Pipeline stub complete for asset=%s job=%s", asset_id, job_id)
    return {
        "asset_id": asset_id,
        "job_id": job_id,
        "status": "stub_complete"
    }