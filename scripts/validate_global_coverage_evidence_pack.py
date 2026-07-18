#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from app.services.coverage_evidence_packs import (  # noqa: E402
    DEFAULT_COVERAGE_EVIDENCE_PACK,
    load_coverage_evidence_pack,
)

TRANCHE_DIRECTORY = ROOT / "knowledge" / "global_coverage" / "tranches"


def discover_canonical_evidence_packs() -> list[Path]:
    paths = {Path(DEFAULT_COVERAGE_EVIDENCE_PACK).resolve()}
    paths.update(path.resolve() for path in TRANCHE_DIRECTORY.glob("*_ready_*.json"))
    return sorted(paths, key=lambda path: path.name)


def validate_sha256_receipt(pack_path: Path) -> str | None:
    receipt_path = pack_path.with_name(f"{pack_path.name}.sha256")
    if not receipt_path.exists():
        return None
    fields = receipt_path.read_text(encoding="utf-8").strip().split()
    if not fields:
        raise ValueError(f"empty SHA-256 receipt: {receipt_path}")
    expected = fields[0].lower()
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ValueError(f"invalid SHA-256 receipt: {receipt_path}")
    actual = hashlib.sha256(pack_path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(
            f"SHA-256 receipt mismatch for {pack_path}: expected {expected}, calculated {actual}"
        )
    return actual


def validate_pack(pack_path: str | Path) -> dict[str, object]:
    path = Path(pack_path).resolve()
    pack = load_coverage_evidence_pack(path)
    summary = pack.summary()
    summary["file_sha256"] = validate_sha256_receipt(path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a review-gated global coverage evidence pack without changing the database."
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--pack", default=DEFAULT_COVERAGE_EVIDENCE_PACK)
    selection.add_argument(
        "--all",
        action="store_true",
        help="Validate the starter and every canonical *_ready_* tranche pack, including SHA-256 receipts.",
    )
    args = parser.parse_args()
    try:
        paths = discover_canonical_evidence_packs() if args.all else [Path(args.pack)]
        summaries = [validate_pack(path) for path in paths]
    except ValueError as exc:
        print(f"Coverage evidence pack validation failed: {exc}", file=sys.stderr)
        return 1
    payload: object
    if args.all:
        payload = {
            "pack_count": len(summaries),
            "packs": summaries,
            "status": "valid",
        }
    else:
        payload = summaries[0]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
