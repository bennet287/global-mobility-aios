from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.autonomy_evidence_profile import CapabilityAutonomyEvidenceObservation
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActivity, OrganizationActorType, OrganizationPosition, now_utc
from app.services.organization_autonomy_profile import (
    AutonomyProfileIntegrityError,
    capability_autonomy_profile_snapshot,
)
from app.services.organization_command import (
    AuditMutation,
    AuthorityDenied,
    DependencyConflict,
    IdempotencyConflict,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    OrganizationCommandError,
    canonical_fingerprint,
    commit_mutations,
    require_human,
    require_role,
    tenant_record,
)


AUTONOMY_EVIDENCE_PROFILE_CONTRACT_VERSION = "v1.3-i.2"
HUMAN_REVIEW_OUTCOMES = frozenset({"accepted", "modified", "rejected", "not_reviewed"})
RECOVERY_OUTCOMES = frozenset({"succeeded", "failed", "not_applicable"})


class AutonomyEvidenceProfileIntegrityError(RuntimeError):
    """Raised when durable I.2 measurement evidence no longer reconciles."""


@dataclass(frozen=True, slots=True)
class AutonomyEvidenceObservationSnapshot:
    observation_id: UUID
    source_activity_id: UUID
    source_activity_fingerprint: str
    human_review_outcome: str
    evidence_grounded: bool
    verifier_contradiction: bool
    policy_compliant: bool
    freshness_compliant: bool
    critical_error: bool
    recovery_outcome: str
    sla_met: bool
    incident_count: int
    idempotency_key: str
    record_fingerprint: str
    created_by_actor_type: str
    created_by_actor_key: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AutonomyEvidenceMetricsSnapshot:
    qualifying_execution_volume: int
    evidence_grounded_count: int
    evidence_grounding_rate: float | None
    human_accepted_count: int
    human_modified_count: int
    human_rejected_count: int
    human_not_reviewed_count: int
    human_acceptance_rate: float | None
    human_modification_rate: float | None
    human_rejection_rate: float | None
    verifier_contradiction_count: int
    verifier_contradiction_rate: float | None
    policy_compliant_count: int
    policy_compliance_rate: float | None
    freshness_compliant_count: int
    freshness_compliance_rate: float | None
    critical_error_count: int
    critical_error_rate: float | None
    recovery_applicable_count: int
    recovery_succeeded_count: int
    recovery_failed_count: int
    recovery_success_rate: float | None
    sla_met_count: int
    sla_met_rate: float | None
    incident_count: int


@dataclass(frozen=True, slots=True)
class CapabilityAutonomyEvidenceProfileSnapshot:
    profile_id: UUID
    position_key: str
    capability_key: str
    context_scope: str
    profile_sequence: int
    current_autonomy_level: str
    board_ceiling: str
    evidence_policy_version: str
    metrics: AutonomyEvidenceMetricsSnapshot
    observations: tuple[AutonomyEvidenceObservationSnapshot, ...]


