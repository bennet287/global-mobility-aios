from __future__ import annotations

from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    EligibilityImmuneSystemError,
    eligibility_circuit_status,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    GovernedEligibilityOrchestrationState,
    orchestrate_governed_eligibility,
)
from app.services.organization_eligibility_revision_conflict import (
    ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE,
    ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION,
    ELIGIBILITY_REVISION_CONFLICT_FAILURE_STAGE,
    EligibilityRevisionConflictAttributionError,
    record_attributed_eligibility_revision_conflict,
)
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPreconditionConflict,
    EligibilityRevisionPreconditionStale,
    eligibility_aggregate_key,
    require_eligibility_revision_precondition_current,
    resolve_eligibility_revision_precondition,
)
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_orchestration import (
    _fixture,
    _fresh_work_pair,
    _plan,
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


def _commit_v1_v2(session: Session):
    lead, _, graph, proposal_work, verification_work = _fixture(session)
    first_plan, _, _ = _plan(graph)
    first = orchestrate_governed_eligibility(
        session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-3-base-v1",
        execution_plan=first_plan,
    )
    assert first.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED

    winner_work, winner_verification_work = _fresh_work_pair(
        session,
        graph=graph,
        source_work=proposal_work,
        suffix="h2-3-winner-v2",
    )
    winner_plan, _, _ = _plan(graph)
    winner = orchestrate_governed_eligibility(
        session,
        tenant_key="tenant-a",
        proposal_work_item_id=winner_work.id,
        verification_work_item_id=winner_verification_work.id,
        idempotency_key="h2-3-winner-v2",
        execution_plan=winner_plan,
        expected_eligibility_revision_version=1,
    )
    assert winner.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert winner.revision_id is not None

    next_work, next_verification_work = _fresh_work_pair(
        session,
        graph=graph,
        source_work=winner_work,
        suffix="h2-3-next-operation",
    )
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    return lead, graph, next_work, next_verification_work, winner, aggregate


def _stale_conflict(
    session: Session,
    *,
    lead_id,
    pathway_id,
) -> EligibilityRevisionPreconditionConflict:
    with pytest.raises(EligibilityRevisionPreconditionConflict) as caught:
        resolve_eligibility_revision_precondition(
            session,
            tenant_key="tenant-a",
            lead_id=lead_id,
            pathway_id=pathway_id,
            expected_revision_version=1,
        )
    return caught.value


def test_h2_3_pre_egress_stale_reassessment_is_attributed_without_provider_egress(
    db_session: Session,
) -> None:
    _, graph, proposal_work, verification_work, winner, aggregate = _commit_v1_v2(db_session)
    stale_plan, producer, verifier = _plan(graph)
    key = "h2-3-stale-pre-egress"
    incident_key = f"{key}:revision-conflict"

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="revision precondition conflicted",
    ):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key=key,
            execution_plan=stale_plan,
            expected_eligibility_revision_version=1,
        )

    assert producer.calls == []
    assert verifier.calls == []
    attribution_key = (
        f"immune:eligibility:{aggregate}:revision-conflict-attribution:{incident_key}"
    )
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
    assert attribution.activity_type == ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE
    assert attribution.source_object_version == ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION
    assert attribution.causation_activity_id is None
    assert attribution.correlation_key is None
    payload = transparency_activity_record(attribution).payload
    assert payload["attribution_contract"] == ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_SCHEMA_VERSION
    assert payload["incident_kind"] == EligibilityImmuneIncidentKind.REVISION_CONFLICT.value
    assert payload["failure_stage"] == ELIGIBILITY_REVISION_CONFLICT_FAILURE_STAGE
    assert payload["conflict_basis"] == "superseded_expected_revision"
    assert payload["expected_revision_version"] == 1
    assert payload["observed_current_revision_id"] == str(winner.revision_id)
    assert payload["observed_current_revision_version"] == 2
    assert payload["observed_current_lifecycle_status"] == "active"
    assert payload["provider_egress_occurred"] is False
    assert payload["control_effect"] == "observation_only"
    assert payload["authority_effect"] == "none"
    assert payload["recurrence_policy_applied"] is False
    assert isinstance(payload["attribution_fingerprint"], str)
    assert len(payload["attribution_fingerprint"]) == 64
    incident_payload = transparency_activity_record(incident).payload
    assert incident.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
    assert incident_payload["severity"] == "warning"
    assert incident_payload["automatic_circuit_action"] == "none"
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h2_3_missing_and_future_expectations_do_not_emit_revision_conflicts(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    initial_plan, _, _ = _plan(graph)
    first = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-3-non-conflict-base",
        execution_plan=initial_plan,
    )
    assert first.revision_id is not None
    proposal_work, verification_work = _fresh_work_pair(
        db_session,
        graph=graph,
        source_work=proposal_work,
        suffix="h2-3-invalid-precondition",
    )
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )

    missing_plan, missing_producer, missing_verifier = _plan(graph)
    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h2-3-missing-expectation",
            execution_plan=missing_plan,
        )
    assert missing_producer.calls == []
    assert missing_verifier.calls == []

    future_plan, future_producer, future_verifier = _plan(graph)
    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h2-3-future-expectation",
            execution_plan=future_plan,
            expected_eligibility_revision_version=2,
        )
    assert future_producer.calls == []
    assert future_verifier.calls == []

    conflicts = [
        row
        for row in _immune_activities(db_session, aggregate_key=aggregate)
        if row.activity_type == ELIGIBILITY_REVISION_CONFLICT_ATTRIBUTION_ACTIVITY_TYPE
        or (
            row.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
            and transparency_activity_record(row).payload.get("incident_kind")
            == EligibilityImmuneIncidentKind.REVISION_CONFLICT.value
        )
    ]
    assert conflicts == []


