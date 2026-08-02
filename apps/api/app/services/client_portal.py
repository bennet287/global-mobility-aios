from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AgencySubmission,
    ApplicationAuthorityChecklistItem,
    ApplicationRecord,
    AuthorityAppointment,
    ClientPortalAccessGrant,
    DocumentRecord,
    ExternalAgency,
    ExternalAgencyAssignment,
    Lead,
    now_utc,
)
from app.services.audit_log import record_audit


PORTAL_SOURCE = "client_portal_v12_0"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _safe_grant(grant: ClientPortalAccessGrant) -> dict[str, object]:
    return {
        "id": str(grant.id),
        "lead_id": str(grant.lead_id),
        "label": grant.label,
        "status": grant.status,
        "expires_at": grant.expires_at.isoformat(),
        "created_by": grant.created_by,
        "access_count": grant.access_count,
        "last_accessed_at": grant.last_accessed_at.isoformat() if grant.last_accessed_at else None,
        "device_fingerprint": grant.device_fingerprint,
        "device_label": grant.device_label,
        "user_agent": grant.user_agent,
        "revoked_by": grant.revoked_by,
        "revoked_at": grant.revoked_at.isoformat() if grant.revoked_at else None,
        "revocation_reason": grant.revocation_reason,
        "created_at": grant.created_at.isoformat(),
        "updated_at": grant.updated_at.isoformat(),
    }


def grant_read(grant: ClientPortalAccessGrant) -> dict[str, object]:
    payload = _safe_grant(grant)
    payload["expired"] = _as_utc(grant.expires_at) <= now_utc()
    return payload


def issue_client_portal_grant(
    session: Session,
    lead_id: UUID,
    *,
    actor: str,
    label: str = "Client portal",
    expires_in_days: int = 30,
) -> tuple[ClientPortalAccessGrant, str]:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    clean_label = label.strip()
    if len(clean_label) < 2 or len(clean_label) > 120:
        raise ValueError("Portal access label must contain 2 to 120 characters")
    if expires_in_days < 1 or expires_in_days > 90:
        raise ValueError("Portal access expiry must be between 1 and 90 days")

    issued_at = now_utc()
    token = f"gmai_portal_{secrets.token_urlsafe(32)}"
    grant = ClientPortalAccessGrant(
        token_hash=_hash_token(token),
        lead_id=lead.id,
        label=clean_label,
        status="active",
        expires_at=issued_at + timedelta(days=expires_in_days),
        created_by=actor,
        created_at=issued_at,
        updated_at=issued_at,
    )
    session.add(grant)
    session.flush()
    record_audit(
        session,
        action="client_portal_grant_created",
        entity_type="client_portal_access_grant",
        entity_id=grant.id,
        after_state=_safe_grant(grant),
        reason="Lead-scoped client portal access issued.",
        actor=actor,
        source=PORTAL_SOURCE,
    )
    session.commit()
    session.refresh(grant)
    return grant, token


def expire_client_portal_grants(
    session: Session,
    *,
    actor: str = "client-portal-expiry-monitor",
) -> int:
    now = now_utc()
    grants = session.exec(
        select(ClientPortalAccessGrant).where(ClientPortalAccessGrant.status == "active")
    ).all()
    expired = 0
    for grant in grants:
        if _as_utc(grant.expires_at) > now:
            continue
        grant.status = "expired"
        grant.updated_at = now
        session.add(grant)
        record_audit(
            session,
            action="client_portal_grant_expired",
            entity_type="client_portal_access_grant",
            entity_id=grant.id,
            after_state=_safe_grant(grant),
            reason="Client portal grant reached its expiry time.",
            actor=actor,
            source=PORTAL_SOURCE,
        )
        expired += 1
    if expired:
        session.commit()
    return expired