def _required(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidTransition(f"{field} is required")
    return normalized


def _normalize_choice(value: str, *, field: str, allowed: frozenset[str]) -> str:
    normalized = _required(value, field=field).lower()
    if normalized not in allowed:
        raise InvalidTransition(f"{field} is invalid")
    return normalized


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _require_measurement_actor(context: OrganizationCommandContext) -> None:
    if context.actor_type is OrganizationActorType.human:
        require_human(context, admin=True)
        if context.position_key != "board":
            raise AuthorityDenied("only the persistent Board position may attest autonomy evidence")
        return
    if context.actor_type is OrganizationActorType.system:
        require_role(context, "admin", "operator")
        if context.authenticated_user_id != "system":
            raise AuthorityDenied("system autonomy evidence must use the trusted system identity")
        return
    raise AuthorityDenied("autonomy evidence cannot be self-graded by this actor type")


def _observation_record_fingerprint(
    *,
    tenant_key: str,
    profile: CapabilityAutonomyProfile,
    source_activity_id: UUID,
    source_activity_fingerprint: str,
    human_review_outcome: str,
    evidence_grounded: bool,
    verifier_contradiction: bool,
    policy_compliant: bool,
    freshness_compliant: bool,
    critical_error: bool,
    recovery_outcome: str,
    sla_met: bool,
    incident_count: int,
    idempotency_key: str,
    created_by_actor_type: str,
    created_by_actor_key: str,
) -> str:
    return canonical_fingerprint(
        {
            "contract_version": AUTONOMY_EVIDENCE_PROFILE_CONTRACT_VERSION,
            "tenant_key": tenant_key,
            "profile_id": str(profile.id),
            "profile_record_fingerprint": profile.record_fingerprint,
            "position_key": profile.position_key,
            "capability_key": profile.capability_key,
            "context_scope": profile.context_scope,
            "profile_sequence": profile.profile_sequence,
            "evidence_policy_version": profile.evidence_policy_version,
            "source_activity_id": str(source_activity_id),
            "source_activity_fingerprint": source_activity_fingerprint,
            "human_review_outcome": human_review_outcome,
            "evidence_grounded": evidence_grounded,
            "verifier_contradiction": verifier_contradiction,
            "policy_compliant": policy_compliant,
            "freshness_compliant": freshness_compliant,
            "critical_error": critical_error,
            "recovery_outcome": recovery_outcome,
            "sla_met": sla_met,
            "incident_count": incident_count,
            "idempotency_key": idempotency_key,
            "created_by_actor_type": created_by_actor_type,
            "created_by_actor_key": created_by_actor_key,
        }
    )


def _idempotent_observation(
    session: Session,
    *,
    tenant_key: str,
    idempotency_key: str,
    record_fingerprint: str,
) -> CapabilityAutonomyEvidenceObservation | None:
    existing = session.exec(
        select(CapabilityAutonomyEvidenceObservation).where(
            CapabilityAutonomyEvidenceObservation.tenant_key == tenant_key,
            CapabilityAutonomyEvidenceObservation.idempotency_key == idempotency_key,
        )
    ).first()
    if existing is None:
        return None
    if existing.record_fingerprint != record_fingerprint:
        raise IdempotencyConflict(
            "autonomy evidence observation idempotency key was already used with different semantics"
        )
    return existing


def establish_capability_autonomy_evidence_observation(
    session: Session,
    context: OrganizationCommandContext,
    *,
    profile_id: UUID,
    source_activity_id: UUID,
    human_review_outcome: str,
    evidence_grounded: bool,
    verifier_contradiction: bool,
    policy_compliant: bool,
    freshness_compliant: bool,
    critical_error: bool,
    recovery_outcome: str,
    sla_met: bool,
    incident_count: int,
    idempotency_key: str,
) -> CapabilityAutonomyEvidenceObservation:
    """Record one immutable shadow measurement without changing autonomy truth."""

    _require_measurement_actor(context)
    human_review_outcome = _normalize_choice(
        human_review_outcome,
        field="human_review_outcome",
        allowed=HUMAN_REVIEW_OUTCOMES,
    )
    recovery_outcome = _normalize_choice(
        recovery_outcome,
        field="recovery_outcome",
        allowed=RECOVERY_OUTCOMES,
    )
    idempotency_key = _required(idempotency_key, field="idempotency_key")
    if incident_count < 0:
        raise InvalidTransition("incident_count must be non-negative")

    profile_statement = select(CapabilityAutonomyProfile).where(
        CapabilityAutonomyProfile.id == profile_id,
        CapabilityAutonomyProfile.tenant_key == context.tenant_key,
    )
    if session.get_bind().dialect.name == "postgresql":
        profile_statement = profile_statement.with_for_update()
    profile = session.exec(profile_statement).first()
    if profile is None:
        raise InvalidReference("capability autonomy profile was not found")

    source_activity = tenant_record(
        session,
        OrganizationActivity,
        source_activity_id,
        context.tenant_key,
        label="autonomy evidence source activity",
    )
    actor_type = context.actor_type.value
    record_fingerprint = _observation_record_fingerprint(
        tenant_key=context.tenant_key,
        profile=profile,
        source_activity_id=source_activity.id,
        source_activity_fingerprint=source_activity.record_fingerprint,
        human_review_outcome=human_review_outcome,
        evidence_grounded=bool(evidence_grounded),
        verifier_contradiction=bool(verifier_contradiction),
        policy_compliant=bool(policy_compliant),
        freshness_compliant=bool(freshness_compliant),
        critical_error=bool(critical_error),
        recovery_outcome=recovery_outcome,
        sla_met=bool(sla_met),
        incident_count=incident_count,
        idempotency_key=idempotency_key,
        created_by_actor_type=actor_type,
        created_by_actor_key=context.actor_id,
    )
    replay = _idempotent_observation(
        session,
        tenant_key=context.tenant_key,
        idempotency_key=idempotency_key,
        record_fingerprint=record_fingerprint,
    )
    if replay is not None:
        return replay

    profile_snapshot = capability_autonomy_profile_snapshot(
        session,
        tenant_key=context.tenant_key,
        position_key=profile.position_key,
        capability_key=profile.capability_key,
        context_scope=profile.context_scope,
    )
    if profile_snapshot is None or profile_snapshot.current_profile_id != profile.id:
        raise InvalidTransition("autonomy evidence observations require the current I.1 profile")

    target_position = session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == profile.position_key,
            OrganizationPosition.status == "active",
        )
    ).first()
    if target_position is None:
        raise InvalidReference("active organization position was not found")

    existing_source = session.exec(
        select(CapabilityAutonomyEvidenceObservation).where(
            CapabilityAutonomyEvidenceObservation.tenant_key == context.tenant_key,
            CapabilityAutonomyEvidenceObservation.profile_id == profile.id,
            CapabilityAutonomyEvidenceObservation.source_activity_id == source_activity.id,
        )
    ).first()
    if existing_source is not None:
        raise DependencyConflict("source Activity is already counted for this autonomy profile")

    occurred_at = now_utc()
    observation = CapabilityAutonomyEvidenceObservation(
        tenant_key=context.tenant_key,
        profile_id=profile.id,
        position_id=target_position.id,
        position_key=profile.position_key,
        capability_key=profile.capability_key,
        context_scope=profile.context_scope,
        profile_sequence=profile.profile_sequence,
        evidence_policy_version=profile.evidence_policy_version,
        source_activity_id=source_activity.id,
        source_activity_fingerprint=source_activity.record_fingerprint,
        human_review_outcome=human_review_outcome,
        evidence_grounded=bool(evidence_grounded),
        verifier_contradiction=bool(verifier_contradiction),
        policy_compliant=bool(policy_compliant),
        freshness_compliant=bool(freshness_compliant),
        critical_error=bool(critical_error),
        recovery_outcome=recovery_outcome,
        sla_met=bool(sla_met),
        incident_count=incident_count,
        idempotency_key=idempotency_key,
        record_fingerprint=record_fingerprint,
        created_by_actor_type=actor_type,
        created_by_actor_key=context.actor_id,
        created_at=occurred_at,
    )
    session.add(observation)
    try:
        commit_mutations(
            session,
            mutations=(
                AuditMutation(
                    action="organization.autonomy_evidence.observe",
                    entity_type="capability_autonomy_evidence_observation",
                    entity_id=observation.id,
                    after_state=observation,
                    reason="Recorded qualifying I.2 shadow autonomy evidence; no autonomy mutation.",
                ),
            ),
            context=context,
            refresh=(observation,),
        )
        return observation
    except IntegrityError as exc:
        session.rollback()
        replay = _idempotent_observation(
            session,
            tenant_key=context.tenant_key,
            idempotency_key=idempotency_key,
            record_fingerprint=record_fingerprint,
        )
        if replay is not None:
            return replay
        duplicate = session.exec(
            select(CapabilityAutonomyEvidenceObservation).where(
                CapabilityAutonomyEvidenceObservation.tenant_key == context.tenant_key,
                CapabilityAutonomyEvidenceObservation.profile_id == profile.id,
                CapabilityAutonomyEvidenceObservation.source_activity_id == source_activity.id,
            )
        ).first()
        if duplicate is not None:
            raise DependencyConflict(
                "source Activity is already counted for this autonomy profile"
            ) from exc
        raise DependencyConflict("autonomy evidence changed concurrently") from exc
    except Exception:
        session.rollback()
        raise


