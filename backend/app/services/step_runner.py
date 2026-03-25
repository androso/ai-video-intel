import logging
from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import StepName, StepStatus
from app.models.models import JobStep

logger = logging.getLogger(__name__)


def run_step(
    db: Session, job_id: UUID, step_name: StepName, execute_fn: Callable[[], None]
) -> StepStatus:
    """Execute a single pipeline step with lifecycle management.

    Handles idempotency (skips completed steps), attempt tracking,
    and status transitions.  The caller supplies *execute_fn* which
    contains the actual work — this wrapper only manages the JobStep record.

    Returns the final StepStatus after execution.
    """
    step = (
        db.query(JobStep)
        .filter(JobStep.job_id == job_id, JobStep.step_name == step_name)
        .one()
    )

    if step.status == StepStatus.COMPLETED:
        logger.info("Step '%s' already completed for job %s, skipping", step_name, job_id)
        return StepStatus.COMPLETED

    if step.attempts >= step.max_attempts:
        logger.warning(
            "Step '%s' for job %s has exhausted %d attempts, marking FAILED",
            step_name, job_id, step.max_attempts,
        )
        step.status = StepStatus.FAILED
        db.commit()
        return StepStatus.FAILED

    step.status = StepStatus.PROCESSING
    step.attempts += 1
    step.started_at = datetime.now(timezone.utc)
    step.error_message = None
    db.commit()

    try:
        execute_fn()
    except Exception as exc:
        logger.exception("Step '%s' failed for job %s on attempt %d", step_name, job_id, step.attempts)
        step.status = StepStatus.FAILED
        step.error_message = str(exc)
        step.completed_at = datetime.now(timezone.utc)
        db.commit()
        return StepStatus.FAILED

    step.status = StepStatus.COMPLETED
    step.completed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("Step '%s' completed for job %s", step_name, job_id)
    return StepStatus.COMPLETED
