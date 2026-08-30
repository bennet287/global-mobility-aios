from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_openfga_conditions_model_declares_temporal_condition() -> None:
    model = json.loads(
        (ROOT / "openfga" / "conditions_model.json").read_text(encoding="utf-8")
    )
    condition = model["conditions"]["non_expired_grant"]
    assert "current_time" in condition["parameters"]
    assert "grant_time" in condition["parameters"]
    assert "grant_duration" in condition["parameters"]
