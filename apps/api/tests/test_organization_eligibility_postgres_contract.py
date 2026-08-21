from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, RiskTier
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActorType, OrganizationPosition
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_autonomy_profile import establish_capability_autonomy_profile
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
)
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
from tests.test_organization_autonomy_profile import _evidence_activity
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


def _autonomy_board(actor_id: str) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id=actor_id,
        actor_type=OrganizationActorType.human,
        authenticated_user_id=actor_id,
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )


def _write_autonomy_profile(
    session: Session,
    *,
    actor_id: str,
    evidence_activity_id,
    idempotency_key: str,
    expected_profile_sequence: int | None,
):
    return establish_capability_autonomy_profile(
        session,
        _autonomy_board(actor_id),
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope="austria:postgres-race",
        autonomy_level=AutonomyLevel.A2,
        board_ceiling=AutonomyLevel.A3,
        authority_requirement="L2",
        risk_ceiling=RiskTier.R3,
        evidence_policy_version="autonomy-evidence-v1",
        evidence_activity_ids=(evidence_activity_id,),
        idempotency_key=idempotency_key,
        expected_profile_sequence=expected_profile_sequence,
    )


def _seed_autonomy_contract(db_session: Session, *, evidence_key: str):
    db_session.add(
        OrganizationPosition(
            position_key="case_operations_specialist",
            title="Case Operations Specialist",
            department="operations",
            authority_level="L2",
            created_by="pytest",
        )
    )
    db_session.commit()
    return _evidence_activity(
        db_session,
        _autonomy_board(f"board-seed-{evidence_key}"),
        key=evidence_key,
    )


def test_postgres_competing_initial_autonomy_profiles_cannot_fork_canonical_truth(
    db_session: Session,
) -> None:
    evidence = _seed_autonomy_contract(db_session, evidence_key="postgres-autonomy-race")
    engine = db_session.get_bind()
    barrier = Barrier(2)

    def compete(index: int) -> tuple[str, str]:
        with Session(engine) as session:
            barrier.wait()
            try:
                profile = _write_autonomy_profile(
                    session,
                    actor_id=f"board-racer-{index}",
                    evidence_activity_id=evidence.id,
                    idempotency_key=f"i1-postgres-racer-{index}",
                    expected_profile_sequence=None,
                )
                return "committed", str(profile.id)
            except (DependencyConflict, InvalidTransition) as exc:
                return "rejected", type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(compete, (1, 2)))

    assert sorted(outcome for outcome, _ in outcomes) == ["committed", "rejected"]
    db_session.expire_all()
    profiles = list(
        db_session.exec(
            select(CapabilityAutonomyProfile).where(
                CapabilityAutonomyProfile.tenant_key == "default",
                CapabilityAutonomyProfile.position_key == "case_operations_specialist",
                CapabilityAutonomyProfile.capability_key == "eligibility.proposal",
                CapabilityAutonomyProfile.context_scope == "austria:postgres-race",
            )
        ).all()
    )
    assert len(profiles) == 1
    assert profiles[0].profile_sequence == 1
    assert profiles[0].supersedes_profile_id is None


def test_postgres_stale_cross_session_autonomy_supersession_is_rejected(
    db_session: Session,
) -> None:
    evidence = _seed_autonomy_contract(db_session, evidence_key="postgres-autonomy-stale")
    first = _write_autonomy_profile(
        db_session,
        actor_id="board-initial",
        evidence_activity_id=evidence.id,
        idempotency_key="i1-postgres-v1",
        expected_profile_sequence=None,
    )
    assert first.profile_sequence == 1
    engine = db_session.get_bind()

    with Session(engine) as winner_session:
        winner = _write_autonomy_profile(
            winner_session,
            actor_id="board-winner",
            evidence_activity_id=evidence.id,
            idempotency_key="i1-postgres-v2",
            expected_profile_sequence=1,
        )
        assert winner.profile_sequence == 2

    with Session(engine) as stale_session:
        with pytest.raises(InvalidTransition, match="stale"):
            _write_autonomy_profile(
                stale_session,
                actor_id="board-stale",
                evidence_activity_id=evidence.id,
                idempotency_key="i1-postgres-stale-v2",
                expected_profile_sequence=1,
            )

    db_session.expire_all()
    profiles = list(
        db_session.exec(
            select(CapabilityAutonomyProfile)
            .where(
                CapabilityAutonomyProfile.tenant_key == "default",
                CapabilityAutonomyProfile.position_key == "case_operations_specialist",
                CapabilityAutonomyProfile.capability_key == "eligibility.proposal",
                CapabilityAutonomyProfile.context_scope == "austria:postgres-race",
            )
            .order_by(CapabilityAutonomyProfile.profile_sequence)
        ).all()
    )
    assert [profile.profile_sequence for profile in profiles] == [1, 2]
    assert profiles[1].supersedes_profile_id == profiles[0].id