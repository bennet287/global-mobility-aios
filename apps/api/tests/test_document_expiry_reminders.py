from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog, DocumentExpiryReminderTask, DocumentRecord, now_utc
from app.services.document_expiry_reminders import scan_document_expiry_reminders

from .conftest import create_lead


def _document(
    session: Session,
    *,
    lead_id: UUID,
    expiry_date: datetime,
    filename: str = "passport.pdf",
) -> DocumentRecord:
    row = DocumentRecord(
        lead_id=lead_id,
        document_type="passport",
        filename=filename,
        status="received",
        expiry_date=expiry_date,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_expiry_scan_is_deduplicated_and_supersedes_less_urgent_tasks(
    db_session: Session,
) -> None:
    reference = datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)
    lead = create_lead(db_session, name="Expiry Monitor Lead")
    document = _document(
        db_session,
        lead_id=lead.id,
        expiry_date=reference + timedelta(days=20),
    )

    first = scan_document_expiry_reminders(
        db_session,
        lead_id=lead.id,
        as_of=reference,
        actor="pytest-monitor",
    )
    assert first["created"] == 1
    assert first["external_messages_sent"] == 0
    tasks = db_session.exec(select(DocumentExpiryReminderTask)).all()
    assert len(tasks) == 1
    assert tasks[0].reminder_type == "expires_within_30_days"
    assert tasks[0].status == "pending"
    assert tasks[0].external_delivery_status == "not_sent"

    repeated = scan_document_expiry_reminders(
        db_session,
        lead_id=lead.id,
        as_of=reference,
        actor="pytest-monitor",
    )
    assert repeated["created"] == 0
    assert repeated["existing"] == 1
    assert len(db_session.exec(select(DocumentExpiryReminderTask)).all()) == 1

    urgent = scan_document_expiry_reminders(
        db_session,
        lead_id=lead.id,
        as_of=reference + timedelta(days=15),
        actor="pytest-monitor",
    )
    assert urgent["created"] == 1
    assert urgent["superseded"] == 1
    tasks = db_session.exec(
        select(DocumentExpiryReminderTask).order_by(DocumentExpiryReminderTask.created_at)
    ).all()
    assert [task.reminder_type for task in tasks] == ["expires_within_30_days", "expires_within_7_days"]
    assert tasks[0].status == "superseded"
    assert tasks[0].superseded_by_id == tasks[1].id
    assert tasks[1].status == "pending"

    expired = scan_document_expiry_reminders(
        db_session,
        lead_id=lead.id,
        as_of=reference + timedelta(days=21),
        actor="pytest-monitor",
    )
    assert expired["created"] == 1
    assert expired["superseded"] == 1
    active = db_session.exec(
        select(DocumentExpiryReminderTask)
        .where(DocumentExpiryReminderTask.document_id == document.id)
        .where(DocumentExpiryReminderTask.status == "pending")
    ).all()
    assert len(active) == 1
    assert active[0].reminder_type == "expired"
    assert active[0].priority == "critical"

    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type.in_([
                "document_expiry_reminder_task",
                "document_expiry_monitor",
            ]))
        ).all()
    }
    assert {
        "document_expiry_reminder_created",
        "document_expiry_reminder_superseded",
        "document_expiry_scan_completed",
    } <= actions


def test_changed_expiry_date_supersedes_stale_task_without_creating_future_noise(
    db_session: Session,
) -> None:
    reference = datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)
    lead = create_lead(db_session, name="Renewed Passport Lead")
    document = _document(
        db_session,
        lead_id=lead.id,
        expiry_date=reference + timedelta(days=10),
    )
    scan_document_expiry_reminders(db_session, lead_id=lead.id, as_of=reference)

    document.expiry_date = reference + timedelta(days=365)
    document.updated_at = reference + timedelta(hours=1)
    db_session.add(document)
    db_session.commit()

    result = scan_document_expiry_reminders(
        db_session,
        lead_id=lead.id,
        as_of=reference + timedelta(hours=2),
    )
    assert result["created"] == 0
    assert result["superseded"] == 1
    assert result["outside_window"] == 1
    task = db_session.exec(select(DocumentExpiryReminderTask)).one()
    assert task.status == "superseded"
    assert task.superseded_by_id is None


def test_expiry_reminder_api_requires_human_review_and_never_sends_messages(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session, name="Expiry Review Lead")
    _document(
        db_session,
        lead_id=lead.id,
        expiry_date=now_utc() + timedelta(days=5),
    )

    scanned = client.post(
        "/api/v1/document-intelligence/expiry-reminders/scan",
        json={"lead_id": str(lead.id)},
    )
    assert scanned.status_code == 200, scanned.text
    assert scanned.json()["created"] == 1
    assert scanned.json()["external_messages_sent"] == 0

    listed = client.get(
        f"/api/v1/document-intelligence/expiry-reminders?lead_id={lead.id}"
    )
    assert listed.status_code == 200, listed.text
    reminder = listed.json()[0]
    assert reminder["status"] == "pending"
    assert reminder["external_delivery_status"] == "not_sent"
    assert reminder["external_message_sent"] is False
    assert reminder["days_until_expiry"] in {4, 5}

    missing_note = client.post(
        f"/api/v1/document-intelligence/expiry-reminders/{reminder['id']}/review",
        json={"decision": "acknowledged", "notes": ""},
    )
    assert missing_note.status_code == 422

    reviewed = client.post(
        f"/api/v1/document-intelligence/expiry-reminders/{reminder['id']}/review",
        json={
            "decision": "acknowledged",
            "notes": "Renewal evidence requested through the controlled case workflow.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "acknowledged"
    assert reviewed.json()["reviewed_by"] == "pytest-admin"
    assert reviewed.json()["external_message_sent"] is False

    repeated = client.post(
        f"/api/v1/document-intelligence/expiry-reminders/{reminder['id']}/review",
        json={"decision": "resolved", "notes": "Duplicate review should be blocked."},
    )
    assert repeated.status_code == 400

    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type == "document_expiry_reminder_task")
        ).all()
    }
    assert "document_expiry_reminder_acknowledged" in actions