def test_h2_3_exact_stale_submission_replays_one_atomic_pair(db_session: Session) -> None:
    _, graph, proposal_work, verification_work, _, aggregate = _commit_v1_v2(db_session)
    key = "h2-3-stale-replay"
    incident_key = f"{key}:revision-conflict"
    attribution_key = (
        f"immune:eligibility:{aggregate}:revision-conflict-attribution:{incident_key}"
    )
    incident_activity_key = f"immune:eligibility:{aggregate}:incident:{incident_key}"

    for _ in range(2):
        plan, producer, verifier = _plan(graph)
        with pytest.raises(
            GovernedEligibilityOrchestrationIntegrityError,
            match="revision precondition conflicted",
        ):
            orchestrate_governed_eligibility(
                db_session,
                tenant_key="tenant-a",
                proposal_work_item_id=proposal_work.id,
                verification_work_item_id=verification_work.id,
                idempotency_key=key,
                execution_plan=plan,
                expected_eligibility_revision_version=1,
            )
        assert producer.calls == []
        assert verifier.calls == []

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
    matching = [
        row
        for row in _immune_activities(db_session, aggregate_key=aggregate)
        if row.activity_key in {attribution_key, incident_activity_key}
    ]
    assert [row.id for row in matching] == [attribution.id, incident.id]


def test_h2_3_repeated_revision_conflicts_remain_observation_only(db_session: Session) -> None:
    _, graph, proposal_work, verification_work, _, aggregate = _commit_v1_v2(db_session)

    for index in range(1, 5):
        plan, producer, verifier = _plan(graph)
        with pytest.raises(GovernedEligibilityOrchestrationIntegrityError):
            orchestrate_governed_eligibility(
                db_session,
                tenant_key="tenant-a",
                proposal_work_item_id=proposal_work.id,
                verification_work_item_id=verification_work.id,
                idempotency_key=f"h2-3-repeated-{index}",
                execution_plan=plan,
                expected_eligibility_revision_version=1,
            )
        assert producer.calls == []
        assert verifier.calls == []
        assert eligibility_circuit_status(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
        ).state is EligibilityCircuitState.CLOSED


def test_h2_3_post_provider_revalidation_collapses_conflict_to_generic_stale(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    initial_plan, _, _ = _plan(graph)
    first = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-3-revalidation-v1",
        execution_plan=initial_plan,
    )
    assert first.revision_id is not None
    precondition = resolve_eligibility_revision_precondition(
        db_session,
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
        expected_revision_version=1,
    )

    proposal_work, verification_work = _fresh_work_pair(
        db_session,
        graph=graph,
        source_work=proposal_work,
        suffix="h2-3-revalidation-v2",
    )
    winner_plan, _, _ = _plan(graph)
    winner = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-3-revalidation-v2",
        execution_plan=winner_plan,
        expected_eligibility_revision_version=1,
    )
    assert winner.revision_id is not None

    with pytest.raises(EligibilityRevisionPreconditionStale) as caught:
        require_eligibility_revision_precondition_current(
            db_session,
            precondition=precondition,
            lead_id=lead.id,
            pathway_id=graph["pathway"].id,
        )
    assert not isinstance(caught.value, EligibilityRevisionPreconditionConflict)


def test_h2_3_attribution_rolls_back_when_paired_incident_cannot_persist(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lead, graph, _, _, _, aggregate = _commit_v1_v2(db_session)
    conflict = _stale_conflict(
        db_session,
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    before_ids = [row.id for row in _immune_activities(db_session, aggregate_key=aggregate)]

    from app.services import organization_eligibility_revision_conflict as revision_conflict

    def fail_paired_incident(*args, **kwargs):
        raise EligibilityImmuneSystemError("synthetic H.2.3 paired incident failure")

    monkeypatch.setattr(
        revision_conflict,
        "record_eligibility_immune_incident",
        fail_paired_incident,
    )

    with pytest.raises(
        EligibilityImmuneSystemError,
        match="synthetic H.2.3 paired incident failure",
    ):
        revision_conflict.record_attributed_eligibility_revision_conflict(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="h2-3-atomic-rollback",
            conflict=conflict,
            summary="Synthetic stale reassessment for H.2.3 rollback proof.",
        )

    after_ids = [row.id for row in _immune_activities(db_session, aggregate_key=aggregate)]
    assert after_ids == before_ids


def test_h2_3_replay_rejects_changed_conflict_snapshot(db_session: Session) -> None:
    lead, graph, _, _, _, aggregate = _commit_v1_v2(db_session)
    conflict = _stale_conflict(
        db_session,
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    incident_key = "h2-3-conflict-snapshot-drift"
    summary = "Synthetic stale reassessment for H.2.3 identity-drift proof."

    first = record_attributed_eligibility_revision_conflict(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=incident_key,
        conflict=conflict,
        summary=summary,
    )
    before_ids = [row.id for row in _immune_activities(db_session, aggregate_key=aggregate)]
    drifted = EligibilityRevisionPreconditionConflict(
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        expected_revision_version=1,
        current_revision_id=uuid4(),
        current_revision_version=3,
    )

    with pytest.raises(
        EligibilityRevisionConflictAttributionError,
        match="idempotency key conflicts with persisted attribution",
    ):
        record_attributed_eligibility_revision_conflict(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=incident_key,
            conflict=drifted,
            summary=summary,
        )

    after = _immune_activities(db_session, aggregate_key=aggregate)
    assert [row.id for row in after] == before_ids
    assert first.attribution_activity.id in before_ids
    assert first.incident.incident_activity.id in before_ids
