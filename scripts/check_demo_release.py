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
from scripts.export_demo_snapshot import build_demo_snapshot, default_snapshot_output_path  # noqa: E402
from scripts.print_demo_runbook import build_demo_runbook  # noqa: E402


DEMO_RELEASE_VERSION = "v5.8"
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
    "docs/AGENT_DUPLICATE_OUTPUT_GUARD_V5_6.md",
    "docs/DEMO_UX_POLISH_V5_7.md",
    "docs/DEMO_EXPORT_CLEANUP_V5_8.md",
    "docs/DEMO_RELEASE_STATUS_V5_9.md",
    "docs/CHANGELOG.md",
)
REQUIRED_GITIGNORE_ENTRIES = (
    ".env.production",
    "demo_exports/",
    "demo-snapshot-*.md",
    "demo-snapshot-*.json",
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


def _gitignore_entries(root: Path = ROOT) -> set[str]:
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return set()
    return {
        line.strip()
        for line in gitignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _export_cleanup_status(root: Path = ROOT) -> dict[str, Any]:
    entries = _gitignore_entries(root)
    missing_ignores = [entry for entry in REQUIRED_GITIGNORE_ENTRIES if entry not in entries]
    default_markdown = default_snapshot_output_path("markdown")
    default_json = default_snapshot_output_path("json")
    exports_to_demo_folder = (
        default_markdown.parts[-2:] == ("demo_exports", "demo-snapshot-v5.2.md")
        and default_json.parts[-2:] == ("demo_exports", "demo-snapshot-v5.2.json")
    )
    return {
        "status": "ready" if not missing_ignores and exports_to_demo_folder else "not_ready",
        "missing_gitignore_entries": missing_ignores,
        "default_markdown": str(default_markdown.relative_to(root) if default_markdown.is_absolute() else default_markdown),
        "default_json": str(default_json.relative_to(root) if default_json.is_absolute() else default_json),
        "exports_to_demo_folder": exports_to_demo_folder,
    }


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
    export_cleanup = _export_cleanup_status()
    missing_files = _missing_files()
    quality_status = "skipped" if quality_results is None else ("passed" if _quality_passed(quality_results) else "failed")
    ok = (
        not missing_files
        and readiness["status"] == "ready"
        and snapshot["status"] == "ready"
        and runbook["status"] == "ready"
        and export_cleanup["status"] == "ready"
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
        "export_cleanup": export_cleanup,
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
        print(f"export_cleanup={result['export_cleanup']['status']}")
        if result["missing_files"]:
            print("missing_files=" + ", ".join(result["missing_files"]))
        if result["export_cleanup"]["missing_gitignore_entries"]:
            print("missing_gitignore_entries=" + ", ".join(result["export_cleanup"]["missing_gitignore_entries"]))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
