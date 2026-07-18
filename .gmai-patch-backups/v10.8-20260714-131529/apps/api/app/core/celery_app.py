from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "gmai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.agent_tasks",
        "app.tasks.training_tasks",
        "app.tasks.source_monitor_tasks",
        "app.tasks.document_extraction_tasks",
        "app.tasks.document_expiry_tasks",
    ],
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
    beat_schedule={
        "enqueue-due-official-source-monitors": {
            "task": "app.tasks.source_monitor_tasks.enqueue_due_source_monitors",
            "schedule": 300.0,
            "args": (100,),
        },
        "scan-document-expiry-reminders": {
            "task": "app.tasks.document_expiry_tasks.scan_document_expiry_reminders_task",
            "schedule": 21600.0,
        },
    },
)
