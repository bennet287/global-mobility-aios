#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from sqlmodel import Session  # noqa: E402

from app.core.db import create_db_and_tables, engine  # noqa: E402
from scripts.check_demo_readiness import check_demo_readiness  # noqa: E402
from scripts.check_local_quality import build_quality_commands, run_command  # noqa: E402
from scripts.export_demo_snapshot import build_demo_snapshot  # noqa: E402
from scripts.print_demo_runbook import build_demo_runbook  # noqa: E402


DEMO_RELEASE_VERSION = "v5.5"
REQUIRED_FILES = (
    "scripts/check_local_quality.py",
    "scripts/check_demo_readiness.py",
    "scripts/print_demo_runbook.py",
    "scripts/export_demo_snapshot.py",
    "scripts/check_demo_release.py",
    "docs/DEMO_RELEASE_RUNBOOK_V5_1.md",
    "docs/DEMO_SNAPSHOT_EXPORT_V5_2.md",
    "docs/DEMO_NAVIGATION_POLISH_V5_3.md",
    "docs/DEMO_READINESS_BANNER_V5_4.md",
    "docs/DEMO_RELEASE_V5_5.md",
    "docs/CHANGELOG.md",
)
REQUIRED_URLS = {
    "/admin/v2",
    "/admin/controlled-agents",
    "/admin/agent-output-reviews",
    "/admin/client-communications/drafts",
    "/admin/audit-logs",
}
REQUIRED_SAFETY_TERMS = {
    "human review",
    "no automatic email",
    "whatsapp",
    "application submission",
    "lead conversion",
}


def _missing_files(root: Path = ROOT) -> list[str]:
    return [path for path in REQUIRED_FILES if not (root / path).exists()]


def _run_quality(*, full_quality: bool) -> list[dict[str, Any]]:
    results = []
    for command in build_quality_commands(skip_pytest=not full_quality):
        result = run_command(command)
        results.append(result)
        if result["returncode"] != 0:
            break
    return results


def _quality_passed(results: list[dict[str, Any]]) -> bool:
    return bool(results) and all(result["returncode"] == 0 for result in results)


def _runbook_status() -> dict[str, Any]:
    runbook = build_demo_runbook()
    paths = {item["url"].replace(runbook["base_url"], "") for item in runbook["urls"]}
    safety = " ".join(runbook["safety_rules"]).lower()
    return {
        "status": "ready" if REQUIRED_URLS <= paths and all(term in safety for term in REQUIRED_SAFETY_TERMS) else "not_ready",
        "missing_urls": sorted(REQUIRED_URLS - paths),
        "missing_safety_terms": sorted(term for term in REQUIRED_SAFETY_TERMS if term not in safety),
    }


def build_demo_release_status(
    session: Session,
    *,
    quality_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    readiness = check_demo_readiness(session)
    snapshot = build_demo_snapshot(session)
    runbook = _runbook_status()
    missing_files = _missing_files()
    quality_status = "skipped" if quality_results is None else ("passed" if _quality_passed(quality_results) else "failed")
    ok = (
        not missing_files
        and readiness["status"] == "ready"
        and snapshot["status"] == "ready"
        and runbook["status"] == "ready"
        and quality_status in {"passed", "skipped"}
    )
    return {
        "status": "ready" if ok else "not_ready",
        "release_version": DEMO_RELEASE_VERSION,
        "quality_status": quality_status,
        "quality_results": quality_results or [],
        "missing_files": missing_files,
        "demo_readiness": readiness,
        "snapshot": {
            "status": snapshot["status"],
            "counts": snapshot["counts"],
            "audit_highlights": snapshot["audit_highlights"],
        },
        "runbook": runbook,
        "safety": {
            "auto_send": "disabled",
            "human_review_required": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the local demo release checkpoint for Global Mobility AIOS.")
    parser.add_argument("--skip-quality", action="store_true", help="Skip local quality commands.")
    parser.add_argument("--full-quality", action="store_true", help="Run the full local quality gate, including pytest.")
    parser.add_argument("--json", action="store_true", help="Print full JSON output.")
    args = parser.parse_args()

    quality_results = None if args.skip_quality else _run_quality(full_quality=args.full_quality)
    create_db_and_tables()
    with Session(engine) as session:
        result = build_demo_release_status(session, quality_results=quality_results)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Demo release {result['release_version']}: {result['status']}")
        print(f"quality_status={result['quality_status']}")
        print(f"demo_readiness={result['demo_readiness']['status']}")
        print(f"snapshot_status={result['snapshot']['status']}")
        print(f"runbook_status={result['runbook']['status']}")
        if result["missing_files"]:
            print("missing_files=" + ", ".join(result["missing_files"]))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
