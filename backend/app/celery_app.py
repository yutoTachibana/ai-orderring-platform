from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "orderring",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "auto-reconcile-daily": {
            "task": "workers.auto_reconcile",
            "schedule": crontab(hour=9, minute=0),
        },
    },
)

celery.autodiscover_tasks(["workers"])
