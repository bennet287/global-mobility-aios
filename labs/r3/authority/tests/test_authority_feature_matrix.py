from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_authority_feature_matrix_has_no_silent_pending_features() -> None:
    matrix = json.loads(
        (ROOT / "feature_exploitation.v1.json").read_text(encoding="utf-8")
    )
    statuses = [
        item["status"]
        for candidate in ("openfga", "opa", "cedar", "spicedb")
        for item in matrix["candidates"][candidate]
    ]
    assert "PENDING" not in statuses


def test_spicedb_schema_is_projection_only() -> None:
    schema = (ROOT / "spicedb" / "schema.zed").read_text(encoding="utf-8")
    assert "permission read" in schema
    assert "AuthorityGrant" not in schema
    assert "VerifiedRule" not in schema
