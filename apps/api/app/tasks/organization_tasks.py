from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.core.celery_app import celery_app
from app.core import db as db_module
from app.models.domain import ExecutiveDecision, OrganizationalWorkItem
from app.services.organization_governance import (
    create_board_packet,
    escalate_work_item,
    execute_work_item,
)


@celery_app.task(name="app.tasks.organization_tasks.execute_organization_work_item")
def execute_organization_work_item_task(work_item_id: str) -> dict:
    with Session(db_module.engine) as session:
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
    with Session(db_module.engine) as session:
        ids = session.exec(
            select(OrganizationalWorkItem.id)
            .where(OrganizationalWorkItem.status == "queued")
            .order_by(OrganizationalWorkItem.created_at)
            .limit(max(1, min(limit, 100)))
        ).all()
    for work_id in ids:
        execute_organization_work_item_task.delay(str(work_id))
    return {"queued": len(ids), "work_item_ids": [str(item) for item in ids]}


@celery_app.task(name="app.tasks.organization_tasks.scan_organization_deadlines")
def scan_organization_deadlines_task(overdue_seconds: int = 60, reminder_seconds: int = 30) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    escalated = 0
    reminded = 0
    with Session(db_module.engine) as session:
        overdue_work = session.exec(
            select(OrganizationalWorkItem).where(
                OrganizationalWorkItem.status.in_(["queued", "running", "pending_ceo", "pending_board"]),
                OrganizationalWorkItem.due_at < now,
                OrganizationalWorkItem.escalated_at.is_(None),
            )
        ).all()
        for work in overdue_work:
            due_at = work.due_at
            if due_at and due_at.tzinfo:
                due_at = due_at.replace(tzinfo=None)
            overdue = due_at and (now - due_at).total_seconds() >= overdue_seconds
            if work.is_emergency or overdue:
                try:
                    escalate_work_item(session, work, reason="Overdue deadline triggered automatic escalation.", actor="organization-deadline-scanner")
                    escalated += 1
                except ValueError:
                    pass

        overdue_decisions = session.exec(
            select(ExecutiveDecision).where(
                ExecutiveDecision.status.in_(["pending_ceo", "pending_board"]),
                ExecutiveDecision.due_at < now,
                ExecutiveDecision.reminded_at.is_(None),
            )
        ).all()
        for decision in overdue_decisions:
            decision.reminded_at = now
            session.add(decision)
            reminded += 1
        session.commit()
    return {"escalated": escalated, "reminded": reminded}


@celery_app.task(name="app.tasks.organization_tasks.generate_recurring_board_packet")
def generate_recurring_board_packet_task(packet_type: str = "daily") -> dict:
    with Session(db_module.engine) as session:
        packet = create_board_packet(
            session,
            packet_type=packet_type,
            actor="organization-board-packet-scheduler",
        )
    return {"packet_id": str(packet.id), "packet_type": packet_type, "packet_key": packet.packet_key}
