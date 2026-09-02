from __future__ import annotations

import json
from dataclasses import replace
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.autonomy_evidence_evaluation_policy import CapabilityAutonomyEvidenceEvaluationPolicy
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActivity, OrganizationActorType, OrganizationPosition, now_utc
from app.services.organization_activity import stage_activity
from app.services.organization_autonomy_evidence_evaluation_contract import (
    AUTONOMY_EVIDENCE_EVALUATION_CONSTITUTIONAL_ACTIVITY_CLASS,
    AUTONOMY_EVIDENCE_EVALUATION_CONTRACT_VERSION,
    AUTONOMY_EVIDENCE_EVALUATION_GOVERNANCE_SOURCE,
    AUTONOMY_EVIDENCE_EVALUATION_POLICY_ACTIVITY_TYPE,
    AUTONOMY_EVIDENCE_EVALUATION_POLICY_SOURCE_TYPE,
    I4_MAX_CANDIDATE_OBSERVATIONS,
    I4_QUALIFICATION_CONTRACT,
    I4_SUPPORTED_CAPABILITY,
    AutonomyEvidenceEvaluationIntegrityError,
    AutonomyEvidenceEvaluationPolicyRevisionSnapshot,
    AutonomyEvidenceEvaluationUnsupported,
    CapabilityAutonomyEvidenceEvaluationPolicySnapshot,
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


def require_supported_i4_adapter(*, capability_key: str, qualification_contract: str) -> None:
    if capability_key != I4_SUPPORTED_CAPABILITY:
        raise AutonomyEvidenceEvaluationUnsupported(
            "I.4 v1 supports only the eligibility.proposal qualification adapter"
        )
    if qualification_contract != I4_QUALIFICATION_CONTRACT:
        raise AutonomyEvidenceEvaluationUnsupported("I.4 qualification contract is unsupported")


def _required(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise InvalidTransition(f"{field} is required")
    return value


def _fingerprint(
    *,
    tenant_key: str,
    profile: CapabilityAutonomyProfile,
    qualification_contract: str,
    max_observation_age_seconds: int,
    max_source_age_seconds: int,
    max_candidate_observations: int,
    policy_reason: str,
    idempotency_key: str,
) -> str:
    return canonical_fingerprint(
        {
            "contract_version": AUTONOMY_EVIDENCE_EVALUATION_CONTRACT_VERSION,
            "tenant_key": tenant_key,
            "profile_id": str(profile.id),
            "profile_sequence": profile.profile_sequence,
            "profile_record_fingerprint": profile.record_fingerprint,
            "position_key": profile.position_key,
            "capability_key": profile.capability_key,
            "context_scope": profile.context_scope,
            "qualification_contract": qualification_contract,
            "max_observation_age_seconds": max_observation_age_seconds,
            "max_source_age_seconds": max_source_age_seconds,
            "max_candidate_observations": max_candidate_observations,
            "policy_reason": policy_reason,
            "governance_source": AUTONOMY_EVIDENCE_EVALUATION_GOVERNANCE_SOURCE,
            "idempotency_key": idempotency_key,
        }
    )


def _replay(
    session: Session, tenant_key: str, idempotency_key: str, fingerprint: str
) -> CapabilityAutonomyEvidenceEvaluationPolicy | None:
    row = session.exec(
        select(CapabilityAutonomyEvidenceEvaluationPolicy).where(
            CapabilityAutonomyEvidenceEvaluationPolicy.tenant_key == tenant_key,
            CapabilityAutonomyEvidenceEvaluationPolicy.idempotency_key == idempotency_key,
        )
    ).first()
    if row is None:
        return None
    if row.record_fingerprint != fingerprint:
        raise IdempotencyConflict(
            "autonomy evidence evaluation policy idempotency key was already used with different semantics"
        )
    return row


def _current_profile(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
) -> CapabilityAutonomyProfile:
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
    if snapshot is None:
        raise InvalidReference("current capability autonomy profile was not found")
    return tenant_record(
        session,
        CapabilityAutonomyProfile,
        snapshot.current_profile_id,
        tenant_key,
        label="current autonomy profile",
    )


def _lock_current_profile(
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
    row = session.exec(statement).first()
    if row is None or (
        row.position_key != position_key
        or row.capability_key != capability_key
        or row.context_scope != context_scope
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
    return row


def establish_capability_autonomy_evidence_evaluation_policy(
    session: Session,
    context: OrganizationCommandContext,
    *,
    position_key: str,
    capability_key: str,
    context_scope: str,
    qualification_contract: str,
    max_observation_age_seconds: int,
    max_source_age_seconds: int,
    max_candidate_observations: int,
    policy_reason: str,
    idempotency_key: str,
    expected_profile_id: UUID | None = None,
    expected_policy_sequence: int | None = None,
) -> CapabilityAutonomyEvidenceEvaluationPolicy:
    """Append Board-authored I.4 evaluation policy without changing autonomy truth."""

    require_human(context, admin=True)
    if context.position_key != "board":
        raise AuthorityDenied(
            "only the persistent Board position may establish autonomy evidence evaluation policy"
        )
    position_key = _required(position_key, "position_key")
    capability_key = _required(capability_key, "capability_key")
    context_scope = _required(context_scope, "context_scope")
    qualification_contract = _required(qualification_contract, "qualification_contract")
    policy_reason = _required(policy_reason, "policy_reason")
    idempotency_key = _required(idempotency_key, "idempotency_key")
    require_supported_i4_adapter(
        capability_key=capability_key, qualification_contract=qualification_contract
    )
    if max_observation_age_seconds < 1 or max_source_age_seconds < 1:
        raise InvalidTransition("evidence age bounds must be at least 1 second")
    if not 1 <= max_candidate_observations <= I4_MAX_CANDIDATE_OBSERVATIONS:
        raise InvalidTransition(
            f"max_candidate_observations must be between 1 and {I4_MAX_CANDIDATE_OBSERVATIONS}"
        )

    observed = _current_profile(
        session,
        tenant_key=context.tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
    )
    if expected_profile_id is not None and expected_profile_id != observed.id:
        raise InvalidTransition("expected autonomy profile is stale")
    position = session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == position_key,
            OrganizationPosition.status == "active",
        )
    ).first()
    if position is None:
        raise InvalidReference("active organization position was not found")

    fingerprint = _fingerprint(
        tenant_key=context.tenant_key,
        profile=observed,
        qualification_contract=qualification_contract,
        max_observation_age_seconds=max_observation_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        max_candidate_observations=max_candidate_observations,
        policy_reason=policy_reason,
        idempotency_key=idempotency_key,
    )
    replay = _replay(session, context.tenant_key, idempotency_key, fingerprint)
    if replay is not None:
        return replay

    profile = _lock_current_profile(
        session,
        tenant_key=context.tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        profile_id=observed.id,
    )
    statement = (
        select(CapabilityAutonomyEvidenceEvaluationPolicy)
        .where(
            CapabilityAutonomyEvidenceEvaluationPolicy.tenant_key == context.tenant_key,
            CapabilityAutonomyEvidenceEvaluationPolicy.profile_id == profile.id,
        )
        .order_by(CapabilityAutonomyEvidenceEvaluationPolicy.policy_sequence.desc())
    )
    if session.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    current = session.exec(statement).first()
    if current is None:
        if expected_policy_sequence not in {None, 0}:
            raise InvalidTransition("expected evidence evaluation policy sequence is stale")
        sequence = 1
    else:
        if expected_policy_sequence is None:
            raise InvalidTransition(
                "expected_policy_sequence is required for evaluation-policy supersession"
            )
        if expected_policy_sequence != current.policy_sequence:
            raise InvalidTransition("expected evidence evaluation policy sequence is stale")
        sequence = current.policy_sequence + 1

    policy_id = uuid4()
    occurred_at = now_utc()
    activity = stage_activity(
        session,
        context,
        activity_key=f"autonomy-evidence-evaluation-policy:{policy_id}",
        stream_key=(
            "autonomy-evidence-evaluation-policy:"
            + canonical_fingerprint(
                {"tenant_key": context.tenant_key, "profile_id": str(profile.id)}
            )[:24]
        ),
        activity_class="decision",
        activity_type=AUTONOMY_EVIDENCE_EVALUATION_POLICY_ACTIVITY_TYPE,
        title="Qualified autonomy evidence evaluation policy established",
        summary=(
            "Human Board established bounded qualification/age policy for promotion-grade "
            "evidence evaluation; no autonomy mutation occurred."
        ),
        source_object_type=AUTONOMY_EVIDENCE_EVALUATION_POLICY_SOURCE_TYPE,
        source_object_id=str(policy_id),
        source_object_version=str(sequence),
        occurred_at=occurred_at,
        supersedes_activity_id=current.decision_activity_id if current else None,
        payload={
            "contract_version": AUTONOMY_EVIDENCE_EVALUATION_CONTRACT_VERSION,
            "constitutional_activity_class": AUTONOMY_EVIDENCE_EVALUATION_CONSTITUTIONAL_ACTIVITY_CLASS,
            "governance_source": AUTONOMY_EVIDENCE_EVALUATION_GOVERNANCE_SOURCE,
            "profile_id": str(profile.id),
            "profile_sequence": profile.profile_sequence,
            "profile_record_fingerprint": profile.record_fingerprint,
            "position_key": position_key,
            "capability_key": capability_key,
            "context_scope": context_scope,
            "policy_sequence": sequence,
            "qualification_contract": qualification_contract,
            "max_observation_age_seconds": max_observation_age_seconds,
            "max_source_age_seconds": max_source_age_seconds,
            "max_candidate_observations": max_candidate_observations,
            "policy_reason": policy_reason,
            "autonomy_mutated": False,
        },
    )
    row = CapabilityAutonomyEvidenceEvaluationPolicy(
        id=policy_id,
        tenant_key=context.tenant_key,
        profile_id=profile.id,
        profile_sequence=profile.profile_sequence,
        profile_record_fingerprint=profile.record_fingerprint,
        position_id=position.id,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        policy_sequence=sequence,
        qualification_contract=qualification_contract,
        max_observation_age_seconds=max_observation_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        max_candidate_observations=max_candidate_observations,
        policy_reason=policy_reason,
        supersedes_policy_id=current.id if current else None,
        decision_activity_id=activity.id,
        decision_activity_fingerprint=activity.record_fingerprint,
        idempotency_key=idempotency_key,
        record_fingerprint=fingerprint,
        effective_from=occurred_at,
        created_at=occurred_at,
        created_by=context.actor_id,
    )
    session.add(row)
    try:
        _lock_current_profile(
            session,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
            profile_id=profile.id,
        )
        commit_mutations(
            session,
            mutations=(
                AuditMutation(
                    action="organization.autonomy_evidence_evaluation_policy.establish",
                    entity_type="capability_autonomy_evidence_evaluation_policy",
                    entity_id=row.id,
                    after_state=row,
                    reason="Recorded Board-authored I.4 evaluation policy; no autonomy mutation.",
                ),
            ),
            context=context,
            refresh=(row,),
        )
        return row
    except IntegrityError as exc:
        session.rollback()
        replay = _replay(session, context.tenant_key, idempotency_key, fingerprint)
        if replay is not None:
            return replay
        raise DependencyConflict("autonomy evidence evaluation policy changed concurrently") from exc
    except Exception:
        session.rollback()
        raise


def _payload(activity: OrganizationActivity) -> dict[str, object]:
    try:
        payload = json.loads(activity.payload_json or "{}")
    except (TypeError, ValueError) as exc:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy Activity payload is invalid"
        ) from exc
    if not isinstance(payload, dict):
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy Activity payload is invalid"
        )
    return payload


