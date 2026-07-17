#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a review-gated global coverage evidence pack without changing the database."
    )
    parser.add_argument("--pack", default=DEFAULT_COVERAGE_EVIDENCE_PACK)
    args = parser.parse_args()
    try:
        pack = load_coverage_evidence_pack(args.pack)
    except ValueError as exc:
        print(f"Coverage evidence pack validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(pack.summary(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
