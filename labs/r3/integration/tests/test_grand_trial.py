from __future__ import annotations

from labs.r3.integration.governed_ui import GovernedUiState, reconcile_with_canonical, reduce_ui_intent
from labs.r3.integration.grand_trial import run_cross_lane_attack


def test_ui_intent_never_grants_authority() -> None:
    state = GovernedUiState(
        canonical_status="HUMAN_REVIEW_REQUIRED",
        authority_state="DENIED",
        human_approval_required=True,
        human_approved=False,
    )
    optimistic = reduce_ui_intent(state, "SUBMIT_APPLICATION")
    assert optimistic.authority_state == "DENIED"
    assert optimistic.optimistic is True

    reconciled = reconcile_with_canonical(
        optimistic,
        canonical_status="HUMAN_REVIEW_REQUIRED",
        authority_state="DENIED",
        human_approval_required=True,
    )
    assert reconciled.authority_state == "DENIED"
    assert reconciled.optimistic is False


def test_cross_lane_attack_fails_closed() -> None:
    result = run_cross_lane_attack()
    assert result["poisoned_memory_overridden"] is False
    assert result["protocol_capability_granted_authority"] is False
    assert result["security_advice_became_canonical"] is False
    assert result["telemetry_became_canonical"] is False
    assert result["secret_outage_failed_closed"] is True
    assert result["external_action_count"] == 0
    assert result["authority_mutation_count"] == 0
