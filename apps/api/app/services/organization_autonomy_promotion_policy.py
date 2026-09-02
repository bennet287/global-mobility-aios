from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.autonomy_promotion_policy import CapabilityAutonomyPromotionPolicy
from app.models.domain import OrganizationActivity, OrganizationActorType, OrganizationPosition, now_utc
from app.services.organization_activity import stage_activity
from app.services.organization_autonomy_evidence_profile import (
    CapabilityAutonomyEvidenceProfileSnapshot,
    capability_autonomy_evidence_profile_snapshot,
)
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
    tenant_record,
)


AUTONOMY_PROMOTION_POLICY_CONTRACT_VERSION = "v1.3-i.3"
AUTONOMY_PROMOTION_POLICY_ACTIVITY_TYPE = "organization.autonomy_promotion_policy.established.v1"
AUTONOMY_PROMOTION_POLICY_SOURCE_TYPE = "capability_autonomy_promotion_policy"
AUTONOMY_PROMOTION_POLICY_GOVERNANCE_SOURCE = "human_board"
AUTONOMY_PROMOTION_CONSTITUTIONAL_ACTIVITY_CLASS = "AUTHORITY"
PROMOTION_ELIGIBLE = "ELIGIBLE"
PROMOTION_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
PROMOTION_HOLD = "HOLD"


class AutonomyPromotionPolicyIntegrityError(RuntimeError):
    """Raised when durable I.3 promotion-policy truth no longer reconciles."""


@dataclass(frozen=True, slots=True)
class AutonomyPromotionPolicyRevisionSnapshot:
    policy_id: UUID
    profile_id: UUID
    profile_sequence: int
    profile_record_fingerprint: str
    policy_sequence: int
    lifecycle_status: str
    from_autonomy_level: str
    target_autonomy_level: str
    evidence_policy_version: str
    min_qualifying_execution_volume: int
    min_human_reviewed_count: int
    min_evidence_grounding_rate: float
    min_human_acceptance_rate: float
    max_human_modification_rate: float
    max_human_rejection_rate: float
    max_verifier_contradiction_rate: float
    min_policy_compliance_rate: float
    min_freshness_compliance_rate: float
    max_critical_error_count: int
    min_recovery_applicable_count: int
    min_recovery_success_rate: float | None
    min_sla_met_rate: float
    max_incident_count: int
    policy_reason: str
    supersedes_policy_id: UUID | None
    decision_activity_id: UUID
    decision_activity_fingerprint: str
    record_fingerprint: str
    effective_from: datetime
    created_at: datetime
    created_by: str


@dataclass(frozen=True, slots=True)
class CapabilityAutonomyPromotionPolicySnapshot:
    profile_id: UUID
    profile_sequence: int
    profile_record_fingerprint: str
    position_key: str
    capability_key: str
    context_scope: str
    current_policy_id: UUID
    current_policy_sequence: int
    from_autonomy_level: str
    target_autonomy_level: str
    evidence_policy_version: str
    revisions: tuple[AutonomyPromotionPolicyRevisionSnapshot, ...]


@dataclass(frozen=True, slots=True)
class AutonomyPromotionCriterionSnapshot:
    criterion_key: str
    comparison: str
    required_value: int | float
    observed_value: int | float | None
    sample_requirement: bool
    evaluable: bool
    passed: bool | None


@dataclass(frozen=True, slots=True)
class AutonomyPromotionEligibilitySnapshot:
    profile_id: UUID
    profile_sequence: int
    position_key: str
    capability_key: str
    context_scope: str
    current_autonomy_level: str
    board_ceiling: str
    evidence_policy_version: str
    policy_id: UUID
    policy_sequence: int
    target_autonomy_level: str
    eligibility_state: str
    criteria: tuple[AutonomyPromotionCriterionSnapshot, ...]
    evidence_profile: CapabilityAutonomyEvidenceProfileSnapshot


