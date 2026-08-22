from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Barrier
from time import monotonic, sleep
from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.models.autonomy_evidence_evaluation_policy import (
    CapabilityAutonomyEvidenceEvaluationPolicy,
)
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.services.organization_autonomy_evidence_evaluation_contract import I4_QUALIFICATION_CONTRACT
from app.services.organization_autonomy_evidence_evaluation_policy import (
    establish_capability_autonomy_evidence_evaluation_policy,
)
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
    max_candidates: int = 100,
    max_source_age: int = 3600,
    expected_profile_id: UUID | None = None,
):
    return establish_capability_autonomy_evidence_evaluation_policy(
        session,
        _autonomy_board(actor_id),
        position_key="case_operations_specialist",
        capability_key="eligibility.proposal",
        context_scope="austria:postgres-race",
        qualification_contract=I4_QUALIFICATION_CONTRACT,
        max_observation_age_seconds=3600,
        max_source_age_seconds=max_source_age,
        max_candidate_observations=max_candidates,
        policy_reason=f"PostgreSQL I.4 policy {idempotency_key}",
        idempotency_key=idempotency_key,
        expected_profile_id=expected_profile_id,
        expected_policy_sequence=expected_policy_sequence,
    )


def _seed_profile(db_session: Session):
    evidence = _seed_autonomy_contract(db_session, evidence_key="postgres-i4-profile")
    return _write_autonomy_profile(
        db_session,
        actor_id="board-i4-profile",
        evidence_activity_id=evidence.id,
        idempotency_key="i4-postgres-profile",
        expected_profile_sequence=None,
    )


def test_postgres_competing_initial_i4_policies_cannot_fork_policy_truth(
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
                    actor_id=f"board-i4-racer-{index}",
                    idempotency_key=f"i4-postgres-racer-{index}",
                    expected_policy_sequence=None,
                    max_candidates=100 + index,
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
            select(CapabilityAutonomyEvidenceEvaluationPolicy).where(
                CapabilityAutonomyEvidenceEvaluationPolicy.tenant_key == "default",
                CapabilityAutonomyEvidenceEvaluationPolicy.position_key == "case_operations_specialist",
                CapabilityAutonomyEvidenceEvaluationPolicy.capability_key == "eligibility.proposal",
                CapabilityAutonomyEvidenceEvaluationPolicy.context_scope == "austria:postgres-race",
            )
        ).all()
    )
    assert len(rows) == 1
    assert rows[0].policy_sequence == 1
    assert rows[0].supersedes_policy_id is None


def test_postgres_stale_cross_session_i4_policy_supersession_is_rejected(
    db_session: Session,
) -> None:
    _seed_profile(db_session)
    first = _write_policy(
        db_session,
        actor_id="board-i4-initial",
        idempotency_key="i4-postgres-v1",
        expected_policy_sequence=None,
    )
    assert first.policy_sequence == 1
    engine = db_session.get_bind()

    with Session(engine) as winner_session:
        winner = _write_policy(
            winner_session,
            actor_id="board-i4-winner",
            idempotency_key="i4-postgres-v2",
            expected_policy_sequence=1,
            max_source_age=1800,
        )
        assert winner.policy_sequence == 2

    with Session(engine) as stale_session:
        with pytest.raises(InvalidTransition, match="stale"):
            _write_policy(
                stale_session,
                actor_id="board-i4-stale",
                idempotency_key="i4-postgres-stale-v2",
                expected_policy_sequence=1,
                max_source_age=900,
            )

    db_session.expire_all()
    rows = list(
        db_session.exec(
            select(CapabilityAutonomyEvidenceEvaluationPolicy)
            .where(
                CapabilityAutonomyEvidenceEvaluationPolicy.tenant_key == "default",
                CapabilityAutonomyEvidenceEvaluationPolicy.position_key == "case_operations_specialist",
                CapabilityAutonomyEvidenceEvaluationPolicy.capability_key == "eligibility.proposal",
                CapabilityAutonomyEvidenceEvaluationPolicy.context_scope == "austria:postgres-race",
            )
            .order_by(CapabilityAutonomyEvidenceEvaluationPolicy.policy_sequence)
        ).all()
    )
    assert [row.policy_sequence for row in rows] == [1, 2]
    assert rows[1].supersedes_policy_id == rows[0].id


def test_postgres_i4_policy_rejects_profile_supersession_that_wins_profile_lock(
    db_session: Session,
) -> None:
    evidence = _seed_autonomy_contract(db_session, evidence_key="postgres-i4-profile-lock-race")
    first_profile = _write_autonomy_profile(
        db_session,
        actor_id="board-i4-profile-lock-v1",
        evidence_activity_id=evidence.id,
        idempotency_key="i4-postgres-profile-lock-v1",
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
                    actor_id="board-i4-profile-lock-policy",
                    idempotency_key="i4-postgres-profile-lock-policy",
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
                pytest.fail("inflight I.4 policy writer never blocked on the I.1 profile lock")

            second_profile = _write_autonomy_profile(
                supersession_session,
                actor_id="board-i4-profile-lock-v2",
                evidence_activity_id=evidence.id,
                idempotency_key="i4-postgres-profile-lock-v2",
                expected_profile_sequence=1,
            )
            assert second_profile.profile_sequence == 2
            outcome, detail = future.result(timeout=5)

    assert outcome == "rejected"
    assert "expected autonomy profile is stale" in detail
    db_session.expire_all()
    policies = list(
        db_session.exec(
            select(CapabilityAutonomyEvidenceEvaluationPolicy).where(
                CapabilityAutonomyEvidenceEvaluationPolicy.tenant_key == "default",
                CapabilityAutonomyEvidenceEvaluationPolicy.profile_id == first_profile.id,
            )
        ).all()
    )
    assert policies == []
