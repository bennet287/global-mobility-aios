from __future__ import annotations

from labs.r3.authority.static_evidence import build_static_evidence


def test_static_authority_evidence_is_clean() -> None:
    result = build_static_evidence("authority-static-20260830-004")

    assert result["invariants"]["passed"] == 12
    assert result["invariants"]["failed"] == 0
    assert result["mutations"]["detected"] == 10
    assert result["mutations"]["escaped"] == 0
    assert result["failures"] == 0
    assert result["unauthorized_canonical_effects"] == 0
