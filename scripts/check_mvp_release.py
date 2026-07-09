#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
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
from scripts.check_demo_release import build_demo_release_status  # noqa: E402
from scripts.check_local_quality import build_quality_commands, run_command  # noqa: E402


MVP_RELEASE_VERSION = "v6.0"
REQUIRED_RELEASE_TAGS = (
    "demo-release-v5.6",
    "demo-release-v5.7",
    "demo-release-v5.8",
    "demo-release-v5.9",
)
REQUIRED_FILES = (
    "scripts/check_mvp_release.py",
    "scripts/check_demo_release.py",
    "scripts/check_local_quality.py",
    "docs/MVP_RELEASE_HARDENING_V6_0.md",
    "docs/DEMO_RELEASE_STATUS_V5_9.md",
    "docs/CHANGELOG.md",
)


def _git_output(args: tuple[str, ...], root: Path = ROOT) -> tuple[int, str]:
    completed = subprocess.run(
        ("git", *args),
        cwd=root,
        text=True,
        capture_output=True,
    )
    return completed.returncode, completed.stdout.strip()


def collect_git_status(root: Path = ROOT) -> dict[str, Any]:
    branch_code, branch = _git_output(("branch", "--show-current"), root)
    head_code, head = _git_output(("rev-parse", "--short", "HEAD"), root)
    status_code, status_output = _git_output(("status", "--porcelain"), root)
    tags_code, tags_output = _git_output(("tag", "--list"), root)

    tags = set(tags_output.splitlines()) if tags_code == 0 and tags_output else set()
    missing_tags = [tag for tag in REQUIRED_RELEASE_TAGS if tag not in tags]
    git_ok = all(code == 0 for code in (branch_code, head_code, status_code, tags_code))
    working_tree_clean = status_code == 0 and not status_output
    return {
        "status": "ready" if git_ok and working_tree_clean and not missing_tags else "not_ready",
        "branch": branch,
        "head": head,
        "working_tree_clean": working_tree_clean,
        "missing_release_tags": missing_tags,
        "required_release_tags": list(REQUIRED_RELEASE_TAGS),
        "tag_count": len(tags),
        "git_commands_ok": git_ok,
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


def _quality_status(quality_results: list[dict[str, Any]] | None) -> str:
    if quality_results is None:
        return "skipped"
    return "passed" if quality_results and all(result["returncode"] == 0 for result in quality_results) else "failed"


def build_mvp_release_status(
    session: Session,
    *,
    git_status: dict[str, Any] | None = None,
    demo_release_status: dict[str, Any] | None = None,
    quality_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    git_status = git_status or collect_git_status()
    demo_release_status = demo_release_status or build_demo_release_status(session, quality_results=None)
    quality_status = _quality_status(quality_results)
    missing_files = _missing_files()
    ready = (
        git_status["status"] == "ready"
        and demo_release_status["status"] == "ready"
        and quality_status in {"passed", "skipped"}
        and not missing_files
    )
    return {
        "status": "ready" if ready else "not_ready",
        "mvp_release_version": MVP_RELEASE_VERSION,
        "quality_status": quality_status,
        "quality_results": quality_results or [],
        "missing_files": missing_files,
        "git": git_status,
        "demo_release": {
            "status": demo_release_status["status"],
            "release_version": demo_release_status["release_version"],
            "demo_readiness": demo_release_status["demo_readiness"]["status"],
            "snapshot": demo_release_status["snapshot"]["status"],
            "runbook": demo_release_status["runbook"]["status"],
            "export_cleanup": demo_release_status["export_cleanup"]["status"],
        },
        "safety": {
            "auto_send": "disabled",
            "human_review_required": True,
            "automatic_submission": "disabled",
            "automatic_lead_conversion": "disabled",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the local MVP release readiness for Global Mobility AIOS.")
    parser.add_argument("--skip-quality", action="store_true", help="Skip local quality commands.")
    parser.add_argument("--full-quality", action="store_true", help="Run the full local quality gate, including pytest.")
    parser.add_argument("--json", action="store_true", help="Print full JSON output.")
    args = parser.parse_args()

    quality_results = None if args.skip_quality else _run_quality(full_quality=args.full_quality)
    create_db_and_tables()
    with Session(engine) as session:
        result = build_mvp_release_status(session, quality_results=quality_results)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"MVP release {result['mvp_release_version']}: {result['status']}")
        print(f"quality_status={result['quality_status']}")
        print(f"git_status={result['git']['status']}")
        print(f"branch={result['git']['branch']}")
        print(f"head={result['git']['head']}")
        print(f"working_tree_clean={result['git']['working_tree_clean']}")
        print(f"demo_release={result['demo_release']['status']} ({result['demo_release']['release_version']})")
        if result["missing_files"]:
            print("missing_files=" + ", ".join(result["missing_files"]))
        if result["git"]["missing_release_tags"]:
            print("missing_release_tags=" + ", ".join(result["git"]["missing_release_tags"]))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
