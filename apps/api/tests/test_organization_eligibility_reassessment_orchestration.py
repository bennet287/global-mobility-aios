from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.routers.organization_eligibility import governed_eligibility_execution_plan
from app.routers.organization_records import organization_command_context
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    GovernedEligibilityOrchestrationState,
    orchestrate_governed_eligibility,
)
from app.services.organization_governance_kernel import GatewayOutcome
from tests.test_organization_eligibility_orchestration import (
    _fixture,
    _human_context,
    _plan,
)


def _run(
    session: Session,
    *,
    proposal_work_item_id,
    verification_work_item_id,
    key: str,
    plan,
    expected_revision: int | None = None,
):
    return orchestrate_governed_eligibility(
        session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work_item_id,
        verification_work_item_id=verification_work_item_id,
        idempotency_key=key,
        execution_plan=plan,
        expected_eligibility_revision_version=expected_revision,
    )


def test_g5_g4_orchestrates_explicit_v1_to_v2_supersession(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)

    first = _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-v1",
        plan=plan,
    )
    second = _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-v2",
        plan=plan,
        expected_revision=1,
    )

    assert first.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert second.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert first.gateway_outcome == GatewayOutcome.AUTO_EXECUTE.value
    assert second.gateway_outcome == GatewayOutcome.AUTO_EXECUTE.value
    assert first.revision_id is not None and second.revision_id is not None
    assert first.revision_id != second.revision_id
    assert len(producer.calls) == 2
    assert len(verifier.calls) == 2

    revision1 = db_session.get(EligibilityAssessmentRevision, first.revision_id)
    revision2 = db_session.get(EligibilityAssessmentRevision, second.revision_id)
    assert revision1 is not None and revision2 is not None
    assert revision1.version == 1
    assert revision1.lifecycle_status == "superseded"
    assert revision1.supersedes_revision_id is None
    assert revision2.version == 2
    assert revision2.lifecycle_status == "active"
    assert revision2.supersedes_revision_id == revision1.id
    assert revision2.aggregate_key == revision1.aggregate_key

    active = list(
        db_session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.tenant_key == "tenant-a",
                EligibilityAssessmentRevision.aggregate_key == revision2.aggregate_key,
                EligibilityAssessmentRevision.lifecycle_status == "active",
            )
        ).all()
    )
    assert [row.id for row in active] == [revision2.id]


def test_g5_g4_historical_v1_replay_after_v2_skips_models(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)
    first = _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-history-v1",
        plan=plan,
    )
    _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-history-v2",
        plan=plan,
        expected_revision=1,
    )
    producer.calls.clear()
    verifier.calls.clear()

    replay = _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-history-v1",
        plan=plan,
    )

    assert replay.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert replay.gateway_outcome == GatewayOutcome.IDEMPOTENT_REPLAY.value
    assert replay.replayed is True
    assert replay.revision_id == first.revision_id
    assert producer.calls == []
    assert verifier.calls == []


def test_g5_g4_replay_rejects_different_revision_expectation_before_models(
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)
    _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-replay-conflict",
        plan=plan,
    )
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="replay eligibility revision expectation",
    ):
        _run(
            db_session,
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            key="g5-g4-replay-conflict",
            plan=plan,
            expected_revision=1,
        )

    assert producer.calls == []
    assert verifier.calls == []


def test_g5_g4_stale_new_reassessment_fails_before_models(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)
    _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-stale-v1",
        plan=plan,
    )
    _run(
        db_session,
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        key="g5-g4-stale-v2",
        plan=plan,
        expected_revision=1,
    )
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="revision precondition conflicted",
    ):
        _run(
            db_session,
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            key="g5-g4-stale-v3-attempt",
            plan=plan,
            expected_revision=1,
        )

    assert producer.calls == []
    assert verifier.calls == []


def test_g5_http_explicit_revision_precondition_drives_v2(
    client: TestClient,
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(graph)
    app.dependency_overrides[governed_eligibility_execution_plan] = lambda: plan
    app.dependency_overrides[organization_command_context] = lambda: _human_context()
    try:
        first = client.post(
            "/api/v1/organization/eligibility/orchestrate",
            json={
                "proposal_work_item_id": str(proposal_work.id),
                "verification_work_item_id": str(verification_work.id),
                "idempotency_key": "g5-http-v1",
            },
        )
        second = client.post(
            "/api/v1/organization/eligibility/orchestrate",
            json={
                "proposal_work_item_id": str(proposal_work.id),
                "verification_work_item_id": str(verification_work.id),
                "idempotency_key": "g5-http-v2",
                "expected_eligibility_revision_version": 1,
            },
        )
        invalid = client.post(
            "/api/v1/organization/eligibility/orchestrate",
            json={
                "proposal_work_item_id": str(proposal_work.id),
                "verification_work_item_id": str(verification_work.id),
                "idempotency_key": "g5-http-invalid-version",
                "expected_eligibility_revision_version": 0,
            },
        )
    finally:
        app.dependency_overrides.pop(governed_eligibility_execution_plan, None)
        app.dependency_overrides.pop(organization_command_context, None)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert invalid.status_code == 422
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["canonical_effect_committed"] is True
    assert second_payload["canonical_effect_committed"] is True
    assert first_payload["revision_id"] != second_payload["revision_id"]

    revision1 = db_session.get(
        EligibilityAssessmentRevision,
        UUID(first_payload["revision_id"]),
    )
    revision2 = db_session.get(
        EligibilityAssessmentRevision,
        UUID(second_payload["revision_id"]),
    )
    assert revision1 is not None and revision2 is not None
    assert revision1.lifecycle_status == "superseded"
    assert revision2.version == 2
    assert revision2.lifecycle_status == "active"
    assert revision2.supersedes_revision_id == revision1.id
