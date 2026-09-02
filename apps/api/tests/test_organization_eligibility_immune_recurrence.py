from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationActorType
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE,
    ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
    ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    ELIGIBILITY_IMMUNE_RECURRENCE_POLICY_VERSION,
    ELIGIBILITY_VERIFIER_DISAGREEMENT_RECURRENCE_THRESHOLD,
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    EligibilityImmuneIncidentSeverity,
    close_eligibility_circuit,
    eligibility_circuit_status,
    record_eligibility_immune_incident,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    orchestrate_governed_eligibility,
)
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_transparency import transparency_activity_record
from tests.test_organization_eligibility_orchestration import _fixture, _plan


_DISAGREEMENT_SUMMARY = (
    "Independent eligibility verification disagreed with the proposer during H.2.1 recurrence proof."
)


def _aggregate(tenant_key: str = "tenant-a") -> str:
    return eligibility_aggregate_key(
        tenant_key=tenant_key,
        lead_id=uuid4(),
        pathway_id=uuid4(),
    )


def _admin_context(tenant_key: str = "tenant-a") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id="board-admin",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="board-admin",
        role="admin",
        department="Governance",
    )


def _activities(session: Session, *, aggregate_key: str) -> list[OrganizationActivity]:
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


def _record_disagreement(
    session: Session,
    *,
    aggregate_key: str,
    key: str,
):
    return record_eligibility_immune_incident(
        session,
        tenant_key="tenant-a",
        aggregate_key=aggregate_key,
        incident_key=key,
        kind=EligibilityImmuneIncidentKind.VERIFIER_DISAGREEMENT,
        summary=_DISAGREEMENT_SUMMARY,
    )


def test_h2_1_third_verifier_disagreement_opens_restrictive_circuit(
    db_session: Session,
) -> None:
    aggregate = _aggregate()

    first = _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-1")
    second = _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-2")

    assert first.severity is EligibilityImmuneIncidentSeverity.WARNING
    assert second.severity is EligibilityImmuneIncidentSeverity.WARNING
    assert first.circuit_status.state is EligibilityCircuitState.CLOSED
    assert second.circuit_status.state is EligibilityCircuitState.CLOSED
    assert first.circuit_opened is False
    assert second.circuit_opened is False

    third = _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-3")

    assert third.severity is EligibilityImmuneIncidentSeverity.WARNING
    assert third.circuit_opened is True
    assert third.circuit_status.state is EligibilityCircuitState.OPEN
    assert third.circuit_status.cause_incident_activity_id == third.incident_activity.id

    incident_payload = transparency_activity_record(third.incident_activity).payload
    assert incident_payload["automatic_circuit_action"] == "none"
    assert incident_payload["recurrence_policy"] == ELIGIBILITY_IMMUNE_RECURRENCE_POLICY_VERSION
    assert (
        incident_payload["recurrence_threshold"]
        == ELIGIBILITY_VERIFIER_DISAGREEMENT_RECURRENCE_THRESHOLD
    )

    activities = _activities(db_session, aggregate_key=aggregate)
    assert [row.activity_type for row in activities] == [
        ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
        ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
        ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
        ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
    ]
    opened = activities[-1]
    assert opened.causation_activity_id == third.incident_activity.id
    open_payload = transparency_activity_record(opened).payload
    assert open_payload["trigger"] == "warning_recurrence"
    assert open_payload["incident_kind"] == EligibilityImmuneIncidentKind.VERIFIER_DISAGREEMENT.value
    assert open_payload["recurrence_count"] == 3
    assert open_payload["recurrence_threshold"] == 3
    assert open_payload["recurrence_epoch_boundary_activity_id"] is None
    assert open_payload["authority_effect"] == "restrict_only"


def test_h2_1_other_warning_kinds_do_not_advance_disagreement_threshold(
    db_session: Session,
) -> None:
    aggregate = _aggregate()
    _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-1")
    _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-2")

    for index in range(1, 5):
        result = record_eligibility_immune_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key=f"runtime-{index}",
            kind=EligibilityImmuneIncidentKind.RUNTIME_HEALTH_FAILURE,
            summary="Synthetic runtime-health warning must not count as verifier disagreement.",
        )
        assert result.severity is EligibilityImmuneIncidentSeverity.WARNING
        assert result.circuit_opened is False
        assert result.circuit_status.state is EligibilityCircuitState.CLOSED

    third = _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-3")
    assert third.circuit_opened is True
    assert third.circuit_status.state is EligibilityCircuitState.OPEN


