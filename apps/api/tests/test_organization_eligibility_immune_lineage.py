from __future__ import annotations

import json
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import EligibilityAssessment, OrganizationActivity
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    close_eligibility_circuit,
    eligibility_circuit_status,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    orchestrate_governed_eligibility,
)
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_orchestration import (
    _fixture,
    _human_context,
    _plan,
)


def _incident_payloads(
    session: Session,
    *,
    aggregate_key: str,
) -> list[dict[str, object]]:
    rows = list(
        session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.tenant_key == "tenant-a",
                OrganizationActivity.source_object_type == "eligibility_aggregate",
                OrganizationActivity.source_object_id == aggregate_key,
                OrganizationActivity.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
            )
        ).all()
    )
    return [transparency_activity_record(row).payload for row in rows]


def _committed_v1(session: Session, *, idempotency_key: str = "h1-lineage-v1"):
    _, _, graph, proposal_work, verification_work = _fixture(session)
    plan, producer, verifier = _plan(graph)
    result = orchestrate_governed_eligibility(
        session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key=idempotency_key,
        execution_plan=plan,
    )
    assert result.revision_id is not None
    revision = session.get(EligibilityAssessmentRevision, result.revision_id)
    assert revision is not None
    return result, revision, graph, proposal_work, verification_work, plan, producer, verifier


def _critical_durable_incidents(
    session: Session,
    *,
    aggregate_key: str,
) -> list[dict[str, object]]:
    return [
        payload
        for payload in _incident_payloads(session, aggregate_key=aggregate_key)
        if payload["incident_kind"] == EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY.value
        and payload["severity"] == "critical"
        and payload["automatic_circuit_action"] == "open"
    ]


def _mutate_lineage_identity(
    session: Session,
    *,
    revision: EligibilityAssessmentRevision,
    mutation: str,
) -> None:
    activity_id = {
        "verification_type": revision.verification_activity_id,
        "floor_type": revision.verification_floor_activity_id,
        "governance_record_kind": revision.governance_activity_id,
        "semantic_type": revision.semantic_activity_id,
    }[mutation]
    assert activity_id is not None
    activity = session.get(OrganizationActivity, activity_id)
    assert activity is not None

    if mutation == "verification_type":
        activity.activity_type = "verification.unrelated.v1"
    elif mutation == "floor_type":
        activity.activity_type = "governance.unrelated.floor.v1"
    elif mutation == "semantic_type":
        activity.activity_type = "organization.unrelated.semantic.v1"
    else:
        payload = json.loads(activity.payload_json or "{}")
        payload["governance_record_kind"] = "unrelated_governance_record"
        activity.payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    session.add(activity)
    session.commit()


def test_h1_torn_durable_lineage_opens_exact_aggregate_before_fresh_provider_egress(
    db_session: Session,
) -> None:
    (
        _,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session)
    aggregate = revision.aggregate_key

    revision.semantic_activity_id = uuid4()
    db_session.add(revision)
    db_session.commit()
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="circuit is open",
    ):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-lineage-blocked-after-tear",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    status = eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    )
    assert status.state is EligibilityCircuitState.OPEN
    durable = _critical_durable_incidents(db_session, aggregate_key=aggregate)
    assert len(durable) == 1
    assert durable[0]["authority_effect"] == "restrict_only"


def test_h1_unrepaired_lineage_reopens_after_human_recovery(
    db_session: Session,
) -> None:
    (
        _,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session)
    aggregate = revision.aggregate_key
    revision.semantic_activity_id = uuid4()
    db_session.add(revision)
    db_session.commit()
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="circuit is open"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-lineage-first-detection",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    closed = close_eligibility_circuit(
        db_session,
        context=_human_context(role="admin"),
        aggregate_key=aggregate,
        recovery_key="h1-lineage-premature-recovery",
        reason="Human admin recovery attempted before the synthetic lineage defect was repaired.",
    )
    assert closed.state is EligibilityCircuitState.CLOSED

    producer.calls.clear()
    verifier.calls.clear()
    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="circuit is open"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-lineage-second-detection",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.OPEN
    durable = _critical_durable_incidents(db_session, aggregate_key=aggregate)
    assert len(durable) == 2