def _validated_observation_snapshot(
    session: Session,
    *,
    profile: CapabilityAutonomyProfile,
    observation: CapabilityAutonomyEvidenceObservation,
) -> AutonomyEvidenceObservationSnapshot:
    if (
        observation.tenant_key != profile.tenant_key
        or observation.profile_id != profile.id
        or observation.position_key != profile.position_key
        or observation.capability_key != profile.capability_key
        or observation.context_scope != profile.context_scope
        or observation.profile_sequence != profile.profile_sequence
        or observation.evidence_policy_version != profile.evidence_policy_version
    ):
        raise AutonomyEvidenceProfileIntegrityError("autonomy evidence scope drifted")
    if observation.human_review_outcome not in HUMAN_REVIEW_OUTCOMES:
        raise AutonomyEvidenceProfileIntegrityError("autonomy evidence human outcome is invalid")
    if observation.recovery_outcome not in RECOVERY_OUTCOMES:
        raise AutonomyEvidenceProfileIntegrityError("autonomy evidence recovery outcome is invalid")
    if observation.incident_count < 0:
        raise AutonomyEvidenceProfileIntegrityError("autonomy evidence incident count is invalid")

    position = session.get(OrganizationPosition, observation.position_id)
    if position is None or position.position_key != profile.position_key:
        raise AutonomyEvidenceProfileIntegrityError("autonomy evidence position identity drifted")
    try:
        source_activity = tenant_record(
            session,
            OrganizationActivity,
            observation.source_activity_id,
            profile.tenant_key,
            label="autonomy evidence source activity",
        )
    except OrganizationCommandError as exc:
        raise AutonomyEvidenceProfileIntegrityError(
            "autonomy evidence source Activity is unavailable"
        ) from exc
    if source_activity.record_fingerprint != observation.source_activity_fingerprint:
        raise AutonomyEvidenceProfileIntegrityError("autonomy evidence source fingerprint drifted")

    expected_fingerprint = _observation_record_fingerprint(
        tenant_key=profile.tenant_key,
        profile=profile,
        source_activity_id=observation.source_activity_id,
        source_activity_fingerprint=observation.source_activity_fingerprint,
        human_review_outcome=observation.human_review_outcome,
        evidence_grounded=observation.evidence_grounded,
        verifier_contradiction=observation.verifier_contradiction,
        policy_compliant=observation.policy_compliant,
        freshness_compliant=observation.freshness_compliant,
        critical_error=observation.critical_error,
        recovery_outcome=observation.recovery_outcome,
        sla_met=observation.sla_met,
        incident_count=observation.incident_count,
        idempotency_key=observation.idempotency_key,
        created_by_actor_type=observation.created_by_actor_type,
        created_by_actor_key=observation.created_by_actor_key,
    )
    if expected_fingerprint != observation.record_fingerprint:
        raise AutonomyEvidenceProfileIntegrityError("autonomy evidence record fingerprint drifted")

    return AutonomyEvidenceObservationSnapshot(
        observation_id=observation.id,
        source_activity_id=observation.source_activity_id,
        source_activity_fingerprint=observation.source_activity_fingerprint,
        human_review_outcome=observation.human_review_outcome,
        evidence_grounded=observation.evidence_grounded,
        verifier_contradiction=observation.verifier_contradiction,
        policy_compliant=observation.policy_compliant,
        freshness_compliant=observation.freshness_compliant,
        critical_error=observation.critical_error,
        recovery_outcome=observation.recovery_outcome,
        sla_met=observation.sla_met,
        incident_count=observation.incident_count,
        idempotency_key=observation.idempotency_key,
        record_fingerprint=observation.record_fingerprint,
        created_by_actor_type=observation.created_by_actor_type,
        created_by_actor_key=observation.created_by_actor_key,
        created_at=observation.created_at,
    )


