from __future__ import annotations

import pytest
from sqlmodel import Session

from app.core.organization_constitution import AutonomyLevel
from app.services.organization_autonomy_promotion_policy import establish_capability_autonomy_promotion_policy
from app.services.organization_command import InvalidTransition
from tests.test_organization_autonomy_promotion_policy import (
    CAPABILITY_KEY,
    CONTEXT_SCOPE,
    EVIDENCE_POLICY_VERSION,
    POSITION_KEY,
    _board_context,
    _position,
    _profile,
)


def _write_policy(
    session: Session,
    *,
    expected_profile_id,
    idempotency_key: str,
):
    return establish_capability_autonomy_promotion_policy(
        session,
        _board_context(),
        position_key=POSITION_KEY,
        capability_key=CAPABILITY_KEY,
        context_scope=CONTEXT_SCOPE,
        from_autonomy_level=AutonomyLevel.A2,
        target_autonomy_level=AutonomyLevel.A3,
        evidence_policy_version=EVIDENCE_POLICY_VERSION,
        min_qualifying_execution_volume=2,
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
        policy_reason="Board policy with exact I.1 profile precondition",
        idempotency_key=idempotency_key,
        expected_profile_id=expected_profile_id,
        expected_policy_sequence=None,
    )


def test_i3_expected_profile_id_rejects_same_level_historical_profile(
    db_session: Session,
) -> None:
    _position(db_session)
    board = _board_context()
    first = _profile(db_session, board, key="precondition-v1")
    second = _profile(
        db_session,
        board,
        key="precondition-v2",
        autonomy_level=AutonomyLevel.A2,
        board_ceiling=AutonomyLevel.A3,
        authority_requirement="L3",
        expected_profile_sequence=1,
    )
    assert second.id != first.id
    assert second.autonomy_level == first.autonomy_level
    assert second.evidence_policy_version == first.evidence_policy_version

    with pytest.raises(InvalidTransition, match="expected autonomy profile is stale"):
        _write_policy(
            db_session,
            expected_profile_id=first.id,
            idempotency_key="i3-stale-profile-precondition",
        )

    accepted = _write_policy(
        db_session,
        expected_profile_id=second.id,
        idempotency_key="i3-current-profile-precondition",
    )
    assert accepted.profile_id == second.id
    assert accepted.profile_sequence == second.profile_sequence