def test_h1_invalid_canonical_revision_lifecycle_opens_aggregate_circuit(
    db_session: Session,
) -> None:
    (
        _,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session)
    aggregate = revision.aggregate_key
    revision.lifecycle_status = "superseded"
    db_session.add(revision)
    db_session.commit()
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="circuit is open"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-invalid-lifecycle",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.OPEN
    aggregate_incidents = [
        payload
        for payload in _incident_payloads(db_session, aggregate_key=aggregate)
        if payload["incident_kind"] == EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY.value
    ]
    assert len(aggregate_incidents) == 1
    assert aggregate_incidents[0]["severity"] == "critical"
    assert aggregate_incidents[0]["automatic_circuit_action"] == "open"


def test_h1_assessment_identity_drift_opens_before_fresh_provider_egress(
    db_session: Session,
) -> None:
    (
        _,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session)
    aggregate = revision.aggregate_key
    assessment = db_session.get(EligibilityAssessment, revision.assessment_id)
    assert assessment is not None
    assessment.profile_version += 1
    db_session.add(assessment)
    db_session.commit()
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="circuit is open"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-assessment-identity-drift",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.OPEN
    assert len(_critical_durable_incidents(db_session, aggregate_key=aggregate)) == 1


def test_h1_semantic_revision_identity_drift_opens_before_fresh_provider_egress(
    db_session: Session,
) -> None:
    (
        _,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session)
    aggregate = revision.aggregate_key
    assert revision.semantic_activity_id is not None
    semantic = db_session.get(OrganizationActivity, revision.semantic_activity_id)
    assert semantic is not None
    semantic.source_object_version = "999"
    db_session.add(semantic)
    db_session.commit()
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="circuit is open"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-semantic-identity-drift",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.OPEN
    assert len(_critical_durable_incidents(db_session, aggregate_key=aggregate)) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "verification_type",
        "floor_type",
        "governance_record_kind",
        "semantic_type",
    ],
)
def test_h1_adversarial_activity_identity_drift_opens_critical_circuit_before_provider_egress(
    db_session: Session,
    mutation: str,
) -> None:
    (
        _,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session, idempotency_key=f"h1-adversarial-base-{mutation}")
    aggregate = revision.aggregate_key
    _mutate_lineage_identity(db_session, revision=revision, mutation=mutation)
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="circuit is open"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key=f"h1-adversarial-fresh-{mutation}",
            execution_plan=plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.OPEN
    assert len(_critical_durable_incidents(db_session, aggregate_key=aggregate)) == 1


def test_g4_historical_replay_uses_canonical_lineage_validator_before_provider_egress(
    db_session: Session,
) -> None:
    key = "g4-shared-lineage-validator"
    (
        first,
        revision,
        _,
        proposal_work,
        verification_work,
        plan,
        producer,
        verifier,
    ) = _committed_v1(db_session, idempotency_key=key)
    assert first.revision_id == revision.id
    _mutate_lineage_identity(db_session, revision=revision, mutation="semantic_type")
    producer.calls.clear()
    verifier.calls.clear()

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="durable lineage validation",
    ):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key=key,
            execution_plan=plan,
        )

    assert producer.calls == []
    assert verifier.calls == []


def test_h1_unresolvable_scope_fails_without_fabricating_circuit_target(
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, producer, verifier = _plan(graph)
    proposal_work.source_object_id = str(uuid4())
    db_session.add(proposal_work)
    db_session.commit()

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="preflight could not resolve canonical scope",
    ):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h1-unresolvable-no-fabricated-target",
            execution_plan=plan,
        )

    assert producer.calls == []
    assert verifier.calls == []
    incidents = list(
        db_session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.tenant_key == "tenant-a",
                OrganizationActivity.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
            )
        ).all()
    )
    assert incidents == []