def _metrics(
    observations: tuple[AutonomyEvidenceObservationSnapshot, ...],
) -> AutonomyEvidenceMetricsSnapshot:
    volume = len(observations)
    evidence_grounded = sum(item.evidence_grounded for item in observations)
    accepted = sum(item.human_review_outcome == "accepted" for item in observations)
    modified = sum(item.human_review_outcome == "modified" for item in observations)
    rejected = sum(item.human_review_outcome == "rejected" for item in observations)
    not_reviewed = sum(item.human_review_outcome == "not_reviewed" for item in observations)
    reviewed = accepted + modified + rejected
    contradictions = sum(item.verifier_contradiction for item in observations)
    policy_compliant = sum(item.policy_compliant for item in observations)
    freshness_compliant = sum(item.freshness_compliant for item in observations)
    critical_errors = sum(item.critical_error for item in observations)
    recovery_succeeded = sum(item.recovery_outcome == "succeeded" for item in observations)
    recovery_failed = sum(item.recovery_outcome == "failed" for item in observations)
    recovery_applicable = recovery_succeeded + recovery_failed
    sla_met = sum(item.sla_met for item in observations)
    incidents = sum(item.incident_count for item in observations)
    return AutonomyEvidenceMetricsSnapshot(
        qualifying_execution_volume=volume,
        evidence_grounded_count=evidence_grounded,
        evidence_grounding_rate=_rate(evidence_grounded, volume),
        human_accepted_count=accepted,
        human_modified_count=modified,
        human_rejected_count=rejected,
        human_not_reviewed_count=not_reviewed,
        human_acceptance_rate=_rate(accepted, reviewed),
        human_modification_rate=_rate(modified, reviewed),
        human_rejection_rate=_rate(rejected, reviewed),
        verifier_contradiction_count=contradictions,
        verifier_contradiction_rate=_rate(contradictions, volume),
        policy_compliant_count=policy_compliant,
        policy_compliance_rate=_rate(policy_compliant, volume),
        freshness_compliant_count=freshness_compliant,
        freshness_compliance_rate=_rate(freshness_compliant, volume),
        critical_error_count=critical_errors,
        critical_error_rate=_rate(critical_errors, volume),
        recovery_applicable_count=recovery_applicable,
        recovery_succeeded_count=recovery_succeeded,
        recovery_failed_count=recovery_failed,
        recovery_success_rate=_rate(recovery_succeeded, recovery_applicable),
        sla_met_count=sla_met,
        sla_met_rate=_rate(sla_met, volume),
        incident_count=incidents,
    )


