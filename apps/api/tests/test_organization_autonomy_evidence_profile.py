from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.organization_constitution import AutonomyLevel, RiskTier
from app.models.autonomy_evidence_profile import CapabilityAutonomyEvidenceObservation
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActorType, OrganizationPosition, now_utc
from app.services.organization_activity import append_activity
from app.services.organization_autonomy_evidence_profile import (
    AutonomyEvidenceProfileIntegrityError,
    capability_autonomy_evidence_profile_snapshot,
    establish_capability_autonomy_evidence_observation,
)
from app.services.organization_autonomy_profile import establish_capability_autonomy_profile
from app.services.organization_command import (
    AuthorityDenied,
    DependencyConflict,
    IdempotencyConflict,
    OrganizationCommandContext,
    OrganizationCommandError,
)


BASE = "/api/v1/organization/transparency/autonomy/profiles"


def _board_context(tenant_key: str = "default", actor_id: str = "board-human") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id=actor_id,
        actor_type=OrganizationActorType.human,
        authenticated_user_id=actor_id,
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )


def _system_context(tenant_key: str = "default") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id="autonomy-measurement-system",
        actor_type=OrganizationActorType.system,
        authenticated_user_id="system",
        role="operator",
        department="platform",
        position_key=None,
        authority_level=None,
    )


def _agent_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="case-operations-specialist",
        actor_type=OrganizationActorType.agent,
        authenticated_user_id="system",
        role="operator",
        department="operations",
        position_key="case_operations_specialist",
        authority_level="L2",
    )


def _position(session: Session) -> OrganizationPosition:
    position = OrganizationPosition(
        position_key="case_operations_specialist",
        title="Case Operations Specialist",
        department="operations",
        authority_level="L2",
        created_by="pytest",
    )
    session.add(position)
    session.commit()
    session.refresh(position)
    return position


def _activity(
    session: Session,
    context: OrganizationCommandContext,
    *,
    key: str,
):
    return append_activity(
        session,
        context,
        activity_key=f"i2-observed:{key}",
        stream_key=f"i2-observed:{key}",
        activity_class="operational",
        activity_type="organization.capability_outcome.observed.v1",
        title=f"I.2 qualifying outcome {key}",
        summary="Synthetic canonical outcome used to prove I.2 shadow measurement.",
        source_object_type="governed_capability_outcome",
        source_object_id=key,
        occurred_at=now_utc(),
        payload={"test_contract": "v1.3-i.2", "qualifying": True},
    )


def _profile(
    session: Session,
    *,
    context_scope: str = "austria:skilled-worker",
    idempotency_key: str = "i2-profile-v1",
    expected_profile_sequence: int | None = None,
    autonomy_level: AutonomyLevel = AutonomyLevel.A2,
) -> CapabilityAutonomyProfile:
    board = _board_context()
    evidence = _activity(session, board, key=f"profile-{idempotency_key}")
    return establish_capability_autonomy_profile(
        session,
        board,
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope=context_scope,
        autonomy_level=autonomy_level,
        board_ceiling=AutonomyLevel.A3,
        authority_requirement="L2",
        risk_ceiling=RiskTier.R3,
        evidence_policy_version="autonomy-evidence-v1",
        evidence_activity_ids=(evidence.id,),
        idempotency_key=idempotency_key,
        expected_profile_sequence=expected_profile_sequence,
    )


def _observe(
    session: Session,
    context: OrganizationCommandContext,
    *,
    profile_id: UUID,
    source_activity_id: UUID,
    idempotency_key: str,
    human_review_outcome: str = "accepted",
    evidence_grounded: bool = True,
    verifier_contradiction: bool = False,
    policy_compliant: bool = True,
    freshness_compliant: bool = True,
    critical_error: bool = False,
    recovery_outcome: str = "not_applicable",
    sla_met: bool = True,
    incident_count: int = 0,
) -> CapabilityAutonomyEvidenceObservation:
    return establish_capability_autonomy_evidence_observation(
        session,
        context,
        profile_id=profile_id,
        source_activity_id=source_activity_id,
        human_review_outcome=human_review_outcome,
        evidence_grounded=evidence_grounded,
        verifier_contradiction=verifier_contradiction,
        policy_compliant=policy_compliant,
        freshness_compliant=freshness_compliant,
        critical_error=critical_error,
        recovery_outcome=recovery_outcome,
        sla_met=sla_met,
        incident_count=incident_count,
        idempotency_key=idempotency_key,
    )


