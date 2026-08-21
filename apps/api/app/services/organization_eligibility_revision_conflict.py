from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationActivityClass, now_utc
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_activity import stage_activity
from app.services.organization_command import canonical_fingerprint
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_CAPABILITY,
    ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
    EligibilityImmuneIncidentKind,
    EligibilityImmuneIncidentResult,
    eligibility_immune_system_context,
    record_eligibility_immune_incident,
)
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPreconditionConflict,
)
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record


ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION = (
    "eligibility-revision-conflict-attribution.v1"
)
ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE = (
    "organization.immune.eligibility_revision_conflict_attributed.v1"
)
ELIGIBILITY_REVISION_CONFLICT_FAILURE_STAGE = "g5_revision_precondition_pre_egress"


class EligibilityRevisionConflictAttributionError(RuntimeError):
    """Trusted H.2.3 revision-conflict attribution is incomplete or inconsistent."""


@dataclass(frozen=True)
class AttributedEligibilityRevisionConflictResult:
    schema_version: str
    attribution_activity: OrganizationActivity
    incident: EligibilityImmuneIncidentResult


def _required_text(value: str, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise EligibilityRevisionConflictAttributionError(f"{label} is required")
    return normalized


def _attribution_activity_key(*, aggregate_key: str, incident_key: str) -> str:
    return f"immune:eligibility:{aggregate_key}:revision-conflict-attribution:{incident_key}"


def _incident_activity_key(*, aggregate_key: str, incident_key: str) -> str:
    return f"immune:eligibility:{aggregate_key}:incident:{incident_key}"


def _validated_conflict(
    *,
    tenant_key: str,
    aggregate_key: str,
    conflict: EligibilityRevisionPreconditionConflict,
) -> None:
    if conflict.tenant_key != tenant_key:
        raise EligibilityRevisionConflictAttributionError(
            "revision conflict belongs to a different tenant"
        )
    if conflict.aggregate_key != aggregate_key:
        raise EligibilityRevisionConflictAttributionError(
            "revision conflict belongs to a different eligibility aggregate"
        )
    if conflict.expected_revision_version < 1:
        raise EligibilityRevisionConflictAttributionError(
            "revision conflict expected version must be positive"
        )
    if conflict.current_revision_version <= conflict.expected_revision_version:
        raise EligibilityRevisionConflictAttributionError(
            "revision conflict attribution requires a superseded caller expectation"
        )


def _matching_existing_attribution(
    existing: OrganizationActivity,
    *,
    attribution_fingerprint: str,
    summary: str,
) -> bool:
    try:
        record = transparency_activity_record(existing)
    except TransparencyDataError as exc:
        raise EligibilityRevisionConflictAttributionError(
            "persisted eligibility revision-conflict attribution Activity is malformed"
        ) from exc
    return (
        record.activity_type == ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE
        and existing.summary == summary
        and existing.causation_activity_id is None
        and existing.correlation_key is None
        and record.payload.get("attribution_fingerprint") == attribution_fingerprint
    )


def record_attributed_eligibility_revision_conflict(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
    incident_key: str,
    conflict: EligibilityRevisionPreconditionConflict,
    summary: str,
) -> AttributedEligibilityRevisionConflictResult:
    """Persist one genuine pre-egress G.5 stale-reassessment conflict atomically.

    H.2.3 is an attribution foundation, not a recurrence or quarantine policy. The
    supplied conflict must originate from the canonical G.5 resolver and proves that a
    caller supplied a previously valid revision version while a newer ACTIVE canonical
    revision already existed before provider egress. Missing expectations, future
    expectations, missing revisions and post-provider races use other error paths and
    are not accepted here.

    The attribution Activity and existing H.1 warning are committed as one pair. The
    warning remains observation-only because REVISION_CONFLICT has no recurrence
    threshold in the accepted H.1/H.2.1 Immune System contract.
    """

    tenant = _required_text(tenant_key, label="tenant_key")
    aggregate = _required_text(aggregate_key, label="aggregate_key")
    key = _required_text(incident_key, label="incident_key")
    detail = _required_text(summary, label="summary")
    if not aggregate.startswith(f"eligibility:{tenant}:"):
        raise EligibilityRevisionConflictAttributionError(
            "eligibility aggregate key does not belong to the supplied tenant"
        )
    _validated_conflict(
        tenant_key=tenant,
        aggregate_key=aggregate,
        conflict=conflict,
    )

    attribution_key = _attribution_activity_key(
        aggregate_key=aggregate,
        incident_key=key,
    )
    incident_activity_key = _incident_activity_key(
        aggregate_key=aggregate,
        incident_key=key,
    )
    attribution_summary = (
        "Attributed a stale canonical eligibility reassessment expectation before provider egress."
    )
    attribution_payload = {
        "attribution_contract": ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION,
        "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
        "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
        "aggregate_key": aggregate,
        "incident_key": key,
        "incident_activity_key": incident_activity_key,
        "incident_kind": EligibilityImmuneIncidentKind.REVISION_CONFLICT.value,
        "failure_stage": ELIGIBILITY_REVISION_CONFLICT_FAILURE_STAGE,
        "conflict_basis": "superseded_expected_revision",
        "expected_revision_version": conflict.expected_revision_version,
        "observed_current_revision_id": str(conflict.current_revision_id),
        "observed_current_revision_version": conflict.current_revision_version,
        "observed_current_lifecycle_status": "active",
        "provider_egress_occurred": False,
        "control_effect": "observation_only",
        "authority_effect": "none",
        "recurrence_policy_applied": False,
    }
    attribution_fingerprint = canonical_fingerprint(attribution_payload)
    attribution_payload["attribution_fingerprint"] = attribution_fingerprint

    existing_attribution = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant,
            OrganizationActivity.activity_key == attribution_key,
        )
    ).first()
    existing_incident = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant,
            OrganizationActivity.activity_key == incident_activity_key,
        )
    ).first()
    if (existing_attribution is None) != (existing_incident is None):
        raise EligibilityRevisionConflictAttributionError(
            "revision-conflict attribution and incident must exist as one atomic pair"
        )
    if existing_attribution is not None:
        if not _matching_existing_attribution(
            existing_attribution,
            attribution_fingerprint=attribution_fingerprint,
            summary=attribution_summary,
        ):
            raise EligibilityRevisionConflictAttributionError(
                "revision-conflict attribution idempotency key conflicts with persisted attribution"
            )
        replay = record_eligibility_immune_incident(
            session,
            tenant_key=tenant,
            aggregate_key=aggregate,
            incident_key=key,
            kind=EligibilityImmuneIncidentKind.REVISION_CONFLICT,
            summary=detail,
        )
        return AttributedEligibilityRevisionConflictResult(
            schema_version=ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION,
            attribution_activity=existing_attribution,
            incident=replay,
        )

    observed_revision = session.get(
        EligibilityAssessmentRevision,
        conflict.current_revision_id,
    )
    if (
        observed_revision is None
        or observed_revision.tenant_key != tenant
        or observed_revision.aggregate_key != aggregate
        or observed_revision.version != conflict.current_revision_version
    ):
        raise EligibilityRevisionConflictAttributionError(
            "revision conflict snapshot cannot be reconciled with durable canonical revision identity"
        )

    context = eligibility_immune_system_context(tenant_key=tenant)
    try:
        attribution = stage_activity(
            session,
            context,
            activity_key=attribution_key,
            stream_key=f"immune:eligibility:{aggregate}",
            activity_class=OrganizationActivityClass.operational,
            activity_type=ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE,
            title="Eligibility revision conflict attributed",
            summary=attribution_summary,
            source_object_type="eligibility_aggregate",
            source_object_id=aggregate,
            source_object_version=ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION,
            occurred_at=now_utc(),
            payload=attribution_payload,
        )
        incident = record_eligibility_immune_incident(
            session,
            tenant_key=tenant,
            aggregate_key=aggregate,
            incident_key=key,
            kind=EligibilityImmuneIncidentKind.REVISION_CONFLICT,
            summary=detail,
        )
    except Exception:
        session.rollback()
        raise

    return AttributedEligibilityRevisionConflictResult(
        schema_version=ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION,
        attribution_activity=attribution,
        incident=incident,
    )