def capability_autonomy_evidence_profile_snapshot(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
) -> CapabilityAutonomyEvidenceProfileSnapshot | None:
    """Compute one validated, measurement-only evidence profile for current I.1 truth."""

    try:
        profile_snapshot = capability_autonomy_profile_snapshot(
            session,
            tenant_key=tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
    except AutonomyProfileIntegrityError as exc:
        raise AutonomyEvidenceProfileIntegrityError("I.1 autonomy profile integrity failed") from exc
    if profile_snapshot is None:
        return None

    profile = tenant_record(
        session,
        CapabilityAutonomyProfile,
        profile_snapshot.current_profile_id,
        tenant_key,
        label="current autonomy profile",
    )
    rows = tuple(
        session.exec(
            select(CapabilityAutonomyEvidenceObservation)
            .where(
                CapabilityAutonomyEvidenceObservation.tenant_key == tenant_key,
                CapabilityAutonomyEvidenceObservation.profile_id == profile.id,
            )
            .order_by(
                CapabilityAutonomyEvidenceObservation.created_at.asc(),
                CapabilityAutonomyEvidenceObservation.id.asc(),
            )
        ).all()
    )
    seen_sources: set[UUID] = set()
    snapshots: list[AutonomyEvidenceObservationSnapshot] = []
    for row in rows:
        if row.source_activity_id in seen_sources:
            raise AutonomyEvidenceProfileIntegrityError("autonomy evidence source was counted twice")
        seen_sources.add(row.source_activity_id)
        snapshots.append(
            _validated_observation_snapshot(session, profile=profile, observation=row)
        )
    observation_snapshots = tuple(snapshots)
    return CapabilityAutonomyEvidenceProfileSnapshot(
        profile_id=profile.id,
        position_key=profile.position_key,
        capability_key=profile.capability_key,
        context_scope=profile.context_scope,
        profile_sequence=profile.profile_sequence,
        current_autonomy_level=profile.autonomy_level,
        board_ceiling=profile.board_ceiling,
        evidence_policy_version=profile.evidence_policy_version,
        metrics=_metrics(observation_snapshots),
        observations=observation_snapshots,
    )
