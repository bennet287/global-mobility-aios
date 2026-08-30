from __future__ import annotations

import pytest

from labs.r3.orchestration.common import NativeDurableReference
from labs.r3.orchestration.native_lab import run_native


def test_native_reference_requires_human_approval() -> None:
    engine = NativeDurableReference()
    with pytest.raises(ValueError):
        engine.apply("early", "COMPLETE")


def test_native_reference_suppresses_duplicate_command() -> None:
    engine = NativeDurableReference()
    assert engine.apply("same", "DOCUMENTS_REQUESTED") is True
    assert engine.apply("same", "DOCUMENTS_REQUESTED") is False


def test_native_reference_full_flow() -> None:
    result = run_native()
    assert result["final_status"] == "COMPLETED"
    assert result["human_gate_observed"] is True
    assert result["canonical_external_actions"] == 0