def test_i2_shadow_observations_are_trusted_idempotent_deduplicated_and_measurement_only(
    db_session: Session,
) -> None:
    _position(db_session)
    profile = _profile(db_session)
    original_autonomy = profile.autonomy_level
    board = _board_context()
    first_source = _activity(db_session, board, key="accepted")
    second_source = _activity(db_session, board, key="modified")

    first = _observe(
        db_session,
        board,
        profile_id=profile.id,
        source_activity_id=first_source.id,
        idempotency_key="i2-observation-1",
        human_review_outcome="accepted",
        recovery_outcome="succeeded",
        incident_count=1,
    )
    replay = _observe(
        db_session,
        board,
        profile_id=profile.id,
        source_activity_id=first_source.id,
        idempotency_key="i2-observation-1",
        human_review_outcome="accepted",
        recovery_outcome="succeeded",
        incident_count=1,
    )
    assert replay.id == first.id

    with pytest.raises(IdempotencyConflict):
        _observe(
            db_session,
            board,
            profile_id=profile.id,
            source_activity_id=first_source.id,
            idempotency_key="i2-observation-1",
            human_review_outcome="rejected",
            recovery_outcome="succeeded",
            incident_count=1,
        )
    with pytest.raises(DependencyConflict, match="already counted"):
        _observe(
            db_session,
            board,
            profile_id=profile.id,
            source_activity_id=first_source.id,
            idempotency_key="i2-observation-duplicate-source",
        )
    with pytest.raises(AuthorityDenied, match="self-graded"):
        _observe(
            db_session,
            _agent_context(),
            profile_id=profile.id,
            source_activity_id=second_source.id,
            idempotency_key="i2-agent-self-grade",
        )

    _observe(
        db_session,
        _system_context(),
        profile_id=profile.id,
        source_activity_id=second_source.id,
        idempotency_key="i2-observation-2",
        human_review_outcome="modified",
        evidence_grounded=True,
        verifier_contradiction=True,
        policy_compliant=True,
        freshness_compliant=False,
        critical_error=True,
        recovery_outcome="not_applicable",
        sla_met=False,
        incident_count=0,
    )

    snapshot = capability_autonomy_evidence_profile_snapshot(
        db_session,
        tenant_key="default",
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope="austria:skilled-worker",
    )
    assert snapshot is not None
    metrics = snapshot.metrics
    assert metrics.qualifying_execution_volume == 2
    assert metrics.evidence_grounded_count == 2
    assert metrics.evidence_grounding_rate == 1.0
    assert metrics.human_accepted_count == 1
    assert metrics.human_modified_count == 1
    assert metrics.human_rejected_count == 0
    assert metrics.human_acceptance_rate == 0.5
    assert metrics.human_modification_rate == 0.5
    assert metrics.human_rejection_rate == 0.0
    assert metrics.verifier_contradiction_count == 1
    assert metrics.verifier_contradiction_rate == 0.5
    assert metrics.policy_compliance_rate == 1.0
    assert metrics.freshness_compliance_rate == 0.5
    assert metrics.critical_error_count == 1
    assert metrics.critical_error_rate == 0.5
    assert metrics.recovery_applicable_count == 1
    assert metrics.recovery_success_rate == 1.0
    assert metrics.sla_met_rate == 0.5
    assert metrics.incident_count == 1

    db_session.refresh(profile)
    assert profile.autonomy_level == original_autonomy
    assert profile.board_ceiling == "A3"