def _required(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidTransition(f"{field} is required")
    return normalized


def _autonomy_rank(level: AutonomyLevel | str) -> int:
    resolved = AutonomyLevel(level)
    return int(resolved.value[1])


def _validate_rate(value: float, *, field: str) -> float:
    resolved = float(value)
    if not math.isfinite(resolved) or resolved < 0 or resolved > 1:
        raise InvalidTransition(f"{field} must be a finite value between 0 and 1")
    return resolved


def _validated_persisted_rate(value: float, *, field: str) -> float:
    resolved = float(value)
    if not math.isfinite(resolved) or resolved < 0 or resolved > 1:
        raise AutonomyPromotionPolicyIntegrityError(f"promotion policy {field} is invalid")
    return resolved


def _criteria_payload(
    *,
    min_qualifying_execution_volume: int,
    min_human_reviewed_count: int,
    min_evidence_grounding_rate: float,
    min_human_acceptance_rate: float,
    max_human_modification_rate: float,
    max_human_rejection_rate: float,
    max_verifier_contradiction_rate: float,
    min_policy_compliance_rate: float,
    min_freshness_compliance_rate: float,
    max_critical_error_count: int,
    min_recovery_applicable_count: int,
    min_recovery_success_rate: float | None,
    min_sla_met_rate: float,
    max_incident_count: int,
) -> dict[str, int | float | None]:
    return {
        "min_qualifying_execution_volume": min_qualifying_execution_volume,
        "min_human_reviewed_count": min_human_reviewed_count,
        "min_evidence_grounding_rate": min_evidence_grounding_rate,
        "min_human_acceptance_rate": min_human_acceptance_rate,
        "max_human_modification_rate": max_human_modification_rate,
        "max_human_rejection_rate": max_human_rejection_rate,
        "max_verifier_contradiction_rate": max_verifier_contradiction_rate,
        "min_policy_compliance_rate": min_policy_compliance_rate,
        "min_freshness_compliance_rate": min_freshness_compliance_rate,
        "max_critical_error_count": max_critical_error_count,
        "min_recovery_applicable_count": min_recovery_applicable_count,
        "min_recovery_success_rate": min_recovery_success_rate,
        "min_sla_met_rate": min_sla_met_rate,
        "max_incident_count": max_incident_count,
    }


def _policy_record_fingerprint(
    *,
    tenant_key: str,
    profile_id: UUID,
    profile_sequence: int,
    profile_record_fingerprint: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
    from_autonomy_level: str,
    target_autonomy_level: str,
    evidence_policy_version: str,
    criteria: dict[str, int | float | None],
    policy_reason: str,
    idempotency_key: str,
) -> str:
    return canonical_fingerprint(
        {
            "contract_version": AUTONOMY_PROMOTION_POLICY_CONTRACT_VERSION,
            "tenant_key": tenant_key,
            "profile_id": str(profile_id),
            "profile_sequence": profile_sequence,
            "profile_record_fingerprint": profile_record_fingerprint,
            "position_key": position_key,
            "capability_key": capability_key,
            "context_scope": context_scope,
            "from_autonomy_level": from_autonomy_level,
            "target_autonomy_level": target_autonomy_level,
            "evidence_policy_version": evidence_policy_version,
            "criteria": criteria,
            "policy_reason": policy_reason,
            "governance_source": AUTONOMY_PROMOTION_POLICY_GOVERNANCE_SOURCE,
            "idempotency_key": idempotency_key,
        }
    )


def _profile_policy_statement(*, tenant_key: str, profile_id: UUID):
    return select(CapabilityAutonomyPromotionPolicy).where(
        CapabilityAutonomyPromotionPolicy.tenant_key == tenant_key,
        CapabilityAutonomyPromotionPolicy.profile_id == profile_id,
    )


def _idempotent_policy(
    session: Session,
    *,
    tenant_key: str,
    idempotency_key: str,
    record_fingerprint: str,
) -> CapabilityAutonomyPromotionPolicy | None:
    existing = session.exec(
        select(CapabilityAutonomyPromotionPolicy).where(
            CapabilityAutonomyPromotionPolicy.tenant_key == tenant_key,
            CapabilityAutonomyPromotionPolicy.idempotency_key == idempotency_key,
        )
    ).first()
    if existing is None:
        return None
    if existing.record_fingerprint != record_fingerprint:
        raise IdempotencyConflict(
            "autonomy promotion policy idempotency key was already used with different semantics"
        )
    return existing


def _locked_current_profile(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
    profile_id: UUID,
) -> CapabilityAutonomyProfile:
    statement = select(CapabilityAutonomyProfile).where(
        CapabilityAutonomyProfile.tenant_key == tenant_key,
        CapabilityAutonomyProfile.id == profile_id,
    )
    if session.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    profile = session.exec(statement).first()
    if profile is None:
        raise InvalidTransition("expected autonomy profile is stale")
    if (
        profile.position_key != position_key
        or profile.capability_key != capability_key
        or profile.context_scope != context_scope
    ):
        raise InvalidTransition("expected autonomy profile is stale")
    try:
        snapshot = capability_autonomy_profile_snapshot(
            session,
            tenant_key=tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
    except AutonomyProfileIntegrityError as exc:
        raise InvalidTransition("current I.1 autonomy profile integrity failed") from exc
    if snapshot is None or snapshot.current_profile_id != profile_id:
        raise InvalidTransition("expected autonomy profile is stale")
    return profile


def establish_capability_autonomy_promotion_policy(
    session: Session,
    context: OrganizationCommandContext,
    *,
    position_key: str,
    capability_key: str,
    context_scope: str,
    from_autonomy_level: AutonomyLevel | str,
    target_autonomy_level: AutonomyLevel | str,
    evidence_policy_version: str,
    min_qualifying_execution_volume: int,
    min_human_reviewed_count: int,
    min_evidence_grounding_rate: float,
    min_human_acceptance_rate: float,
    max_human_modification_rate: float,
    max_human_rejection_rate: float,
    max_verifier_contradiction_rate: float,
    min_policy_compliance_rate: float,
    min_freshness_compliance_rate: float,
    max_critical_error_count: int,
    min_recovery_applicable_count: int,
    min_recovery_success_rate: float | None,
    min_sla_met_rate: float,
    max_incident_count: int,
    policy_reason: str,
    idempotency_key: str,
    expected_profile_id: UUID | None = None,
    expected_policy_sequence: int | None = None,
) -> CapabilityAutonomyPromotionPolicy:
    """Append Board-authored promotion criteria without changing autonomy truth."""

    require_human(context, admin=True)
    if context.position_key != "board":
        raise AuthorityDenied("only the persistent Board position may establish promotion criteria")

    position_key = _required(position_key, field="position_key")
    capability_key = _required(capability_key, field="capability_key")
    context_scope = _required(context_scope, field="context_scope")
    evidence_policy_version = _required(evidence_policy_version, field="evidence_policy_version")
    policy_reason = _required(policy_reason, field="policy_reason")
    idempotency_key = _required(idempotency_key, field="idempotency_key")
    try:
        from_level = AutonomyLevel(from_autonomy_level)
        target_level = AutonomyLevel(target_autonomy_level)
    except ValueError as exc:
        raise InvalidTransition("from_autonomy_level or target_autonomy_level is invalid") from exc
    if _autonomy_rank(target_level) != _autonomy_rank(from_level) + 1:
        raise InvalidTransition("promotion policy target must be exactly one autonomy level above current")

    if min_qualifying_execution_volume < 1:
        raise InvalidTransition("min_qualifying_execution_volume must be at least 1")
    if min_human_reviewed_count < 1:
        raise InvalidTransition("min_human_reviewed_count must be at least 1")
    if max_critical_error_count < 0:
        raise InvalidTransition("max_critical_error_count must be non-negative")
    if min_recovery_applicable_count < 0:
        raise InvalidTransition("min_recovery_applicable_count must be non-negative")
    if max_incident_count < 0:
        raise InvalidTransition("max_incident_count must be non-negative")

    min_evidence_grounding_rate = _validate_rate(
        min_evidence_grounding_rate, field="min_evidence_grounding_rate"
    )
    min_human_acceptance_rate = _validate_rate(
        min_human_acceptance_rate, field="min_human_acceptance_rate"
    )
    max_human_modification_rate = _validate_rate(
        max_human_modification_rate, field="max_human_modification_rate"
    )
    max_human_rejection_rate = _validate_rate(
        max_human_rejection_rate, field="max_human_rejection_rate"
    )
    max_verifier_contradiction_rate = _validate_rate(
        max_verifier_contradiction_rate, field="max_verifier_contradiction_rate"
    )
    min_policy_compliance_rate = _validate_rate(
        min_policy_compliance_rate, field="min_policy_compliance_rate"
    )
    min_freshness_compliance_rate = _validate_rate(
        min_freshness_compliance_rate, field="min_freshness_compliance_rate"
    )
    min_sla_met_rate = _validate_rate(min_sla_met_rate, field="min_sla_met_rate")
    if min_recovery_success_rate is not None:
        min_recovery_success_rate = _validate_rate(
            min_recovery_success_rate, field="min_recovery_success_rate"
        )
        if min_recovery_applicable_count < 1:
            raise InvalidTransition(
                "min_recovery_applicable_count must be at least 1 when recovery rate is required"
            )
    elif min_recovery_applicable_count != 0:
        raise InvalidTransition(
            "min_recovery_applicable_count must be 0 when no recovery success rate is required"
        )

    try:
        current_profile_snapshot = capability_autonomy_profile_snapshot(
            session,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
    except AutonomyProfileIntegrityError as exc:
        raise InvalidTransition("current I.1 autonomy profile integrity failed") from exc
    if current_profile_snapshot is None:
        raise InvalidReference("current capability autonomy profile was not found")
    observed_profile_id = current_profile_snapshot.current_profile_id
    if expected_profile_id is not None and expected_profile_id != observed_profile_id:
        raise InvalidTransition("expected autonomy profile is stale")
    current_profile = tenant_record(
        session,
        CapabilityAutonomyProfile,
        observed_profile_id,
        context.tenant_key,
        label="current autonomy profile",
    )
    if current_profile.autonomy_level != from_level.value:
        raise InvalidTransition("promotion policy from level must match current I.1 autonomy")
    if current_profile.evidence_policy_version != evidence_policy_version:
        raise InvalidTransition("promotion policy evidence version must match current I.1 profile")
    if _autonomy_rank(target_level) > _autonomy_rank(current_profile.board_ceiling):
        raise AuthorityDenied("promotion policy target exceeds the Human Board ceiling")

    target_position = session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == position_key,
            OrganizationPosition.status == "active",
        )
    ).first()
    if target_position is None:
        raise InvalidReference("active organization position was not found")

    criteria = _criteria_payload(
        min_qualifying_execution_volume=min_qualifying_execution_volume,
        min_human_reviewed_count=min_human_reviewed_count,
        min_evidence_grounding_rate=min_evidence_grounding_rate,
        min_human_acceptance_rate=min_human_acceptance_rate,
        max_human_modification_rate=max_human_modification_rate,
        max_human_rejection_rate=max_human_rejection_rate,
        max_verifier_contradiction_rate=max_verifier_contradiction_rate,
        min_policy_compliance_rate=min_policy_compliance_rate,
        min_freshness_compliance_rate=min_freshness_compliance_rate,
        max_critical_error_count=max_critical_error_count,
        min_recovery_applicable_count=min_recovery_applicable_count,
        min_recovery_success_rate=min_recovery_success_rate,
        min_sla_met_rate=min_sla_met_rate,
        max_incident_count=max_incident_count,
    )
    record_fingerprint = _policy_record_fingerprint(
        tenant_key=context.tenant_key,
        profile_id=current_profile.id,
        profile_sequence=current_profile.profile_sequence,
        profile_record_fingerprint=current_profile.record_fingerprint,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        from_autonomy_level=from_level.value,
        target_autonomy_level=target_level.value,
        evidence_policy_version=evidence_policy_version,
        criteria=criteria,
        policy_reason=policy_reason,
        idempotency_key=idempotency_key,
    )
    replay = _idempotent_policy(
        session,
        tenant_key=context.tenant_key,
        idempotency_key=idempotency_key,
        record_fingerprint=record_fingerprint,
    )
    if replay is not None:
        return replay

    current_profile = _locked_current_profile(
        session,
        tenant_key=context.tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        profile_id=observed_profile_id,
    )
    if current_profile.autonomy_level != from_level.value:
        raise InvalidTransition("promotion policy from level must match current I.1 autonomy")
    if current_profile.evidence_policy_version != evidence_policy_version:
        raise InvalidTransition("promotion policy evidence version must match current I.1 profile")
    if _autonomy_rank(target_level) > _autonomy_rank(current_profile.board_ceiling):
        raise AuthorityDenied("promotion policy target exceeds the Human Board ceiling")

    current_statement = _profile_policy_statement(
        tenant_key=context.tenant_key,
        profile_id=current_profile.id,
    ).order_by(CapabilityAutonomyPromotionPolicy.policy_sequence.desc())
    if session.get_bind().dialect.name == "postgresql":
        current_statement = current_statement.with_for_update()
    current_policy = session.exec(current_statement).first()
    if current_policy is None:
        if expected_policy_sequence not in {None, 0}:
            raise InvalidTransition("expected promotion policy sequence is stale")
        next_sequence = 1
    else:
        if expected_policy_sequence is None:
            raise InvalidTransition("expected_policy_sequence is required for policy supersession")
        if expected_policy_sequence != current_policy.policy_sequence:
            raise InvalidTransition("expected promotion policy sequence is stale")
        next_sequence = current_policy.policy_sequence + 1

    policy_id = uuid4()
    occurred_at = now_utc()
    scope_digest = canonical_fingerprint(
        {
            "tenant_key": context.tenant_key,
            "profile_id": str(current_profile.id),
        }
    )[:24]
    decision_activity = stage_activity(
        session,
        context,
        activity_key=f"autonomy-promotion-policy:{policy_id}",
        stream_key=f"autonomy-promotion-policy:{scope_digest}",
        activity_class="decision",
        activity_type=AUTONOMY_PROMOTION_POLICY_ACTIVITY_TYPE,
        title="Autonomy promotion criteria established",
        summary=(
            f"Human Board established one-step {from_level.value}→{target_level.value} "
            "promotion eligibility criteria; no autonomy mutation occurred."
        ),
        source_object_type=AUTONOMY_PROMOTION_POLICY_SOURCE_TYPE,
        source_object_id=str(policy_id),
        source_object_version=str(next_sequence),
        occurred_at=occurred_at,
        supersedes_activity_id=(
            current_policy.decision_activity_id if current_policy is not None else None
        ),
        payload={
            "contract_version": AUTONOMY_PROMOTION_POLICY_CONTRACT_VERSION,
            "constitutional_activity_class": AUTONOMY_PROMOTION_CONSTITUTIONAL_ACTIVITY_CLASS,
            "governance_source": AUTONOMY_PROMOTION_POLICY_GOVERNANCE_SOURCE,
            "profile_id": str(current_profile.id),
            "profile_sequence": current_profile.profile_sequence,
            "profile_record_fingerprint": current_profile.record_fingerprint,
            "position_key": position_key,
            "capability_key": capability_key,
            "context_scope": context_scope,
            "policy_sequence": next_sequence,
            "from_autonomy_level": from_level.value,
            "target_autonomy_level": target_level.value,
            "evidence_policy_version": evidence_policy_version,
            "criteria": criteria,
            "policy_reason": policy_reason,
            "autonomy_mutated": False,
        },
    )
    policy = CapabilityAutonomyPromotionPolicy(
        id=policy_id,
        tenant_key=context.tenant_key,
        profile_id=current_profile.id,
        profile_sequence=current_profile.profile_sequence,
        profile_record_fingerprint=current_profile.record_fingerprint,
        position_id=target_position.id,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        policy_sequence=next_sequence,
        from_autonomy_level=from_level.value,
        target_autonomy_level=target_level.value,
        evidence_policy_version=evidence_policy_version,
        min_qualifying_execution_volume=min_qualifying_execution_volume,
        min_human_reviewed_count=min_human_reviewed_count,
        min_evidence_grounding_rate=min_evidence_grounding_rate,
        min_human_acceptance_rate=min_human_acceptance_rate,
        max_human_modification_rate=max_human_modification_rate,
        max_human_rejection_rate=max_human_rejection_rate,
        max_verifier_contradiction_rate=max_verifier_contradiction_rate,
        min_policy_compliance_rate=min_policy_compliance_rate,
        min_freshness_compliance_rate=min_freshness_compliance_rate,
        max_critical_error_count=max_critical_error_count,
        min_recovery_applicable_count=min_recovery_applicable_count,
        min_recovery_success_rate=min_recovery_success_rate,
        min_sla_met_rate=min_sla_met_rate,
        max_incident_count=max_incident_count,
        policy_reason=policy_reason,
        supersedes_policy_id=current_policy.id if current_policy is not None else None,
        decision_activity_id=decision_activity.id,
        decision_activity_fingerprint=decision_activity.record_fingerprint,
        idempotency_key=idempotency_key,
        record_fingerprint=record_fingerprint,
        effective_from=occurred_at,
        created_at=occurred_at,
        created_by=context.actor_id,
    )
    session.add(policy)
    try:
        _locked_current_profile(
            session,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
            profile_id=current_profile.id,
        )
        commit_mutations(
            session,
            mutations=(
                AuditMutation(
                    action="organization.autonomy_promotion_policy.establish",
                    entity_type="capability_autonomy_promotion_policy",
                    entity_id=policy.id,
                    after_state=policy,
                    reason="Recorded Board-authored I.3 promotion criteria; no autonomy mutation.",
                ),
            ),
            context=context,
            refresh=(policy,),
        )
        return policy
    except IntegrityError as exc:
        session.rollback()
        replay = _idempotent_policy(
            session,
            tenant_key=context.tenant_key,
            idempotency_key=idempotency_key,
            record_fingerprint=record_fingerprint,
        )
        if replay is not None:
            return replay
        raise DependencyConflict("autonomy promotion policy changed concurrently") from exc
    except Exception:
        session.rollback()
        raise


def _policy_semantic_fingerprint(policy: CapabilityAutonomyPromotionPolicy) -> str:
    return _policy_record_fingerprint(
        tenant_key=policy.tenant_key,
        profile_id=policy.profile_id,
        profile_sequence=policy.profile_sequence,
        profile_record_fingerprint=policy.profile_record_fingerprint,
        position_key=policy.position_key,
        capability_key=policy.capability_key,
        context_scope=policy.context_scope,
        from_autonomy_level=policy.from_autonomy_level,
        target_autonomy_level=policy.target_autonomy_level,
        evidence_policy_version=policy.evidence_policy_version,
        criteria=_criteria_payload(
            min_qualifying_execution_volume=policy.min_qualifying_execution_volume,
            min_human_reviewed_count=policy.min_human_reviewed_count,
            min_evidence_grounding_rate=policy.min_evidence_grounding_rate,
            min_human_acceptance_rate=policy.min_human_acceptance_rate,
            max_human_modification_rate=policy.max_human_modification_rate,
            max_human_rejection_rate=policy.max_human_rejection_rate,
            max_verifier_contradiction_rate=policy.max_verifier_contradiction_rate,
            min_policy_compliance_rate=policy.min_policy_compliance_rate,
            min_freshness_compliance_rate=policy.min_freshness_compliance_rate,
            max_critical_error_count=policy.max_critical_error_count,
            min_recovery_applicable_count=policy.min_recovery_applicable_count,
            min_recovery_success_rate=policy.min_recovery_success_rate,
            min_sla_met_rate=policy.min_sla_met_rate,
            max_incident_count=policy.max_incident_count,
        ),
        policy_reason=policy.policy_reason,
        idempotency_key=policy.idempotency_key,
    )


def _activity_payload(activity: OrganizationActivity) -> dict[str, object]:
    try:
        payload = json.loads(activity.payload_json or "{}")
    except (TypeError, ValueError) as exc:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy Activity payload is invalid") from exc
    if not isinstance(payload, dict):
        raise AutonomyPromotionPolicyIntegrityError("promotion policy Activity payload is invalid")
    return payload


def _validated_policy_revision(
    session: Session,
    *,
    profile: CapabilityAutonomyProfile,
    policy: CapabilityAutonomyPromotionPolicy,
    expected_sequence: int,
    previous_policy: CapabilityAutonomyPromotionPolicy | None,
) -> AutonomyPromotionPolicyRevisionSnapshot:
    if (
        policy.profile_id != profile.id
        or policy.profile_sequence != profile.profile_sequence
        or policy.profile_record_fingerprint != profile.record_fingerprint
        or policy.position_key != profile.position_key
        or policy.capability_key != profile.capability_key
        or policy.context_scope != profile.context_scope
        or policy.from_autonomy_level != profile.autonomy_level
        or policy.evidence_policy_version != profile.evidence_policy_version
    ):
        raise AutonomyPromotionPolicyIntegrityError("promotion policy exact I.1 profile binding drifted")
    if policy.policy_sequence != expected_sequence:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy sequence is not contiguous")
    if expected_sequence == 1:
        if policy.supersedes_policy_id is not None:
            raise AutonomyPromotionPolicyIntegrityError("first promotion policy unexpectedly supersedes another")
    elif previous_policy is None or policy.supersedes_policy_id != previous_policy.id:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy supersession chain drifted")
    try:
        from_level = AutonomyLevel(policy.from_autonomy_level)
        target_level = AutonomyLevel(policy.target_autonomy_level)
    except ValueError as exc:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy autonomy level is invalid") from exc
    if _autonomy_rank(target_level) != _autonomy_rank(from_level) + 1:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy is not a one-step promotion")
    if policy.min_qualifying_execution_volume < 1 or policy.min_human_reviewed_count < 1:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy sample threshold is invalid")
    if policy.max_critical_error_count < 0 or policy.max_incident_count < 0:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy count threshold is invalid")
    if policy.min_recovery_applicable_count < 0:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy recovery threshold is invalid")
    for field in (
        "min_evidence_grounding_rate",
        "min_human_acceptance_rate",
        "max_human_modification_rate",
        "max_human_rejection_rate",
        "max_verifier_contradiction_rate",
        "min_policy_compliance_rate",
        "min_freshness_compliance_rate",
        "min_sla_met_rate",
    ):
        _validated_persisted_rate(getattr(policy, field), field=field)
    if policy.min_recovery_success_rate is not None:
        _validated_persisted_rate(
            policy.min_recovery_success_rate,
            field="min_recovery_success_rate",
        )
        if policy.min_recovery_applicable_count < 1:
            raise AutonomyPromotionPolicyIntegrityError("promotion policy recovery sample is invalid")
    elif policy.min_recovery_applicable_count != 0:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy recovery sample is inconsistent")

    position = session.get(OrganizationPosition, policy.position_id)
    if position is None or position.position_key != profile.position_key:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy position identity drifted")
    try:
        activity = tenant_record(
            session,
            OrganizationActivity,
            policy.decision_activity_id,
            policy.tenant_key,
            label="promotion policy decision activity",
        )
    except OrganizationCommandError as exc:
        raise AutonomyPromotionPolicyIntegrityError(
            "promotion policy decision Activity is unavailable"
        ) from exc
    if activity.record_fingerprint != policy.decision_activity_fingerprint:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy Activity fingerprint drifted")
    physical_class = getattr(activity.activity_class, "value", activity.activity_class)
    if (
        physical_class != "decision"
        or activity.activity_type != AUTONOMY_PROMOTION_POLICY_ACTIVITY_TYPE
        or activity.source_object_type != AUTONOMY_PROMOTION_POLICY_SOURCE_TYPE
        or activity.source_object_id != str(policy.id)
        or activity.source_object_version != str(policy.policy_sequence)
        or activity.actor_type is not OrganizationActorType.human
        or activity.position_key != "board"
    ):
        raise AutonomyPromotionPolicyIntegrityError("promotion policy Activity identity drifted")
    payload = _activity_payload(activity)
    if (
        payload.get("contract_version") != AUTONOMY_PROMOTION_POLICY_CONTRACT_VERSION
        or payload.get("constitutional_activity_class")
        != AUTONOMY_PROMOTION_CONSTITUTIONAL_ACTIVITY_CLASS
        or payload.get("governance_source") != AUTONOMY_PROMOTION_POLICY_GOVERNANCE_SOURCE
        or payload.get("profile_id") != str(profile.id)
        or payload.get("profile_sequence") != profile.profile_sequence
        or payload.get("profile_record_fingerprint") != profile.record_fingerprint
        or payload.get("policy_sequence") != policy.policy_sequence
        or payload.get("autonomy_mutated") is not False
    ):
        raise AutonomyPromotionPolicyIntegrityError("promotion policy constitutional Activity payload drifted")
    expected_supersedes_activity = previous_policy.decision_activity_id if previous_policy else None
    if activity.supersedes_activity_id != expected_supersedes_activity:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy Activity supersession drifted")
    if _policy_semantic_fingerprint(policy) != policy.record_fingerprint:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy record fingerprint drifted")

    return AutonomyPromotionPolicyRevisionSnapshot(
        policy_id=policy.id,
        profile_id=policy.profile_id,
        profile_sequence=policy.profile_sequence,
        profile_record_fingerprint=policy.profile_record_fingerprint,
        policy_sequence=policy.policy_sequence,
        lifecycle_status="HISTORICAL",
        from_autonomy_level=policy.from_autonomy_level,
        target_autonomy_level=policy.target_autonomy_level,
        evidence_policy_version=policy.evidence_policy_version,
        min_qualifying_execution_volume=policy.min_qualifying_execution_volume,
        min_human_reviewed_count=policy.min_human_reviewed_count,
        min_evidence_grounding_rate=policy.min_evidence_grounding_rate,
        min_human_acceptance_rate=policy.min_human_acceptance_rate,
        max_human_modification_rate=policy.max_human_modification_rate,
        max_human_rejection_rate=policy.max_human_rejection_rate,
        max_verifier_contradiction_rate=policy.max_verifier_contradiction_rate,
        min_policy_compliance_rate=policy.min_policy_compliance_rate,
        min_freshness_compliance_rate=policy.min_freshness_compliance_rate,
        max_critical_error_count=policy.max_critical_error_count,
        min_recovery_applicable_count=policy.min_recovery_applicable_count,
        min_recovery_success_rate=policy.min_recovery_success_rate,
        min_sla_met_rate=policy.min_sla_met_rate,
        max_incident_count=policy.max_incident_count,
        policy_reason=policy.policy_reason,
        supersedes_policy_id=policy.supersedes_policy_id,
        decision_activity_id=policy.decision_activity_id,
        decision_activity_fingerprint=policy.decision_activity_fingerprint,
        record_fingerprint=policy.record_fingerprint,
        effective_from=policy.effective_from,
        created_at=policy.created_at,
        created_by=policy.created_by,
    )


def capability_autonomy_promotion_policy_snapshot(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
    from_autonomy_level: str,
    evidence_policy_version: str,
    profile_id: UUID | None = None,
) -> CapabilityAutonomyPromotionPolicySnapshot | None:
    """Return validated Board policy lineage for one exact I.1 profile revision."""

    try:
        profile_snapshot = capability_autonomy_profile_snapshot(
            session,
            tenant_key=tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
    except AutonomyProfileIntegrityError as exc:
        raise AutonomyPromotionPolicyIntegrityError("I.1 autonomy profile integrity failed") from exc
    if profile_snapshot is None:
        return None
    resolved_profile_id = profile_id or profile_snapshot.current_profile_id
    try:
        profile = tenant_record(
            session,
            CapabilityAutonomyProfile,
            resolved_profile_id,
            tenant_key,
            label="autonomy promotion policy profile",
        )
    except OrganizationCommandError as exc:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy I.1 profile is unavailable") from exc
    if (
        profile.position_key != position_key
        or profile.capability_key != capability_key
        or profile.context_scope != context_scope
    ):
        raise AutonomyPromotionPolicyIntegrityError("promotion policy profile scope drifted")
    try:
        from_level = AutonomyLevel(from_autonomy_level)
    except ValueError as exc:
        raise AutonomyPromotionPolicyIntegrityError("current autonomy level is invalid") from exc
    if profile.autonomy_level != from_level.value:
        return None
    if profile.evidence_policy_version != evidence_policy_version:
        return None
    if from_level is AutonomyLevel.A5:
        return None
    target_level = AutonomyLevel(f"A{_autonomy_rank(from_level) + 1}")

    rows = tuple(
        session.exec(
            _profile_policy_statement(
                tenant_key=tenant_key,
                profile_id=profile.id,
            ).order_by(CapabilityAutonomyPromotionPolicy.policy_sequence.asc())
        ).all()
    )
    if not rows:
        return None
    revisions: list[AutonomyPromotionPolicyRevisionSnapshot] = []
    previous: CapabilityAutonomyPromotionPolicy | None = None
    for index, row in enumerate(rows, start=1):
        if row.target_autonomy_level != target_level.value:
            raise AutonomyPromotionPolicyIntegrityError("promotion policy target drifted")
        revisions.append(
            _validated_policy_revision(
                session,
                profile=profile,
                policy=row,
                expected_sequence=index,
                previous_policy=previous,
            )
        )
        previous = row
    current = rows[-1]
    revisions[-1] = replace(revisions[-1], lifecycle_status="CURRENT")
    return CapabilityAutonomyPromotionPolicySnapshot(
        profile_id=profile.id,
        profile_sequence=profile.profile_sequence,
        profile_record_fingerprint=profile.record_fingerprint,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        current_policy_id=current.id,
        current_policy_sequence=current.policy_sequence,
        from_autonomy_level=current.from_autonomy_level,
        target_autonomy_level=current.target_autonomy_level,
        evidence_policy_version=current.evidence_policy_version,
        revisions=tuple(revisions),
    )


def _criterion(
    key: str,
    comparison: str,
    required: int | float,
    observed: int | float | None,
    *,
    sample: bool = False,
) -> AutonomyPromotionCriterionSnapshot:
    if observed is None:
        return AutonomyPromotionCriterionSnapshot(
            criterion_key=key,
            comparison=comparison,
            required_value=required,
            observed_value=None,
            sample_requirement=sample,
            evaluable=False,
            passed=None,
        )
    if comparison == ">=":
        passed = observed >= required
    elif comparison == "<=":
        passed = observed <= required
    else:
        raise RuntimeError(f"unsupported promotion criterion comparison: {comparison}")
    return AutonomyPromotionCriterionSnapshot(
        criterion_key=key,
        comparison=comparison,
        required_value=required,
        observed_value=observed,
        sample_requirement=sample,
        evaluable=True,
        passed=bool(passed),
    )


def capability_autonomy_promotion_eligibility_snapshot(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
) -> AutonomyPromotionEligibilitySnapshot | None:
    """Evaluate current I.2 evidence against current exact-profile Board criteria."""

    evidence_profile = capability_autonomy_evidence_profile_snapshot(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
    )
    if evidence_profile is None:
        return None
    if evidence_profile.current_autonomy_level == AutonomyLevel.A5.value:
        return None
    current_profile = tenant_record(
        session,
        CapabilityAutonomyProfile,
        evidence_profile.profile_id,
        tenant_key,
        label="current autonomy profile",
    )
    policy_snapshot = capability_autonomy_promotion_policy_snapshot(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        from_autonomy_level=evidence_profile.current_autonomy_level,
        evidence_policy_version=evidence_profile.evidence_policy_version,
        profile_id=current_profile.id,
    )
    if policy_snapshot is None:
        return None
    policy = tenant_record(
        session,
        CapabilityAutonomyPromotionPolicy,
        policy_snapshot.current_policy_id,
        tenant_key,
        label="current autonomy promotion policy",
    )
    if (
        policy.profile_id != current_profile.id
        or policy.profile_sequence != current_profile.profile_sequence
        or policy.profile_record_fingerprint != current_profile.record_fingerprint
    ):
        raise AutonomyPromotionPolicyIntegrityError("promotion policy no longer matches current I.1 profile")
    if current_profile.autonomy_level != policy.from_autonomy_level:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy no longer matches current autonomy")
    if current_profile.evidence_policy_version != policy.evidence_policy_version:
        raise AutonomyPromotionPolicyIntegrityError("promotion policy evidence version drifted")

    metrics = evidence_profile.metrics
    reviewed_count = (
        metrics.human_accepted_count
        + metrics.human_modified_count
        + metrics.human_rejected_count
    )
    criteria: list[AutonomyPromotionCriterionSnapshot] = [
        _criterion(
            "qualifying_execution_volume",
            ">=",
            policy.min_qualifying_execution_volume,
            metrics.qualifying_execution_volume,
            sample=True,
        ),
        _criterion(
            "human_reviewed_count",
            ">=",
            policy.min_human_reviewed_count,
            reviewed_count,
            sample=True,
        ),
        _criterion(
            "evidence_grounding_rate",
            ">=",
            policy.min_evidence_grounding_rate,
            metrics.evidence_grounding_rate,
        ),
        _criterion(
            "human_acceptance_rate",
            ">=",
            policy.min_human_acceptance_rate,
            metrics.human_acceptance_rate,
        ),
        _criterion(
            "human_modification_rate",
            "<=",
            policy.max_human_modification_rate,
            metrics.human_modification_rate,
        ),
        _criterion(
            "human_rejection_rate",
            "<=",
            policy.max_human_rejection_rate,
            metrics.human_rejection_rate,
        ),
        _criterion(
            "verifier_contradiction_rate",
            "<=",
            policy.max_verifier_contradiction_rate,
            metrics.verifier_contradiction_rate,
        ),
        _criterion(
            "policy_compliance_rate",
            ">=",
            policy.min_policy_compliance_rate,
            metrics.policy_compliance_rate,
        ),
        _criterion(
            "freshness_compliance_rate",
            ">=",
            policy.min_freshness_compliance_rate,
            metrics.freshness_compliance_rate,
        ),
        _criterion(
            "critical_error_count",
            "<=",
            policy.max_critical_error_count,
            metrics.critical_error_count,
        ),
        _criterion(
            "sla_met_rate",
            ">=",
            policy.min_sla_met_rate,
            metrics.sla_met_rate,
        ),
        _criterion(
            "incident_count",
            "<=",
            policy.max_incident_count,
            metrics.incident_count,
        ),
        _criterion(
            "target_within_board_ceiling",
            "<=",
            _autonomy_rank(current_profile.board_ceiling),
            _autonomy_rank(policy.target_autonomy_level),
        ),
    ]
    if policy.min_recovery_success_rate is not None:
        criteria.append(
            _criterion(
                "recovery_applicable_count",
                ">=",
                policy.min_recovery_applicable_count,
                metrics.recovery_applicable_count,
                sample=True,
            )
        )
        criteria.append(
            _criterion(
                "recovery_success_rate",
                ">=",
                policy.min_recovery_success_rate,
                metrics.recovery_success_rate,
            )
        )

    quality_failed = any(
        item.passed is False and not item.sample_requirement for item in criteria
    )
    sample_failed = any(
        item.passed is False and item.sample_requirement for item in criteria
    )
    quality_unevaluable = any(
        not item.sample_requirement and not item.evaluable for item in criteria
    )
    if quality_failed:
        state = PROMOTION_HOLD
    elif sample_failed or quality_unevaluable:
        state = PROMOTION_INSUFFICIENT_EVIDENCE
    else:
        state = PROMOTION_ELIGIBLE

    return AutonomyPromotionEligibilitySnapshot(
        profile_id=current_profile.id,
        profile_sequence=current_profile.profile_sequence,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        current_autonomy_level=current_profile.autonomy_level,
        board_ceiling=current_profile.board_ceiling,
        evidence_policy_version=current_profile.evidence_policy_version,
        policy_id=policy.id,
        policy_sequence=policy.policy_sequence,
        target_autonomy_level=policy.target_autonomy_level,
        eligibility_state=state,
        criteria=tuple(criteria),
        evidence_profile=evidence_profile,
    )
