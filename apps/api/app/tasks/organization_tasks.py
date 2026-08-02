from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.core.celery_app import celery_app
from app.core.db import engine
from app.models.domain import OrganizationalWorkItem
from app.services.organization_governance import execute_work_item


@celery_app.task(name="app.tasks.organization_tasks.execute_organization_work_item")
def execute_organization_work_item_task(work_item_id: str) -> dict:
    with Session(engine) as session:
        work = session.get(OrganizationalWorkItem, UUID(work_item_id))
        if work is None:
            return {"status": "not_found", "work_item_id": work_item_id}
        try:
            result = execute_work_item(session, work)
        except ValueError as exc:
            return {"status": "skipped", "work_item_id": work_item_id, "reason": str(exc)}
        return {"status": result.status, "work_item_id": str(result.id)}


@celery_app.task(name="app.tasks.organization_tasks.scan_organization_work")
def scan_organization_work_task(limit: int = 25) -> dict:
    with Session(engine) as session:
        ids = session.exec(
            select(OrganizationalWorkItem.id)
            .where(OrganizationalWorkItem.status == "queued")
            .order_by(OrganizationalWorkItem.created_at)
            .limit(max(1, min(limit, 100)))
        ).all()
    for work_id in ids:
        execute_organization_work_item_task.delay(str(work_id))
    return {"queued": len(ids), "work_item_ids": [str(item) for item in ids]}
