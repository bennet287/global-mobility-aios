from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity
from app.services.organization_eligibility_immune_system import EligibilityImmuneSystemError
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_eligibility_runtime_failure import (
    EligibilityRuntimeFailureProvenance,
)
from app.services.organization_eligibility_runtime_health import (
    EligibilityRuntimeExecutionRole,
    EligibilityRuntimeHealthAttributionError,
    record_attributed_eligibility_runtime_health_incident,
)
from tests.test_organization_eligibility_orchestration import _fixture, _plan


def _aggregate() -> str:
    return eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=uuid4(),
        pathway_id=uuid4(),
    )


def _immune_activities(session: Session, *, aggregate_key: str) -> list[OrganizationActivity]:
    return list(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.tenant_key == "tenant-a",
                OrganizationActivity.source_object_type == "eligibility_aggregate",
                OrganizationActivity.source_object_id == aggregate_key,
            )
            .order_by(OrganizationActivity.stream_sequence)
        ).all()
    )


def test_h2_2_runtime_attribution_rolls_back_when_paired_incident_cannot_persist(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, graph, _, _ = _fixture(db_session)
    plan, _, _ = _plan(graph)
    aggregate = _aggregate()

    from app.services import organization_eligibility_runtime_health as runtime_health

    def fail_paired_incident(*args, **kwargs):
        raise EligibilityImmuneSystemError("synthetic H.2.2 paired incident failure")

    monkeypatch.setattr(
        runtime_health,
        "record_eligibility_immune_incident",
        fail_paired_incident,
    )

    with pytest.raises(
        EligibilityImmuneSystemError,
        match="synthetic H.2.2 paired incident failure",
    ):
        runtime_health.record_attributed_eligibility_runtime_health_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="runtime-atomic-rollback",
            execution_role=EligibilityRuntimeExecutionRole.PRODUCER,
            position_key=plan.producer_position_key,
            runtime_profile=plan.producer_runtime_profile,
            summary="Synthetic producer runtime failure for atomic rollback proof.",
        )

    assert _immune_activities(db_session, aggregate_key=aggregate) == []


def test_h2_2_runtime_attribution_replay_rejects_trusted_runtime_identity_drift(
    db_session: Session,
) -> None:
    _, _, graph, _, _ = _fixture(db_session)
    plan, _, _ = _plan(graph)
    aggregate = _aggregate()
    incident_key = "runtime-identity-drift"
    summary = "Synthetic producer runtime failure for identity-drift proof."

    first = record_attributed_eligibility_runtime_health_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=incident_key,
        execution_role=EligibilityRuntimeExecutionRole.PRODUCER,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary=summary,
    )
    before_ids = [row.id for row in _immune_activities(db_session, aggregate_key=aggregate)]

    drifted_profile = replace(
        plan.producer_runtime_profile,
        model_key="deepseek-reasoner-drifted",
    )
    with pytest.raises(
        EligibilityRuntimeHealthAttributionError,
        match="idempotency key conflicts with persisted attribution",
    ):
        record_attributed_eligibility_runtime_health_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=incident_key,
            execution_role=EligibilityRuntimeExecutionRole.PRODUCER,
            position_key=plan.producer_position_key,
            runtime_profile=drifted_profile,
            summary=summary,
        )

    after = _immune_activities(db_session, aggregate_key=aggregate)
    assert [row.id for row in after] == before_ids
    assert first.attribution_activity.id == after[0].id
    assert first.incident.incident_activity.id == after[1].id


def test_h2_2_runtime_attribution_replay_rejects_failure_classification_drift(
    db_session: Session,
) -> None:
    _, _, graph, _, _ = _fixture(db_session)
    plan, _, _ = _plan(graph)
    aggregate = _aggregate()
    incident_key = "runtime-failure-classification-drift"
    summary = "Synthetic producer runtime failure classification drift proof."

    first = record_attributed_eligibility_runtime_health_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=incident_key,
        execution_role=EligibilityRuntimeExecutionRole.PRODUCER,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary=summary,
        failure_provenance=(
            EligibilityRuntimeFailureProvenance.provider_transport()
        ),
    )
    before_ids = [
        row.id
        for row in _immune_activities(
            db_session,
            aggregate_key=aggregate,
        )
    ]

    with pytest.raises(
        EligibilityRuntimeHealthAttributionError,
        match="idempotency key conflicts with persisted attribution",
    ):
        record_attributed_eligibility_runtime_health_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=incident_key,
            execution_role=EligibilityRuntimeExecutionRole.PRODUCER,
            position_key=plan.producer_position_key,
            runtime_profile=plan.producer_runtime_profile,
            summary=summary,
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.provider_response_contract()
            ),
        )

    after = _immune_activities(db_session, aggregate_key=aggregate)
    assert [row.id for row in after] == before_ids
    assert first.attribution_activity.id == after[0].id
    assert first.incident.incident_activity.id == after[1].id
