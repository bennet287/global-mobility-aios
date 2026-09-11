from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "check_austria_source_certification_review_pack.py"
SPEC = importlib.util.spec_from_file_location(
    "check_austria_source_certification_review_pack",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _pack() -> dict[str, Any]:
    entries = [
        {
            "source_ordinal": ordinal,
            "occupation_group": f"Group {ordinal}",
            "occupation_aliases": [f"Alias {ordinal}"],
            "entry_sha256": f"{ordinal:064x}",
        }
        for ordinal in range(1, 65)
    ]
    entry_hashes = [entry["entry_sha256"] for entry in entries]
    source_content_text = "For the year 2026\n" + "\n".join(
        f"{ordinal}. Group {ordinal}\nAlias {ordinal}" for ordinal in range(1, 65)
    )
    snapshot_hash = "b" * 64
    return {
        "pack_version": MODULE.EXPECTED_PACK_VERSION,
        "evidence_pack_sha256": "a" * 64,
        "certification_id": "11111111-1111-1111-1111-111111111111",
        "certification_status": "pending_review",
        "proposed_by": "operator",
        "jurisdiction": {"code": "AT", "name": "Austria"},
        "source_snapshot": {
            "id": "22222222-2222-2222-2222-222222222222",
            "content_hash": snapshot_hash,
            "content_text_sha256": MODULE._sha256_text(source_content_text),
        },
        "source_content_text": source_content_text,
        "structured_projection": {
            "year": 2026,
            "scope": "national",
            "entry_count": 64,
            "entry_set_sha256": MODULE._sha256_canonical(entry_hashes),
            "source_snapshot_content_hash": snapshot_hash,
        },
        "structured_entries": entries,
    }


def test_check_review_pack_recomputes_exported_internal_hashes() -> None:
    report = MODULE.check_review_pack(_pack())

    assert report["status"] == "passed"
    assert report["errors"] == []
    assert report["checks"]["actual_entry_count"] == 64
    assert report["checks"]["source_ordinals_contiguous"] is True
    assert report["checks"]["entry_set_sha256_recomputed"]
    assert report["checks"]["source_content_text_sha256_recomputed"]
    assert report["evidence_pack_sha256_recomputable_from_exported_pack"] is False
    assert "independent_human_attestation" in report["acceptance_boundary"]


def test_check_review_pack_accepts_handoff_wrapper() -> None:
    pack = _pack()
    report = MODULE.check_review_pack({"contract_version": "handoff.v1", "review_pack": pack})

    assert report["status"] == "passed"
    assert report["input_shape"] == "handoff_packet"


def test_check_review_pack_rejects_wrong_entry_set_hash() -> None:
    pack = _pack()
    pack["structured_projection"]["entry_set_sha256"] = "f" * 64

    report = MODULE.check_review_pack(pack)

    assert report["status"] == "failed"
    assert (
        "structured_projection.entry_set_sha256 does not match ordered entry hashes"
        in report["errors"]
    )


def test_check_review_pack_rejects_snapshot_text_hash_mismatch() -> None:
    pack = _pack()
    pack["source_snapshot"]["content_text_sha256"] = "f" * 64

    report = MODULE.check_review_pack(pack)

    assert report["status"] == "failed"
    assert (
        "source_snapshot.content_text_sha256 does not match source_content_text"
        in report["errors"]
    )


def test_check_review_pack_rejects_non_64_group_projection() -> None:
    pack = _pack()
    pack["structured_entries"] = pack["structured_entries"][:-1]
    pack["structured_projection"]["entry_count"] = 63

    report = MODULE.check_review_pack(pack)

    assert report["status"] == "failed"
    assert (
        "structured_entries must contain exactly 64 Austria-wide 2026 groups"
        in report["errors"]
    )
