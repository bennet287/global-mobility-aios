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

from sqlmodel import Session  # noqa: E402

from app.core.db import engine  # noqa: E402
from app.services.jurisdiction_registry import import_un_m49_registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import the fixed allowlisted UN M49 jurisdiction registry source."
    )
    parser.add_argument("--actor", default="registry-seed-script")
    args = parser.parse_args()
    with Session(engine) as session:
        release, created = import_un_m49_registry(session, actor=args.actor)
    print(json.dumps({
        "created": created,
        "version": release.version,
        "source_sha256": release.source_sha256,
        "imported_entries": release.imported_entries,
        "status": release.status,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
