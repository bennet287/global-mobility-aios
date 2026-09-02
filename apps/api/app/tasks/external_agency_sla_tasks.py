from __future__ import annotations

from sqlmodel import Session

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.services.external_agencies import scan_assignment_sla_evaluations


@celery_app.task
def evaluate_external_agency_assignment_sla_task() -> dict:
    with Session(db_module.engine) as session:
        result = scan_assignment_sla_evaluations(
            session,
            actor="external-agency-sla-monitor",
        )
        return result
