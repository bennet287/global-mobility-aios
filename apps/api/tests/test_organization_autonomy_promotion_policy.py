from __future__ import annotations

import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, RiskTier
from app.models.autonomy_evidence_profile import CapabilityAutonomyEvidenceObservation
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.autonomy_promotion_policy import CapabilityAutonomyPromotionPolicy
from app.models.domain import OrganizationActivity, OrganizationActorType, OrganizationPosition, now_utc
from app.services.organization_activity import append_activity
from app.services.organization_autonomy_evidence_profile import (
    AutonomyEvidenceProfileIntegrityError,
    establish_capability_autonomy_evidence_observation,
)
from app.services.organization_autonomy_profile import establish_capability_autonomy_profile
from app.services.organization_autonomy_promotion_policy import (
    PROMOTION_ELIGIBLE,
    PROMOTION_HOLD,
    PROMOTION_INSUFFICIENT_EVIDENCE,
    AutonomyPromotionPolicyIntegrityError,
    capability_autonomy_promotion_eligibility_snapshot,
    capability_autonomy_promotion_policy_snapshot,
    establish_capability_autonomy_promotion_policy,
)
from app.services.organization_command import (
    AuthorityDenied,
    IdempotencyConflict,
    InvalidHumanActor,
    InvalidTransition,
    OrganizationCommandContext,
)


BASE = "/api/v1/organization/transparency/autonomy/profiles"
POSITION_KEY = "case_operations_specialist"
CAPABILITY_KEY = "eligibility.proposal"
CONTEXT_SCOPE = "austria:skilled-worker"
EVIDENCE_POLICY_VERSION = "autonomy-evidence-v1"


def _board_context(tenant_key: str = "default") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id="board-human",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="board-human",
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )


def _agent_context(tenant_key: str = "default") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id="case-ops-agent",
        actor_type=OrganizationActorType.agent,
        authenticated_user_id="system",
        role="operator",
        department="operations",
        position_key=POSITION_KEY,
        authority_level="L2",
    )


def _position(session: Session) -> OrganizationPosition:
    position = OrganizationPosition(
        position_key=POSITION_KEY,
        title="Case Operations Specialist",
        department="operations",
        authority_level="L2",
        created_by="pytest",
    )
    session.add(position)
    session.commit()
    session.refresh(position)
    return position


def _activity(session: Session, context: OrganizationCommandContext, *, key: str) -> OrganizationActivity:
    return append_activity(
        session,
        context,
        activity_key=f"i3-source:{key}",
        stream_key="i3-source",
        activity_class="operational",
        activity_type="organization.capability_outcome.observed.v1",
        title=f"I.3 source {key}",
        summary="Canonical execution evidence for the I.3 promotion-eligibility contract.",
        source_object_type="governed_capability_outcome",
        source_object_id=key,
        occurred_at=now_utc(),
        payload={"test_contract": "v1.3-i.3", "key": key},
    )


def _profile(
    session: Session,
    board: OrganizationCommandContext,
    *,
    key: str = "v1",
    autonomy_level: AutonomyLevel = AutonomyLevel.A2,
    board_ceiling: AutonomyLevel = AutonomyLevel.A3,
    authority_requirement: str = "L2",
    risk_ceiling: RiskTier = RiskTier.R3,
    expected_profile_sequence: int | None = None,
    evidence_activity_ids: tuple[UUID, ...] | None = None,
) -> CapabilityAutonomyProfile:
    evidence_ids = evidence_activity_ids or (_activity(session, board, key=f"profile-{key}").id,)
    return establish_capability_autonomy_profile(
        session,
        board,
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        autonomy_level=autonomy_level,
        board_ceiling=board_ceiling,
        authority_requirement=authority_requirement,
        risk_ceiling=risk_ceiling,
        evidence_policy_version=EVIDENCE_POLICY_VERSION,
        evidence_activity_ids=evidence_ids,
        idempotency_key=f"i3-profile-{key}",
        expected_profile_sequence=expected_profile_sequence,
    )


