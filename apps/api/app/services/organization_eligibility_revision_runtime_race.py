from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationActivityClass, now_utc
from app.models.eligibility_revision import EligibilityAssessmentRevision
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
from app.services.organization_eligibility_lineage import (
    CanonicalEligibilityLineageError,
    validate_canonical_eligibility_lineage,
)
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPostResolutionAdvance,
)
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record


ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_SCHEMA_VERSION = (
    "eligibility-revision-runtime-race-attribution.v1"
)
ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_ACTIVITY_TYPE = (
    "organization.immune.eligibility_revision_runtime_race_attributed.v1"
)
ELIGIBILITY_REVISION_RUNTIME_RACE_FAILURE_STAGE = (
    "e2_revision_precondition_post_producer_egress"
)


class EligibilityRevisionRuntimeRaceAttributionError(RuntimeError):
    """Trusted H.2.4 post-producer revision-race attribution is inconsistent."""


@dataclass(frozen=True)
class AttributedEligibilityRevisionRuntimeRaceResult:
    schema_version: str
    attribution_activity: OrganizationActivity
    incident: EligibilityImmuneIncidentResult


def _required_text(value: str, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise EligibilityRevisionRuntimeRaceAttributionError(f"{label} is required")
    return normalized


def _attribution_activity_key(*, aggregate_key: str, incident_key: str) -> str:
    return f"immune:eligibility:{aggregate_key}:revision-runtime-race-attribution:{incident_key}"


def _incident_activity_key(*, aggregate_key: str, incident_key: str) -> str:
    return f"immune:eligibility:{aggregate_key}:incident:{incident_key}"


def _validate_race(
    *,
    tenant_key: str,
    aggregate_key: str,
    race: EligibilityRevisionPostResolutionAdvance,
) -> None:
    if race.tenant_key != tenant_key:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "revision runtime race belongs to a different tenant"
        )
    if race.aggregate_key != aggregate_key:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "revision runtime race belongs to a different eligibility aggregate"
        )
    if race.expected_revision_version < 1:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "revision runtime race expected version must be positive"
        )
    if race.expected_revision_version != race.resolved_revision_version:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "revision runtime race must begin from an exact accepted reassessment revision"
        )
    if race.observed_current_revision_id == race.resolved_revision_id:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "revision runtime race must observe a different canonical revision identity"
        )
    if race.observed_current_revision_version <= race.resolved_revision_version:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "revision runtime race must advance to a newer canonical revision"
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
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "persisted eligibility revision runtime-race attribution Activity is malformed"
        ) from exc
    return (
        record.activity_type == ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_ACTIVITY_TYPE
        and existing.summary == summary
        and existing.causation_activity_id is None
        and existing.correlation_key is None
        and record.payload.get("attribution_fingerprint") == attribution_fingerprint
    )


def _fresh_revision(
    session: Session,
    *,
    revision_id: UUID,
) -> EligibilityAssessmentRevision | None:
    return session.exec(
        select(EligibilityAssessmentRevision)
        .where(EligibilityAssessmentRevision.id == revision_id)
        .execution_options(populate_existing=True)
    ).first()


def _reconcile_event_time_revision_snapshot(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
    race: EligibilityRevisionPostResolutionAdvance,
) -> None:
    """Prove an observed event-time revision remains on the canonical descendant chain."""

    resolved_revision = _fresh_revision(
        session,
        revision_id=race.resolved_revision_id,
    )
    observed_revision = _fresh_revision(
        session,
        revision_id=race.observed_current_revision_id,
    )
    if (
        resolved_revision is None
        or resolved_revision.tenant_key != tenant_key
        or resolved_revision.aggregate_key != aggregate_key
        or resolved_revision.version != race.resolved_revision_version
        or resolved_revision.lifecycle_status != "superseded"
    ):
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "resolved revision snapshot cannot be reconciled with durable superseded lineage"
        )
    if (
        observed_revision is None
        or observed_revision.tenant_key != tenant_key
        or observed_revision.aggregate_key != aggregate_key
        or observed_revision.version != race.observed_current_revision_version
        or observed_revision.lifecycle_status not in {"active", "superseded"}
    ):
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "observed revision snapshot cannot be reconciled with durable canonical lineage"
        )

    active_revisions = list(
        session.exec(
            select(EligibilityAssessmentRevision)
            .where(
                EligibilityAssessmentRevision.tenant_key == tenant_key,
                EligibilityAssessmentRevision.aggregate_key == aggregate_key,
                EligibilityAssessmentRevision.lifecycle_status == "active",
            )
            .order_by(EligibilityAssessmentRevision.version.desc())
            .execution_options(populate_existing=True)
        ).all()
    )
    if len(active_revisions) != 1:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "eligibility aggregate must have exactly one current ACTIVE revision"
        )
    current_revision = active_revisions[0]
    if current_revision.id == observed_revision.id:
        if observed_revision.lifecycle_status != "active":
            raise EligibilityRevisionRuntimeRaceAttributionError(
                "observed revision lifecycle conflicts with the current ACTIVE revision"
            )
    elif (
        observed_revision.lifecycle_status != "superseded"
        or current_revision.version <= observed_revision.version
    ):
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "a superseded observed revision requires a newer current ACTIVE descendant"
        )

    observed_seen = False
    cursor = current_revision
    while True:
        fresh_cursor = _fresh_revision(session, revision_id=cursor.id)
        if fresh_cursor is None:
            raise EligibilityRevisionRuntimeRaceAttributionError(
                "canonical revision descendant chain contains a missing revision"
            )
        if fresh_cursor.supersedes_revision_id is not None:
            _fresh_revision(
                session,
                revision_id=fresh_cursor.supersedes_revision_id,
            )
        try:
            lineage = validate_canonical_eligibility_lineage(
                session,
                tenant_key=tenant_key,
                revision=fresh_cursor,
            )
        except CanonicalEligibilityLineageError as exc:
            raise EligibilityRevisionRuntimeRaceAttributionError(
                "revision runtime-race snapshot conflicts with canonical eligibility lineage"
            ) from exc

        if fresh_cursor.id == observed_revision.id:
            observed_seen = True
        if fresh_cursor.id == resolved_revision.id:
            break
        if (
            fresh_cursor.version <= resolved_revision.version
            or lineage.predecessor_revision is None
        ):
            raise EligibilityRevisionRuntimeRaceAttributionError(
                "revision runtime-race snapshot is not on the current canonical descendant chain"
            )
        cursor = lineage.predecessor_revision

    if not observed_seen:
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "observed revision snapshot is not on the current canonical descendant chain"
        )


