from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, RiskTier
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import OrganizationActorType, OrganizationPosition
from app.services.organization_autonomy_profile import establish_capability_autonomy_profile
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
)
from tests.test_organization_autonomy_profile import _evidence_activity


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL contract requires GMAI_TEST_DATABASE_URL",
)


def _board(actor_id: str) -> OrganizationCommandContext:
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


def _write(
    session: Session,
    *,
    actor_id: str,
    evidence_activity_id,
    idempotency_key: str,
    expected_profile_sequence: int | None,
):
    return establish_capability_autonomy_profile(
        session,
        _board(actor_id),
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


def test_i1_postgres_competing_initial_profiles_cannot_fork_canonical_truth(
    db_session: Session,
) -> None:
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
    evidence = _evidence_activity(db_session, _board("board-seed"), key="postgres-race")
    engine = db_session.get_bind()
    barrier = Barrier(2)

    def compete(index: int) -> tuple[str, str]:
        with Session(engine) as session:
            barrier.wait()
            try:
                profile = _write(
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


def test_i1_postgres_stale_cross_session_supersession_is_rejected(
    db_session: Session,
) -> None:
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
    evidence = _evidence_activity(db_session, _board("board-seed"), key="postgres-stale")
    first = _write(
        db_session,
        actor_id="board-initial",
        evidence_activity_id=evidence.id,
        idempotency_key="i1-postgres-v1",
        expected_profile_sequence=None,
    )
    assert first.profile_sequence == 1
    engine = db_session.get_bind()

    with Session(engine) as winner_session:
        winner = _write(
            winner_session,
            actor_id="board-winner",
            evidence_activity_id=evidence.id,
            idempotency_key="i1-postgres-v2",
            expected_profile_sequence=1,
        )
        assert winner.profile_sequence == 2

    with Session(engine) as stale_session:
        with pytest.raises(InvalidTransition, match="stale"):
            _write(
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
