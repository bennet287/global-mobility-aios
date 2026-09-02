from __future__ import annotations

from sqlmodel import Session

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.services.authority_appointments import scan_appointment_reminders


@celery_app.task
def appointment_reminder_task() -> dict:
    with Session(db_module.engine) as session:
        result = scan_appointment_reminders(
            session,
            actor="appointment-reminder-monitor",
        )
        return result
