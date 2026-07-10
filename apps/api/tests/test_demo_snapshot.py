from __future__ import annotations

import sys
from pathlib import Path

from sqlmodel import Session

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.export_demo_snapshot import (  # noqa: E402
    build_demo_snapshot,
    default_snapshot_output_path,
    render_markdown,
    resolve_snapshot_output_path,
)
from scripts.seed_demo_data import seed_demo_data  # noqa: E402


def test_demo_snapshot_reports_seeded_demo_state(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    snapshot = build_demo_snapshot(db_session, "http://localhost:9000")

    assert snapshot["status"] == "ready"
    assert snapshot["snapshot_version"] == "v5.2"
    assert snapshot["base_url"] == "http://localhost:9000"
    assert snapshot["counts"]["demo_leads"] == 4
    assert snapshot["counts"]["demo_agent_runs"] == 4
    assert snapshot["counts"]["demo_client_drafts"] >= 5
    assert {"completed", "approved", "rejected", "converted"} <= set(snapshot["agent_status_counts"])


def test_demo_snapshot_tracks_draft_and_audit_highlights(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    snapshot = build_demo_snapshot(db_session)

    assert snapshot["client_draft_status_counts"]["reviewed"] >= 5
    assert snapshot["audit_highlights"]["controlled_agent_run"] >= 1
    assert snapshot["audit_highlights"]["agent_output_approved"] >= 1
    assert snapshot["audit_highlights"]["agent_output_rejected"] >= 1
    assert snapshot["audit_highlights"]["agent_output_converted_to_client_draft"] >= 1
    assert snapshot["audit_highlights"]["client_draft_reviewed"] >= 1


def test_demo_snapshot_markdown_contains_demo_sections(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)
    snapshot = build_demo_snapshot(db_session)

    markdown = render_markdown(snapshot)

    assert "# Global Mobility AIOS Demo Snapshot" in markdown
    assert "## Lead Summary" in markdown
    assert "Demo 3 - Ready For Application" in markdown
    assert "/admin/controlled-agents" in markdown
    assert "/admin/client-communications/drafts" in markdown
    assert "No automatic email" in markdown


def test_demo_snapshot_export_paths_use_ignored_demo_exports_folder() -> None:
    default_markdown = default_snapshot_output_path("markdown")
    default_json = default_snapshot_output_path("json")
    bare_markdown = resolve_snapshot_output_path("demo-snapshot-custom.md", "markdown")
    nested_markdown = resolve_snapshot_output_path("custom_exports/demo-snapshot-custom.md", "markdown")

    assert default_markdown.parts[-2:] == ("demo_exports", "demo-snapshot-v5.2.md")
    assert default_json.parts[-2:] == ("demo_exports", "demo-snapshot-v5.2.json")
    assert bare_markdown.parts[-2:] == ("demo_exports", "demo-snapshot-custom.md")
    assert nested_markdown.parts[-2:] == ("custom_exports", "demo-snapshot-custom.md")
