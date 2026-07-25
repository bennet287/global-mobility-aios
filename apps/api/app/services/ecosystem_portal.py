from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    CorporateAccount,
    CorporateComplianceEvent,
    CorporateMobilityCase,
    CorporateRelocationTask,
    EcosystemPortalAccessGrant,
    Lead,
    now_utc,
)
from app.services.audit_log import record_audit


PORTAL_SOURCE = "ecosystem_portal_v12_1"
AUDIENCE_TYPES = {"employer", "partner"}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _safe_grant(grant: EcosystemPortalAccessGrant) -> dict[str, object]:
    return {
        "id": str(grant.id),
        "corporate_account_id": str(grant.corporate_account_id),
        "audience_type": grant.audience_type,
        "label": grant.label,
        "status": grant.status,
        "expires_at": grant.expires_at.isoformat(),
        "created_by": grant.created_by,
        "access_count": grant.access_count,
        "last_accessed_at": grant.last_accessed_at.isoformat() if grant.last_accessed_at else None,
        "revoked_by": grant.revoked_by,
        "revoked_at": grant.revoked_at.isoformat() if grant.revoked_at else None,
        "revocation_reason": grant.revocation_reason,
        "created_at": grant.created_at.isoformat(),
        "updated_at": grant.updated_at.isoformat(),
    }


def ecosystem_grant_read(grant: EcosystemPortalAccessGrant) -> dict[str, object]:
    payload = _safe_grant(grant)
    payload["expired"] = _as_utc(grant.expires_at) <= now_utc()
    return payload


def issue_ecosystem_portal_grant(
    session: Session,
    corporate_account_id: UUID,
    *,
    actor: str,
    audience_type: str,
    label: str,
    expires_in_days: int = 30,
) -> tuple[EcosystemPortalAccessGrant, str]:
    account = session.get(CorporateAccount, corporate_account_id)
    if account is None:
        raise ValueError("Corporate account not found")
    if account.account_status != "active":
        raise ValueError("Portal access can only be issued for an active corporate account")
    audience = audience_type.strip().lower()
    if audience not in AUDIENCE_TYPES:
        raise ValueError("Audience type must be employer or partner")
    clean_label = label.strip()
    if len(clean_label) < 2 or len(clean_label) > 120:
        raise ValueError("Portal access label must contain 2 to 120 characters")
    if expires_in_days < 1 or expires_in_days > 90:
        raise ValueError("Portal access expiry must be between 1 and 90 days")

    issued_at = now_utc()
    token = f"gmai_ecosystem_{secrets.token_urlsafe(32)}"
    grant = EcosystemPortalAccessGrant(
        token_hash=_hash_token(token),
        corporate_account_id=account.id,
        audience_type=audience,
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
        action="ecosystem_portal_grant_created",
        entity_type="ecosystem_portal_access_grant",
        entity_id=grant.id,
        after_state=_safe_grant(grant),
        reason=f"{audience.title()} portal access issued for one corporate account.",
        actor=actor,
        source=PORTAL_SOURCE,
    )
    session.commit()
    session.refresh(grant)
    return grant, token


def expire_ecosystem_portal_grants(
    session: Session,
    *,
    actor: str = "ecosystem-portal-expiry-monitor",
) -> int:
    now = now_utc()
    expired = 0
    for grant in session.exec(
        select(EcosystemPortalAccessGrant).where(EcosystemPortalAccessGrant.status == "active")
    ).all():
        if _as_utc(grant.expires_at) > now:
            continue
        grant.status = "expired"
        grant.updated_at = now
        session.add(grant)
        record_audit(
            session,
            action="ecosystem_portal_grant_expired",
            entity_type="ecosystem_portal_access_grant",
            entity_id=grant.id,
            after_state=_safe_grant(grant),
            reason="Ecosystem portal grant reached its expiry time.",
            actor=actor,
            source=PORTAL_SOURCE,
        )
        expired += 1
    if expired:
        session.commit()
    return expired


def resolve_ecosystem_portal_grant(
    session: Session,
    token: str,
) -> EcosystemPortalAccessGrant:
    clean_token = token.strip()
    if not clean_token.startswith("gmai_ecosystem_") or len(clean_token) > 256:
        raise ValueError("Ecosystem portal access is invalid or unavailable")
    token_hash = _hash_token(clean_token)
    grant = session.exec(
        select(EcosystemPortalAccessGrant).where(
            EcosystemPortalAccessGrant.token_hash == token_hash
        )
    ).first()
    if grant is None or not hmac.compare_digest(grant.token_hash, token_hash):
        raise ValueError("Ecosystem portal access is invalid or unavailable")
    if grant.status != "active":
        raise ValueError("Ecosystem portal access is invalid or unavailable")
    if _as_utc(grant.expires_at) <= now_utc():
        grant.status = "expired"
        grant.updated_at = now_utc()
        session.add(grant)
        record_audit(
            session,
            action="ecosystem_portal_grant_expired",
            entity_type="ecosystem_portal_access_grant",
            entity_id=grant.id,
            after_state=_safe_grant(grant),
            reason="Expired ecosystem portal grant was presented.",
            actor="ecosystem-portal",
            source=PORTAL_SOURCE,
        )
        session.commit()
        raise ValueError("Ecosystem portal access is invalid or unavailable")
    account = session.get(CorporateAccount, grant.corporate_account_id)
    if account is None or account.account_status != "active":
        raise ValueError("Ecosystem portal access is invalid or unavailable")
    return grant