def test_i2_rejects_foreign_tenant_source_and_separates_profile_revisions(
    db_session: Session,
) -> None:
    _position(db_session)
    first_profile = _profile(db_session, idempotency_key="i2-revision-v1")
    foreign_source = _activity(db_session, _board_context("tenant-b", "foreign-board"), key="foreign")
    with pytest.raises(OrganizationCommandError):
        _observe(
            db_session,
            _board_context(),
            profile_id=first_profile.id,
            source_activity_id=foreign_source.id,
            idempotency_key="i2-foreign-source",
        )

    v1_source = _activity(db_session, _board_context(), key="v1-observation")
    _observe(
        db_session,
        _board_context(),
        profile_id=first_profile.id,
        source_activity_id=v1_source.id,
        idempotency_key="i2-v1-observation",
    )
    second_profile = _profile(
        db_session,
        idempotency_key="i2-revision-v2",
        expected_profile_sequence=1,
        autonomy_level=AutonomyLevel.A3,
    )
    v2_source = _activity(db_session, _board_context(), key="v2-observation")
    _observe(
        db_session,
        _board_context(),
        profile_id=second_profile.id,
        source_activity_id=v2_source.id,
        idempotency_key="i2-v2-observation",
        human_review_outcome="not_reviewed",
    )

    snapshot = capability_autonomy_evidence_profile_snapshot(
        db_session,
        tenant_key="default",
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope="austria:skilled-worker",
    )
    assert snapshot is not None
    assert snapshot.profile_id == second_profile.id
    assert snapshot.profile_sequence == 2
    assert snapshot.current_autonomy_level == "A3"
    assert snapshot.metrics.qualifying_execution_volume == 1
    assert snapshot.metrics.human_not_reviewed_count == 1
    assert snapshot.metrics.human_acceptance_rate is None
    assert [item.source_activity_id for item in snapshot.observations] == [v2_source.id]

    historical_replay = _observe(
        db_session,
        _board_context(),
        profile_id=first_profile.id,
        source_activity_id=v1_source.id,
        idempotency_key="i2-v1-observation",
    )
    assert historical_replay.profile_id == first_profile.id


def test_i2_transparency_is_board_only_read_only_and_exposes_no_raw_payload(
    client: TestClient,
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _position(db_session)
    profile = _profile(db_session, idempotency_key="i2-api-profile")
    source = _activity(db_session, _board_context(), key="api-observation")
    _observe(
        db_session,
        _board_context(),
        profile_id=profile.id,
        source_activity_id=source.id,
        idempotency_key="i2-api-observation",
    )
    path = (
        f"{BASE}/case_operations_specialist/eligibility.proposal/evidence"
        "?context_scope=austria%3Askilled-worker"
    )
    response = client.get(path)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["profile_id"] == str(profile.id)
    assert body["metrics"]["qualifying_execution_volume"] == 1
    assert body["observations"][0]["source_activity_id"] == str(source.id)
    assert "payload" not in response.text

    denied = raw_client.get(
        path,
        headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator-user"},
    )
    assert denied.status_code == 403
    assert raw_client.post(
        path,
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "board-human"},
        json={"human_review_outcome": "accepted"},
    ).status_code == 405


def test_i2_snapshot_fails_closed_on_source_or_observation_fingerprint_drift(
    db_session: Session,
) -> None:
    _position(db_session)
    profile = _profile(db_session, idempotency_key="i2-drift-profile")
    source = _activity(db_session, _board_context(), key="drift-source")
    observation = _observe(
        db_session,
        _board_context(),
        profile_id=profile.id,
        source_activity_id=source.id,
        idempotency_key="i2-drift-observation",
    )

    source.record_fingerprint = "0" * 64
    db_session.add(source)
    db_session.commit()
    with pytest.raises(AutonomyEvidenceProfileIntegrityError, match="source fingerprint"):
        capability_autonomy_evidence_profile_snapshot(
            db_session,
            tenant_key="default",
            position_key="case_operations_specialist",
            capability_key="eligibility.proposal",
            context_scope="austria:skilled-worker",
        )

    source.record_fingerprint = observation.source_activity_fingerprint
    db_session.add(source)
    db_session.commit()
    observation.human_review_outcome = "rejected"
    db_session.add(observation)
    db_session.commit()
    with pytest.raises(AutonomyEvidenceProfileIntegrityError, match="record fingerprint"):
        capability_autonomy_evidence_profile_snapshot(
            db_session,
            tenant_key="default",
            position_key="case_operations_specialist",
            capability_key="eligibility.proposal",
            context_scope="austria:skilled-worker",
        )
