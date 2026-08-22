from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Barrier
from time import monotonic, sleep
from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.autonomy_promotion_policy import CapabilityAutonomyPromotionPolicy
from app.services.organization_autonomy_promotion_policy import establish_capability_autonomy_promotion_policy
from app.services.organization_command import DependencyConflict, InvalidTransition
from tests.test_organization_eligibility_postgres_contract import (
    _autonomy_board,
    _seed_autonomy_contract,
    _write_autonomy_profile,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL contract requires GMAI_TEST_DATABASE_URL",
)


def _write_policy(
    session: Session,
    *,
    actor_id: str,
    idempotency_key: str,
    expected_policy_sequence: int | None,
    min_volume: int = 2,
    expected_profile_id: UUID | None = None,
):
    return establish_capability_autonomy_promotion_policy(
        session,
        _autonomy_board(actor_id),
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope="austria:postgres-race",
        from_autonomy_level=AutonomyLevel.A2,
        target_autonomy_level=AutonomyLevel.A3,
        evidence_policy_version="autonomy-evidence-v1",
        min_qualifying_execution_volume=min_volume,
        min_human_reviewed_count=2,
        min_evidence_grounding_rate=1.0,
        min_human_acceptance_rate=1.0,
        max_human_modification_rate=0.0,
        max_human_rejection_rate=0.0,
        max_verifier_contradiction_rate=0.0,
        min_policy_compliance_rate=1.0,
        min_freshness_compliance_rate=1.0,
        max_critical_error_count=0,
        min_recovery_applicable_count=0,
        min_recovery_success_rate=None,
        min_sla_met_rate=1.0,
        max_incident_count=0,
        policy_reason=f"PostgreSQL I.3 policy {idempotency_key}",
        idempotency_key=idempotency_key,
        expected_profile_id=expected_profile_id,
        expected_policy_sequence=expected_policy_sequence,
    )


def _seed_profile(db_session: Session):
    evidence = _seed_autonomy_contract(db_session, evidence_key="postgres-i3-profile")
    return _write_autonomy_profile(
        db_session,
        actor_id="board-i3-profile",
        evidence_activity_id=evidence.id,
        idempotency_key="i3-postgres-profile",
        expected_profile_sequence=None,
    )


def test_postgres_competing_initial_i3_policies_cannot_fork_policy_truth(
    db_session: Session,
) -> None:
    _seed_profile(db_session)
    engine = db_session.get_bind()
    barrier = Barrier(2)

    def compete(index: int) -> tuple[str, str]:
        with Session(engine) as session:
            barrier.wait()
            try:
                policy = _write_policy(
                    session,
                    actor_id=f"board-i3-racer-{index}",
                    idempotency_key=f"i3-postgres-racer-{index}",
                    expected_policy_sequence=None,
                    min_volume=index + 1,
                )
                return "committed", str(policy.id)
            except (DependencyConflict, InvalidTransition) as exc:
                return "rejected", type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(compete, (1, 2)))

    assert sorted(outcome for outcome, _ in outcomes) == ["committed", "rejected"]
    db_session.expire_all()
    rows = list(
        db_session.exec(
            select(CapabilityAutonomyPromotionPolicy).where(
                CapabilityAutonomyPromotionPolicy.tenant_key == "default",
                CapabilityAutonomyPromotionPolicy.position_key == "case_operations_specialist",
                CapabilityAutonomyPromotionPolicy.capability_key == "eligibility.proposal",
                CapabilityAutonomyPromotionPolicy.context_scope == "austria:postgres-race",
            )
        ).all()
    )
    assert len(rows) == 1
    assert rows[0].policy_sequence == 1
    assert rows[0].supersedes_policy_id is None


