#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "austria-source-certification-review-pack-check.v1"
EXPECTED_PACK_VERSION = "source_certification_structured_evidence_v1"
EXPECTED_JURISDICTION_CODE = "AT"
EXPECTED_YEAR = 2026
EXPECTED_SCOPE = "national"
EXPECTED_ENTRY_COUNT = 64


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_canonical(value: object) -> str:
    return _sha256_text(_canonical_json(value))


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdefABCDEF" for char in value)
    )


def _require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def load_review_pack(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Unable to read review pack: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Review pack is not valid JSON: {exc}") from exc
    return _require_mapping(payload, "review pack")


def check_review_pack(payload: dict[str, Any]) -> dict[str, Any]:
    nested_review_pack = payload.get("review_pack")
    input_shape = "handoff_packet" if isinstance(nested_review_pack, dict) else "review_pack"
    pack = nested_review_pack if isinstance(nested_review_pack, dict) else payload
    errors: list[str] = []

    if pack.get("pack_version") != EXPECTED_PACK_VERSION:
        errors.append(f"pack_version must be {EXPECTED_PACK_VERSION}")
    if pack.get("certification_status") != "pending_review":
        errors.append("certification_status must be pending_review")

    evidence_hash = pack.get("evidence_pack_sha256")
    if not _is_sha256(evidence_hash):
        errors.append("evidence_pack_sha256 must be a 64-character hexadecimal SHA-256")

    jurisdiction = pack.get("jurisdiction")
    if not isinstance(jurisdiction, dict):
        errors.append("jurisdiction must be a JSON object")
    elif str(jurisdiction.get("code", "")).strip().upper() != EXPECTED_JURISDICTION_CODE:
        errors.append("jurisdiction.code must be AT")

    snapshot = pack.get("source_snapshot")
    if not isinstance(snapshot, dict):
        errors.append("source_snapshot must be a JSON object")
        snapshot = {}

    projection = pack.get("structured_projection")
    if not isinstance(projection, dict):
        errors.append("structured_projection must be a JSON object")
        projection = {}

    if projection.get("year") != EXPECTED_YEAR:
        errors.append(f"structured_projection.year must be {EXPECTED_YEAR}")
    if projection.get("scope") != EXPECTED_SCOPE:
        errors.append(f"structured_projection.scope must be {EXPECTED_SCOPE}")

    entries = pack.get("structured_entries")
    if not isinstance(entries, list):
        errors.append("structured_entries must be an array")
        entries = []
    if len(entries) != EXPECTED_ENTRY_COUNT:
        errors.append(
            f"structured_entries must contain exactly {EXPECTED_ENTRY_COUNT} Austria-wide 2026 groups"
        )
    if projection.get("entry_count") != len(entries):
        errors.append("structured_projection.entry_count must equal structured_entries length")

    ordinals: list[object] = []
    entry_hashes: list[str] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"structured_entries[{index - 1}] must be a JSON object")
            continue
        ordinals.append(entry.get("source_ordinal"))
        entry_hash = entry.get("entry_sha256")
        if not _is_sha256(entry_hash):
            errors.append(f"structured_entries[{index - 1}].entry_sha256 is not a SHA-256")
            continue
        entry_hashes.append(str(entry_hash).lower())

    if ordinals != list(range(1, len(entries) + 1)):
        errors.append("structured_entries source_ordinal values must be contiguous from 1")

    expected_entry_set_sha256: str | None = None
    if len(entry_hashes) == len(entries):
        expected_entry_set_sha256 = _sha256_canonical(entry_hashes)
        actual_entry_set_sha256 = projection.get("entry_set_sha256")
        if not _is_sha256(actual_entry_set_sha256):
            errors.append("structured_projection.entry_set_sha256 is not a SHA-256")
        elif str(actual_entry_set_sha256).lower() != expected_entry_set_sha256:
            errors.append("structured_projection.entry_set_sha256 does not match ordered entry hashes")

    source_content_text = pack.get("source_content_text")
    source_content_text_sha256: str | None = None
    if not isinstance(source_content_text, str) or not source_content_text:
        errors.append("source_content_text must be a non-empty string")
    else:
        source_content_text_sha256 = _sha256_text(source_content_text)
        snapshot_text_sha256 = snapshot.get("content_text_sha256")
        if not _is_sha256(snapshot_text_sha256):
            errors.append("source_snapshot.content_text_sha256 is not a SHA-256")
        elif str(snapshot_text_sha256).lower() != source_content_text_sha256:
            errors.append("source_snapshot.content_text_sha256 does not match source_content_text")

    snapshot_content_hash = snapshot.get("content_hash")
    projection_snapshot_content_hash = projection.get("source_snapshot_content_hash")
    if not _is_sha256(snapshot_content_hash):
        errors.append("source_snapshot.content_hash is not a SHA-256")
    if not _is_sha256(projection_snapshot_content_hash):
        errors.append("structured_projection.source_snapshot_content_hash is not a SHA-256")
    if (
        _is_sha256(snapshot_content_hash)
        and _is_sha256(projection_snapshot_content_hash)
        and str(snapshot_content_hash).lower() != str(projection_snapshot_content_hash).lower()
    ):
        errors.append(
            "structured_projection.source_snapshot_content_hash does not match source_snapshot.content_hash"
        )

    return {
        "contract_version": CONTRACT_VERSION,
        "status": "passed" if not errors else "failed",
        "input_shape": input_shape,
        "errors": errors,
        "checks": {
            "jurisdiction_code": EXPECTED_JURISDICTION_CODE,
            "year": EXPECTED_YEAR,
            "scope": EXPECTED_SCOPE,
            "expected_entry_count": EXPECTED_ENTRY_COUNT,
            "actual_entry_count": len(entries),
            "source_ordinals_contiguous": ordinals == list(range(1, len(entries) + 1)),
            "entry_set_sha256_recomputed": expected_entry_set_sha256,
            "source_content_text_sha256_recomputed": source_content_text_sha256,
            "source_snapshot_content_hash_pinned": snapshot_content_hash,
            "evidence_pack_sha256_pinned": evidence_hash,
        },
        "evidence_pack_sha256_recomputable_from_exported_pack": False,
        "evidence_pack_sha256_reproducibility_note": (
            "The exported v1 review pack does not include the complete canonical_evidence object used by "
            "source_certification_review.py to compute evidence_pack_sha256. This checker therefore verifies "
            "the pinned evidence hash format but does not claim to independently recompute it."
        ),
        "acceptance_boundary": (
            "This is deterministic internal-integrity checking only. It does not compare the pack with the "
            "current government page and does not satisfy independent_human_attestation."
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check deterministic internal invariants of the Austria 2026 source-certification review pack. "
            "This tool never submits or approves a certification."
        )
    )
    parser.add_argument("--review-pack", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        pack = load_review_pack(args.review_pack)
        report = check_review_pack(pack)
    except ValueError as exc:
        report = {
            "contract_version": CONTRACT_VERSION,
            "status": "failed",
            "errors": [str(exc)],
            "acceptance_boundary": (
                "This is deterministic internal-integrity checking only and cannot satisfy "
                "independent_human_attestation."
            ),
        }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get("status") == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
