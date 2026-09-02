from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AgencySubmission,
    ApplicationAuthorityChecklistItem,
    ApplicationRecord,
    AuthorityAppointment,
    ClientPortalAccessGrant,
    DocumentRecord,
    DocumentRequirementAssessment,
    ExternalAgency,
    ExternalAgencyAssignment,
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityTimeline,
    MobilityTimelineMilestone,
    PathwayComparisonAssessment,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.mobility_profiles import current_mobility_profile


PORTAL_SOURCE = "client_portal_v12_0"


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _safe_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _journey_state(
    milestone: MobilityTimelineMilestone,
    current_stage_key: str | None,
) -> str:
    if milestone.status == "completed":
        return "complete"
    if milestone.status == "blocked":
        return "attention"
    if (
        milestone.stage_key == current_stage_key
        or milestone.status in {"ready", "in_progress"}
    ):
        return "current"
    return "upcoming"


def _client_safe_plan_and_evidence(
    session: Session,
    lead_id: UUID,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    """Return only a current, human-activated, non-simulation client plan.

    This read never generates a comparison, timeline, eligibility assessment,
    document assessment, or replacement pathway. Failure to satisfy every
    provenance/review invariant produces an honest null plan.
    """
    profile = current_mobility_profile(session, lead_id)
    if profile is None or profile.consent_status != "granted":
        return None, None

    timelines = list(
        session.exec(
            select(MobilityTimeline)
            .where(
                MobilityTimeline.lead_id == lead_id,
                MobilityTimeline.status.in_(["active", "completed"]),
            )
            .order_by(
                MobilityTimeline.updated_at.desc(),
                MobilityTimeline.created_at.desc(),
            )
        ).all()
    )

    for timeline in timelines:
        if not timeline.activated_by or timeline.activated_at is None:
            continue
        if timeline.profile_id is None or timeline.profile_version is None:
            continue
        if (
            profile.id != timeline.profile_id
            or profile.profile_version != timeline.profile_version
        ):
            continue

        assessment = session.get(
            PathwayComparisonAssessment,
            timeline.comparison_assessment_id,
        )
        pathway = session.get(
            MobilityPathway,
            timeline.primary_pathway_id,
        )
        version = session.get(
            MobilityPathwayVersion,
            timeline.primary_pathway_version_id,
        )

        if assessment is None or pathway is None or version is None:
            continue
        if assessment.lead_id != lead_id:
            continue
        if assessment.status not in {
            "ready_for_review",
            "needs_profile_review",
        }:
            continue
        if (
            assessment.profile_id != timeline.profile_id
            or assessment.profile_version != timeline.profile_version
        ):
            continue
        if (
            assessment.primary_pathway_id != timeline.primary_pathway_id
            or assessment.primary_pathway_version_id
            != timeline.primary_pathway_version_id
        ):
            continue
        if version.pathway_id != pathway.id:
            continue
        if version.lifecycle_status not in {
            "published",
            "superseded",
            "retired",
        }:
            continue
        if not version.approved_by or version.published_at is None:
            continue

        comparison = _load_json(
            assessment.comparison_json,
            {},
        )
        if not isinstance(comparison, dict):
            continue
        if comparison.get("simulation") is True:
            continue
        if comparison.get("consent_status") != "granted":
            continue

        cost_payload = _load_json(
            assessment.cost_summary_json,
            {},
        )
        if not isinstance(cost_payload, dict):
            cost_payload = {}

        risk_payload = _load_json(
            assessment.risk_summary_json,
            {},
        )
        if not isinstance(risk_payload, dict):
            risk_payload = {}

        primary_payload = comparison.get("primary")
        if not isinstance(primary_payload, dict):
            primary_payload = {}

        processing_status = primary_payload.get(
            "processing_evidence_status"
        )
        if processing_status not in {
            "established",
            "not_established",
        }:
            processing = _load_json(
                version.processing_time_json,
                {},
            )
            if not isinstance(processing, dict):
                processing = {}
            processing_status = (
                "established"
                if (
                    processing.get("minimum_weeks") is not None
                    or processing.get("maximum_weeks") is not None
                )
                else "not_established"
            )

        currency = cost_payload.get("currency")
        if not isinstance(currency, str) or not currency.strip():
            currency = None
        else:
            currency = currency.strip().upper()

        fee_scope = cost_payload.get(
            "government_application_fee_scope"
        )
        if (
            not isinstance(fee_scope, str)
            or not fee_scope.strip()
        ):
            fee_scope = None
        else:
            fee_scope = fee_scope.strip()

        estimated_total_status = cost_payload.get(
            "estimated_total_status"
        )
        if estimated_total_status not in {
            "established",
            "not_established",
        }:
            estimated_total_status = "not_established"

        risk_level = risk_payload.get("level")
        risk: dict[str, object] | None = None
        if risk_level in {"low", "medium", "high"}:
            declared = risk_payload.get("declared_risks")
            evidence = risk_payload.get("evidence_risks")
            regulatory = risk_payload.get("regulatory_risks")
            risk = {
                "level": risk_level,
                "declared_count": len(declared)
                if isinstance(declared, list)
                else 0,
                "evidence_count": len(evidence)
                if isinstance(evidence, list)
                else 0,
                "regulatory_count": len(regulatory)
                if isinstance(regulatory, list)
                else 0,
            }

        milestones = list(
            session.exec(
                select(MobilityTimelineMilestone)
                .where(
                    MobilityTimelineMilestone.timeline_id
                    == timeline.id
                )
                .order_by(
                    MobilityTimelineMilestone.stage_order
                )
            ).all()
        )

        plan: dict[str, object] = {
            "timeline_id": timeline.id,
            "comparison_assessment_id": assessment.id,
            "profile_version": timeline.profile_version,
            "pathway_id": pathway.id,
            "pathway_version_id": version.id,
            "pathway_version_number": version.version_number,
            "pathway_name": pathway.name,
            "country": pathway.country,
            "domain": pathway.domain,
            "plan_status": timeline.status,
            "current_stage_key": timeline.current_stage_key,
            "activated_at": timeline.activated_at,
            "published_at": version.published_at,
            "processing_evidence_status": processing_status,
            "cost": {
                "currency": currency,
                "government_application_fee": _safe_number(
                    cost_payload.get(
                        "government_application_fee"
                    )
                ),
                "government_application_fee_scope": fee_scope,
                "estimated_total_status": estimated_total_status,
                "minimum_funds": _safe_number(
                    cost_payload.get("minimum_funds")
                ),
            },
            "risk": risk,
            "journey": [
                {
                    "key": milestone.stage_key,
                    "title": milestone.title,
                    "state": _journey_state(
                        milestone,
                        timeline.current_stage_key,
                    ),
                    "due_at": milestone.due_at,
                    "requires_human_approval":
                        milestone.requires_human_approval,
                }
                for milestone in milestones
            ],
        }

        approved_assessment = session.exec(
            select(DocumentRequirementAssessment)
            .where(
                DocumentRequirementAssessment.lead_id
                == lead_id,
                DocumentRequirementAssessment.pathway_id
                == pathway.id,
                DocumentRequirementAssessment.pathway_version_id
                == version.id,
                DocumentRequirementAssessment.profile_id
                == timeline.profile_id,
                DocumentRequirementAssessment.profile_version
                == timeline.profile_version,
                DocumentRequirementAssessment.review_status
                == "approved",
                DocumentRequirementAssessment.reviewed_by.is_not(
                    None
                ),
                DocumentRequirementAssessment.reviewed_at.is_not(
                    None
                ),
            )
            .order_by(
                DocumentRequirementAssessment.reviewed_at.desc(),
                DocumentRequirementAssessment.created_at.desc(),
            )
        ).first()

        evidence_summary: dict[str, object] | None = None
        if (
            approved_assessment is not None
            and approved_assessment.reviewed_at is not None
        ):
            evidence_summary = {
                "assessment_id": approved_assessment.id,
                "requirement_source":
                    approved_assessment.requirement_source,
                "result_status":
                    approved_assessment.result_status,
                "review_status": "approved",
                "required_count":
                    approved_assessment.required_count,
                "satisfied_count":
                    approved_assessment.satisfied_count,
                "missing_count":
                    approved_assessment.missing_count,
                "inconsistency_count":
                    approved_assessment.inconsistency_count,
                "reviewed_at":
                    approved_assessment.reviewed_at,
            }

        return plan, evidence_summary

    return None, None


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

    mobility_plan, evidence_summary = _client_safe_plan_and_evidence(
        session,
        lead.id,
    )

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
        "mobility_plan": mobility_plan,
        "evidence_summary": evidence_summary,
        "expires_at": grant.expires_at,
        "updated_at": lead.updated_at,
    }
