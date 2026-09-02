from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.validate_global_coverage_evidence_pack import validate_sha256_receipt


def test_json_receipt_hash_is_stable_across_line_endings(tmp_path: Path) -> None:
    canonical = b'{\n  "review_status": "pending_independent_review"\n}\n'
    expected = hashlib.sha256(canonical).hexdigest()

    pack_path = tmp_path / "sample.json"
    receipt_path = tmp_path / "sample.json.sha256"
    receipt_path.write_text(f"{expected}  sample.json\n", encoding="utf-8")

    pack_path.write_bytes(canonical)
    assert validate_sha256_receipt(pack_path) == expected

    pack_path.write_bytes(canonical.replace(b"\n", b"\r\n"))
    assert validate_sha256_receipt(pack_path) == expected
