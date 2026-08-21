from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel
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
