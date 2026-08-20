from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models.domain import EligibilityAssessment, OrganizationActorType, OrganizationPosition
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.routers.organization_eligibility import governed_eligibility_execution_plan
from app.routers.organization_records import organization_command_context
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_eligibility_orchestration import (
    ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
    GovernedEligibilityExecutionPlan,
    GovernedEligibilityOrchestrationIntegrityError,
    GovernedEligibilityOrchestrationState,
    orchestrate_governed_eligibility,
)
from app.services.organization_governance_kernel import GatewayOutcome
from tests.test_organization_eligibility_verification_floor import _authority_with
from tests.test_organization_independent_eligibility_verification import (
    FakeProvider,
    _authority_graph,
    _case,
    _position,
    _proposer_output,
    _runtime,
    _verifier_output,
    _verifier_runtime,
    _work,
)


def _fixture(session: Session):
    _position(
        session,
        position_key="austria_mobility_specialist",
        title="Austria Mobility Specialist",
        version=20,
    )
    _position(
        session,
        position_key="austria_independent_verifier",
        title="Austria Independent Verifier",
        version=11,
    )
    lead, profile = _case(session)
    graph = _authority_graph(session)
    proposal_work = _work(
        session,
        position_key="austria_mobility_specialist",
        lead=lead,
        profile=profile,
        version=graph["version"],
        title="Orchestrate governed eligibility proposal",
    )
    verification_work = _work(
        session,
        position_key="austria_independent_verifier",
        lead=lead,
        profile=profile,
        version=graph["version"],
        title="Orchestrate independent eligibility verification",
    )
    return lead, profile, graph, proposal_work, verification_work


def _plan(
    graph: dict[str, object],
    *,
    verifier_conclusion: str = "supports_potential_eligibility",
    authority=None,
):
    producer = FakeProvider(
        name="deepseek",
        model="deepseek-reasoner",
        content=_proposer_output(graph),
    )
    verifier = FakeProvider(
        name="openai",
        model="gpt-verifier",
        content=_verifier_output(graph, conclusion=verifier_conclusion),
    )
    plan = GovernedEligibilityExecutionPlan(
        producer_position_key="austria_mobility_specialist",
        producer_runtime_profile=_runtime(
            profile_key="orchestration-producer",
            provider_key="deepseek",
            model_key="deepseek-reasoner",
            independence_group="orchestration-producer-group",
        ),
        producer_provider=producer,
        verifier_position_key="austria_independent_verifier",
        verifier_runtime_profile=_verifier_runtime(),
        verifier_provider=verifier,
        authority=authority or _authority_with(),
    )
    return plan, producer, verifier


def _human_context(*, role: str = "admin") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="tenant-a",
        actor_id="pytest-human",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="pytest-human",
        role=role,
        department="operations",
        position_key="board" if role == "admin" else "organization_operator",
        authority_level="L4" if role == "admin" else "L2",
        request_id="g4-pytest-request",
    )


def test_g4_orchestrates_accepted_vertical_to_first_canonical_effect(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)

    result = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="g4-complete",
        execution_plan=plan,
    )

    assert result.schema_version == ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION
    assert result.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert result.gateway_outcome == GatewayOutcome.AUTO_EXECUTE.value
    assert result.canonical_effect_committed is True
    assert result.replayed is False
    assert result.assessment_id is not None
    assert result.revision_id is not None
    assert result.semantic_activity_id is not None
    assert result.verification_activity_id is not None
    assert result.verification_floor_activity_id is not None
    assert len(producer.calls) == 1
    assert len(verifier.calls) == 1

    revision = db_session.get(EligibilityAssessmentRevision, result.revision_id)
    assessment = db_session.get(EligibilityAssessment, result.assessment_id)
    assert revision is not None and assessment is not None
    assert revision.assessment_id == assessment.id
    assert revision.version == 1
    assert assessment.status == "potentially_eligible"


def test_g4_post_commit_retry_resolves_durable_effect_without_model_calls(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)
    first = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="g4-replay",
        execution_plan=plan,
    )
    producer.calls.clear()
    verifier.calls.clear()

    second = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="g4-replay",
        execution_plan=plan,
    )

    assert second.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert second.gateway_outcome == GatewayOutcome.IDEMPOTENT_REPLAY.value
    assert second.replayed is True
    assert second.assessment_id == first.assessment_id
    assert second.revision_id == first.revision_id
    assert producer.calls == []
    assert verifier.calls == []


