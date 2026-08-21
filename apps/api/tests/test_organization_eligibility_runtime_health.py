from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity
from app.services.organization_agent_runtime import runtime_profile_fingerprint
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    eligibility_circuit_status,
    record_eligibility_immune_incident,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    orchestrate_governed_eligibility,
)
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_eligibility_runtime_health import (
    ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_ACTIVITY_TYPE,
    ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION,
    EligibilityRuntimeExecutionRole,
    EligibilityRuntimeHealthAttributionError,
    record_attributed_eligibility_runtime_health_incident,
)
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_immune_orchestration import _FailingProvider
from tests.test_organization_eligibility_orchestration import _fixture, _plan


def _aggregate(tenant_key: str = "tenant-a") -> str:
    return eligibility_aggregate_key(
        tenant_key=tenant_key,
        lead_id=uuid4(),
        pathway_id=uuid4(),
    )


def _activity(
    session: Session,
    *,
    tenant_key: str,
    activity_key: str,
) -> OrganizationActivity | None:
    return session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.activity_key == activity_key,
        )
    ).first()


def _assert_runtime_attribution(
    activity: OrganizationActivity,
    *,
    aggregate_key: str,
    incident_activity_key: str,
    role: EligibilityRuntimeExecutionRole,
    failure_stage: str,
    position_key: str,
    runtime_profile,
) -> None:
    assert activity.activity_type == ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_ACTIVITY_TYPE
    assert activity.source_object_type == "eligibility_aggregate"
    assert activity.source_object_id == aggregate_key
    assert activity.source_object_version == ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION
    record = transparency_activity_record(activity)
    payload = record.payload
    assert payload["attribution_contract"] == ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION_SCHEMA_VERSION
    assert payload["aggregate_key"] == aggregate_key
    assert payload["incident_activity_key"] == incident_activity_key
    assert payload["incident_kind"] == EligibilityImmuneIncidentKind.RUNTIME_HEALTH_FAILURE.value
    assert payload["execution_role"] == role.value
    assert payload["failure_stage"] == failure_stage
    assert payload["position_key"] == position_key
    assert payload["runtime_profile_key"] == runtime_profile.profile_key
    assert payload["runtime_profile_version"] == runtime_profile.profile_version
    assert payload["runtime_profile_fingerprint"] == runtime_profile_fingerprint(runtime_profile)
    assert payload["runtime_class"] == runtime_profile.runtime_class.value
    assert payload["adapter_key"] == runtime_profile.adapter_key
    assert payload["provider_key"] == runtime_profile.provider_key
    assert payload["model_key"] == runtime_profile.model_key
    assert payload["independence_group"] == runtime_profile.independence_group
    assert payload["control_effect"] == "observation_only"
    assert payload["authority_effect"] == "none"
    assert payload["provider_health_policy_applied"] is False
    assert isinstance(payload["attribution_fingerprint"], str)
    assert len(payload["attribution_fingerprint"]) == 64


