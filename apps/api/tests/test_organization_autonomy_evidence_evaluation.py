from __future__ import annotations

from datetime import timedelta, timezone

import pytest
from sqlmodel import Session, select

from app.models.autonomy_evidence_evaluation_policy import (
    CapabilityAutonomyEvidenceEvaluationPolicy,
)
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActivity, OrganizationHumanActionType, now_utc
from app.services.organization_activity import append_activity
from app.services.organization_autonomy_evidence_evaluation import (
    AutonomyEvidenceEvaluationBoundExceeded,
    AutonomyEvidenceEvaluationIntegrityError,
    capability_autonomy_evidence_evaluation_provenance_page,
    capability_autonomy_evidence_evaluation_snapshot,
)
from app.services.organization_autonomy_evidence_evaluation_contract import (
    I4_ALWAYS_UNAVAILABLE_DERIVATIONS,
    I4_QUALIFICATION_CONTRACT,
    PROVENANCE_QUALIFIED,
    PROVENANCE_STALE_OBSERVATION,
    PROVENANCE_STALE_SOURCE,
    PROVENANCE_UNQUALIFIED_SOURCE,
)
from app.services.organization_autonomy_evidence_evaluation_policy import (
    establish_capability_autonomy_evidence_evaluation_policy,
)
from app.services.organization_autonomy_evidence_profile import (
    establish_capability_autonomy_evidence_observation,
)
from app.services.organization_command import IdempotencyConflict, InvalidHumanActor, InvalidTransition
from app.services.organization_eligibility_effect import commit_governed_eligibility_effect
from app.services.organization_human_action import append_human_action
from tests.test_organization_autonomy_promotion_policy import (
    CAPABILITY_KEY,
    CONTEXT_SCOPE,
    POSITION_KEY,
    _agent_context,
    _board_context,
    _policy,
    _position,
    _profile,
)
from tests.test_organization_eligibility_effect import _floor_ready


CANONICAL_TENANT_KEY = "tenant-a"


def _aware_utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _evaluation_policy(
    session: Session,
    *,
    key: str,
    max_observation_age_seconds: int = 3600,
    max_source_age_seconds: int = 3600,
    max_candidate_observations: int = 100,
    expected_policy_sequence: int | None = None,
    tenant_key: str = "default",
) -> CapabilityAutonomyEvidenceEvaluationPolicy:
    return establish_capability_autonomy_evidence_evaluation_policy(
        session,
        _board_context(tenant_key),
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        qualification_contract=I4_QUALIFICATION_CONTRACT,
        max_observation_age_seconds=max_observation_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        max_candidate_observations=max_candidate_observations,
        policy_reason=f"I.4 policy {key}",
        idempotency_key=f"i4-policy-{key}",
        expected_policy_sequence=expected_policy_sequence,
    )


def _canonical_effect(session: Session):
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(session)
    return commit_governed_eligibility_effect(
        session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )


