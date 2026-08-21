from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationActivityClass, now_utc
from app.services.organization_activity import stage_activity
from app.services.organization_agent_runtime import AgentRuntimeProfile, runtime_profile_fingerprint
from app.services.organization_command import canonical_fingerprint
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_CAPABILITY,
    ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
    EligibilityImmuneIncidentKind,
    EligibilityImmuneIncidentResult,
    eligibility_immune_system_context,
    record_eligibility_immune_incident,
)
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record


ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION = (
    "eligibility-runtime-health-attribution.v1"
)
ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_ACTIVITY_TYPE = (
    "organization.immune.eligibility_runtime_health_attributed.v1"
)


class EligibilityRuntimeHealthAttributionError(RuntimeError):
    """Trusted runtime-failure attribution is incomplete or inconsistent."""


class EligibilityRuntimeExecutionRole(str, Enum):
    PRODUCER = "producer"
    VERIFIER = "verifier"


@dataclass(frozen=True)
class AttributedEligibilityRuntimeHealthIncidentResult:
    schema_version: str
    attribution_activity: OrganizationActivity
    incident: EligibilityImmuneIncidentResult


def _required_text(value: str, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise EligibilityRuntimeHealthAttributionError(f"{label} is required")
    return normalized


def _failure_stage(role: EligibilityRuntimeExecutionRole) -> str:
    if role is EligibilityRuntimeExecutionRole.PRODUCER:
        return "e2_proposal_runtime"
    return "g1_independent_verification_runtime"


def _attribution_activity_key(*, aggregate_key: str, incident_key: str) -> str:
    return f"immune:eligibility:{aggregate_key}:runtime-attribution:{incident_key}"


def _incident_activity_key(*, aggregate_key: str, incident_key: str) -> str:
    return f"immune:eligibility:{aggregate_key}:incident:{incident_key}"


def _matching_existing_attribution(
    existing: OrganizationActivity,
    *,
    attribution_fingerprint: str,
    summary: str,
    source_activity_id: UUID | None,
    correlation_key: str | None,
) -> bool:
    try:
        record = transparency_activity_record(existing)
    except TransparencyDataError as exc:
        raise EligibilityRuntimeHealthAttributionError(
            "persisted eligibility runtime-health attribution Activity is malformed"
        ) from exc
    return (
        record.activity_type == ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_ACTIVITY_TYPE
        and existing.summary == summary
        and existing.causation_activity_id == source_activity_id
        and existing.correlation_key == correlation_key
        and record.payload.get("attribution_fingerprint") == attribution_fingerprint
    )


def record_attributed_eligibility_runtime_health_incident(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
    incident_key: str,
    execution_role: EligibilityRuntimeExecutionRole | str,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
    summary: str,
    source_activity_id: UUID | None = None,
    correlation_key: str | None = None,
) -> AttributedEligibilityRuntimeHealthIncidentResult:
    """Persist trusted G.4 runtime attribution and its H.1 warning atomically.

    H.2.2 deliberately adds measurement/provenance, not a wider circuit. The runtime
    identity comes only from the trusted server-side execution plan. The attribution
    Activity is staged first in the existing aggregate immune stream; the accepted H.1
    incident command then commits both records in one transaction. The warning remains
    observation-only and does not participate in H.2.1 verifier-disagreement recurrence.
    """

    tenant = _required_text(tenant_key, label="tenant_key")
    aggregate = _required_text(aggregate_key, label="aggregate_key")
    key = _required_text(incident_key, label="incident_key")
    position = _required_text(position_key, label="position_key")
    detail = _required_text(summary, label="summary")
    if not aggregate.startswith(f"eligibility:{tenant}:"):
        raise EligibilityRuntimeHealthAttributionError(
            "eligibility aggregate key does not belong to the supplied tenant"
        )
    try:
        role = EligibilityRuntimeExecutionRole(execution_role)
    except ValueError as exc:
        raise EligibilityRuntimeHealthAttributionError(
            "unsupported eligibility runtime execution role"
        ) from exc

    attribution_key = _attribution_activity_key(
        aggregate_key=aggregate,
        incident_key=key,
    )
    incident_activity_key = _incident_activity_key(
        aggregate_key=aggregate,
        incident_key=key,
    )
    attribution_summary = (
        f"Attributed {role.value} eligibility runtime failure to trusted runtime "
        f"profile {runtime_profile.profile_key!r}."
    )
    runtime_profile_fp = runtime_profile_fingerprint(runtime_profile)
    attribution_payload = {
        "attribution_contract": ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION,
        "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
        "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
        "aggregate_key": aggregate,
        "incident_key": key,
        "incident_activity_key": incident_activity_key,
        "incident_kind": EligibilityImmuneIncidentKind.RUNTIME_HEALTH_FAILURE.value,
        "execution_role": role.value,
        "failure_stage": _failure_stage(role),
        "position_key": position,
        "runtime_profile_key": runtime_profile.profile_key,
        "runtime_profile_version": runtime_profile.profile_version,
        "runtime_profile_fingerprint": runtime_profile_fp,
        "runtime_class": runtime_profile.runtime_class.value,
        "adapter_key": runtime_profile.adapter_key,
        "provider_key": runtime_profile.provider_key,
        "model_key": runtime_profile.model_key,
        "independence_group": runtime_profile.independence_group,
        "control_effect": "observation_only",
        "authority_effect": "none",
        "provider_health_policy_applied": False,
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
        raise EligibilityRuntimeHealthAttributionError(
            "runtime-health attribution and incident must exist as one atomic pair"
        )
    if existing_attribution is not None:
        if not _matching_existing_attribution(
            existing_attribution,
            attribution_fingerprint=attribution_fingerprint,
            summary=attribution_summary,
            source_activity_id=source_activity_id,
            correlation_key=correlation_key,
        ):
            raise EligibilityRuntimeHealthAttributionError(
                "runtime-health attribution idempotency key conflicts with persisted attribution"
            )
        replay = record_eligibility_immune_incident(
            session,
            tenant_key=tenant,
            aggregate_key=aggregate,
            incident_key=key,
            kind=EligibilityImmuneIncidentKind.RUNTIME_HEALTH_FAILURE,
            summary=detail,
            source_activity_id=source_activity_id,
            correlation_key=correlation_key,
        )
        return AttributedEligibilityRuntimeHealthIncidentResult(
            schema_version=ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION,
            attribution_activity=existing_attribution,
            incident=replay,
        )

    context = eligibility_immune_system_context(
        tenant_key=tenant,
        correlation_key=correlation_key,
    )
    try:
        attribution = stage_activity(
            session,
            context,
            activity_key=attribution_key,
            stream_key=f"immune:eligibility:{aggregate}",
            activity_class=OrganizationActivityClass.operational,
            activity_type=ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_ACTIVITY_TYPE,
            title="Eligibility runtime-health failure attributed",
            summary=attribution_summary,
            source_object_type="eligibility_aggregate",
            source_object_id=aggregate,
            source_object_version=ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION,
            causation_activity_id=source_activity_id,
            occurred_at=now_utc(),
            payload=attribution_payload,
            correlation_key=correlation_key,
        )
        incident = record_eligibility_immune_incident(
            session,
            tenant_key=tenant,
            aggregate_key=aggregate,
            incident_key=key,
            kind=EligibilityImmuneIncidentKind.RUNTIME_HEALTH_FAILURE,
            summary=detail,
            source_activity_id=source_activity_id,
            correlation_key=correlation_key,
        )
    except Exception:
        session.rollback()
        raise

    return AttributedEligibilityRuntimeHealthIncidentResult(
        schema_version=ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION,
        attribution_activity=attribution,
        incident=incident,
    )
