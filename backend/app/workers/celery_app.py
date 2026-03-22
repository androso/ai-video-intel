from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_video_intel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True
)

celery_app.autodiscover_tasks(["app.workers"])