def _policy(
    session: Session,
    context: OrganizationCommandContext,
    *,
    key: str,
    expected_policy_sequence: int | None = None,
    from_level: AutonomyLevel = AutonomyLevel.A2,
    target_level: AutonomyLevel = AutonomyLevel.A3,
    min_volume: int = 2,
    min_reviewed: int = 2,
    min_grounding: float = 1.0,
    min_acceptance: float = 1.0,
    max_modification: float = 0.0,
    max_rejection: float = 0.0,
    max_contradiction: float = 0.0,
    min_policy_compliance: float = 1.0,
    min_freshness: float = 1.0,
    max_critical: int = 0,
    min_recovery_count: int = 0,
    min_recovery_rate: float | None = None,
    min_sla: float = 1.0,
    max_incidents: int = 0,
    evidence_policy_version: str = EVIDENCE_POLICY_VERSION,
) -> CapabilityAutonomyPromotionPolicy:
    return establish_capability_autonomy_promotion_policy(
        session,
        context,
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        from_autonomy_level=from_level,
        target_autonomy_level=target_level,
        evidence_policy_version=evidence_policy_version,
        min_qualifying_execution_volume=min_volume,
        min_human_reviewed_count=min_reviewed,
        min_evidence_grounding_rate=min_grounding,
        min_human_acceptance_rate=min_acceptance,
        max_human_modification_rate=max_modification,
        max_human_rejection_rate=max_rejection,
        max_verifier_contradiction_rate=max_contradiction,
        min_policy_compliance_rate=min_policy_compliance,
        min_freshness_compliance_rate=min_freshness,
        max_critical_error_count=max_critical,
        min_recovery_applicable_count=min_recovery_count,
        min_recovery_success_rate=min_recovery_rate,
        min_sla_met_rate=min_sla,
        max_incident_count=max_incidents,
        policy_reason=f"Board policy {key}",
        idempotency_key=f"i3-policy-{key}",
        expected_policy_sequence=expected_policy_sequence,
    )


def _observation(
    session: Session,
    board: OrganizationCommandContext,
    profile: CapabilityAutonomyProfile,
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
) -> CapabilityAutonomyEvidenceObservation:
    source = _activity(session, board, key=f"observation-{key}")
    return establish_capability_autonomy_evidence_observation(
        session,
        board,
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
        idempotency_key=f"i3-observation-{key}",
    )


def _eligibility(session: Session):
    return capability_autonomy_promotion_eligibility_snapshot(
        session,
        tenant_key="default",
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
    )


def _policy_snapshot(session: Session, *, profile_id: UUID | None = None):
    return capability_autonomy_promotion_policy_snapshot(
        session,
        tenant_key="default",
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        from_autonomy_level="A2",
        evidence_policy_version=EVIDENCE_POLICY_VERSION,
        profile_id=profile_id,
    )


