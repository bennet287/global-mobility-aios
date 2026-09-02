from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import AgencySubmission, ApplicationRecord
from app.schemas_agency_submissions import AgencySubmissionCreate
from app.services.audit_log import record_audit, to_audit_dict
from app.services.automation_bridge import capture_application_status_event
from app.services.authority_checklists import validate_required_checklist_items_complete
from app.services.external_action_gates import assert_agency_submission_tracking_authorized


SUBMISSION_CHANNELS = {"online", "in_person", "courier", "agency"}
SUBMISSION_STATUSES = {
    "submitted",
    "acknowledged",
    "under_review",
    "decision_received",
    "returned",
}
TERMINAL_STATUSES = {"decision_received", "returned"}

# Forward-only transitions. Submitted -> acknowledged -> under_review -> terminal.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "submitted": {"acknowledged"},
    "acknowledged": {"under_review"},
    "under_review": {"decision_received", "returned"},
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _submission_to_dict(submission: AgencySubmission) -> dict:
    return to_audit_dict(submission)


def create_submission(
    session: Session,
    payload: AgencySubmissionCreate,
    *,
    actor: str,
) -> AgencySubmission:
    application = session.get(ApplicationRecord, payload.application_id)
    if application is None:
        raise ValueError("Application not found")

    assert_agency_submission_tracking_authorized(application)

    validate_required_checklist_items_complete(
        session, application.id, payload.authority_name
    )

    channel = payload.submission_channel.strip().lower()
    if channel not in SUBMISSION_CHANNELS:
        raise ValueError(f"Invalid submission channel: {payload.submission_channel}")

    submission = AgencySubmission(
        application_id=application.id,
        authority_name=payload.authority_name.strip(),
        submission_channel=channel,
        submitted_at=payload.submitted_at,
        reference_number=payload.reference_number.strip() if payload.reference_number else None,
        tracking_url=payload.tracking_url.strip() if payload.tracking_url else None,
        notes=payload.notes.strip() if payload.notes else None,
        created_by=actor,
        updated_by=actor,
        status="submitted",
    )
    session.add(submission)
    session.flush()

    record_audit(
        session,
        action="agency_submission_created",
        entity_type="agency_submission",
        entity_id=submission.id,
        after_state=_submission_to_dict(submission),
        actor=actor,
        source="agency_submission_v12_6",
    )
    session.commit()
    session.refresh(submission)
    return submission


def update_submission_status(
    session: Session,
    submission: AgencySubmission,
    *,
    status: str,
    reason: str,
    actor: str,
) -> AgencySubmission:
    normalized_status = status.strip().lower()
    if normalized_status not in SUBMISSION_STATUSES:
        raise ValueError(f"Invalid submission status: {status}")

    if submission.status in TERMINAL_STATUSES:
        raise ValueError(
            f"Cannot change status from terminal state {submission.status}"
        )

    allowed = _ALLOWED_TRANSITIONS.get(submission.status, set())
    if normalized_status not in allowed:
        raise ValueError(
            f"Cannot transition from {submission.status} to {normalized_status}"
        )

    before = _submission_to_dict(submission)
    application = session.get(ApplicationRecord, submission.application_id)
    now = _now()
    submission.status = normalized_status
    submission.updated_by = actor
    submission.updated_at = now
    session.add(submission)

    record_audit(
        session,
        action=f"agency_submission_{normalized_status}",
        entity_type="agency_submission",
        entity_id=submission.id,
        before_state=before,
        after_state=_submission_to_dict(submission),
        reason=reason.strip(),
        actor=actor,
        source="agency_submission_v12_6",
    )
    session.commit()
    session.refresh(submission)

    if application is not None:
        capture_application_status_event(
            session,
            application=application,
            event_type="submission.status_changed",
            entity_type="agency_submission",
            entity_id=submission.id,
            status=normalized_status,
            actor=actor,
        )

    return submission


def list_submissions_for_application(
    session: Session,
    application_id: UUID,
    *,
    status: str | None = None,
) -> Sequence[AgencySubmission]:
    statement = (
        select(AgencySubmission)
        .where(AgencySubmission.application_id == application_id)
        .order_by(AgencySubmission.submitted_at.desc())
    )
    if status is not None:
        statement = statement.where(AgencySubmission.status == status.strip().lower())
    return session.exec(statement).all()


def list_submissions(
    session: Session,
    *,
    application_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
) -> Sequence[AgencySubmission]:
    statement = select(AgencySubmission).order_by(
        AgencySubmission.submitted_at.desc()
    )
    if application_id is not None:
        statement = statement.where(AgencySubmission.application_id == application_id)
    if status is not None:
        statement = statement.where(AgencySubmission.status == status.strip().lower())
    return session.exec(statement.limit(limit)).all()