def test_g4_a1_stops_after_verified_floor_without_canonical_effect(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(
        graph,
        authority=_authority_with(autonomy="A1"),
    )
    before = len(list(db_session.exec(select(EligibilityAssessment)).all()))

    result = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="g4-a1",
        execution_plan=plan,
    )

    assert result.state is GovernedEligibilityOrchestrationState.AWAITING_AUTHORITY
    assert result.gateway_outcome == GatewayOutcome.REVIEW_REQUIRED.value
    assert result.canonical_effect_committed is False
    assert result.assessment_id is None
    assert len(list(db_session.exec(select(EligibilityAssessment)).all())) == before


def test_g4_verifier_disagreement_never_reaches_floor_or_effect(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(
        graph,
        verifier_conclusion="supports_potential_ineligibility",
    )

    result = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="g4-disagreement",
        execution_plan=plan,
    )

    assert result.state is GovernedEligibilityOrchestrationState.VERIFICATION_DISAGREES
    assert result.verification_activity_id is not None
    assert result.verification_floor_activity_id is None
    assert result.assessment_id is None
    assert result.canonical_effect_committed is False


def test_g4_rejects_untrusted_or_nonindependent_execution_plan_before_runtime(db_session: Session) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)
    bad_verifier_runtime = _verifier_runtime(
        provider_key="deepseek",
        model_key="deepseek-reasoner",
        independence_group="orchestration-producer-group",
    )
    bad_plan = replace(
        plan,
        verifier_runtime_profile=bad_verifier_runtime,
        verifier_provider=FakeProvider(
            name="deepseek",
            model="deepseek-reasoner",
            content=_verifier_output(graph),
        ),
    )

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="g4-invalid-plan",
            execution_plan=bad_plan,
        )
    assert producer.calls == []
    assert verifier.calls == []


def test_g4_http_route_fails_closed_without_server_execution_policy(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/organization/eligibility/orchestrate",
        json={
            "proposal_work_item_id": str(uuid4()),
            "verification_work_item_id": str(uuid4()),
            "idempotency_key": "g4-unconfigured",
        },
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Governed eligibility execution policy is not configured."}


def test_g4_http_route_executes_only_with_trusted_dependency_plan(
    client: TestClient,
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(graph)
    app.dependency_overrides[governed_eligibility_execution_plan] = lambda: plan
    app.dependency_overrides[organization_command_context] = lambda: _human_context()
    try:
        response = client.post(
            "/api/v1/organization/eligibility/orchestrate",
            json={
                "proposal_work_item_id": str(proposal_work.id),
                "verification_work_item_id": str(verification_work.id),
                "idempotency_key": "g4-http-complete",
            },
        )
    finally:
        app.dependency_overrides.pop(governed_eligibility_execution_plan, None)
        app.dependency_overrides.pop(organization_command_context, None)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["state"] == GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED.value
    assert payload["canonical_effect_committed"] is True
    assert payload["assessment_id"] is not None
    assert payload["revision_id"] is not None


def test_g4_http_request_cannot_supply_runtime_provider_or_authority_fields(
    client: TestClient,
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(graph)
    app.dependency_overrides[governed_eligibility_execution_plan] = lambda: plan
    app.dependency_overrides[organization_command_context] = lambda: _human_context()
    try:
        response = client.post(
            "/api/v1/organization/eligibility/orchestrate",
            json={
                "proposal_work_item_id": str(proposal_work.id),
                "verification_work_item_id": str(verification_work.id),
                "idempotency_key": "g4-forged-request",
                "producer_position_key": "board",
                "provider": "attacker-provider",
                "autonomy_level": "A5",
            },
        )
    finally:
        app.dependency_overrides.pop(governed_eligibility_execution_plan, None)
        app.dependency_overrides.pop(organization_command_context, None)

    assert response.status_code == 422


def test_g4_http_route_rejects_non_operator_human_initiator(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(graph)
    app.dependency_overrides[governed_eligibility_execution_plan] = lambda: plan
    app.dependency_overrides[organization_command_context] = lambda: _human_context(role="reviewer")
    try:
        response = raw_client.post(
            "/api/v1/organization/eligibility/orchestrate",
            headers={"X-GMAI-Role": "reviewer", "X-GMAI-User": "pytest-reviewer"},
            json={
                "proposal_work_item_id": str(proposal_work.id),
                "verification_work_item_id": str(verification_work.id),
                "idempotency_key": "g4-reviewer-denied",
            },
        )
    finally:
        app.dependency_overrides.pop(governed_eligibility_execution_plan, None)
        app.dependency_overrides.pop(organization_command_context, None)

    assert response.status_code == 403
    assert response.json() == {"detail": "Organization action is not permitted."}


def test_g4_plan_authority_tenant_and_actor_are_not_replaceable_by_human_initiator(
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(graph)
    foreign = replace(plan, authority=replace(plan.authority, actor_id="pytest-human"))
    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="g4-human-cannot-become-actor",
            execution_plan=foreign,
        )
