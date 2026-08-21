from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, RiskTier
from app.models.autonomy_profile import CapabilityAutonomyEvidence, CapabilityAutonomyProfile
from app.models.domain import OrganizationActivity, OrganizationActorType, OrganizationPosition, now_utc
from app.services.organization_activity import append_activity
from app.services.organization_autonomy_profile import (
    AutonomyProfileIntegrityError,
    capability_autonomy_profile_snapshot,
    establish_capability_autonomy_profile,
)
from app.services.organization_command import (
    AuthorityDenied,
    IdempotencyConflict,
    InvalidHumanActor,
    OrganizationCommandContext,
)


BASE = "/api/v1/organization/transparency/autonomy/profiles"


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
        position_key="case_operations_specialist",
        authority_level="L2",
    )


def _position(session: Session, key: str = "case_operations_specialist") -> OrganizationPosition:
    position = OrganizationPosition(
        position_key=key,
        title="Case Operations Specialist",
        department="operations",
        authority_level="L2",
        created_by="pytest",
    )
    session.add(position)
    session.commit()
    session.refresh(position)
    return position


def _evidence_activity(
    session: Session,
    context: OrganizationCommandContext,
    *,
    key: str,
) -> OrganizationActivity:
    return append_activity(
        session,
        context,
        activity_key=f"i1-evidence:{key}",
        stream_key="i1-evidence",
        activity_class="operational",
        activity_type="organization.capability_outcome.observed.v1",
        title=f"Governed capability outcome {key}",
        summary="Synthetic governed outcome used only to prove deterministic I.1 evidence lineage.",
        source_object_type="governed_capability_outcome",
        source_object_id=key,
        occurred_at=now_utc(),
        payload={"outcome": "verified", "test_contract": "v1.3-i.1"},
    )


def _establish(
    session: Session,
    context: OrganizationCommandContext,
    *,
    evidence_activity_ids: tuple[UUID, ...],
    idempotency_key: str,
    autonomy_level: AutonomyLevel = AutonomyLevel.A2,
    board_ceiling: AutonomyLevel = AutonomyLevel.A3,
    expected_profile_sequence: int | None = None,
) -> CapabilityAutonomyProfile:
    return establish_capability_autonomy_profile(
        session,
        context,
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope="austria:skilled-worker",
        autonomy_level=autonomy_level,
        board_ceiling=board_ceiling,
        authority_requirement="L2",
        risk_ceiling=RiskTier.R3,
        evidence_policy_version="autonomy-evidence-v1",
        evidence_activity_ids=evidence_activity_ids,
        idempotency_key=idempotency_key,
        expected_profile_sequence=expected_profile_sequence,
    )


def test_i1_profile_is_board_only_ceiling_bounded_idempotent_and_append_only(
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    first_evidence = _evidence_activity(db_session, board, key="first")
    second_evidence = _evidence_activity(db_session, board, key="second")

    with pytest.raises(InvalidHumanActor):
        _establish(
            db_session,
            _agent_context(),
            evidence_activity_ids=(first_evidence.id,),
            idempotency_key="i1-agent-self-promotion",
        )

    with pytest.raises(AuthorityDenied, match="exceeds the Human Board ceiling"):
        _establish(
            db_session,
            board,
            evidence_activity_ids=(first_evidence.id,),
            idempotency_key="i1-above-ceiling",
            autonomy_level=AutonomyLevel.A4,
            board_ceiling=AutonomyLevel.A3,
        )

    first = _establish(
        db_session,
        board,
        evidence_activity_ids=(first_evidence.id,),
        idempotency_key="i1-profile-v1",
    )
    original_fingerprint = first.record_fingerprint
    original_created_at = first.created_at
    replay = _establish(
        db_session,
        board,
        evidence_activity_ids=(first_evidence.id,),
        idempotency_key="i1-profile-v1",
    )
    assert replay.id == first.id

    with pytest.raises(IdempotencyConflict):
        _establish(
            db_session,
            board,
            evidence_activity_ids=(first_evidence.id,),
            idempotency_key="i1-profile-v1",
            autonomy_level=AutonomyLevel.A3,
        )

    second = _establish(
        db_session,
        board,
        evidence_activity_ids=(first_evidence.id, second_evidence.id),
        idempotency_key="i1-profile-v2",
        autonomy_level=AutonomyLevel.A3,
        expected_profile_sequence=1,
    )
    assert second.profile_sequence == 2
    assert second.supersedes_profile_id == first.id

    db_session.expire_all()
    preserved_first = db_session.get(CapabilityAutonomyProfile, first.id)
    assert preserved_first is not None
    assert preserved_first.record_fingerprint == original_fingerprint
    assert preserved_first.created_at == original_created_at

    snapshot = capability_autonomy_profile_snapshot(
        db_session,
        tenant_key="default",
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope="austria:skilled-worker",
    )
    assert snapshot is not None
    assert snapshot.current_profile_id == second.id
    assert snapshot.current_autonomy_level == "A3"
    assert [revision.profile_sequence for revision in snapshot.revisions] == [1, 2]
    assert [revision.lifecycle_status for revision in snapshot.revisions] == ["superseded", "current"]
    assert snapshot.revisions[0].board_ceiling == "A3"
    assert snapshot.revisions[0].authority_requirement == "L2"
    assert snapshot.revisions[0].risk_ceiling == "R3"
    assert [item.source_activity_id for item in snapshot.revisions[1].evidence] == sorted(
        [first_evidence.id, second_evidence.id],
        key=str,
    )

    profile_rows = list(
        db_session.exec(
            select(CapabilityAutonomyProfile).where(
                CapabilityAutonomyProfile.tenant_key == "default"
            )
        ).all()
    )
    evidence_rows = list(
        db_session.exec(
            select(CapabilityAutonomyEvidence).where(
                CapabilityAutonomyEvidence.tenant_key == "default"
            )
        ).all()
    )
    assert len(profile_rows) == 2
    assert len(evidence_rows) == 3


def test_i1_transparency_is_board_only_read_only_and_exposes_no_raw_payload(
    client: TestClient,
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    evidence = _evidence_activity(db_session, board, key="api")
    profile = _establish(
        db_session,
        board,
        evidence_activity_ids=(evidence.id,),
        idempotency_key="i1-api-profile",
    )
    path = f"{BASE}/case_operations_specialist/eligibility.proposal?context_scope=austria%3Askilled-worker"

    response = client.get(path)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["current_profile_id"] == str(profile.id)
    assert body["current_autonomy_level"] == "A2"
    assert body["revisions"][0]["board_ceiling"] == "A3"
    assert body["revisions"][0]["evidence"][0]["source_activity_id"] == str(evidence.id)
    assert "payload" not in response.text

    denied = raw_client.get(
        path,
        headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator-user"},
    )
    assert denied.status_code == 403
    assert raw_client.post(
        path,
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "board-human"},
        json={"autonomy_level": "A5"},
    ).status_code == 405


def test_i1_transparency_fails_closed_on_evidence_fingerprint_drift(
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    evidence = _evidence_activity(db_session, board, key="drift")
    _establish(
        db_session,
        board,
        evidence_activity_ids=(evidence.id,),
        idempotency_key="i1-drift-profile",
    )

    evidence.record_fingerprint = "0" * 64
    db_session.add(evidence)
    db_session.commit()

    with pytest.raises(AutonomyProfileIntegrityError, match="fingerprint drifted"):
        capability_autonomy_profile_snapshot(
            db_session,
            tenant_key="default",
            position_key="case_operations_specialist",
            capability_key="eligibility.proposal",
            context_scope="austria:skilled-worker",
        )