def resolve_client_portal_grant(
    session: Session,
    token: str,
    *,
    expected_lead_id: UUID | None = None,
    device_fingerprint: str | None = None,
    device_label: str | None = None,
    user_agent: str | None = None,
) -> ClientPortalAccessGrant:
    clean_token = token.strip()
    if not clean_token.startswith("gmai_portal_") or len(clean_token) > 256:
        raise ValueError("Client portal access is invalid or unavailable")
    token_hash = _hash_token(clean_token)
    grant = session.exec(
        select(ClientPortalAccessGrant).where(ClientPortalAccessGrant.token_hash == token_hash)
    ).first()
    if grant is None or not hmac.compare_digest(grant.token_hash, token_hash):
        raise ValueError("Client portal access is invalid or unavailable")
    if expected_lead_id is not None and grant.lead_id != expected_lead_id:
        raise ValueError("Client portal access is invalid or unavailable")
    if grant.status != "active":
        raise ValueError("Client portal access is invalid or unavailable")
    if _as_utc(grant.expires_at) <= now_utc():
        grant.status = "expired"
        grant.updated_at = now_utc()
        session.add(grant)
        record_audit(
            session,
            action="client_portal_grant_expired",
            entity_type="client_portal_access_grant",
            entity_id=grant.id,
            after_state=_safe_grant(grant),
            reason="Expired client portal grant was presented.",
            actor="client-portal",
            source=PORTAL_SOURCE,
        )
        session.commit()
        raise ValueError("Client portal access is invalid or unavailable")

    # Device binding: first access binds; subsequent accesses must match.
    normalized_fingerprint = (device_fingerprint or "").strip() or None
    if grant.device_fingerprint is None:
        if normalized_fingerprint:
            grant.device_fingerprint = normalized_fingerprint
            grant.device_label = (device_label or "").strip()[:120] or None
            grant.user_agent = (user_agent or "").strip()[:500] or None
            grant.updated_at = now_utc()
            session.add(grant)
            record_audit(
                session,
                action="client_portal_device_bound",
                entity_type="client_portal_access_grant",
                entity_id=grant.id,
                after_state={
                    "grant_id": str(grant.id),
                    "lead_id": str(grant.lead_id),
                    "device_fingerprint": grant.device_fingerprint,
                    "device_label": grant.device_label,
                    "user_agent": grant.user_agent,
                },
                reason="First portal access bound this device to the grant.",
                actor="client-portal",
                source=PORTAL_SOURCE,
            )
            session.commit()
            session.refresh(grant)
    elif not normalized_fingerprint or not hmac.compare_digest(
        grant.device_fingerprint, normalized_fingerprint
    ):
        raise ValueError("device_mismatch: client portal grant is bound to a different device")

    return grant


def revoke_client_portal_grant(
    session: Session,
    grant_id: UUID,
    *,
    actor: str,
    reason: str,
) -> ClientPortalAccessGrant:
    grant = session.get(ClientPortalAccessGrant, grant_id)
    if grant is None:
        raise ValueError("Client portal grant not found")
    if grant.status != "active":
        raise ValueError(f"Client portal grant is already {grant.status}")
    clean_reason = reason.strip()
    if len(clean_reason) < 3:
        raise ValueError("A revocation reason is required")
    before = _safe_grant(grant)
    now = now_utc()
    grant.status = "revoked"
    grant.revoked_by = actor
    grant.revoked_at = now
    grant.revocation_reason = clean_reason
    grant.updated_at = now
    session.add(grant)
    record_audit(
        session,
        action="client_portal_grant_revoked",
        entity_type="client_portal_access_grant",
        entity_id=grant.id,
        before_state=before,
        after_state=_safe_grant(grant),
        reason=clean_reason,
        actor=actor,
        source=PORTAL_SOURCE,
    )
    session.commit()
    session.refresh(grant)
    return grant


def _case_next_action(lead: Lead, application: ApplicationRecord | None, documents: list[DocumentRecord]) -> str:
    status = str(getattr(lead.status, "value", lead.status))
    if status == "needs_documents":
        return "Upload the requested documents so your consultant can continue the review."
    if status == "human_review":
        return "Your consultant is reviewing the case. You will be contacted when the next action is ready."
    if status == "converted":
        return "Your case is active with the mobility team. Follow the latest consultant instructions."
    if status == "closed":
        return "This case is closed. Contact your mobility team if you need it reopened."
    if application is not None:
        return f"Your application is currently at the {application.status.replace('_', ' ')} stage."
    if not documents:
        return "Prepare your identity and supporting documents while the mobility team reviews your case."
    return "Your information is with the mobility team. No client action is required right now."


def _milestones(lead: Lead, application: ApplicationRecord | None, documents: list[DocumentRecord]) -> list[dict[str, str]]:
    lead_status = str(getattr(lead.status, "value", lead.status))
    document_complete = bool(documents) and all(
        document.status.lower() in {"verified", "approved", "accepted"} for document in documents
    )
    review_complete = lead_status in {"converted", "closed"} or application is not None
    application_complete = application is not None and application.status.lower() in {
        "approved",
        "completed",
        "decision_received",
    }
    return [
        {"key": "received", "label": "Case received", "state": "complete"},
        {
            "key": "documents",
            "label": "Documents prepared",
            "state": "complete" if document_complete else "current",
        },
        {
            "key": "review",
            "label": "Consultant review",
            "state": "complete" if review_complete else ("current" if document_complete else "upcoming"),
        },
        {
            "key": "application",
            "label": "Application progress",
            "state": "complete" if application_complete else ("current" if application else "upcoming"),
        },
    ]


