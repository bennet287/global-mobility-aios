from __future__ import annotations

from datetime import timedelta

import pytest
from sqlmodel import Session, select

from app.models.autonomy_evidence_evaluation_policy import (
    CapabilityAutonomyEvidenceEvaluationPolicy,
)
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActivity, now_utc
from app.services.organization_activity import append_activity
from app.services.organization_autonomy_evidence_evaluation import (
    AutonomyEvidenceEvaluationBoundExceeded,
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


def _evaluation_policy(
    session: Session,
    *,
    key: str,
    max_observation_age_seconds: int = 3600,
    max_source_age_seconds: int = 3600,
    max_candidate_observations: int = 100,
    expected_policy_sequence: int | None = None,
) -> CapabilityAutonomyEvidenceEvaluationPolicy:
    return establish_capability_autonomy_evidence_evaluation_policy(
        session,
        _board_context(),
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


def _canonical_source(session: Session) -> OrganizationActivity:
    proposal, readiness, verification, floor, authority, *_ = _floor_ready(session)
    result = commit_governed_eligibility_effect(
        session,
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        authority=authority,
    )
    return result.semantic_activity


def _ordinary_source(session: Session, *, key: str) -> OrganizationActivity:
    return append_activity(
        session,
        _board_context(),
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
    recovery: str = "not_applicable",
):
    return establish_capability_autonomy_evidence_observation(
        session,
        _board_context(),
        profile_id=profile.id,
        source_activity_id=source.id,
        human_review_outcome="accepted",
        evidence_grounded=True,
        verifier_contradiction=False,
        policy_compliant=True,
        freshness_compliant=True,
        critical_error=False,
        recovery_outcome=recovery,
        sla_met=True,
        incident_count=0,
        idempotency_key=f"i4-observation-{key}",
    )


def _foundation(session: Session, *, candidate_bound: int = 100):
    _position(session)
    profile = _profile(session, _board_context(), key="i4")
    _policy(
        session,
        _board_context(),
        key="i4",
        min_volume=1,
        min_reviewed=1,
    )
    evaluation_policy = _evaluation_policy(
        session,
        key="v1",
        max_candidate_observations=candidate_bound,
    )
    return profile, evaluation_policy


def _snapshot(session: Session, *, evaluation_as_of=None):
    return capability_autonomy_evidence_evaluation_snapshot(
        session,
        tenant_key="default",
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


def test_i4_qualifies_only_validated_canonical_eligibility_effects(db_session: Session) -> None:
    profile, _ = _foundation(db_session)
    canonical = _canonical_source(db_session)
    ordinary = _ordinary_source(db_session, key="ordinary")
    _observation(db_session, profile, canonical, key="canonical")
    _observation(db_session, profile, ordinary, key="ordinary")

    snapshot = _snapshot(db_session)
    assert snapshot is not None
    assert snapshot.candidate_count == 2
    assert snapshot.qualified_count == 1
    assert snapshot.excluded_unqualified_source_count == 1
    assert snapshot.metrics.qualifying_execution_volume == 1
    assert snapshot.metrics.evidence_grounding_rate == 1.0
    assert snapshot.metrics.human_acceptance_rate == 1.0
    assert snapshot.metrics.policy_compliance_rate == 1.0
    assert snapshot.missing_derivation_fields == I4_ALWAYS_UNAVAILABLE_DERIVATIONS
    assert snapshot.promotion_grade_ready is False
    assert {item.disposition for item in snapshot.recent_provenance} == {
        PROVENANCE_QUALIFIED,
        PROVENANCE_UNQUALIFIED_SOURCE,
    }
    qualified = next(
        item for item in snapshot.recent_provenance if item.disposition == PROVENANCE_QUALIFIED
    )
    assert qualified.canonical_revision_id is not None
    assert qualified.effect_fingerprint is not None
    assert profile.autonomy_level == "A2"
    db_session.refresh(profile)
    assert profile.autonomy_level == "A2"


def test_i4_applies_observation_and_source_age_boundaries_deterministically(db_session: Session) -> None:
    profile, policy = _foundation(db_session)
    canonical = _canonical_source(db_session)
    _observation(db_session, profile, canonical, key="age")

    # Supersede the broad policy with a source-age bound smaller than the
    # observation-age bound. At the exact same as-of instant the disposition is
    # deterministic and no stored I.2 freshness flag is reinterpreted.
    narrow = establish_capability_autonomy_evidence_evaluation_policy(
        db_session,
        _board_context(),
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
    as_of = narrow.effective_from + timedelta(seconds=2)
    first = _snapshot(db_session, evaluation_as_of=as_of)
    second = _snapshot(db_session, evaluation_as_of=as_of)
    assert first == second
    assert first is not None
    assert first.qualified_count == 0
    assert first.excluded_stale_source_count == 1
    assert first.recent_provenance[0].disposition == PROVENANCE_STALE_SOURCE

    # Make the observation window even narrower than the source window; the
    # observation-age exclusion is the first temporal boundary.
    newest = establish_capability_autonomy_evidence_evaluation_policy(
        db_session,
        _board_context(),
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
        evaluation_as_of=newest.effective_from + timedelta(seconds=2),
    )
    assert stale_observation is not None
    assert stale_observation.excluded_stale_observation_count == 1
    assert stale_observation.recent_provenance[0].disposition == PROVENANCE_STALE_OBSERVATION


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
