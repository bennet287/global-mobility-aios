from __future__ import annotations

import pytest

from labs.r3.observability.secondary_candidates import (
    ExecutionBlocked,
    _canonical_result,
    _require_local,
    _sanitized_payload,
)


def test_secondary_observability_is_local_only() -> None:
    _require_local("http://127.0.0.1:6006")
    with pytest.raises(ExecutionBlocked):
        _require_local("https://cloud.example.com")


def test_payload_is_pre_redacted() -> None:
    payload = _sanitized_payload()
    assert payload["secret"] == "[REDACTED]"


def test_observability_reference_result_is_denied_and_effect_free() -> None:
    assert _canonical_result() == {
        "decision": "DENY",
        "reason_class": "HUMAN_APPROVAL_REQUIRED",
        "canonical_effects": 0,
    }
