from __future__ import annotations

import json
from pathlib import Path

from labs.r3.integration.governed_ui import (
    GovernedUiState,
    reconnect_with_snapshot,
    reconcile_with_canonical,
    reduce_ui_intent,
)
from labs.r3.integration.grand_trial import REQUIRED_LANES, _classify_lane, run_cross_lane_attack


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
        canonical_revision=1,
    )
    assert reconciled.authority_state == "DENIED"
    assert reconciled.optimistic is False


def test_stale_snapshot_cannot_roll_authority_backward() -> None:
    state = GovernedUiState(
        canonical_status="HUMAN_REVIEW_REQUIRED",
        authority_state="DENIED",
        human_approval_required=True,
        human_approved=False,
        canonical_revision=9,
    )
    stale = reconcile_with_canonical(
        state,
        canonical_status="COMPLETED",
        authority_state="ALLOW",
        human_approval_required=False,
        canonical_revision=8,
    )
    assert stale == state


def test_disconnect_reconnect_clears_optimistic_intent() -> None:
    state = GovernedUiState(
        canonical_status="HUMAN_REVIEW_REQUIRED",
        authority_state="DENIED",
        human_approval_required=True,
        human_approved=False,
        canonical_revision=4,
    )
    optimistic = reduce_ui_intent(state, "SUBMIT_APPLICATION")
    disconnected = reduce_ui_intent(optimistic, "CONNECTION_LOST")
    assert disconnected.connected is False
    assert disconnected.authority_state == "DENIED"

    restored = reconnect_with_snapshot(
        disconnected,
        canonical_status="HUMAN_REVIEW_REQUIRED",
        authority_state="DENIED",
        human_approval_required=True,
        canonical_revision=5,
    )
    assert restored.connected is True
    assert restored.optimistic is False
    assert restored.pending_intent is None
    assert restored.authority_state == "DENIED"


def test_grand_trial_requires_all_eleven_runtime_radar_lanes() -> None:
    assert REQUIRED_LANES == {
        "authority",
        "interoperability",
        "security",
        "skills",
        "sandbox",
        "observability",
        "secrets",
        "recovery",
        "memory",
        "orchestration",
        "ui",
    }
    assert _classify_lane({"candidate": "aios-skill-registry", "experiment": "lifecycle"}) == "skills"
    assert _classify_lane({"candidate": "microsandbox", "experiment": "isolation"}) == "sandbox"
    assert _classify_lane({"candidate": "ag-ui-protocol", "experiment": "interaction"}) == "ui"
    assert _classify_lane({"candidate": "copilotkit-runtime", "experiment": "interaction"}) == "ui"


def test_cross_lane_attack_fails_closed() -> None:
    result = run_cross_lane_attack()
    assert result["poisoned_memory_overridden"] is False
    assert result["protocol_capability_granted_authority"] is False
    assert result["skill_advertisement_granted_authority"] is False
    assert result["sandbox_availability_granted_execution_authority"] is False
    assert result["sandbox_state_became_canonical"] is False
    assert result["security_advice_became_canonical"] is False
    assert result["telemetry_became_canonical"] is False
    assert result["secret_outage_failed_closed"] is True
    assert result["external_action_count"] == 0
    assert result["authority_mutation_count"] == 0


def test_lane_status_never_conflates_implementation_with_adoption() -> None:
    status_path = Path(__file__).resolve().parents[2] / "lane_status.v1.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["programme_status"] == "R3_IMPLEMENTATION_SURFACE_COMPLETE_EXECUTION_PENDING"
    assert status["evidence_status"] == "NOT_RECONCILED"
    assert status["production_adoption"] is False
