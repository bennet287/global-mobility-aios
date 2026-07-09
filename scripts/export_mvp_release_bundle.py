#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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
from scripts.check_mvp_release import build_mvp_release_status  # noqa: E402
from scripts.export_demo_snapshot import build_demo_snapshot  # noqa: E402
from scripts.print_demo_runbook import build_demo_runbook  # noqa: E402


BUNDLE_VERSION = "v6.1"
DEFAULT_EXPORT_DIR = ROOT / "release_exports"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_bundle_output_path(output_format: str) -> Path:
    extension = "md" if output_format == "markdown" else "json"
    return DEFAULT_EXPORT_DIR / f"mvp-release-bundle-{BUNDLE_VERSION}.{extension}"


def resolve_bundle_output_path(output: str | None, output_format: str) -> Path | None:
    if not output:
        return default_bundle_output_path(output_format)
    path = Path(output)
    if not path.is_absolute() and path.parent == Path("."):
        return DEFAULT_EXPORT_DIR / path
    return path


def build_mvp_release_bundle(
    session: Session,
    *,
    base_url: str = DEFAULT_BASE_URL,
    mvp_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mvp_status = mvp_status or build_mvp_release_status(session, quality_results=None)
    snapshot = build_demo_snapshot(session, base_url)
    runbook = build_demo_runbook(base_url)
    return {
        "status": "ready" if mvp_status["status"] == "ready" and snapshot["status"] == "ready" else "not_ready",
        "bundle_version": BUNDLE_VERSION,
        "generated_at": _utcnow_iso(),
        "base_url": base_url.rstrip("/"),
        "mvp_release": mvp_status,
        "demo_snapshot": {
            "status": snapshot["status"],
            "snapshot_version": snapshot["snapshot_version"],
            "counts": snapshot["counts"],
            "agent_status_counts": snapshot["agent_status_counts"],
            "client_draft_status_counts": snapshot["client_draft_status_counts"],
            "audit_highlights": snapshot["audit_highlights"],
        },
        "runbook": {
            "status": runbook["status"],
            "urls": runbook["urls"],
            "flow": runbook["flow"],
        },
        "safety_rules": runbook["safety_rules"],
    }


def render_markdown(bundle: dict[str, Any]) -> str:
    mvp = bundle["mvp_release"]
    demo = bundle["demo_snapshot"]
    lines = [
        "# Global Mobility AIOS MVP Release Bundle",
        "",
        f"- Bundle status: `{bundle['status']}`",
        f"- Bundle version: `{bundle['bundle_version']}`",
        f"- Generated at: `{bundle['generated_at']}`",
        f"- Base URL: `{bundle['base_url']}`",
        f"- MVP release: `{mvp['mvp_release_version']}`",
        f"- MVP status: `{mvp['status']}`",
        f"- Demo release: `{mvp['demo_release']['release_version']}`",
        f"- Demo status: `{mvp['demo_release']['status']}`",
        f"- Git branch: `{mvp['git']['branch']}`",
        f"- Git head: `{mvp['git']['head']}`",
        f"- Working tree clean: `{mvp['git']['working_tree_clean']}`",
        "",
        "## Demo Counts",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in demo["counts"].items():
        lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## Audit Highlights",
        "",
        "| Action | Count |",
        "|---|---:|",
    ])
    for action, count in demo["audit_highlights"].items():
        lines.append(f"| {action} | {count} |")

    lines.extend([
        "",
        "## Required Release Tags",
        "",
    ])
    for tag in mvp["git"]["required_release_tags"]:
        lines.append(f"- `{tag}`")

    lines.extend([
        "",
        "## Demo URLs",
        "",
    ])
    for item in bundle["runbook"]["urls"]:
        lines.append(f"- [{item['label']}]({item['url']}) - {item['purpose']}")

    lines.extend([
        "",
        "## Demo Flow",
        "",
    ])
    for index, step in enumerate(bundle["runbook"]["flow"], start=1):
        lines.append(f"{index}. {step}")

    lines.extend([
        "",
        "## Safety Rules",
        "",
    ])
    for rule in bundle["safety_rules"]:
        lines.append(f"- {rule}")

    lines.append("")
    return "\n".join(lines)


def _write_or_print(text: str, output: str | None, output_format: str) -> None:
    if output:
        path = resolve_bundle_output_path(output, output_format)
        assert path is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"MVP release bundle written to {path}")
    else:
        print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a local MVP release bundle for Global Mobility AIOS.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Local API base URL.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown", help="Output format.")
    parser.add_argument(
        "--output",
        default="",
        help="Optional output file path. Bare filenames are written under release_exports/.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing to release_exports/.")
    args = parser.parse_args()

    create_db_and_tables()
    with Session(engine) as session:
        bundle = build_mvp_release_bundle(session, base_url=args.base_url)

    output = None if args.stdout else args.output or str(default_bundle_output_path(args.format))
    if args.format == "markdown":
        _write_or_print(render_markdown(bundle), output, args.format)
    else:
        _write_or_print(json.dumps(bundle, indent=2, sort_keys=True), output, args.format)
    return 0 if bundle["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
