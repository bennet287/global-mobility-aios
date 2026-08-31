from __future__ import annotations

from labs.r3.memory.native_lab import run_native_memory


def test_native_memory_evidence_runner_is_clean() -> None:
    result = run_native_memory()
    assert result["failures"] == 0
    assert result["passes"] == len(result["outcomes"])
    assert result["feature_coverage"]["verified_rule_precedence"] is True
    assert result["feature_coverage"]["tenant_scoping"] is True
