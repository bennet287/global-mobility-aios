from __future__ import annotations

import pytest
from sqlmodel import Session

from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationState,
    orchestrate_governed_eligibility,
)
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPostResolutionAdvance,
)
from app.services.organization_eligibility_revision_runtime_race import (
    EligibilityRevisionRuntimeRaceAttributionError,
    record_attributed_eligibility_revision_runtime_race,
)
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_orchestration import _plan
from tests.test_organization_eligibility_revision_runtime_race import (
    _commit_v1_v2,
    _race_snapshot,
)


def test_h2_4_historical_attribution_replay_survives_later_canonical_supersession(
    db_session: Session,
) -> None:
    _, graph, proposal_work, verification_work, first, second, aggregate = _commit_v1_v2(
        db_session
    )
    plan, _, _ = _plan(graph)
    race = _race_snapshot(
        db_session,
        first_revision_id=first.revision_id,
        second_revision_id=second.revision_id,
        aggregate_key=aggregate,
    )
    incident_key = "h2-4-historical-replay"
    summary = "Synthetic H.2.4 historical replay proof."

    original = record_attributed_eligibility_revision_runtime_race(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=incident_key,
        race=race,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary=summary,
    )

    v3_plan, _, _ = _plan(graph)
    v3 = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-4-later-v3",
        execution_plan=v3_plan,
        expected_eligibility_revision_version=2,
    )
    assert v3.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert v3.revision_id is not None

    replay = record_attributed_eligibility_revision_runtime_race(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=incident_key,
        race=race,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary=summary,
    )

    assert replay.attribution_activity.id == original.attribution_activity.id
    assert replay.incident.incident_activity.id == original.incident.incident_activity.id
    assert replay.incident.replayed is True


def test_h2_4_initial_attribution_survives_observed_revision_superseded_before_persistence(
    db_session: Session,
) -> None:
    _, graph, proposal_work, verification_work, first, second, aggregate = _commit_v1_v2(
        db_session
    )
    plan, _, _ = _plan(graph)
    race = _race_snapshot(
        db_session,
        first_revision_id=first.revision_id,
        second_revision_id=second.revision_id,
        aggregate_key=aggregate,
    )

    v3_plan, _, _ = _plan(graph)
    v3 = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="h2-4-pre-persistence-v3",
        execution_plan=v3_plan,
        expected_eligibility_revision_version=2,
    )
    assert v3.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert v3.revision_id is not None

    observed = db_session.get(EligibilityAssessmentRevision, second.revision_id)
    current = db_session.get(EligibilityAssessmentRevision, v3.revision_id)
    assert observed is not None and observed.lifecycle_status == "superseded"
    assert current is not None and current.lifecycle_status == "active"

    result = record_attributed_eligibility_revision_runtime_race(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="h2-4-pre-persistence-v3-race",
        race=race,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary="Synthetic H.2.4 event-time race persisted after v3 supersession.",
    )

    payload = transparency_activity_record(result.attribution_activity).payload
    assert payload["resolved_revision_id"] == str(first.revision_id)
    assert payload["resolved_revision_version"] == 1
    assert payload["observed_current_revision_id"] == str(second.revision_id)
    assert payload["observed_current_revision_version"] == 2
    assert payload["observed_current_lifecycle_status"] == "active"
    assert payload["producer_egress_occurred"] is True
    assert payload["verifier_egress_occurred"] is False
    assert payload["canonical_effect_committed"] is False

    db_session.refresh(observed)
    db_session.refresh(current)
    assert observed.lifecycle_status == "superseded"
    assert current.lifecycle_status == "active"


def test_h2_4_replay_rejects_changed_revision_snapshot(
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
    incident_key = "h2-4-revision-snapshot-drift"
    summary = "Synthetic H.2.4 revision snapshot drift proof."

    record_attributed_eligibility_revision_runtime_race(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key=incident_key,
        race=race,
        position_key=plan.producer_position_key,
        runtime_profile=plan.producer_runtime_profile,
        summary=summary,
    )

    drifted_race = EligibilityRevisionPostResolutionAdvance(
        tenant_key=race.tenant_key,
        aggregate_key=race.aggregate_key,
        expected_revision_version=race.expected_revision_version,
        resolved_revision_id=race.resolved_revision_id,
        resolved_revision_version=race.resolved_revision_version,
        observed_current_revision_id=race.observed_current_revision_id,
        observed_current_revision_version=race.observed_current_revision_version + 1,
    )
    with pytest.raises(
        EligibilityRevisionRuntimeRaceAttributionError,
        match="idempotency key conflicts",
    ):
        record_attributed_eligibility_revision_runtime_race(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=incident_key,
            race=drifted_race,
            position_key=plan.producer_position_key,
            runtime_profile=plan.producer_runtime_profile,
            summary=summary,
        )
