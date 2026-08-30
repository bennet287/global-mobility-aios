from __future__ import annotations

from labs.r3.sandbox.microsandbox_depth_lab import SYNTHETIC_SECRET


def test_secret_canary_is_explicitly_synthetic() -> None:
    assert "SYNTHETIC" in SYNTHETIC_SECRET
    assert "PRODUCTION" in SYNTHETIC_SECRET
