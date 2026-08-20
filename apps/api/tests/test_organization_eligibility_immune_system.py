from __future__ import annotations

from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationActorType
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_eligibility_immune_system import (
    ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE,
    ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
    ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    EligibilityCircuitOpen,
    EligibilityCircuitRecoveryError,
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    EligibilityImmuneIncidentSeverity,
    EligibilityImmuneSystemError,
    close_eligibility_circuit,
    eligibility_circuit_status,
    eligibility_immune_system_context,
    record_eligibility_immune_incident,
    require_eligibility_circuit_closed,
)
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_transparency import transparency_activity_record


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


def _activities(session: Session, *, tenant_key: str, aggregate_key: str):
    return list(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.tenant_key == tenant_key,
                OrganizationActivity.source_object_type == "eligibility_aggregate",
                OrganizationActivity.source_object_id == aggregate_key,
            )
            .order_by(OrganizationActivity.stream_sequence)
        ).all()
    )


def test_h1_eligibility_circuit_is_closed_without_control_activity(db_session: Session) -> None:
    aggregate = _aggregate()

    status = eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    )

    assert status.state is EligibilityCircuitState.CLOSED
    assert status.control_activity_id is None
    assert status.cause_incident_activity_id is None
    assert require_eligibility_circuit_closed(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ) == status


def test_h1_warning_signal_is_board_visible_but_does_not_open_circuit(db_session: Session) -> None:
    aggregate = _aggregate()

    result = record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="verifier-disagreement-1",
        kind=EligibilityImmuneIncidentKind.VERIFIER_DISAGREEMENT,
        summary="Independent verifier disagreed with the governed eligibility proposal.",
    )

    assert result.severity is EligibilityImmuneIncidentSeverity.WARNING
    assert result.circuit_opened is False
    assert result.replayed is False
    assert result.circuit_status.state is EligibilityCircuitState.CLOSED
    record = transparency_activity_record(result.incident_activity)
    assert record.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
    assert record.board_inspectable is True
    assert record.payload["incident_kind"] == "verifier_disagreement"
    assert record.payload["automatic_circuit_action"] == "none"
    assert record.payload["authority_effect"] == "restrict_only"
    assert len(_activities(db_session, tenant_key="tenant-a", aggregate_key=aggregate)) == 1


def test_h1_critical_integrity_signal_atomically_opens_and_blocks_aggregate(
    db_session: Session,
) -> None:
    aggregate = _aggregate()

    result = record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="aggregate-integrity-1",
        kind=EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
        summary="Canonical eligibility aggregate has multiple active revisions.",
    )

    assert result.severity is EligibilityImmuneIncidentSeverity.CRITICAL
    assert result.circuit_opened is True
    assert result.circuit_status.state is EligibilityCircuitState.OPEN
    assert result.circuit_status.cause_incident_activity_id == result.incident_activity.id

    activities = _activities(db_session, tenant_key="tenant-a", aggregate_key=aggregate)
    assert [row.activity_type for row in activities] == [
        ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
        ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
    ]
    assert activities[1].causation_activity_id == activities[0].id

    with pytest.raises(EligibilityCircuitOpen, match="circuit-broken"):
        require_eligibility_circuit_closed(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
        )


def test_h1_critical_incident_and_open_transition_roll_back_together(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aggregate = _aggregate()
    from app.services import organization_eligibility_immune_system as immune

    real_stage = immune.stage_activity
    calls = 0

    def fail_second_stage(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("synthetic circuit-open staging failure")
        return real_stage(*args, **kwargs)

    monkeypatch.setattr(immune, "stage_activity", fail_second_stage)

    with pytest.raises(RuntimeError, match="synthetic circuit-open staging failure"):
        record_eligibility_immune_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="atomic-failure-1",
            kind=EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY,
            summary="Canonical eligibility lineage is torn.",
        )

    assert _activities(db_session, tenant_key="tenant-a", aggregate_key=aggregate) == []
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    ).state is EligibilityCircuitState.CLOSED


def test_h1_incident_replay_is_idempotent_and_does_not_duplicate_open(db_session: Session) -> None:
    aggregate = _aggregate()
    first = record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="lineage-1",
        kind=EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY,
        summary="Durable canonical effect lineage is incomplete.",
    )
    count = len(_activities(db_session, tenant_key="tenant-a", aggregate_key=aggregate))

    replay = record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="lineage-1",
        kind=EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY,
        summary="Durable canonical effect lineage is incomplete.",
    )

    assert replay.replayed is True
    assert replay.circuit_opened is False
    assert replay.incident_activity.id == first.incident_activity.id
    assert replay.circuit_status.state is EligibilityCircuitState.OPEN
    assert len(_activities(db_session, tenant_key="tenant-a", aggregate_key=aggregate)) == count

    with pytest.raises(EligibilityImmuneSystemError, match="idempotency key conflicts"):
        record_eligibility_immune_incident(
            db_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="lineage-1",
            kind=EligibilityImmuneIncidentKind.REVISION_CONFLICT,
            summary="Same key, different incident meaning.",
        )


def test_h1_circuit_recovery_requires_human_admin_and_does_not_grant_authority(
    db_session: Session,
) -> None:
    aggregate = _aggregate()
    opened = record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="aggregate-integrity-recoverable",
        kind=EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
        summary="Aggregate integrity failure requires recovery.",
    )
    assert opened.circuit_status.state is EligibilityCircuitState.OPEN

    with pytest.raises(EligibilityCircuitRecoveryError, match="human admin"):
        close_eligibility_circuit(
            db_session,
            context=eligibility_immune_system_context(tenant_key="tenant-a"),
            aggregate_key=aggregate,
            recovery_key="recovery-1",
            reason="Canonical aggregate repaired and independently verified.",
        )

    operator_human = OrganizationCommandContext(
        tenant_key="tenant-a",
        actor_id="operator-user",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="operator-user",
        role="operator",
    )
    with pytest.raises(EligibilityCircuitRecoveryError, match="human admin"):
        close_eligibility_circuit(
            db_session,
            context=operator_human,
            aggregate_key=aggregate,
            recovery_key="recovery-1",
            reason="Canonical aggregate repaired and independently verified.",
        )

    closed = close_eligibility_circuit(
        db_session,
        context=_admin_context(),
        aggregate_key=aggregate,
        recovery_key="recovery-1",
        reason="Canonical aggregate repaired and independently verified.",
    )
    assert closed.state is EligibilityCircuitState.CLOSED
    require_eligibility_circuit_closed(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
    )

    activities = _activities(db_session, tenant_key="tenant-a", aggregate_key=aggregate)
    assert activities[-1].activity_type == ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE
    assert activities[-1].supersedes_activity_id == opened.circuit_status.control_activity_id
    payload = transparency_activity_record(activities[-1]).payload
    assert payload["restores_execution_attempts_only"] is True
    assert payload["grants_authority"] is False


def test_h1_old_recovery_replay_cannot_close_a_later_reopened_circuit(db_session: Session) -> None:
    aggregate = _aggregate()
    record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="first-critical",
        kind=EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
        summary="First structural integrity failure.",
    )
    close_eligibility_circuit(
        db_session,
        context=_admin_context(),
        aggregate_key=aggregate,
        recovery_key="first-recovery",
        reason="First structural issue repaired.",
    )
    reopened = record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate,
        incident_key="second-critical",
        kind=EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY,
        summary="A later durable-lineage integrity failure occurred.",
    )
    assert reopened.circuit_status.state is EligibilityCircuitState.OPEN

    replay_old_recovery = close_eligibility_circuit(
        db_session,
        context=_admin_context(),
        aggregate_key=aggregate,
        recovery_key="first-recovery",
        reason="First structural issue repaired.",
    )
    assert replay_old_recovery.state is EligibilityCircuitState.OPEN


def test_h1_circuit_scope_isolated_by_tenant_and_aggregate(db_session: Session) -> None:
    aggregate_a = _aggregate("tenant-a")
    aggregate_b = _aggregate("tenant-a")

    record_eligibility_immune_incident(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate_a,
        incident_key="scope-a-critical",
        kind=EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
        summary="Only aggregate A is structurally inconsistent.",
    )

    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate_a,
    ).state is EligibilityCircuitState.OPEN
    assert eligibility_circuit_status(
        db_session,
        tenant_key="tenant-a",
        aggregate_key=aggregate_b,
    ).state is EligibilityCircuitState.CLOSED
    with pytest.raises(EligibilityImmuneSystemError, match="does not belong"):
        eligibility_circuit_status(
            db_session,
            tenant_key="tenant-b",
            aggregate_key=aggregate_a,
        )
