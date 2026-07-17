from __future__ import annotations

from sqlmodel import Session

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.services.document_requirement_assessments import scan_document_requirement_assessments


@celery_app.task
def scan_document_requirement_assessments_task() -> dict:
    with Session(db_module.engine) as session:
        result = scan_document_requirement_assessments(
            session,
            actor="document-requirement-monitor",
        )
        return {
            **result,
            "lead_id": str(result["lead_id"]) if result["lead_id"] else None,
        }