def test_postgres_stale_cross_session_i3_policy_supersession_is_rejected(
    db_session: Session,
) -> None:
    _seed_profile(db_session)
    first = _write_policy(
        db_session,
        actor_id="board-i3-initial",
        idempotency_key="i3-postgres-v1",
        expected_policy_sequence=None,
    )
    assert first.policy_sequence == 1
    engine = db_session.get_bind()

    with Session(engine) as winner_session:
        winner = _write_policy(
            winner_session,
            actor_id="board-i3-winner",
            idempotency_key="i3-postgres-v2",
            expected_policy_sequence=1,
            min_volume=3,
        )
        assert winner.policy_sequence == 2

    with Session(engine) as stale_session:
        with pytest.raises(InvalidTransition, match="stale"):
            _write_policy(
                stale_session,
                actor_id="board-i3-stale",
                idempotency_key="i3-postgres-stale-v2",
                expected_policy_sequence=1,
                min_volume=4,
            )

    db_session.expire_all()
    rows = list(
        db_session.exec(
            select(CapabilityAutonomyPromotionPolicy)
            .where(
                CapabilityAutonomyPromotionPolicy.tenant_key == "default",
                CapabilityAutonomyPromotionPolicy.position_key == "case_operations_specialist",
                CapabilityAutonomyPromotionPolicy.capability_key == "eligibility.proposal",
                CapabilityAutonomyPromotionPolicy.context_scope == "austria:postgres-race",
            )
            .order_by(CapabilityAutonomyPromotionPolicy.policy_sequence)
        ).all()
    )
    assert [row.policy_sequence for row in rows] == [1, 2]
    assert rows[1].supersedes_policy_id == rows[0].id


def test_postgres_i3_policy_rejects_profile_supersession_that_wins_profile_lock(
    db_session: Session,
) -> None:
    evidence = _seed_autonomy_contract(db_session, evidence_key="postgres-i3-profile-lock-race")
    first_profile = _write_autonomy_profile(
        db_session,
        actor_id="board-i3-profile-lock-v1",
        evidence_activity_id=evidence.id,
        idempotency_key="i3-postgres-profile-lock-v1",
        expected_profile_sequence=None,
    )
    engine = db_session.get_bind()
    pid_queue: Queue[int] = Queue()

    def write_inflight_policy() -> tuple[str, str]:
        with Session(engine) as session:
            pid = session.connection().exec_driver_sql("SELECT pg_backend_pid()").scalar_one()
            pid_queue.put(int(pid))
            try:
                _write_policy(
                    session,
                    actor_id="board-i3-profile-lock-policy",
                    idempotency_key="i3-postgres-profile-lock-policy",
                    expected_policy_sequence=None,
                    expected_profile_id=first_profile.id,
                )
                return "committed", "unexpected"
            except InvalidTransition as exc:
                return "rejected", str(exc)

    with Session(engine) as supersession_session:
        locked_profile = supersession_session.exec(
            select(CapabilityAutonomyProfile)
            .where(CapabilityAutonomyProfile.id == first_profile.id)
            .with_for_update()
        ).one()
        assert locked_profile.id == first_profile.id

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(write_inflight_policy)
            policy_pid = pid_queue.get(timeout=5)
            deadline = monotonic() + 5
            while monotonic() < deadline:
                wait_event_type = supersession_session.connection().exec_driver_sql(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s",
                    (policy_pid,),
                ).scalar_one_or_none()
                if wait_event_type == "Lock":
                    break
                sleep(0.02)
            else:
                pytest.fail("inflight I.3 policy writer never blocked on the I.1 profile lock")

            second_profile = _write_autonomy_profile(
                supersession_session,
                actor_id="board-i3-profile-lock-v2",
                evidence_activity_id=evidence.id,
                idempotency_key="i3-postgres-profile-lock-v2",
                expected_profile_sequence=1,
            )
            assert second_profile.profile_sequence == 2
            outcome, detail = future.result(timeout=5)

    assert outcome == "rejected"
    assert "expected autonomy profile is stale" in detail
    db_session.expire_all()
    policies = list(
        db_session.exec(
            select(CapabilityAutonomyPromotionPolicy).where(
                CapabilityAutonomyPromotionPolicy.tenant_key == "default",
                CapabilityAutonomyPromotionPolicy.profile_id == first_profile.id,
            )
        ).all()
    )
    assert policies == []
