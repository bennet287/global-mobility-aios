from __future__ import annotations

import pytest


def test_langgraph_real_candidate_if_installed() -> None:
    pytest.importorskip("langgraph")
    from labs.r3.orchestration.langgraph_lab import run_langgraph

    result = run_langgraph()
    assert result["resumed_after_pause"] is True
    assert result["canonical_authority_effects"] == 0


def test_agno_real_candidate_if_installed() -> None:
    pytest.importorskip("agno")
    from labs.r3.orchestration.agno_lab import run_agno

    result = run_agno()
    assert result["resumed_after_pause"] is True
    assert result["canonical_authority_effects"] == 0