def _canonical_effect_with_work(session: Session):
    (
        proposal,
        readiness,
        verification,
        floor,
        authority,
        _,
        _,
        _,
        proposal_work,
        _,
    ) = _floor_ready(session)
    effect = commit_governed_eligibility_effect(
        session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    return effect, proposal_work


def _ordinary_source(
    session: Session,
    *,
    key: str,
    tenant_key: str = "default",
) -> OrganizationActivity:
    return append_activity(
        session,
        _board_context(tenant_key),
        activity_key=f"i4-unqualified:{key}",
        stream_key="i4-unqualified",
        activity_class="operational",
        activity_type="organization.capability_outcome.observed.v1",
        title=f"Unqualified I.4 source {key}",
        summary="Valid Activity, but not a canonical governed eligibility effect.",
        source_object_type="governed_capability_outcome",
        source_object_id=key,
        occurred_at=now_utc(),
        payload={"test_contract": "v1.3-i.4", "key": key},
    )


def _observation(
    session: Session,
    profile: CapabilityAutonomyProfile,
    source: OrganizationActivity,
    *,
    key: str,
    review: str = "accepted",
    grounded: bool = True,
    contradiction: bool = False,
    policy_compliant: bool = True,
    freshness_compliant: bool = True,
    critical_error: bool = False,
    recovery: str = "not_applicable",
    sla_met: bool = True,
    incident_count: int = 0,
    tenant_key: str = "default",
):
    return establish_capability_autonomy_evidence_observation(
        session,
        _board_context(tenant_key),
        profile_id=profile.id,
        source_activity_id=source.id,
        human_review_outcome=review,
        evidence_grounded=grounded,
        verifier_contradiction=contradiction,
        policy_compliant=policy_compliant,
        freshness_compliant=freshness_compliant,
        critical_error=critical_error,
        recovery_outcome=recovery,
        sla_met=sla_met,
        incident_count=incident_count,
        idempotency_key=f"i4-observation-{key}",
    )


def _human_review(
    session: Session,
    effect,
    *,
    key: str,
    action_type: OrganizationHumanActionType,
    work_item_id,
    occurred_at=None,
    tenant_key: str = "default",
):
    return append_human_action(
        session,
        _board_context(tenant_key),
        action_key=f"i4-human-review-{key}",
        action_type=action_type,
        outcome=f"I.4 human review {key}",
        occurred_at=occurred_at or now_utc(),
        work_item_id=work_item_id,
        source_object_type="eligibility_assessment",
        source_object_id=str(effect.assessment.id),
        source_object_version=str(effect.revision.version),
    )


def _foundation(
    session: Session,
    *,
    candidate_bound: int = 100,
    tenant_key: str = "default",
):
    _position(session)
    board = _board_context(tenant_key)
    profile = _profile(session, board, key="i4")
    _policy(
        session,
        board,
        key="i4",
        min_volume=1,
        min_reviewed=1,
    )
    evaluation_policy = _evaluation_policy(
        session,
        key="v1",
        max_candidate_observations=candidate_bound,
        tenant_key=tenant_key,
    )
    return profile, evaluation_policy


def _snapshot(
    session: Session,
    *,
    evaluation_as_of=None,
    tenant_key: str = "default",
):
    return capability_autonomy_evidence_evaluation_snapshot(
        session,
        tenant_key=tenant_key,
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        evaluation_as_of=evaluation_as_of,
    )


def test_i4_policy_is_board_only_append_only_bounded_and_idempotent(db_session: Session) -> None:
    _position(db_session)
    profile = _profile(db_session, _board_context(), key="policy")

    with pytest.raises(InvalidHumanActor):
        establish_capability_autonomy_evidence_evaluation_policy(
            db_session,
            _agent_context(),
            position_key=POSITION_KEY,
            capability_key=CAPABILITY_KEY,
            context_scope=CONTEXT_SCOPE,
            qualification_contract=I4_QUALIFICATION_CONTRACT,
            max_observation_age_seconds=60,
            max_source_age_seconds=60,
            max_candidate_observations=10,
            policy_reason="agent must not author this",
            idempotency_key="i4-agent-policy",
        )
    with pytest.raises(InvalidTransition, match="at least 1 second"):
        establish_capability_autonomy_evidence_evaluation_policy(
            db_session,
            _board_context(),
            position_key=POSITION_KEY,
            capability_key=CAPABILITY_KEY,
            context_scope=CONTEXT_SCOPE,
            qualification_contract=I4_QUALIFICATION_CONTRACT,
            max_observation_age_seconds=0,
            max_source_age_seconds=60,
            max_candidate_observations=10,
            policy_reason="invalid age",
            idempotency_key="i4-invalid-age",
        )

    first = _evaluation_policy(db_session, key="first")
    replay = _evaluation_policy(db_session, key="first")
    assert replay.id == first.id
    assert first.profile_id == profile.id
    with pytest.raises(IdempotencyConflict):
        establish_capability_autonomy_evidence_evaluation_policy(
            db_session,
            _board_context(),
            position_key=POSITION_KEY,
            capability_key=CAPABILITY_KEY,
            context_scope=CONTEXT_SCOPE,
            qualification_contract=I4_QUALIFICATION_CONTRACT,
            max_observation_age_seconds=7200,
            max_source_age_seconds=3600,
            max_candidate_observations=100,
            policy_reason="changed semantics",
            idempotency_key="i4-policy-first",
        )
    with pytest.raises(InvalidTransition, match="expected_policy_sequence"):
        _evaluation_policy(db_session, key="missing-sequence")
    second = _evaluation_policy(
        db_session,
        key="second",
        max_source_age_seconds=1800,
        expected_policy_sequence=1,
    )
    assert second.policy_sequence == 2
    assert second.supersedes_policy_id == first.id
    rows = tuple(
        db_session.exec(
            select(CapabilityAutonomyEvidenceEvaluationPolicy).order_by(
                CapabilityAutonomyEvidenceEvaluationPolicy.policy_sequence
            )
        ).all()
    )
    assert [row.policy_sequence for row in rows] == [1, 2]


def test_i4_qualifies_only_canonical_effect_and_ignores_i2_quality_attestations(
    db_session: Session,
) -> None:
    profile, _ = _foundation(db_session, tenant_key=CANONICAL_TENANT_KEY)
    effect = _canonical_effect(db_session)
    ordinary = _ordinary_source(
        db_session,
        key="ordinary",
        tenant_key=CANONICAL_TENANT_KEY,
    )
    _observation(
        db_session,
        profile,
        effect.semantic_activity,
        key="canonical-adversarial-i2",
        review="rejected",
        grounded=False,
        contradiction=True,
        policy_compliant=False,
        freshness_compliant=True,
        critical_error=True,
        recovery="failed",
        sla_met=False,
        incident_count=7,
        tenant_key=CANONICAL_TENANT_KEY,
    )
    _observation(
        db_session,
        profile,
        ordinary,
        key="ordinary",
        tenant_key=CANONICAL_TENANT_KEY,
    )

    snapshot = _snapshot(db_session, tenant_key=CANONICAL_TENANT_KEY)
    assert snapshot is not None
    assert snapshot.candidate_count == 2
    assert snapshot.qualified_count == 1
    assert snapshot.excluded_unqualified_source_count == 1
    assert snapshot.metrics.qualifying_execution_volume == 1
    # These are derived from the canonical G.1/G.2/G.3 effect, not copied from
    # deliberately contradictory I.2 attestation inputs above.
    assert snapshot.metrics.evidence_grounding_rate == 1.0
    assert snapshot.metrics.verifier_contradiction_rate == 0.0
    assert snapshot.metrics.policy_compliance_rate == 1.0
    assert snapshot.metrics.human_not_reviewed_count == 1
    assert snapshot.metrics.human_reviewed_count == 0
    assert snapshot.metrics.human_acceptance_rate is None
    assert snapshot.metrics.freshness_compliance_rate is None
    assert snapshot.metrics.critical_error_count is None
    assert snapshot.metrics.recovery_applicable_count is None
    assert snapshot.metrics.recovery_success_rate is None
    assert snapshot.metrics.sla_met_rate is None
    assert snapshot.metrics.incident_count is None
    assert snapshot.missing_derivation_fields == I4_ALWAYS_UNAVAILABLE_DERIVATIONS
    assert snapshot.promotion_grade_ready is False
    assert {item.disposition for item in snapshot.recent_provenance} == {
        PROVENANCE_QUALIFIED,
        PROVENANCE_UNQUALIFIED_SOURCE,
    }
    qualified = next(
        item for item in snapshot.recent_provenance if item.disposition == PROVENANCE_QUALIFIED
    )
    assert qualified.canonical_revision_id == effect.revision.id
    assert qualified.effect_fingerprint == effect.revision.effect_fingerprint
    assert qualified.human_review_outcome == "not_reviewed"
    assert qualified.evidence_grounded is True
    assert qualified.verifier_contradiction is False
    assert qualified.policy_compliant is True
    db_session.refresh(profile)
    assert profile.autonomy_level == "A2"


def test_i4_derives_only_explicit_terminal_human_review_actions(db_session: Session) -> None:
    profile, _ = _foundation(db_session, tenant_key=CANONICAL_TENANT_KEY)
    effect, proposal_work = _canonical_effect_with_work(db_session)
    _observation(
        db_session,
        profile,
        effect.semantic_activity,
        key="human-review",
        tenant_key=CANONICAL_TENANT_KEY,
    )

    _human_review(
        db_session,
        effect,
        key="generic-reviewed",
        action_type=OrganizationHumanActionType.reviewed,
        work_item_id=proposal_work.id,
        tenant_key=CANONICAL_TENANT_KEY,
    )
    before_terminal = _snapshot(db_session, tenant_key=CANONICAL_TENANT_KEY)
    assert before_terminal is not None
    assert before_terminal.metrics.human_not_reviewed_count == 1
    assert before_terminal.metrics.human_reviewed_count == 0

    approved = _human_review(
        db_session,
        effect,
        key="approved",
        action_type=OrganizationHumanActionType.approved,
        work_item_id=proposal_work.id,
        tenant_key=CANONICAL_TENANT_KEY,
    )
    accepted = _snapshot(
        db_session,
        evaluation_as_of=approved.occurred_at + timedelta(microseconds=1),
        tenant_key=CANONICAL_TENANT_KEY,
    )
    assert accepted is not None
    assert accepted.metrics.human_accepted_count == 1
    assert accepted.metrics.human_reviewed_count == 1
    assert accepted.metrics.human_acceptance_rate == 1.0
    assert accepted.recent_provenance[0].human_review_outcome == "accepted"

    changed = _human_review(
        db_session,
        effect,
        key="requested-changes",
        action_type=OrganizationHumanActionType.requested_changes,
        work_item_id=proposal_work.id,
        occurred_at=approved.occurred_at + timedelta(seconds=1),
        tenant_key=CANONICAL_TENANT_KEY,
    )
    modified = _snapshot(
        db_session,
        evaluation_as_of=changed.occurred_at + timedelta(microseconds=1),
        tenant_key=CANONICAL_TENANT_KEY,
    )
    assert modified is not None
    assert modified.metrics.human_modified_count == 1
    assert modified.metrics.human_accepted_count == 0
    assert modified.recent_provenance[0].human_review_outcome == "modified"


def test_i4_conflicting_equal_time_terminal_human_reviews_fail_closed(db_session: Session) -> None:
    profile, _ = _foundation(db_session, tenant_key=CANONICAL_TENANT_KEY)
    effect, proposal_work = _canonical_effect_with_work(db_session)
    _observation(
        db_session,
        profile,
        effect.semantic_activity,
        key="ambiguous-review",
        tenant_key=CANONICAL_TENANT_KEY,
    )
    same_time = now_utc()
    _human_review(
        db_session,
        effect,
        key="same-time-approved",
        action_type=OrganizationHumanActionType.approved,
        work_item_id=proposal_work.id,
        occurred_at=same_time,
        tenant_key=CANONICAL_TENANT_KEY,
    )
    _human_review(
        db_session,
        effect,
        key="same-time-rejected",
        action_type=OrganizationHumanActionType.rejected,
        work_item_id=proposal_work.id,
        occurred_at=same_time,
        tenant_key=CANONICAL_TENANT_KEY,
    )
    with pytest.raises(AutonomyEvidenceEvaluationIntegrityError, match="ambiguous"):
        _snapshot(
            db_session,
            evaluation_as_of=same_time + timedelta(microseconds=1),
            tenant_key=CANONICAL_TENANT_KEY,
        )


def test_i4_torn_canonical_lineage_and_i2_source_fingerprint_drift_fail_closed(
    db_session: Session,
) -> None:
    profile, _ = _foundation(db_session, tenant_key=CANONICAL_TENANT_KEY)
    effect = _canonical_effect(db_session)
    _observation(
        db_session,
        profile,
        effect.semantic_activity,
        key="lineage-drift",
        tenant_key=CANONICAL_TENANT_KEY,
    )

    verification_activity = db_session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.id == effect.revision.verification_activity_id,
            OrganizationActivity.tenant_key == CANONICAL_TENANT_KEY,
        )
    ).one()
    original_activity_type = verification_activity.activity_type
    verification_activity.activity_type = "verification.eligibility.corrupted.v1"
    db_session.add(verification_activity)
    db_session.commit()
    with pytest.raises(AutonomyEvidenceEvaluationIntegrityError, match="lineage"):
        _snapshot(db_session, tenant_key=CANONICAL_TENANT_KEY)

    # Restore the non-source lineage row, then corrupt the I.2 source witness itself.
    verification_activity.activity_type = original_activity_type
    db_session.add(verification_activity)
    db_session.commit()
    effect.semantic_activity.record_fingerprint = "0" * 64
    db_session.add(effect.semantic_activity)
    db_session.commit()
    with pytest.raises(AutonomyEvidenceEvaluationIntegrityError, match="I.2 evidence integrity"):
        _snapshot(db_session, tenant_key=CANONICAL_TENANT_KEY)


