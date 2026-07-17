from __future__ import annotations

from sqlmodel import Session

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.services.document_expiry_reminders import scan_document_expiry_reminders


@celery_app.task
def scan_document_expiry_reminders_task() -> dict:
    with Session(db_module.engine) as session:
        result = scan_document_expiry_reminders(
            session,
            actor="document-expiry-monitor",
        )
        return {
            **result,
            "as_of": result["as_of"].isoformat(),
            "lead_id": str(result["lead_id"]) if result["lead_id"] else None,
        }