def test_h2_1_threshold_open_is_atomic_with_crossing_incident(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aggregate = _aggregate()
    _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-1")
    _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-2")

    from app.services import organization_eligibility_immune_system as immune

    real_stage = immune.stage_activity
    calls = 0

    def fail_open_stage(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("synthetic H.2.1 recurrence-open staging failure")
        return real_stage(*args, **kwargs)

    monkeypatch.setattr(immune, "stage_activity", fail_open_stage)

    with pytest.raises(RuntimeError, match="recurrence-open staging failure"):
        _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-3")

    activities = _activities(db_session, aggregate_key=aggregate)
    assert [row.activity_type for row in activities] == [
        ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
        ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    ]
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h2_1_threshold_incident_replay_does_not_duplicate_open(db_session: Session) -> None:
    aggregate = _aggregate()
    _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-1")
    _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-2")
    third = _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-3")
    count = len(_activities(db_session, aggregate_key=aggregate))

    replay = _record_disagreement(db_session, aggregate_key=aggregate, key="disagreement-3")

    assert replay.replayed is True
    assert replay.circuit_opened is False
    assert replay.incident_activity.id == third.incident_activity.id
    assert replay.circuit_status.state is EligibilityCircuitState.OPEN
    assert len(_activities(db_session, aggregate_key=aggregate)) == count


def test_h2_1_human_recovery_starts_a_fresh_recurrence_epoch(db_session: Session) -> None:
    aggregate = _aggregate()
    _record_disagreement(db_session, aggregate_key=aggregate, key="epoch-1-disagreement-1")
    _record_disagreement(db_session, aggregate_key=aggregate, key="epoch-1-disagreement-2")
    opened = _record_disagreement(db_session, aggregate_key=aggregate, key="epoch-1-disagreement-3")
    assert opened.circuit_status.state is EligibilityCircuitState.OPEN

    closed = close_eligibility_circuit(
        db_session,
        context=_admin_context(),
        aggregate_key=aggregate,
        recovery_key="h2-1-recovery",
        reason="Human admin reviewed the repeated disagreement and authorized a fresh execution epoch.",
    )
    assert closed.state is EligibilityCircuitState.CLOSED
    assert closed.control_activity_id is not None

    post_one = _record_disagreement(
        db_session,
        aggregate_key=aggregate,
        key="epoch-2-disagreement-1",
    )
    post_two = _record_disagreement(
        db_session,
        aggregate_key=aggregate,
        key="epoch-2-disagreement-2",
    )
    assert post_one.circuit_status.state is EligibilityCircuitState.CLOSED
    assert post_two.circuit_status.state is EligibilityCircuitState.CLOSED

    post_three = _record_disagreement(
        db_session,
        aggregate_key=aggregate,
        key="epoch-2-disagreement-3",
    )
    assert post_three.circuit_status.state is EligibilityCircuitState.OPEN

    opened_activity = _activities(db_session, aggregate_key=aggregate)[-1]
    open_payload = transparency_activity_record(opened_activity).payload
    assert opened_activity.activity_type == ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE
    assert open_payload["recurrence_count"] == 3
    assert open_payload["recurrence_epoch_boundary_activity_id"] == str(closed.control_activity_id)

    controls = [
        row.activity_type
        for row in _activities(db_session, aggregate_key=aggregate)
        if row.activity_type
        in {
            ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
            ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE,
        }
    ]
    assert controls == [
        ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
        ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE,
        ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
    ]


def test_h2_1_recurrence_open_blocks_fresh_g4_before_provider_egress(
    db_session: Session,
) -> None:
    lead, _, graph, proposal_work, verification_work = _fixture(db_session)
    aggregate = eligibility_aggregate_key(
        tenant_key="tenant-a",
        lead_id=lead.id,
        pathway_id=graph["pathway"].id,
    )
    _record_disagreement(db_session, aggregate_key=aggregate, key="preflight-disagreement-1")
    _record_disagreement(db_session, aggregate_key=aggregate, key="preflight-disagreement-2")
    opened = _record_disagreement(
        db_session,
        aggregate_key=aggregate,
        key="preflight-disagreement-3",
    )
    assert opened.circuit_status.state is EligibilityCircuitState.OPEN

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
            idempotency_key="h2-1-blocked-after-recurrence",
            execution_plan=plan,
        )

    assert producer.calls == []
    assert verifier.calls == []


def test_h2_1_postgres_concurrent_threshold_crossing_appends_one_open(
    db_session: Session,
) -> None:
    engine = db_session.get_bind()
    if engine.dialect.name != "postgresql":
        pytest.skip("concurrent stream-lock contract requires PostgreSQL")

    aggregate = _aggregate()
    _record_disagreement(db_session, aggregate_key=aggregate, key="concurrent-disagreement-1")
    _record_disagreement(db_session, aggregate_key=aggregate, key="concurrent-disagreement-2")

    barrier = Barrier(2)

    def record_crossing(key: str):
        with Session(engine) as session:
            barrier.wait(timeout=10)
            return _record_disagreement(session, aggregate_key=aggregate, key=key)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(record_crossing, "concurrent-disagreement-3a"),
            executor.submit(record_crossing, "concurrent-disagreement-3b"),
        ]
        results = [future.result(timeout=30) for future in futures]

    assert sum(1 for result in results if result.circuit_opened) == 1
    assert all(result.circuit_status.state is EligibilityCircuitState.OPEN for result in results)

    db_session.expire_all()
    activities = _activities(db_session, aggregate_key=aggregate)
    incidents = [
        row for row in activities if row.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
    ]
    opens = [
        row for row in activities if row.activity_type == ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE
    ]
    assert len(incidents) == 4
    assert len(opens) == 1
    assert opens[0].causation_activity_id in {result.incident_activity.id for result in results}