def test_i4_applies_observation_and_source_age_boundaries_deterministically(db_session: Session) -> None:
    profile, policy = _foundation(db_session, tenant_key=CANONICAL_TENANT_KEY)
    effect = _canonical_effect(db_session)
    _observation(
        db_session,
        profile,
        effect.semantic_activity,
        key="age",
        tenant_key=CANONICAL_TENANT_KEY,
    )

    narrow = establish_capability_autonomy_evidence_evaluation_policy(
        db_session,
        _board_context(CANONICAL_TENANT_KEY),
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        qualification_contract=I4_QUALIFICATION_CONTRACT,
        max_observation_age_seconds=3600,
        max_source_age_seconds=1,
        max_candidate_observations=100,
        policy_reason="Bound source age for deterministic I.4 test",
        idempotency_key="i4-policy-source-age",
        expected_policy_sequence=policy.policy_sequence,
    )
    as_of = _aware_utc(narrow.effective_from) + timedelta(seconds=2)
    first = _snapshot(
        db_session,
        evaluation_as_of=as_of,
        tenant_key=CANONICAL_TENANT_KEY,
    )
    second = _snapshot(
        db_session,
        evaluation_as_of=as_of,
        tenant_key=CANONICAL_TENANT_KEY,
    )
    assert first == second
    assert first is not None
    assert first.qualified_count == 0
    assert first.excluded_stale_source_count == 1
    assert first.recent_provenance[0].disposition == PROVENANCE_STALE_SOURCE

    newest = establish_capability_autonomy_evidence_evaluation_policy(
        db_session,
        _board_context(CANONICAL_TENANT_KEY),
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        qualification_contract=I4_QUALIFICATION_CONTRACT,
        max_observation_age_seconds=1,
        max_source_age_seconds=3600,
        max_candidate_observations=100,
        policy_reason="Bound observation age for deterministic I.4 test",
        idempotency_key="i4-policy-observation-age",
        expected_policy_sequence=narrow.policy_sequence,
    )
    stale_observation = _snapshot(
        db_session,
        evaluation_as_of=_aware_utc(newest.effective_from) + timedelta(seconds=2),
        tenant_key=CANONICAL_TENANT_KEY,
    )
    assert stale_observation is not None
    assert stale_observation.excluded_stale_observation_count == 1
    assert stale_observation.recent_provenance[0].disposition == PROVENANCE_STALE_OBSERVATION