def _validated_revision(
    session: Session,
    *,
    profile: CapabilityAutonomyProfile,
    row: CapabilityAutonomyEvidenceEvaluationPolicy,
    sequence: int,
    previous: CapabilityAutonomyEvidenceEvaluationPolicy | None,
) -> AutonomyEvidenceEvaluationPolicyRevisionSnapshot:
    if (
        row.profile_id != profile.id
        or row.profile_sequence != profile.profile_sequence
        or row.profile_record_fingerprint != profile.record_fingerprint
        or row.position_key != profile.position_key
        or row.capability_key != profile.capability_key
        or row.context_scope != profile.context_scope
        or row.policy_sequence != sequence
    ):
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy exact I.1 profile binding drifted"
        )
    expected_previous = previous.id if previous else None
    if row.supersedes_policy_id != expected_previous:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy supersession chain drifted"
        )
    require_supported_i4_adapter(
        capability_key=row.capability_key,
        qualification_contract=row.qualification_contract,
    )
    if (
        row.max_observation_age_seconds < 1
        or row.max_source_age_seconds < 1
        or not 1 <= row.max_candidate_observations <= I4_MAX_CANDIDATE_OBSERVATIONS
        or not row.policy_reason.strip()
    ):
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy bounds or reason are invalid"
        )
    position = session.get(OrganizationPosition, row.position_id)
    if position is None or position.position_key != profile.position_key:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy position identity drifted"
        )
    try:
        activity = tenant_record(
            session,
            OrganizationActivity,
            row.decision_activity_id,
            row.tenant_key,
            label="evidence evaluation policy decision activity",
        )
    except OrganizationCommandError as exc:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy decision Activity is unavailable"
        ) from exc
    expected_activity_previous = previous.decision_activity_id if previous else None
    if (
        activity.record_fingerprint != row.decision_activity_fingerprint
        or getattr(activity.activity_class, "value", activity.activity_class) != "decision"
        or activity.activity_type != AUTONOMY_EVIDENCE_EVALUATION_POLICY_ACTIVITY_TYPE
        or activity.source_object_type != AUTONOMY_EVIDENCE_EVALUATION_POLICY_SOURCE_TYPE
        or activity.source_object_id != str(row.id)
        or activity.source_object_version != str(sequence)
        or activity.actor_type is not OrganizationActorType.human
        or activity.position_key != "board"
        or activity.supersedes_activity_id != expected_activity_previous
    ):
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy Activity identity drifted"
        )
    payload = _payload(activity)
    expected = {
        "contract_version": AUTONOMY_EVIDENCE_EVALUATION_CONTRACT_VERSION,
        "constitutional_activity_class": AUTONOMY_EVIDENCE_EVALUATION_CONSTITUTIONAL_ACTIVITY_CLASS,
        "governance_source": AUTONOMY_EVIDENCE_EVALUATION_GOVERNANCE_SOURCE,
        "profile_id": str(profile.id),
        "profile_sequence": profile.profile_sequence,
        "profile_record_fingerprint": profile.record_fingerprint,
        "position_key": profile.position_key,
        "capability_key": profile.capability_key,
        "context_scope": profile.context_scope,
        "policy_sequence": sequence,
        "qualification_contract": row.qualification_contract,
        "max_observation_age_seconds": row.max_observation_age_seconds,
        "max_source_age_seconds": row.max_source_age_seconds,
        "max_candidate_observations": row.max_candidate_observations,
        "policy_reason": row.policy_reason,
        "autonomy_mutated": False,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy constitutional Activity payload drifted"
        )
    if _fingerprint(
        tenant_key=row.tenant_key,
        profile=profile,
        qualification_contract=row.qualification_contract,
        max_observation_age_seconds=row.max_observation_age_seconds,
        max_source_age_seconds=row.max_source_age_seconds,
        max_candidate_observations=row.max_candidate_observations,
        policy_reason=row.policy_reason,
        idempotency_key=row.idempotency_key,
    ) != row.record_fingerprint:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy record fingerprint drifted"
        )
    return AutonomyEvidenceEvaluationPolicyRevisionSnapshot(
        policy_id=row.id,
        profile_id=row.profile_id,
        profile_sequence=row.profile_sequence,
        profile_record_fingerprint=row.profile_record_fingerprint,
        policy_sequence=row.policy_sequence,
        lifecycle_status="HISTORICAL",
        qualification_contract=row.qualification_contract,
        max_observation_age_seconds=row.max_observation_age_seconds,
        max_source_age_seconds=row.max_source_age_seconds,
        max_candidate_observations=row.max_candidate_observations,
        policy_reason=row.policy_reason,
        supersedes_policy_id=row.supersedes_policy_id,
        decision_activity_id=row.decision_activity_id,
        decision_activity_fingerprint=row.decision_activity_fingerprint,
        record_fingerprint=row.record_fingerprint,
        effective_from=row.effective_from,
        created_at=row.created_at,
        created_by=row.created_by,
    )


