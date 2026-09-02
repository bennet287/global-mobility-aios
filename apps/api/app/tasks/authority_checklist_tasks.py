from __future__ import annotations

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.services.authority_checklists import scan_checklist_reminders
from sqlmodel import Session


@celery_app.task
def scan_checklist_reminders_task() -> dict:
    with Session(db_module.engine) as session:
        result = scan_checklist_reminders(
            session,
            actor="authority-checklist-monitor",
        )
        return result