def test_i4_future_source_time_fails_closed(db_session: Session) -> None:
    profile, _ = _foundation(db_session, tenant_key=CANONICAL_TENANT_KEY)
    effect = _canonical_effect(db_session)
    _observation(
        db_session,
        profile,
        effect.semantic_activity,
        key="future-source",
        tenant_key=CANONICAL_TENANT_KEY,
    )
    as_of = now_utc()
    effect.semantic_activity.occurred_at = as_of + timedelta(minutes=1)
    db_session.add(effect.semantic_activity)
    db_session.commit()
    with pytest.raises(AutonomyEvidenceEvaluationIntegrityError, match="after evaluation_as_of"):
        _snapshot(
            db_session,
            evaluation_as_of=as_of,
            tenant_key=CANONICAL_TENANT_KEY,
        )


def test_i4_candidate_bound_fails_closed_without_silent_truncation(db_session: Session) -> None:
    profile, _ = _foundation(db_session, candidate_bound=1)
    _observation(db_session, profile, _ordinary_source(db_session, key="one"), key="one")
    _observation(db_session, profile, _ordinary_source(db_session, key="two"), key="two")
    with pytest.raises(AutonomyEvidenceEvaluationBoundExceeded):
        _snapshot(db_session)


def test_i4_provenance_is_stable_paged_and_cursor_bound_to_profile_policy(db_session: Session) -> None:
    profile, _ = _foundation(db_session)
    _observation(db_session, profile, _ordinary_source(db_session, key="p1"), key="p1")
    _observation(db_session, profile, _ordinary_source(db_session, key="p2"), key="p2")
    _observation(db_session, profile, _ordinary_source(db_session, key="p3"), key="p3")
    as_of = now_utc()

    first = capability_autonomy_evidence_evaluation_provenance_page(
        db_session,
        tenant_key="default",
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        page_limit=2,
        evaluation_as_of=as_of,
    )
    assert first is not None
    assert len(first.items) == 2
    assert first.next_cursor is not None
    second = capability_autonomy_evidence_evaluation_provenance_page(
        db_session,
        tenant_key="default",
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        page_limit=2,
        cursor=first.next_cursor,
    )
    assert second is not None
    assert second.evaluation_as_of == first.evaluation_as_of
    assert len(second.items) == 1
    assert second.next_cursor is None
    assert {item.observation_id for item in first.items}.isdisjoint(
        {item.observation_id for item in second.items}
    )


def test_i4_same_level_profile_supersession_does_not_inherit_evaluation_policy(
    db_session: Session,
) -> None:
    profile, _ = _foundation(db_session)
    assert _snapshot(db_session) is not None
    replacement = _profile(
        db_session,
        _board_context(),
        key="i4-v2",
        expected_profile_sequence=profile.profile_sequence,
        authority_requirement="L3",
    )
    assert replacement.id != profile.id
    assert _snapshot(db_session) is None
