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
        "app.tasks.document_requirement_tasks",
        "app.tasks.document_fraud_risk_tasks",
        "app.tasks.document_access_tasks",
        "app.tasks.automation_tasks",
        "app.tasks.authority_checklist_tasks",
        "app.tasks.authority_appointment_tasks",
        "app.tasks.external_agency_sla_tasks",
        "app.tasks.organization_tasks",
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
        "scan-document-requirement-assessments": {
            "task": "app.tasks.document_requirement_tasks.scan_document_requirement_assessments_task",
            "schedule": 43200.0,
        },
        "scan-document-fraud-risk-assessments": {
            "task": "app.tasks.document_fraud_risk_tasks.scan_document_fraud_risk_assessments_task",
            "schedule": 43200.0,
        },
        "expire-document-access-grants": {
            "task": "app.tasks.document_access_tasks.expire_document_access_grants_task",
            "schedule": 3600.0,
        },
        "dispatch-ready-automation-deliveries": {
            "task": "app.tasks.automation_tasks.dispatch_automation_deliveries_task",
            "schedule": 60.0,
            "args": (100,),
        },
        "reconcile-dispatched-automation-deliveries": {
            "task": "app.tasks.automation_tasks.reconcile_automation_deliveries_task",
            "schedule": 86400.0,
            "args": (24,),
        },
        "scan-authority-checklist-reminders": {
            "task": "app.tasks.authority_checklist_tasks.scan_checklist_reminders_task",
            "schedule": 86400.0,
        },
        "appointment-reminders": {
            "task": "app.tasks.authority_appointment_tasks.appointment_reminder_task",
            "schedule": 3600.0,
        },
        "evaluate-external-agency-assignment-sla": {
            "task": "app.tasks.external_agency_sla_tasks.evaluate_external_agency_assignment_sla_task",
            "schedule": 3600.0,
        },
        "scan-ai-organization-work": {
            "task": "app.tasks.organization_tasks.scan_organization_work",
            "schedule": 30.0,
            "args": (25,),
        },
        "coordinate-pending-ceo-decisions": {
            "task": "app.tasks.organization_tasks.scan_ceo_decisions",
            "schedule": 30.0,
            "args": (25,),
        },
        "generate-daily-board-packet": {
            "task": "app.tasks.organization_tasks.generate_recurring_board_packet",
            "schedule": 86400.0,
            "args": ("daily",),
        },
        "generate-weekly-board-packet": {
            "task": "app.tasks.organization_tasks.generate_recurring_board_packet",
            "schedule": 604800.0,
            "args": ("weekly",),
        },
    },
)
