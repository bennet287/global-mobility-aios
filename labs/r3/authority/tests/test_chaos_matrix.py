from __future__ import annotations

import pytest

from labs.r3.authority.chaos_matrix import FAILURE_MODES, run_matrix


@pytest.mark.parametrize("candidate", ["openfga", "opa"])
def test_full_adapter_chaos_matrix_fails_closed(candidate: str) -> None:
    outcomes = run_matrix(candidate)

    assert len(outcomes) == len(FAILURE_MODES)
    assert all(outcome["passed"] for outcome in outcomes)
    assert all(outcome["observed_decision"] == "DENY" for outcome in outcomes)
    assert all(outcome["provider_called"] is True for outcome in outcomes)
