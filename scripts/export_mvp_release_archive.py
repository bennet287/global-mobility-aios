#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
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
from scripts.export_mvp_release_bundle import (  # noqa: E402
    build_mvp_release_bundle,
    render_markdown as render_bundle_markdown,
)

ARCHIVE_VERSION = "v6.2"
DEFAULT_EXPORT_DIR = ROOT / "release_exports"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_DOCS = (
    "docs/CHANGELOG.md",
    "docs/DEMO_RELEASE_RUNBOOK_V5_1.md",
    "docs/DEMO_SNAPSHOT_EXPORT_V5_2.md",
    "docs/DEMO_READINESS_BANNER_V5_4.md",
    "docs/DEMO_RELEASE_STATUS_V5_9.md",
    "docs/AGENT_DUPLICATE_OUTPUT_GUARD_V5_6.md",
    "docs/DEMO_UX_POLISH_V5_7.md",
    "docs/DEMO_EXPORT_CLEANUP_V5_8.md",
    "docs/MVP_RELEASE_HARDENING_V6_0.md",
    "docs/MVP_RELEASE_BUNDLE_EXPORT_V6_1.md",
    "docs/MVP_RELEASE_ARCHIVE_V6_2.md",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_archive_output_path() -> Path:
    return DEFAULT_EXPORT_DIR / f"mvp-release-archive-{ARCHIVE_VERSION}.zip"


def resolve_archive_output_path(output: str | None) -> Path:
    if not output:
        return default_archive_output_path()
    path = Path(output)
    if not path.is_absolute() and path.parent == Path("."):
        return DEFAULT_EXPORT_DIR / path
    return path


def _safe_read_text(relative_path: str) -> str | None:
    path = ROOT / relative_path
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def build_archive_manifest(
    bundle: dict[str, Any],
    *,
    included_files: list[str],
    missing_docs: list[str],
    archive_name: str,
) -> dict[str, Any]:
    mvp = bundle["mvp_release"]
    return {
        "status": "ready" if bundle["status"] == "ready" and not missing_docs else "not_ready",
        "archive_version": ARCHIVE_VERSION,
        "archive_name": archive_name,
        "generated_at": _utcnow_iso(),
        "bundle_version": bundle["bundle_version"],
        "mvp_release_version": mvp["mvp_release_version"],
        "demo_release_version": mvp["demo_release"]["release_version"],
        "git": {
            "branch": mvp["git"]["branch"],
            "head": mvp["git"]["head"],
            "working_tree_clean": mvp["git"]["working_tree_clean"],
            "required_release_tags": mvp["git"].get("required_release_tags", []),
        },
        "safety": mvp["safety"],
        "demo_counts": bundle["demo_snapshot"]["counts"],
        "included_files": included_files,
        "missing_docs": missing_docs,
    }


def build_release_archive(
    bundle: dict[str, Any],
    *,
    output_path: Path,
    doc_paths: tuple[str, ...] = DEFAULT_DOCS,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bundle_json = json.dumps(bundle, indent=2, sort_keys=True)
    bundle_markdown = render_bundle_markdown(bundle)

    included_files = [
        "release/mvp-release-bundle-v6.1.md",
        "release/mvp-release-bundle-v6.1.json",
    ]
    missing_docs: list[str] = []
    docs_to_write: list[tuple[str, str]] = []

    for relative_path in doc_paths:
        content = _safe_read_text(relative_path)
        if content is None:
            missing_docs.append(relative_path)
            continue
        archive_path = f"project/{relative_path}"
        included_files.append(archive_path)
        docs_to_write.append((archive_path, content))

    manifest = build_archive_manifest(
        bundle,
        included_files=included_files + ["metadata/manifest.json"],
        missing_docs=missing_docs,
        archive_name=output_path.name,
    )

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("release/mvp-release-bundle-v6.1.md", bundle_markdown)
        archive.writestr("release/mvp-release-bundle-v6.1.json", bundle_json)
        for archive_path, content in docs_to_write:
            archive.writestr(archive_path, content)
        archive.writestr("metadata/manifest.json", json.dumps(manifest, indent=2, sort_keys=True))

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a local shareable MVP release archive zip.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Local API base URL.")
    parser.add_argument(
        "--output",
        default="",
        help="Optional output zip path. Bare filenames are written under release_exports/.",
    )
    parser.add_argument("--json", action="store_true", help="Print manifest JSON after creating the archive.")
    args = parser.parse_args()

    create_db_and_tables()
    with Session(engine) as session:
        bundle = build_mvp_release_bundle(session, base_url=args.base_url)

    output_path = resolve_archive_output_path(args.output)
    manifest = build_release_archive(bundle, output_path=output_path)

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(f"MVP release archive written to {output_path}")
        print(f"archive_status={manifest['status']}")
        print(f"included_files={len(manifest['included_files'])}")
        if manifest["missing_docs"]:
            print("missing_docs=" + ",".join(manifest["missing_docs"]))

    return 0 if manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
