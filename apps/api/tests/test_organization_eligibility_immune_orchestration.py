from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models.domain import OrganizationActivity
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.routers.organization_eligibility import governed_eligibility_execution_plan
from app.routers.organization_records import organization_command_context
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    eligibility_circuit_status,
    record_eligibility_immune_incident,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    GovernedEligibilityOrchestrationState,
    orchestrate_governed_eligibility,
)
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_governance_kernel import GatewayOutcome
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_orchestration import (
    _fixture,
    _human_context,
    _plan,
)


def _aggregate(*, lead, graph) -> str:
    return eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )


def _open_critical_circuit(
    session: Session,
    *,
    aggregate_key: str,
    incident_key: str,
) -> None:
    result = record_eligibility_immune_incident(
        session,
        tenant_key="tenant-a",
        aggregate_key=aggregate_key,
        incident_key=incident_key,
        kind=EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
        summary="Canonical eligibility aggregate failed an H.1 integrity check.",
    )
    assert result.circuit_status.state is EligibilityCircuitState.OPEN


def test_h1_open_circuit_blocks_fresh_g4_before_any_provider_call(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    aggregate = _aggregate(lead=lead, graph=graph)
    _open_critical_circuit(
        db_session,
        aggregate_key=aggregate,
        incident_key="h1-g4-preflight-open",
    )
    plan, producer, verifier = _plan(graph)

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="circuit is open",
    ):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-g4-blocked-before-egress",
            execution_plan=plan,
        )

    assert producer.calls == []
    assert verifier.calls == []


def test_h1_open_circuit_for_different_aggregate_does_not_block_case(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    unrelated = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=uuid4(),
    )
    _open_critical_circuit(
        db_session,
        aggregate_key=unrelated,
        incident_key="h1-unrelated-aggregate-open",
    )
    plan, producer, verifier = _plan(graph)

    result = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h1-g4-unrelated-circuit",
        execution_plan=plan,
    )

    assert result.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert result.gateway_outcome == GatewayOutcome.AUTO_EXECUTE.value
    assert len(producer.calls) == 1
    assert len(verifier.calls) == 1


def test_h1_open_circuit_does_not_block_historical_committed_effect_replay(
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)
    first = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h1-g4-historical-replay",
        execution_plan=plan,
    )
    assert first.revision_id is not None
    revision = db_session.get(EligibilityAssessmentRevision, first.revision_id)
    assert revision is not None

    _open_critical_circuit(
        db_session,
        aggregate_key=revision.aggregate_key,
        incident_key="h1-open-after-canonical-effect",
    )
    producer.calls.clear()
    verifier.calls.clear()

    replay = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h1-g4-historical-replay",
        execution_plan=plan,
    )

    assert replay.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert replay.gateway_outcome == GatewayOutcome.IDEMPOTENT_REPLAY.value
    assert replay.replayed is True
    assert replay.revision_id == first.revision_id
    assert producer.calls == []
    assert verifier.calls == []


def test_h1_http_open_circuit_returns_conflict_before_provider_egress(
    client: TestClient,
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    _open_critical_circuit(
        db_session,
        aggregate_key=_aggregate(lead=lead, graph=graph),
        incident_key="h1-http-open",
    )
    plan, producer, verifier = _plan(graph)
    app.dependency_overrides[governed_eligibility_execution_plan] = lambda: plan
    app.dependency_overrides[organization_command_context] = lambda: _human_context()
    try:
        response = client.post(
            "/api/v1/organization/eligibility/orchestrate",
            json={
                "proposal_work_item_id": str(proposal_work.id),
                "verification_work_item_id": str(verification_work.id),
                "idempotency_key": "h1-http-blocked-before-egress",
            },
        )
    finally:
        app.dependency_overrides.pop(governed_eligibility_execution_plan, None)
        app.dependency_overrides.pop(organization_command_context, None)

    assert response.status_code == 409, response.text
    assert response.json() == {
        "detail": "Governed eligibility orchestration could not proceed with current canonical state."
    }
    assert producer.calls == []
    assert verifier.calls == []


def test_h1_verifier_disagreement_emits_warning_incident_without_opening_circuit(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    aggregate = _aggregate(lead=lead, graph=graph)
    plan, producer, verifier = _plan(
        graph,
        verifier_conclusion="supports_potential_ineligibility",
    )
    key = "h1-observe-verifier-disagreement"

    result = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key=key,
        execution_plan=plan,
    )

    assert result.state is GovernedEligibilityOrchestrationState.VERIFICATION_DISAGREES
    assert result.verification_activity_id is not None
    assert result.canonical_effect_committed is False
    assert len(producer.calls) == 1
    assert len(verifier.calls) == 1

    incident = db_session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == "tenant-a",
            OrganizationActivity.activity_key
            == f"immune:eligibility:{aggregate}:incident:{key}:verifier-disagreement",
        )
    ).first()
    assert incident is not None
    assert incident.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
    assert incident.causation_activity_id == result.verification_activity_id
    payload = transparency_activity_record(incident).payload
    assert payload["incident_kind"] == EligibilityImmuneIncidentKind.VERIFIER_DISAGREEMENT.value
    assert payload["severity"] == "warning"
    assert payload["automatic_circuit_action"] == "none"
    assert payload["authority_effect"] == "restrict_only"
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h1_insufficient_basis_is_not_mislabeled_as_verifier_disagreement(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    aggregate = _aggregate(lead=lead, graph=graph)
    plan, _, _ = _plan(
        graph,
        verifier_conclusion="insufficient_basis",
    )
    key = "h1-insufficient-basis-not-disagreement"

    result = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key=key,
        execution_plan=plan,
    )

    assert result.state is GovernedEligibilityOrchestrationState.VERIFICATION_INSUFFICIENT_BASIS
    incidents = list(
        db_session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.tenant_key == "tenant-a",
                OrganizationActivity.source_object_type == "eligibility_aggregate",
                OrganizationActivity.source_object_id == aggregate,
                OrganizationActivity.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
            )
        ).all()
    )
    assert incidents == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED
