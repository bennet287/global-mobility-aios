from __future__ import annotations

import os

import pytest
from sqlmodel import Session

from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_eligibility_immune_system import (
    EligibilityCircuitState,
    EligibilityImmuneIncidentKind,
    close_eligibility_circuit,
    eligibility_circuit_status,
    record_eligibility_immune_incident,
)
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityOrchestrationIntegrityError,
    GovernedEligibilityOrchestrationState,
    orchestrate_governed_eligibility,
)
from tests.test_organization_eligibility_orchestration import (
    _fixture,
    _human_context,
    _plan,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL contract requires GMAI_TEST_DATABASE_URL",
)


def test_postgres_cross_session_stale_reassessment_fails_before_provider_egress(
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    initial_plan, _, _ = _plan(graph)
    first = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="postgres-v1",
        execution_plan=initial_plan,
    )
    assert first.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
    assert first.revision_id is not None

    engine = db_session.get_bind()
    with Session(engine) as winner_session:
        winner_plan, winner_producer, winner_verifier = _plan(graph)
        winner = orchestrate_governed_eligibility(
            winner_session,
            tenant_key="tenant-a",
            proposal_work_item_id=proposal_work.id,
            verification_work_item_id=verification_work.id,
            idempotency_key="postgres-reassessment-winner",
            execution_plan=winner_plan,
            expected_eligibility_revision_version=1,
        )
        assert winner.state is GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED
        assert winner.revision_id is not None
        assert len(winner_producer.calls) == 1
        assert len(winner_verifier.calls) == 1

    with Session(engine) as stale_session:
        stale_plan, stale_producer, stale_verifier = _plan(graph)
        with pytest.raises(GovernedEligibilityOrchestrationIntegrityError):
            orchestrate_governed_eligibility(
                stale_session,
                tenant_key="tenant-a",
                proposal_work_item_id=proposal_work.id,
                verification_work_item_id=verification_work.id,
                idempotency_key="postgres-reassessment-stale",
                execution_plan=stale_plan,
                expected_eligibility_revision_version=1,
            )
        assert stale_producer.calls == []
        assert stale_verifier.calls == []

    db_session.expire_all()
    revisions = list(
        db_session.exec(
            EligibilityAssessmentRevision.__table__.select().where(
                EligibilityAssessmentRevision.tenant_key == "tenant-a"
            )
        ).all()
    )
    assert len(revisions) == 2


def test_postgres_cross_session_circuit_recovery_cannot_override_later_incident(
    db_session: Session,
) -> None:
    _, _, graph, proposal_work, verification_work = _fixture(db_session)
    plan, _, _ = _plan(graph)
    first = orchestrate_governed_eligibility(
        db_session,
        tenant_key="tenant-a",
        proposal_work_item_id=proposal_work.id,
        verification_work_item_id=verification_work.id,
        idempotency_key="postgres-circuit-base",
        execution_plan=plan,
    )
    assert first.revision_id is not None
    revision = db_session.get(EligibilityAssessmentRevision, first.revision_id)
    assert revision is not None
    aggregate = revision.aggregate_key
    engine = db_session.get_bind()

    with Session(engine) as opener_session:
        opened = record_eligibility_immune_incident(
            opener_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="postgres-critical-a",
            kind=EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
            summary="Synthetic PostgreSQL critical integrity incident A.",
        )
        assert opened.circuit_status.state is EligibilityCircuitState.OPEN

    with Session(engine) as recovery_session:
        closed = close_eligibility_circuit(
            recovery_session,
            context=_human_context(role="admin"),
            aggregate_key=aggregate,
            recovery_key="postgres-recovery-a",
            reason="Synthetic PostgreSQL recovery A.",
        )
        assert closed.state is EligibilityCircuitState.CLOSED

    with Session(engine) as reopen_session:
        reopened = record_eligibility_immune_incident(
            reopen_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
            incident_key="postgres-critical-b",
            kind=EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY,
            summary="Synthetic PostgreSQL critical integrity incident B.",
        )
        assert reopened.circuit_status.state is EligibilityCircuitState.OPEN

    with Session(engine) as replay_session:
        replayed_old_recovery = close_eligibility_circuit(
            replay_session,
            context=_human_context(role="admin"),
            aggregate_key=aggregate,
            recovery_key="postgres-recovery-a",
            reason="Synthetic PostgreSQL recovery A.",
        )
        assert replayed_old_recovery.state is EligibilityCircuitState.OPEN
        assert eligibility_circuit_status(
            replay_session,
            tenant_key="tenant-a",
            aggregate_key=aggregate,
        ).state is EligibilityCircuitState.OPEN