def client_portal_dashboard(
    session: Session,
    token: str,
    *,
    device_fingerprint: str | None = None,
    device_label: str | None = None,
    user_agent: str | None = None,
) -> dict[str, object]:
    grant = resolve_client_portal_grant(
        session,
        token,
        device_fingerprint=device_fingerprint,
        device_label=device_label,
        user_agent=user_agent,
    )
    lead = session.get(Lead, grant.lead_id)
    if lead is None:
        raise ValueError("Client portal access is invalid or unavailable")
    documents = list(session.exec(
        select(DocumentRecord)
        .where(DocumentRecord.lead_id == lead.id)
        .order_by(DocumentRecord.created_at.desc())
    ).all())
    applications = list(session.exec(
        select(ApplicationRecord)
        .where(ApplicationRecord.lead_id == lead.id)
        .order_by(ApplicationRecord.created_at.desc())
    ).all())
    application = applications[0] if applications else None
    application_ids = [app.id for app in applications]

    appointments: list[AuthorityAppointment] = []
    submissions: list[AgencySubmission] = []
    assignments: list[tuple[ExternalAgencyAssignment, ExternalAgency]] = []
    checklist_items: list[ApplicationAuthorityChecklistItem] = []
    if application_ids:
        appointments = list(session.exec(
            select(AuthorityAppointment)
            .where(AuthorityAppointment.application_id.in_(application_ids))
            .order_by(AuthorityAppointment.scheduled_at.desc())
        ).all())
        submissions = list(session.exec(
            select(AgencySubmission)
            .where(AgencySubmission.application_id.in_(application_ids))
            .order_by(AgencySubmission.submitted_at.desc())
        ).all())
        assignments = list(session.exec(
            select(ExternalAgencyAssignment, ExternalAgency)
            .join(ExternalAgency, ExternalAgencyAssignment.external_agency_id == ExternalAgency.id)
            .where(ExternalAgencyAssignment.application_id.in_(application_ids))
            .order_by(ExternalAgencyAssignment.created_at.desc())
        ).all())
        checklist_items = list(session.exec(
            select(ApplicationAuthorityChecklistItem)
            .where(ApplicationAuthorityChecklistItem.application_id.in_(application_ids))
            .order_by(
                ApplicationAuthorityChecklistItem.authority_name,
                ApplicationAuthorityChecklistItem.created_at.desc(),
            )
        ).all())

    document_counts: dict[str, int] = {}
    for document in documents:
        key = document.status.lower().replace(" ", "_")
        document_counts[key] = document_counts.get(key, 0) + 1

    now = now_utc()
    grant.access_count += 1
    grant.last_accessed_at = now
    grant.updated_at = now
    session.add(grant)
    record_audit(
        session,
        action="client_portal_accessed",
        entity_type="client_portal_access_grant",
        entity_id=grant.id,
        after_state={
            "grant_id": str(grant.id),
            "lead_id": str(grant.lead_id),
            "access_count": grant.access_count,
        },
        reason="Client-safe case dashboard accessed.",
        actor=f"client-portal:{grant.id}",
        source=PORTAL_SOURCE,
    )
    session.commit()
    return {
        "grant_id": grant.id,
        "client_name": lead.full_name,
        "target_country": lead.target_country,
        "intent": str(getattr(lead.intent, "value", lead.intent)),
        "case_status": str(getattr(lead.status, "value", lead.status)),
        "application_stage": application.status if application else None,
        "next_action": _case_next_action(lead, application, documents),
        "documents": [
            {
                "id": document.id,
                "document_type": document.document_type,
                "filename": document.filename,
                "status": document.status,
                "uploaded_at": document.uploaded_at,
                "expiry_date": document.expiry_date,
            }
            for document in documents
        ],
        "document_counts": document_counts,
        "milestones": _milestones(lead, application, documents),
        "appointments": [
            {
                "id": appointment.id,
                "authority_name": appointment.authority_name,
                "appointment_type": appointment.appointment_type,
                "location": appointment.location,
                "scheduled_at": appointment.scheduled_at,
                "timezone": appointment.timezone,
                "status": appointment.status,
                "reference_number": appointment.reference_number,
            }
            for appointment in appointments
        ],
        "submissions": [
            {
                "id": submission.id,
                "authority_name": submission.authority_name,
                "submission_channel": submission.submission_channel,
                "submitted_at": submission.submitted_at,
                "status": submission.status,
                "reference_number": submission.reference_number,
                "tracking_url": submission.tracking_url,
            }
            for submission in submissions
        ],
        "external_agency_assignments": [
            {
                "id": assignment.id,
                "agency_name": agency.name,
                "status": assignment.status,
                "agency_reference_number": assignment.agency_reference_number,
                "handoff_at": assignment.handoff_at,
                "completed_at": assignment.completed_at,
                "sla_due_at": assignment.sla_due_at,
                "sla_status": assignment.sla_status,
                "sla_breached_at": assignment.sla_breached_at,
            }
            for assignment, agency in assignments
        ],
        "authority_checklist": [
            {
                "id": item.id,
                "authority_name": item.authority_name,
                "item_label": item.item_label,
                "category": item.category,
                "is_required": item.is_required,
                "status": item.status,
            }
            for item in checklist_items
        ],
        "expires_at": grant.expires_at,
        "updated_at": lead.updated_at,
    }
