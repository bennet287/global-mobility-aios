from __future__ import annotations

import json
from pathlib import Path

import pytest

from labs.r3.integration.copilotkit_lab import (
    LAB_DIR,
    ExecutionBlocked,
    run_copilotkit,
)


def test_copilotkit_lab_is_isolated_from_product_web_dependencies() -> None:
    package = json.loads((LAB_DIR / "package.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert package["dependencies"]["@copilotkit/runtime"] == "1.69.3"
    assert package["dependencies"]["@ag-ui/client"] == "0.0.57"


def test_runtime_probe_encodes_authority_boundary() -> None:
    text = (LAB_DIR / "runtime_probe.mjs").read_text(encoding="utf-8")

    assert "authority_state: \"DENIED\"" in text
    assert "government_application.submit" in text
    assert "authorized: false" in text
    assert "executed: false" in text
    assert "externalActions = 0" in text


def test_copilotkit_real_probe_if_dependencies_installed() -> None:
    if not (LAB_DIR / "node_modules" / "@copilotkit" / "runtime").exists():
        pytest.skip("isolated CopilotKit dependencies are not installed")

    result = run_copilotkit()
    assert result["failures"] == 0
    assert result["unauthorized_canonical_effects"] == 0
    assert result["feature_coverage"]["real_runtime_v2"] is True
