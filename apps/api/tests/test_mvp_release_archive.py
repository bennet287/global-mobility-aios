from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.export_mvp_release_archive import (
    ARCHIVE_VERSION,
    build_archive_manifest,
    build_release_archive,
    default_archive_output_path,
    resolve_archive_output_path,
)


def _ready_bundle() -> dict:
    return {
        "status": "ready",
        "bundle_version": "v6.1",
        "mvp_release": {
            "mvp_release_version": "v6.0",
            "status": "ready",
            "git": {
                "branch": "feature/mvp-release-bundle-export-v6.1",
                "head": "abc1234",
                "working_tree_clean": True,
                "required_release_tags": ["demo-release-v5.9", "mvp-release-v6.0"],
            },
            "demo_release": {"release_version": "v5.8", "status": "ready"},
            "safety": {
                "auto_send": "disabled",
                "human_review_required": True,
                "automatic_submission": "disabled",
                "automatic_lead_conversion": "disabled",
            },
        },
        "demo_snapshot": {
            "counts": {"demo_leads": 4, "demo_agent_runs": 6, "demo_client_drafts": 6},
            "audit_highlights": {"controlled_agent_run": 6},
        },
        "runbook": {
            "urls": [],
            "flow": [],
        },
        "safety_rules": ["No automatic email, WhatsApp, portal send, application submission, or lead conversion is performed."],
        "base_url": "http://127.0.0.1:8000",
        "generated_at": "2026-07-09T10:00:00Z",
    }


def test_release_archive_paths_use_ignored_release_exports_folder() -> None:
    default_path = default_archive_output_path()
    bare_path = resolve_archive_output_path("handoff.zip")
    nested_path = resolve_archive_output_path("custom_exports/handoff.zip")

    assert default_path.parts[-2:] == ("release_exports", f"mvp-release-archive-{ARCHIVE_VERSION}.zip")
    assert bare_path.parts[-2:] == ("release_exports", "handoff.zip")
    assert nested_path.parts[-2:] == ("custom_exports", "handoff.zip")


def test_release_archive_manifest_reports_ready_state() -> None:
    manifest = build_archive_manifest(
        _ready_bundle(),
        included_files=["release/mvp-release-bundle-v6.1.md", "metadata/manifest.json"],
        missing_docs=[],
        archive_name="archive.zip",
    )

    assert manifest["status"] == "ready"
    assert manifest["archive_version"] == "v6.2"
    assert manifest["bundle_version"] == "v6.1"
    assert manifest["mvp_release_version"] == "v6.0"
    assert manifest["demo_release_version"] == "v5.8"
    assert manifest["safety"]["auto_send"] == "disabled"
    assert "metadata/manifest.json" in manifest["included_files"]


def test_release_archive_zip_contains_bundle_manifest_and_docs(tmp_path: Path) -> None:
    doc = tmp_path / "DOC.md"
    doc.write_text("# Demo Doc\n", encoding="utf-8")

    # Use paths relative to the repository root that are guaranteed to exist in this project.
    output = tmp_path / "mvp-release-archive-test.zip"
    manifest = build_release_archive(
        _ready_bundle(),
        output_path=output,
        doc_paths=("docs/CHANGELOG.md",),
    )

    assert manifest["status"] == "ready"
    assert output.exists()

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "release/mvp-release-bundle-v6.1.md" in names
        assert "release/mvp-release-bundle-v6.1.json" in names
        assert "metadata/manifest.json" in names
        assert "project/docs/CHANGELOG.md" in names
        loaded_manifest = json.loads(archive.read("metadata/manifest.json").decode("utf-8"))

    assert loaded_manifest["archive_version"] == "v6.2"
    assert loaded_manifest["status"] == "ready"
