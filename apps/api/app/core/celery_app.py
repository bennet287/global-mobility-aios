from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "gmai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.agent_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    result_expires=3600,  # 1 hour
)