def revoke_ecosystem_portal_grant(
    session: Session,
    grant_id: UUID,
    *,
    actor: str,
    reason: str,
) -> EcosystemPortalAccessGrant:
    grant = session.get(EcosystemPortalAccessGrant, grant_id)
    if grant is None:
        raise ValueError("Ecosystem portal grant not found")
    if grant.status != "active":
        raise ValueError(f"Ecosystem portal grant is already {grant.status}")
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
        action="ecosystem_portal_grant_revoked",
        entity_type="ecosystem_portal_access_grant",
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


def _next_action(
    case: CorporateMobilityCase,
    open_events: list[CorporateComplianceEvent],
    open_tasks: list[CorporateRelocationTask],
) -> str:
    if case.status == "draft":
        return "Confirm the case scope with the mobility team before activation."
    overdue = [event for event in open_events if _as_utc(event.due_at) <= now_utc()]
    if overdue:
        return f"Resolve {len(overdue)} overdue compliance item(s) with the assigned mobility team."
    if open_events:
        return f"Prepare for the next compliance deadline: {open_events[0].title}."
    if open_tasks:
        return f"Track the next controlled task: {open_tasks[0].title}."
    if case.status in {"completed", "closed"}:
        return "No employer or partner action is currently required."
    return "The mobility team is coordinating the next controlled action."


def ecosystem_portal_dashboard(session: Session, token: str) -> dict[str, object]:
    grant = resolve_ecosystem_portal_grant(session, token)
    account = session.get(CorporateAccount, grant.corporate_account_id)
    if account is None:
        raise ValueError("Ecosystem portal access is invalid or unavailable")

    # Every downstream query is constrained by the account embedded in the grant.
    cases = list(session.exec(
        select(CorporateMobilityCase)
        .where(CorporateMobilityCase.corporate_account_id == grant.corporate_account_id)
        .order_by(CorporateMobilityCase.updated_at.desc())
    ).all())
    case_ids = {case.id for case in cases}
    leads = {
        lead.id: lead
        for lead in session.exec(
            select(Lead).where(Lead.id.in_({
                case.employee_lead_id for case in cases if case.employee_lead_id is not None
            }))
        ).all()
    } if any(case.employee_lead_id for case in cases) else {}
    events = list(session.exec(
        select(CorporateComplianceEvent)
        .where(CorporateComplianceEvent.corporate_mobility_case_id.in_(case_ids))
        .order_by(CorporateComplianceEvent.due_at)
    ).all()) if case_ids else []
    tasks = list(session.exec(
        select(CorporateRelocationTask)
        .where(CorporateRelocationTask.corporate_mobility_case_id.in_(case_ids))
        .order_by(CorporateRelocationTask.created_at)
    ).all()) if case_ids else []

    case_counts: dict[str, int] = {}
    case_payloads: list[dict[str, object]] = []
    for case in cases:
        case_counts[case.status] = case_counts.get(case.status, 0) + 1
        open_events = [
            event for event in events
            if event.corporate_mobility_case_id == case.id and event.status == "open"
        ]
        open_tasks = [
            task for task in tasks
            if task.corporate_mobility_case_id == case.id
            and task.status not in {"completed", "cancelled"}
        ]
        employee = leads.get(case.employee_lead_id)
        case_payloads.append({
            "case_reference": case.case_reference,
            "case_type": case.case_type,
            "status": case.status,
            "employee_name": employee.full_name if employee else None,
            "origin_country": case.origin_country,
            "destination_country": case.destination_country,
            "target_start_date": case.target_start_date,
            "compliance_due_date": case.compliance_due_date,
            "open_compliance_items": len(open_events),
            "open_tasks": len(open_tasks),
            "next_action": _next_action(case, open_events, open_tasks),
            "updated_at": case.updated_at,
        })

    references = {case.id: case.case_reference for case in cases}
    upcoming = [
        {
            "case_reference": references[event.corporate_mobility_case_id],
            "title": event.title,
            "event_type": event.event_type,
            "due_at": event.due_at,
            "status": event.status,
            "evidence_required": event.evidence_required,
        }
        for event in events
        if event.status == "open"
    ][:12]

    now = now_utc()
    grant.access_count += 1
    grant.last_accessed_at = now
    grant.updated_at = now
    session.add(grant)
    record_audit(
        session,
        action="ecosystem_portal_accessed",
        entity_type="ecosystem_portal_access_grant",
        entity_id=grant.id,
        after_state={
            "grant_id": str(grant.id),
            "corporate_account_id": str(grant.corporate_account_id),
            "audience_type": grant.audience_type,
            "access_count": grant.access_count,
        },
        reason="Tenant-scoped employer or partner dashboard accessed.",
        actor=f"ecosystem-portal:{grant.id}",
        source=PORTAL_SOURCE,
    )
    session.commit()
    return {
        "grant_id": grant.id,
        "audience_type": grant.audience_type,
        "account_name": account.display_name or account.legal_name,
        "primary_country": account.primary_country,
        "account_status": account.account_status,
        "case_counts": case_counts,
        "cases": case_payloads,
        "upcoming_compliance": upcoming,
        "expires_at": grant.expires_at,
        "updated_at": account.updated_at,
    }