def test_i3_policy_is_board_only_one_step_ceiling_bounded_finite_and_idempotent(
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    first_evidence = _activity(db_session, board, key="low-ceiling-profile")
    _profile(
        db_session,
        board,
        key="low-ceiling",
        board_ceiling=AutonomyLevel.A2,
        evidence_activity_ids=(first_evidence.id,),
    )

    with pytest.raises(InvalidHumanActor):
        _policy(db_session, _agent_context(), key="agent")
    with pytest.raises(InvalidTransition, match="exactly one autonomy level"):
        _policy(db_session, board, key="two-step", target_level=AutonomyLevel.A4)
    with pytest.raises(AuthorityDenied, match="Board ceiling"):
        _policy(db_session, board, key="above-ceiling")

    second_evidence = _activity(db_session, board, key="normal-ceiling-profile")
    profile = _profile(
        db_session,
        board,
        key="normal-ceiling",
        board_ceiling=AutonomyLevel.A3,
        expected_profile_sequence=1,
        evidence_activity_ids=(first_evidence.id, second_evidence.id),
    )
    with pytest.raises(InvalidTransition, match="evidence version"):
        _policy(db_session, board, key="wrong-version", evidence_policy_version="autonomy-evidence-v2")
    with pytest.raises(InvalidTransition, match="between 0 and 1"):
        _policy(db_session, board, key="bad-rate", min_grounding=1.1)
    for label, invalid in (
        ("nan", float("nan")),
        ("pos-inf", float("inf")),
        ("neg-inf", float("-inf")),
    ):
        with pytest.raises(InvalidTransition, match="finite value"):
            _policy(db_session, board, key=f"nonfinite-{label}", min_grounding=invalid)
    with pytest.raises(InvalidTransition, match="min_recovery_applicable_count"):
        _policy(db_session, board, key="bad-recovery", min_recovery_rate=1.0)

    first = _policy(db_session, board, key="v1")
    assert first.profile_id == profile.id
    assert first.profile_sequence == profile.profile_sequence
    assert first.profile_record_fingerprint == profile.record_fingerprint
    replay = _policy(db_session, board, key="v1")
    assert replay.id == first.id
    with pytest.raises(IdempotencyConflict):
        establish_capability_autonomy_promotion_policy(
            db_session,
            board,
            position_key=POSITION_KEY,
            capability_key=CAPABILITY_KEY,
            context_scope=CONTEXT_SCOPE,
            from_autonomy_level=AutonomyLevel.A2,
            target_autonomy_level=AutonomyLevel.A3,
            evidence_policy_version=EVIDENCE_POLICY_VERSION,
            min_qualifying_execution_volume=3,
            min_human_reviewed_count=2,
            min_evidence_grounding_rate=1.0,
            min_human_acceptance_rate=1.0,
            max_human_modification_rate=0.0,
            max_human_rejection_rate=0.0,
            max_verifier_contradiction_rate=0.0,
            min_policy_compliance_rate=1.0,
            min_freshness_compliance_rate=1.0,
            max_critical_error_count=0,
            min_recovery_applicable_count=0,
            min_recovery_success_rate=None,
            min_sla_met_rate=1.0,
            max_incident_count=0,
            policy_reason="Changed semantics",
            idempotency_key="i3-policy-v1",
        )


def test_i3_policy_activity_uses_decision_physical_class_and_constitutional_authority(
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    profile = _profile(db_session, board)
    policy = _policy(db_session, board, key="activity")
    activity = db_session.get(OrganizationActivity, policy.decision_activity_id)
    assert activity is not None
    assert getattr(activity.activity_class, "value", activity.activity_class) == "decision"
    payload = json.loads(activity.payload_json)
    assert payload["constitutional_activity_class"] == "AUTHORITY"
    assert payload["profile_id"] == str(profile.id)
    assert payload["profile_sequence"] == profile.profile_sequence
    assert payload["profile_record_fingerprint"] == profile.record_fingerprint
    assert payload["autonomy_mutated"] is False

    payload["constitutional_activity_class"] = "OPERATIONAL"
    activity.payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    db_session.add(activity)
    db_session.commit()
    with pytest.raises(AutonomyPromotionPolicyIntegrityError, match="constitutional Activity payload"):
        _policy_snapshot(db_session)


def test_i3_policy_supersession_is_append_only_and_semantic_drift_fails_closed(
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    _profile(db_session, board)
    first = _policy(db_session, board, key="v1")
    with pytest.raises(InvalidTransition, match="expected_policy_sequence"):
        _policy(db_session, board, key="missing-sequence")
    with pytest.raises(InvalidTransition, match="stale"):
        _policy(db_session, board, key="stale", expected_policy_sequence=2)
    second = _policy(db_session, board, key="v2", expected_policy_sequence=1, min_volume=3, min_reviewed=3)
    assert second.policy_sequence == 2
    assert second.supersedes_policy_id == first.id

    snapshot = _policy_snapshot(db_session)
    assert snapshot is not None
    assert snapshot.profile_id == second.profile_id
    assert [row.policy_sequence for row in snapshot.revisions] == [1, 2]
    assert [row.lifecycle_status for row in snapshot.revisions] == ["HISTORICAL", "CURRENT"]

    second.min_sla_met_rate = 0.5
    db_session.add(second)
    db_session.commit()
    with pytest.raises(AutonomyPromotionPolicyIntegrityError, match="record fingerprint"):
        _policy_snapshot(db_session)


def test_i3_policy_activity_fingerprint_drift_fails_closed(db_session: Session) -> None:
    _position(db_session)
    board = _board_context()
    _profile(db_session, board)
    policy = _policy(db_session, board, key="fingerprint")
    activity = db_session.get(OrganizationActivity, policy.decision_activity_id)
    assert activity is not None
    activity.record_fingerprint = "0" * 64
    db_session.add(activity)
    db_session.commit()
    with pytest.raises(AutonomyPromotionPolicyIntegrityError, match="Activity fingerprint"):
        _policy_snapshot(db_session)


def test_i3_eligibility_states_are_deterministic_and_do_not_mutate_autonomy(db_session: Session) -> None:
    _position(db_session)
    board = _board_context()
    profile = _profile(db_session, board)
    _policy(db_session, board, key="states")

    insufficient = _eligibility(db_session)
    assert insufficient is not None
    assert insufficient.eligibility_state == PROMOTION_INSUFFICIENT_EVIDENCE
    assert insufficient.evidence_profile.metrics.human_acceptance_rate is None

    _observation(db_session, board, profile, key="good-1")
    _observation(db_session, board, profile, key="good-2")
    eligible = _eligibility(db_session)
    assert eligible is not None
    assert eligible.eligibility_state == PROMOTION_ELIGIBLE
    assert all(item.passed is True for item in eligible.criteria)
    preserved = db_session.get(CapabilityAutonomyProfile, profile.id)
    assert preserved is not None and preserved.autonomy_level == "A2"


def test_i3_quality_failure_dominates_sample_deficit(db_session: Session) -> None:
    _position(db_session)
    board = _board_context()
    profile = _profile(db_session, board)
    _policy(db_session, board, key="quality", min_recovery_count=1, min_recovery_rate=1.0)
    _observation(db_session, board, profile, key="bad", critical_error=True, recovery="not_applicable")
    hold = _eligibility(db_session)
    assert hold is not None
    assert hold.eligibility_state == PROMOTION_HOLD
    assert any(item.criterion_key == "critical_error_count" and item.passed is False for item in hold.criteria)
    assert any(item.criterion_key == "recovery_applicable_count" and item.passed is False for item in hold.criteria)


def test_i3_recovery_success_exact_boundary_is_eligible(db_session: Session) -> None:
    _position(db_session)
    board = _board_context()
    profile = _profile(db_session, board)
    _policy(
        db_session,
        board,
        key="recovery-boundary",
        min_volume=1,
        min_reviewed=1,
        min_recovery_count=1,
        min_recovery_rate=1.0,
    )
    _observation(db_session, board, profile, key="recovered", recovery="succeeded")
    eligible = _eligibility(db_session)
    assert eligible is not None
    assert eligible.eligibility_state == PROMOTION_ELIGIBLE
    recovery = {item.criterion_key: item for item in eligible.criteria}
    assert recovery["recovery_applicable_count"].observed_value == 1
    assert recovery["recovery_applicable_count"].passed is True
    assert recovery["recovery_success_rate"].observed_value == 1.0
    assert recovery["recovery_success_rate"].passed is True


def test_i3_same_level_i1_supersession_invalidates_old_policy(db_session: Session) -> None:
    _position(db_session)
    board = _board_context()
    first_evidence = _activity(db_session, board, key="profile-v1")
    first = _profile(db_session, board, key="v1", evidence_activity_ids=(first_evidence.id,))
    old_policy = _policy(db_session, board, key="v1")
    _observation(db_session, board, first, key="first")

    second_evidence = _activity(db_session, board, key="profile-v2")
    second = _profile(
        db_session,
        board,
        key="v2",
        autonomy_level=AutonomyLevel.A2,
        board_ceiling=AutonomyLevel.A3,
        authority_requirement="L3",
        risk_ceiling=RiskTier.R2,
        expected_profile_sequence=1,
        evidence_activity_ids=(first_evidence.id, second_evidence.id),
    )
    assert second.id != first.id
    assert second.autonomy_level == first.autonomy_level
    assert second.evidence_policy_version == first.evidence_policy_version
    assert _eligibility(db_session) is None
    assert _policy_snapshot(db_session) is None
    historical = _policy_snapshot(db_session, profile_id=first.id)
    assert historical is not None
    assert historical.current_policy_id == old_policy.id


def test_i3_same_level_board_ceiling_reduction_requires_new_policy(db_session: Session) -> None:
    _position(db_session)
    board = _board_context()
    first_evidence = _activity(db_session, board, key="ceiling-v1")
    _profile(db_session, board, key="ceiling-v1", evidence_activity_ids=(first_evidence.id,))
    _policy(db_session, board, key="ceiling-v1")

    second_evidence = _activity(db_session, board, key="ceiling-v2")
    _profile(
        db_session,
        board,
        key="ceiling-v2",
        autonomy_level=AutonomyLevel.A2,
        board_ceiling=AutonomyLevel.A2,
        expected_profile_sequence=1,
        evidence_activity_ids=(first_evidence.id, second_evidence.id),
    )
    assert _eligibility(db_session) is None
    with pytest.raises(AuthorityDenied, match="Board ceiling"):
        _policy(db_session, board, key="ceiling-v2")


def test_i3_i2_observation_drift_fails_closed_through_evaluator(db_session: Session) -> None:
    _position(db_session)
    board = _board_context()
    profile = _profile(db_session, board)
    _policy(db_session, board, key="i2-drift", min_volume=1, min_reviewed=1)
    observation = _observation(db_session, board, profile, key="drift")
    observation.sla_met = False
    db_session.add(observation)
    db_session.commit()
    with pytest.raises(AutonomyEvidenceProfileIntegrityError, match="record fingerprint"):
        _eligibility(db_session)


def test_i3_transparency_is_board_only_get_only_and_exposes_criteria(
    client: TestClient,
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    profile = _profile(db_session, board)
    policy = _policy(db_session, board, key="api", min_volume=1, min_reviewed=1)
    _observation(db_session, board, profile, key="api")
    path = (
        f"{BASE}/{POSITION_KEY}/{CAPABILITY_KEY}/promotion-eligibility"
        f"?context_scope=austria%3Askilled-worker"
    )

    response = client.get(path)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["profile_id"] == str(profile.id)
    assert body["policy_id"] == str(policy.id)
    assert body["eligibility_state"] == PROMOTION_ELIGIBLE
    assert any(item["criterion_key"] == "target_within_board_ceiling" for item in body["criteria"])
    assert "payload_json" not in response.text

    denied = raw_client.get(
        path,
        headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator-user"},
    )
    assert denied.status_code == 403
    admin_headers = {"X-GMAI-Role": "admin", "X-GMAI-User": "board-human"}
    assert raw_client.post(path, headers=admin_headers, json={}).status_code == 405
    assert raw_client.put(path, headers=admin_headers, json={}).status_code == 405
    assert raw_client.patch(path, headers=admin_headers, json={}).status_code == 405
    assert raw_client.delete(path, headers=admin_headers).status_code == 405

    policies = list(
        db_session.exec(
            select(CapabilityAutonomyPromotionPolicy).where(
                CapabilityAutonomyPromotionPolicy.tenant_key == "default"
            )
        ).all()
    )
    assert len(policies) == 1