def capability_autonomy_evidence_evaluation_policy_snapshot(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
    profile_id: UUID | None = None,
) -> CapabilityAutonomyEvidenceEvaluationPolicySnapshot | None:
    require_supported_i4_adapter(
        capability_key=capability_key,
        qualification_contract=I4_QUALIFICATION_CONTRACT,
    )
    try:
        current = capability_autonomy_profile_snapshot(
            session,
            tenant_key=tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
    except AutonomyProfileIntegrityError as exc:
        raise AutonomyEvidenceEvaluationIntegrityError("I.1 autonomy profile integrity failed") from exc
    if current is None:
        return None
    resolved_id = profile_id or current.current_profile_id
    try:
        profile = tenant_record(
            session,
            CapabilityAutonomyProfile,
            resolved_id,
            tenant_key,
            label="autonomy evidence evaluation profile",
        )
    except OrganizationCommandError as exc:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation I.1 profile is unavailable"
        ) from exc
    if (
        profile.position_key != position_key
        or profile.capability_key != capability_key
        or profile.context_scope != context_scope
    ):
        raise AutonomyEvidenceEvaluationIntegrityError(
            "evidence evaluation policy profile scope drifted"
        )
    rows = tuple(
        session.exec(
            select(CapabilityAutonomyEvidenceEvaluationPolicy)
            .where(
                CapabilityAutonomyEvidenceEvaluationPolicy.tenant_key == tenant_key,
                CapabilityAutonomyEvidenceEvaluationPolicy.profile_id == profile.id,
            )
            .order_by(CapabilityAutonomyEvidenceEvaluationPolicy.policy_sequence.asc())
        ).all()
    )
    if not rows:
        return None
    revisions = []
    previous = None
    for sequence, row in enumerate(rows, start=1):
        revisions.append(
            _validated_revision(
                session,
                profile=profile,
                row=row,
                sequence=sequence,
                previous=previous,
            )
        )
        previous = row
    revisions[-1] = replace(revisions[-1], lifecycle_status="CURRENT")
    row = rows[-1]
    return CapabilityAutonomyEvidenceEvaluationPolicySnapshot(
        profile_id=profile.id,
        profile_sequence=profile.profile_sequence,
        profile_record_fingerprint=profile.record_fingerprint,
        position_key=profile.position_key,
        capability_key=profile.capability_key,
        context_scope=profile.context_scope,
        current_policy_id=row.id,
        current_policy_sequence=row.policy_sequence,
        qualification_contract=row.qualification_contract,
        max_observation_age_seconds=row.max_observation_age_seconds,
        max_source_age_seconds=row.max_source_age_seconds,
        max_candidate_observations=row.max_candidate_observations,
        revisions=tuple(revisions),
    )
