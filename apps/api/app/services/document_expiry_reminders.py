from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import DocumentExpiryReminderTask, DocumentRecord, now_utc
from app.schemas import DocumentExpiryReminderRead
from app.services.audit_log import record_audit


ACTIVE_STATUSES = {"pending"}
REVIEW_DECISIONS = {"acknowledged", "dismissed", "resolved"}


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _same_instant(left: datetime, right: datetime) -> bool:
    return _utc(left) == _utc(right)


def _classification(expiry_date: datetime, as_of: datetime) -> dict[str, Any] | None:
    expiry = _utc(expiry_date)
    reference = _utc(as_of)
    days_remaining = (expiry.date() - reference.date()).days
    if days_remaining < 0:
        return {
            "reminder_type": "expired",
            "threshold_days": 0,
            "priority": "critical",
            "due_at": expiry,
            "days_remaining": days_remaining,
        }
    if days_remaining <= 7:
        threshold = 7
        priority = "high"
    elif days_remaining <= 30:
        threshold = 30
        priority = "warning"
    elif days_remaining <= 90:
        threshold = 90
        priority = "normal"
    else:
        return None
    return {
        "reminder_type": f"expires_within_{threshold}_days",
        "threshold_days": threshold,
        "priority": priority,
        "due_at": expiry - timedelta(days=threshold),
        "days_remaining": days_remaining,
    }


def _reminder_key(document_id: UUID, expiry_date: datetime, reminder_type: str) -> str:
    return f"document-expiry:{document_id}:{_utc(expiry_date).isoformat()}:{reminder_type}"


def reminder_read(reminder: DocumentExpiryReminderTask, *, as_of: datetime | None = None) -> DocumentExpiryReminderRead:
    reference = _utc(as_of or now_utc())
    days_remaining = (_utc(reminder.expiry_date).date() - reference.date()).days
    return DocumentExpiryReminderRead(
        **reminder.model_dump(),
        days_until_expiry=days_remaining,
        external_message_sent=False,
    )