def test_h2_2_producer_runtime_failure_is_attributed_to_trusted_execution_plan(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    plan, _, verifier = _plan(graph)
    failing = _FailingProvider(
        name=plan.producer_runtime_profile.provider_key,
        model=plan.producer_runtime_profile.model_key or "",
    )
    plan = replace(plan, producer_provider=failing)
    key = "h2-2-producer-runtime-attribution"
    incident_key = f"{key}:producer-runtime-health"

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="proposal runtime failed",
    ):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key=key,
            execution_plan=plan,
        )

    assert len(failing.calls) == 1
    assert verifier.calls == []
    attribution_key = f"immune:eligibility:{aggregate}:runtime-attribution:{incident_key}"
    incident_activity_key = f"immune:eligibility:{aggregate}:incident:{incident_key}"
    attribution = _activity(
        db_session,
        tenant_key="tenant-a",
        activity_key=attribution_key,
    )
    incident = _activity(
        db_session,
        tenant_key="tenant-a",
        activity_key=incident_activity_key,
    )
    assert attribution is not None
    assert incident is not None
    assert attribution.causation_activity_id is None
    assert incident.causation_activity_id is None
    _assert_runtime_attribution(
        attribution,
        aggregate_key=aggregate,
        incident_activity_key=incident_activity_key,
        role=EligibilityRuntimeExecutionRole.PRODUCER,
        failure_stage="e2_proposal_runtime",
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
    )
    incident_payload = transparency_activity_record(incident).payload
    assert incident_payload["severity"] == "warning"
    assert incident_payload["automatic_circuit_action"] == "none"
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h2_2_verifier_runtime_failure_is_attributed_and_proposal_linked(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    plan, producer, _ = _plan(graph)
    failing = _FailingProvider(
        name=plan.verifier_runtime_profile.provider_key,
        model=plan.verifier_runtime_profile.model_key or "",
    )
    plan = replace(plan, verifier_provider=failing)
    key = "h2-2-verifier-runtime-attribution"
    incident_key = f"{key}:verifier-runtime-health"

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="verification runtime failed",
    ):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key=key,
            execution_plan=plan,
        )

    assert len(producer.calls) == 1
    assert len(failing.calls) == 1
    attribution_key = f"immune:eligibility:{aggregate}:runtime-attribution:{incident_key}"
    incident_activity_key = f"immune:eligibility:{aggregate}:incident:{incident_key}"
    attribution = _activity(
        db_session,
        tenant_key="tenant-a",
        activity_key=attribution_key,
    )
    incident = _activity(
        db_session,
        tenant_key="tenant-a",
        activity_key=incident_activity_key,
    )
    assert attribution is not None
    assert incident is not None
    assert attribution.causation_activity_id is not None
    assert attribution.causation_activity_id == incident.causation_activity_id
    cause = db_session.get(OrganizationActivity, attribution.causation_activity_id)
    assert cause is not None
    assert cause.activity_key.startswith("governance:attempt:")
    assert attribution.correlation_key == cause.correlation_key
    _assert_runtime_attribution(
        attribution,
        aggregate_key=aggregate,
        incident_activity_key=incident_activity_key,
        role=EligibilityRuntimeExecutionRole.VERIFIER,
        failure_stage="g1_independent_verification_runtime",
        position_key=plan.verifier_position_key,
        runtime_profile=plan.verifier_runtime_profile,
    )
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h2_2_runtime_attribution_pair_is_idempotent(db_session: Session) -> None:
    _, _, graph, _, _ = _fixture(db_session)
    plan, _, _ = _plan(graph)
    aggregate = _aggregate()
    kwargs = {
        "tenant_key": "tenant-a",
        "aggregate_key": aggregate,
        "incident_key": "runtime-pair-replay",
        "execution_role": EligibilityRuntimeExecutionRole.PRODUCER,
        "position_key": plan.producer_position_key,
        "runtime_profile": plan.producer_runtime_profile,
        "summary": "Synthetic producer runtime failure for H.2.2 replay proof.",
    }

    first = record_attributed_eligibility_runtime_health_incident(db_session, **kwargs)
    second = record_attributed_eligibility_runtime_health_incident(db_session, **kwargs)

    assert second.attribution_activity.id == first.attribution_activity.id
    assert second.incident.incident_activity.id == first.incident.incident_activity.id
    assert second.incident.replayed is True
    assert second.incident.circuit_opened is False
    assert second.incident.circuit_status.state is EligibilityCircuitState.CLOSED


def test_h2_2_legacy_unattributed_runtime_incident_fails_closed_for_pairing(
    db_session: Session,
) -> None:
    _, _, graph, _, _ = _fixture(db_session)
    plan, _, _ = _plan(graph)
    aggregate = _aggregate()
    record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="legacy-runtime-warning",
        kind=EligibilityImmuneIncidentKind.RUNTIME_HEALTH_FAILURE,
        summary="Legacy runtime warning without H.2.2 attribution.",
    )

    with pytest.raises(
        EligibilityRuntimeHealthAttributionError,
        match="must exist as one atomic pair",
    ):
        record_attributed_eligibility_runtime_health_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="legacy-runtime-warning",
            execution_role=EligibilityRuntimeExecutionRole.PRODUCER,
            position_key=plan.producer_position_key,
            runtime_profile=plan.producer_runtime_profile,
            summary="Legacy runtime warning without H.2.2 attribution.",
        )


def test_h2_2_repeated_runtime_health_failures_remain_observation_only(
    db_session: Session,
) -> None:
    _, _, graph, _, _ = _fixture(db_session)
    plan, _, _ = _plan(graph)
    aggregate = _aggregate()

    for index in range(1, 5):
        result = record_attributed_eligibility_runtime_health_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=f"runtime-observation-{index}",
            execution_role=(
                EligibilityRuntimeExecutionRole.PRODUCER
                if index % 2
                else EligibilityRuntimeExecutionRole.VERIFIER
            ),
            position_key=(
                plan.producer_position_key if index % 2 else plan.verifier_position_key
            ),
            runtime_profile=(
                plan.producer_runtime_profile
                if index % 2
                else plan.verifier_runtime_profile
            ),
            summary="Repeated runtime failure remains observation-only in H.2.2.",
        )
        assert result.incident.incident_activity.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
        assert result.incident.circuit_opened is False
        assert result.incident.circuit_status.state is EligibilityCircuitState.CLOSED

    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED
