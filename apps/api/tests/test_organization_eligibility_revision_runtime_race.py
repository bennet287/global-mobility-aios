from __future__ import annotations

import os
from dataclasses import replace

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity
from app.models.eligibility_revision import EligibilityAssessmentRevision
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
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPostResolutionAdvance,
    eligibility_aggregate_key,
)
from app.services.organization_eligibility_revision_runtime_race import (
    ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_ACTIVITY_TYPE,
    ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_SCHEMA_VERSION,
    ELIGIBILITY_REVISION_RUNTIME_RACE_FAILURE_STAGE,
    EligibilityRevisionRuntimeRaceAttributionError,
    record_attributed_eligibility_revision_runtime_race,
)
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_orchestration import _fixture, _plan


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


def _runtime_race_activities(
    session: Session,
    *,
    aggregate_key: str,
) -> list[OrganizationActivity]:
    return list(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.tenant_key == "tenant-a",
                OrganizationActivity.source_object_type == "eligibility_aggregate",
                OrganizationActivity.source_object_id == aggregate_key,
                OrganizationActivity.activity_type
                == ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_ACTIVITY_TYPE,
            )
            .order_by(OrganizationActivity.stream_sequence)
        ).all()
    )


def _commit_v1(session: Session):
    lead, _, graph, proposal_work, verification_work = _fixture(session)
    plan, _, _ = _plan(graph)
    first = orchestrate_governed_eligibility(
        session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-4-base-v1",
        execution_plan=plan,
    )
    assert first.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert first.revision_id is not None
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    return lead, graph, proposal_work, verification_work, first, aggregate


def _commit_v1_v2(session: Session):
    lead, graph, proposal_work, verification_work, first, aggregate = _commit_v1(session)
    plan, _, _ = _plan(graph)
    second = orchestrate_governed_eligibility(
        session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-4-base-v2",
        execution_plan=plan,
        expected_eligibility_revision_version=1,
    )
    assert second.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert second.revision_id is not None
    return lead, graph, proposal_work, verification_work, first, second, aggregate


def _race_snapshot(
    session: Session,
    *,
    first_revision_id,
    second_revision_id,
    aggregate_key: str,
) -> EligibilityRevisionPostResolutionAdvance:
    first = session.get(EligibilityAssessmentRevision, first_revision_id)
    second = session.get(EligibilityAssessmentRevision, second_revision_id)
    assert first is not None and second is not None
    assert first.lifecycle_status == "superseded"
    assert second.lifecycle_status == "active"
    return EligibilityRevisionPostResolutionAdvance(
        tenant_key="tenant-a",
        aggregate_key=aggregate_key,
        expected_revision_version=first.version,
        resolved_revision_id=first.id,
        resolved_revision_version=first.version,
        observed_current_revision_id=second.id,
        observed_current_revision_version=second.version,
    )


def test_h2_4_revision_advance_during_producer_runtime_is_attributed_before_verifier(
    db_session: Session,
) -> None:
    _, graph, proposal_work, verification_work, first, aggregate = _commit_v1(db_session)
    stale_plan, stale_producer, stale_verifier = _plan(graph)
    winner: dict[str, object] = {}

    def commit_winner() -> None:
        winner_plan, _, _ = _plan(graph)
        result = orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h2-4-runtime-winner-v2",
            execution_plan=winner_plan,
            expected_eligibility_revision_version=1,
        )
        assert result.revision_id is not None
        winner["revision_id"] = result.revision_id

    stale_producer.on_complete = commit_winner
    key = "h2-4-post-producer-stale"
    incident_key = f"{key}:revision-runtime-race"

    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="revision advanced during producer runtime",
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

    assert len(stale_producer.calls) == 1
    assert stale_verifier.calls == []
    assert winner.get("revision_id") is not None
    revisions = list(
        db_session.exec(
            select(EligibilityAssessmentRevision)
            .where(
                EligibilityAssessmentRevision.tenant_key == "tenant-a",
                EligibilityAssessmentRevision.aggregate_key == aggregate,
            )
            .order_by(EligibilityAssessmentRevision.version)
        ).all()
    )
    assert [revision.version for revision in revisions] == [1, 2]
    assert revisions[0].id == first.revision_id
    assert revisions[0].lifecycle_status == "superseded"
    assert revisions[1].id == winner["revision_id"]
    assert revisions[1].lifecycle_status == "active"

    attribution_key = (
        f"immune:eligibility:{aggregate}:revision-runtime-race-attribution:{incident_key}"
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
    assert attribution.activity_type == ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_ACTIVITY_TYPE
    assert attribution.source_object_version == ELIGIBILITY_REVISION_RUNTIME_RACE_ATTRIBUTION_SCHEMA_VERSION
    payload = transparency_activity_record(attribution).payload
    assert payload["failure_stage"] == ELIGIBILITY_REVISION_RUNTIME_RACE_FAILURE_STAGE
    assert payload["conflict_basis"] == "canonical_revision_advanced_during_producer_runtime"
    assert payload["expected_revision_version"] == 1
    assert payload["resolved_revision_id"] == str(first.revision_id)
    assert payload["resolved_revision_version"] == 1
    assert payload["observed_current_revision_id"] == str(winner["revision_id"])
    assert payload["observed_current_revision_version"] == 2
    assert payload["producer_egress_occurred"] is True
    assert payload["verifier_egress_occurred"] is False
    assert payload["canonical_effect_committed"] is False
    assert payload["execution_role"] == "producer"
    assert payload["position_key"] == stale_plan.producer_position_key
    assert payload["runtime_profile_key"] == stale_plan.producer_runtime_profile.profile_key
    assert payload["provider_key"] == stale_plan.producer_runtime_profile.provider_key
    assert payload["model_key"] == stale_plan.producer_runtime_profile.model_key
    assert payload["control_effect"] == "observation_only"
    assert payload["authority_effect"] == "none"
    assert payload["recurrence_policy_applied"] is False
    assert payload["automatic_retry_applied"] is False
    assert len(payload["runtime_profile_fingerprint"]) == 64
    assert len(payload["attribution_fingerprint"]) == 64

    incident_payload = transparency_activity_record(incident).payload
    assert incident.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
    assert incident_payload["incident_kind"] == EligibilityImmuneIncidentKind.REVISION_CONFLICT.value
    assert incident_payload["severity"] == "warning"
    assert incident_payload["automatic_circuit_action"] == "none"
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h2_4_concurrent_initial_creation_is_not_runtime_race_attribution(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    stale_plan, stale_producer, stale_verifier = _plan(graph)

    def commit_initial_winner() -> None:
        winner_plan, _, _ = _plan(graph)
        winner = orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h2-4-initial-winner",
            execution_plan=winner_plan,
        )
        assert winner.revision_id is not None

    stale_producer.on_complete = commit_initial_winner
    with pytest.raises(GovernedEligibilityOrchestrationIntegrityError, match="proposal stage failed"):
        orchestrate_governed_eligibility(
            db_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="h2-4-initial-race-loser",
            execution_plan=stale_plan,
        )

    assert len(stale_producer.calls) == 1
    assert stale_verifier.calls == []
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    assert _runtime_race_activities(db_session, aggregate_key=aggregate) == []


def test_h2_4_exact_replay_reuses_pair_and_runtime_identity_drift_fails_closed(
    db_session: Session,
) -> None:
    _, graph, _, _, first, second, aggregate = _commit_v1_v2(db_session)
    plan, _, _ = _plan(graph)
    race = _race_snapshot(
        db_session,
        first_revision_id=first.revision_id,
        second_revision_id=second.revision_id,
        aggregate_key=aggregate,
    )
    key = "h2-4-direct-replay"
    summary = "Synthetic H.2.4 post-producer revision race."

    first_record = record_attributed_eligibility_revision_runtime_race(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=key,
        race=race,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary=summary,
    )
    second_record = record_attributed_eligibility_revision_runtime_race(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=key,
        race=race,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary=summary,
    )
    assert second_record.attribution_activity.id == first_record.attribution_activity.id
    assert second_record.incident.incident_activity.id == first_record.incident.incident_activity.id
    assert second_record.incident.replayed is True

    drifted_runtime = replace(
        plan.producer_runtime_profile,
        model_key="different-model",
    )
    with pytest.raises(
        EligibilityRevisionRuntimeRaceAttributionError,
        match="idempotency key conflicts",
    ):
        record_attributed_eligibility_revision_runtime_race(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=key,
            race=race,
            position_key=plan.producer_position_key,
            runtime_profile=drifted_runtime,
            summary=summary,
        )


def test_h2_4_pair_rolls_back_when_incident_persistence_fails(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, graph, _, _, first, second, aggregate = _commit_v1_v2(db_session)
    plan, _, _ = _plan(graph)
    race = _race_snapshot(
        db_session,
        first_revision_id=first.revision_id,
        second_revision_id=second.revision_id,
        aggregate_key=aggregate,
    )
    before_ids = [row.id for row in _runtime_race_activities(db_session, aggregate_key=aggregate)]

    from app.services import organization_eligibility_revision_runtime_race as runtime_race

    def fail_paired_incident(*args, **kwargs):
        raise EligibilityImmuneSystemError("synthetic H.2.4 paired incident failure")

    monkeypatch.setattr(runtime_race, "record_eligibility_immune_incident", fail_paired_incident)
    with pytest.raises(EligibilityImmuneSystemError, match="synthetic H.2.4 paired incident failure"):
        runtime_race.record_attributed_eligibility_revision_runtime_race(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="h2-4-atomic-rollback",
            race=race,
            position_key=plan.producer_position_key,
            runtime_profile=plan.producer_runtime_profile,
            summary="Synthetic H.2.4 rollback proof.",
        )

    after_ids = [row.id for row in _runtime_race_activities(db_session, aggregate_key=aggregate)]
    assert after_ids == before_ids


def test_h2_4_torn_pair_fails_closed_and_repeated_observations_do_not_open_circuit(
    db_session: Session,
) -> None:
    _, graph, _, _, first, second, aggregate = _commit_v1_v2(db_session)
    plan, _, _ = _plan(graph)
    race = _race_snapshot(
        db_session,
        first_revision_id=first.revision_id,
        second_revision_id=second.revision_id,
        aggregate_key=aggregate,
    )

    for index in range(4):
        record_attributed_eligibility_revision_runtime_race(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=f"h2-4-observation-{index}",
            race=race,
            position_key=plan.producer_position_key,
            runtime_profile=plan.producer_runtime_profile,
            summary=f"Synthetic H.2.4 observation {index}.",
        )
        assert eligibility_circuit_status(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
        ).state is EligibilityCircuitState.CLOSED

    torn = record_attributed_eligibility_revision_runtime_race(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="h2-4-torn-pair",
        race=race,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary="Synthetic H.2.4 torn-pair proof.",
    )
    db_session.delete(torn.incident.incident_activity)
    db_session.commit()

    with pytest.raises(
        EligibilityRevisionRuntimeRaceAttributionError,
        match="must exist as one atomic pair",
    ):
        record_attributed_eligibility_revision_runtime_race(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="h2-4-torn-pair",
            race=race,
            position_key=plan.producer_position_key,
            runtime_profile=plan.producer_runtime_profile,
            summary="Synthetic H.2.4 torn-pair proof.",
        )


@pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL H.2.4 race requires GMAI_TEST_DATABASE_URL",
)
def test_h2_4_postgres_cross_session_revision_advances_during_producer_runtime(
    db_session: Session,
) -> None:
    _, graph, proposal_work, verification_work, first, aggregate = _commit_v1(db_session)
    engine = db_session.get_bind()
    stale_plan, stale_producer, stale_verifier = _plan(graph)
    winner: dict[str, object] = {}

    def commit_winner_cross_session() -> None:
        with Session(engine) as winner_session:
            winner_plan, _, _ = _plan(graph)
            result = orchestrate_governed_eligibility(
                winner_session,
                tenant_key="tenant-a",
                proposal_work_item_id=proposal_work.id,
                verification_work_item_id=verification_work.id,
                idempotency_key="h2-4-postgres-winner-v2",
                execution_plan=winner_plan,
                expected_eligibility_revision_version=1,
            )
            assert result.revision_id is not None
            winner["revision_id"] = result.revision_id

    stale_producer.on_complete = commit_winner_cross_session
    key = "h2-4-postgres-stale"
    with pytest.raises(
        GovernedEligibilityOrchestrationIntegrityError,
        match="revision advanced during producer runtime",
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

    assert len(stale_producer.calls) == 1
    assert stale_verifier.calls == []
    assert winner.get("revision_id") is not None
    db_session.expire_all()
    current = list(
        db_session.exec(
            select(EligibilityAssessmentRevision)
            .where(
                EligibilityAssessmentRevision.tenant_key == "tenant-a",
                EligibilityAssessmentRevision.aggregate_key == aggregate,
            )
            .order_by(EligibilityAssessmentRevision.version)
        ).all()
    )
    assert [revision.version for revision in current] == [1, 2]
    assert current[0].id == first.revision_id
    assert current[1].id == winner["revision_id"]
    assert len(_runtime_race_activities(db_session, aggregate_key=aggregate)) == 1