def scan_document_expiry_reminders(
    session: Session,
    *,
    lead_id: UUID | None = None,
    as_of: datetime | None = None,
    actor: str = "document-expiry-monitor",
) -> dict[str, Any]:
    reference = _utc(as_of or now_utc())
    statement = (
        select(DocumentRecord)
        .where(DocumentRecord.expiry_date.is_not(None))
        .order_by(DocumentRecord.expiry_date, DocumentRecord.created_at)
    )
    if lead_id:
        statement = statement.where(DocumentRecord.lead_id == lead_id)
    documents = session.exec(statement).all()

    created_ids: list[str] = []
    created = existing = superseded = outside_window = 0
    for document in documents:
        assert document.expiry_date is not None
        expiry = _utc(document.expiry_date)
        classification = _classification(expiry, reference)

        stale_rows = session.exec(
            select(DocumentExpiryReminderTask)
            .where(DocumentExpiryReminderTask.document_id == document.id)
            .where(DocumentExpiryReminderTask.status == "pending")
        ).all()
        for stale in stale_rows:
            if not _same_instant(stale.expiry_date, expiry):
                stale.status = "superseded"
                stale.superseded_by_id = None
                stale.updated_at = reference
                session.add(stale)
                record_audit(
                    session,
                    action="document_expiry_reminder_superseded",
                    entity_type="document_expiry_reminder_task",
                    entity_id=stale.id,
                    before_state={"status": "pending", "expiry_date": stale.expiry_date},
                    after_state={"status": "superseded", "current_document_expiry_date": expiry},
                    reason="Document expiry date changed",
                    actor=actor,
                    source="document_expiry_monitor_v9_2",
                )
                superseded += 1

        if classification is None:
            outside_window += 1
            continue

        key = _reminder_key(document.id, expiry, classification["reminder_type"])
        current = session.exec(
            select(DocumentExpiryReminderTask).where(DocumentExpiryReminderTask.reminder_key == key)
        ).first()
        if current is not None:
            existing += 1
            continue

        reminder = DocumentExpiryReminderTask(
            reminder_key=key,
            document_id=document.id,
            lead_id=document.lead_id,
            document_type=document.document_type,
            filename=document.filename,
            expiry_date=expiry,
            reminder_type=classification["reminder_type"],
            threshold_days=classification["threshold_days"],
            due_at=classification["due_at"],
            priority=classification["priority"],
            generated_by=actor,
            created_at=reference,
            updated_at=reference,
        )
        session.add(reminder)
        session.flush()

        prior_pending = session.exec(
            select(DocumentExpiryReminderTask)
            .where(DocumentExpiryReminderTask.document_id == document.id)
            .where(DocumentExpiryReminderTask.status == "pending")
            .where(DocumentExpiryReminderTask.id != reminder.id)
        ).all()
        for prior in prior_pending:
            if _same_instant(prior.expiry_date, expiry):
                prior.status = "superseded"
                prior.superseded_by_id = reminder.id
                prior.updated_at = reference
                session.add(prior)
                record_audit(
                    session,
                    action="document_expiry_reminder_superseded",
                    entity_type="document_expiry_reminder_task",
                    entity_id=prior.id,
                    before_state={"status": "pending", "reminder_type": prior.reminder_type},
                    after_state={"status": "superseded", "superseded_by_id": reminder.id},
                    reason="A more urgent reminder threshold became active",
                    actor=actor,
                    source="document_expiry_monitor_v9_2",
                )
                superseded += 1

        record_audit(
            session,
            action="document_expiry_reminder_created",
            entity_type="document_expiry_reminder_task",
            entity_id=reminder.id,
            after_state={
                "document_id": document.id,
                "lead_id": document.lead_id,
                "expiry_date": expiry,
                "reminder_type": reminder.reminder_type,
                "priority": reminder.priority,
                "external_delivery_status": reminder.external_delivery_status,
            },
            reason="Document entered a configured expiry urgency window",
            actor=actor,
            source="document_expiry_monitor_v9_2",
        )
        created += 1
        created_ids.append(str(reminder.id))

    record_audit(
        session,
        action="document_expiry_scan_completed",
        entity_type="document_expiry_monitor",
        entity_id=lead_id or "global",
        after_state={
            "as_of": reference,
            "lead_id": lead_id,
            "documents_scanned": len(documents),
            "created": created,
            "existing": existing,
            "superseded": superseded,
            "outside_window": outside_window,
            "external_messages_sent": 0,
        },
        reason="Completed deterministic document expiry scan",
        actor=actor,
        source="document_expiry_monitor_v9_2",
    )
    session.commit()
    return {
        "as_of": reference,
        "lead_id": lead_id,
        "documents_scanned": len(documents),
        "created": created,
        "existing": existing,
        "superseded": superseded,
        "outside_window": outside_window,
        "reminder_ids": created_ids,
        "external_messages_sent": 0,
    }


def review_document_expiry_reminder(
    session: Session,
    reminder_id: UUID,
    *,
    decision: str,
    notes: str,
    actor: str,
) -> DocumentExpiryReminderTask:
    if decision not in REVIEW_DECISIONS:
        raise ValueError("Unsupported reminder review decision")
    reminder = session.get(DocumentExpiryReminderTask, reminder_id)
    if reminder is None:
        raise ValueError("Document expiry reminder not found")
    if reminder.status != "pending":
        raise ValueError("Only a pending document expiry reminder can be reviewed")
    cleaned_notes = notes.strip()
    if len(cleaned_notes) < 3:
        raise ValueError("A review note is required")
    before = reminder.model_dump()
    reviewed_at = now_utc()
    reminder.status = decision
    reminder.reviewed_by = actor
    reminder.reviewed_at = reviewed_at
    reminder.review_notes = cleaned_notes
    reminder.updated_at = reviewed_at
    session.add(reminder)
    record_audit(
        session,
        action=f"document_expiry_reminder_{decision}",
        entity_type="document_expiry_reminder_task",
        entity_id=reminder.id,
        before_state=before,
        after_state=reminder,
        reason=cleaned_notes,
        actor=actor,
        source="document_expiry_monitor_v9_2",
    )
    session.commit()
    session.refresh(reminder)
    return reminder