def record_attributed_eligibility_revision_runtime_race(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
    incident_key: str,
    race: EligibilityRevisionPostResolutionAdvance,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
    summary: str,
) -> AttributedEligibilityRevisionRuntimeRaceResult:
    """Persist one H.2.4 post-producer stale-reassessment observation atomically.

    The supplied race proves only canonical-state advancement. This command is called
    exclusively from the trusted G.4/E.2 producer boundary after a successful producer
    response, so provider egress is known to have occurred while verifier egress and a
    canonical effect have not. The paired REVISION_CONFLICT incident remains warning-only
    and does not participate in H.2.1 recurrence.

    First persistence treats the observed revision as an event-time snapshot. It may
    already have become superseded, but only if the durable canonical aggregate proves
    that it remains on the contiguous descendant chain from the resolved revision to the
    single newer ACTIVE head. Historical replay validates the immutable persisted
    attribution before requiring that once-observed revision to remain current.
    """

    tenant = _required_text(tenant_key, label="tenant_key")
    aggregate = _required_text(aggregate_key, label="aggregate_key")
    key = _required_text(incident_key, label="incident_key")
    position = _required_text(position_key, label="position_key")
    detail = _required_text(summary, label="summary")
    if not aggregate.startswith(f"eligibility:{tenant}:"):
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "eligibility aggregate key does not belong to the supplied tenant"
        )
    _validate_race(
        tenant_key=tenant,
        aggregate_key=aggregate,
        race=race,
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
        "Attributed a canonical eligibility revision advance detected after producer egress."
    )
    runtime_profile_fp = runtime_profile_fingerprint(runtime_profile)
    attribution_payload = {
        "attribution_contract": ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_SCHEMA_VERSION,
        "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
        "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
        "aggregate_key": aggregate,
        "incident_key": key,
        "incident_activity_key": incident_activity_key,
        "incident_kind": EligibilityImmuneIncidentKind.REVISION_CONFLICT.value,
        "failure_stage": ELIGIBILITY_REVISION_RUNTIME_RACE_FAILURE_STAGE,
        "conflict_basis": "canonical_revision_advanced_during_producer_runtime",
        "expected_revision_version": race.expected_revision_version,
        "resolved_revision_id": str(race.resolved_revision_id),
        "resolved_revision_version": race.resolved_revision_version,
        "observed_current_revision_id": str(race.observed_current_revision_id),
        "observed_current_revision_version": race.observed_current_revision_version,
        "observed_current_lifecycle_status": "active",
        "producer_egress_occurred": True,
        "verifier_egress_occurred": False,
        "canonical_effect_committed": False,
        "execution_role": "producer",
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
        "recurrence_policy_applied": False,
        "automatic_retry_applied": False,
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
        raise EligibilityRevisionRuntimeRaceAttributionError(
            "revision runtime-race attribution and incident must exist as one atomic pair"
        )
    if existing_attribution is not None:
        if not _matching_existing_attribution(
            existing_attribution,
            attribution_fingerprint=attribution_fingerprint,
            summary=attribution_summary,
        ):
            raise EligibilityRevisionRuntimeRaceAttributionError(
                "revision runtime-race idempotency key conflicts with persisted attribution"
            )
        replay = record_eligibility_immune_incident(
            session,
            tenant_key=tenant,
            aggregate_key=aggregate,
            incident_key=key,
            kind=EligibilityImmuneIncidentKind.REVISION_CONFLICT,
            summary=detail,
        )
        return AttributedEligibilityRevisionRuntimeRaceResult(
            schema_version=ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_SCHEMA_VERSION,
            attribution_activity=existing_attribution,
            incident=replay,
        )

    _reconcile_event_time_revision_snapshot(
        session,
        tenant_key=tenant,
        aggregate_key=aggregate,
        race=race,
    )

    context = eligibility_immune_system_context(tenant_key=tenant)
    try:
        attribution = stage_activity(
            session,
            context,
            activity_key=attribution_key,
            stream_key=f"immune:eligibility:{aggregate}",
            activity_class=OrganizationActivityClass.operational,
            activity_type=ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_ACTIVITY_TYPE,
            title="Eligibility revision runtime race attributed",
            summary=attribution_summary,
            source_object_type="eligibility_aggregate",
            source_object_id=aggregate,
            source_object_version=ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_SCHEMA_VERSION,
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

    return AttributedEligibilityRevisionRuntimeRaceResult(
        schema_version=ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_SCHEMA_VERSION,
        attribution_activity=attribution,
        incident=incident,
    )
