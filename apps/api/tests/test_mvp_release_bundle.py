from __future__ import annotations

from sqlmodel import Session

from scripts.export_mvp_release_bundle import (
    build_mvp_release_bundle,
    default_bundle_output_path,
    render_markdown,
    resolve_bundle_output_path,
)
from scripts.seed_demo_data import seed_demo_data


def _ready_mvp_status() -> dict:
    return {
        "status": "ready",
        "mvp_release_version": "v6.0",
        "quality_status": "passed",
        "quality_results": [],
        "missing_files": [],
        "git": {
            "status": "ready",
            "branch": "feature/mvp-release-hardening-v6.0",
            "head": "abc1234",
            "working_tree_clean": True,
            "missing_release_tags": [],
            "required_release_tags": [
                "demo-release-v5.6",
                "demo-release-v5.7",
                "demo-release-v5.8",
                "demo-release-v5.9",
            ],
            "tag_count": 5,
            "git_commands_ok": True,
        },
        "demo_release": {
            "status": "ready",
            "release_version": "v5.8",
            "demo_readiness": "ready",
            "snapshot": "ready",
            "runbook": "ready",
            "export_cleanup": "ready",
        },
        "safety": {
            "auto_send": "disabled",
            "human_review_required": True,
            "automatic_submission": "disabled",
            "automatic_lead_conversion": "disabled",
        },
    }


def test_mvp_release_bundle_reports_ready_demo_state(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    bundle = build_mvp_release_bundle(
        db_session,
        base_url="http://localhost:9000",
        mvp_status=_ready_mvp_status(),
    )

    assert bundle["status"] == "ready"
    assert bundle["bundle_version"] == "v6.1"
    assert bundle["base_url"] == "http://localhost:9000"
    assert bundle["mvp_release"]["mvp_release_version"] == "v6.0"
    assert bundle["demo_snapshot"]["status"] == "ready"
    assert bundle["demo_snapshot"]["counts"]["demo_leads"] == 4
    assert len(bundle["runbook"]["urls"]) >= 5


def test_mvp_release_bundle_markdown_contains_handoff_sections(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)
    bundle = build_mvp_release_bundle(db_session, mvp_status=_ready_mvp_status())

    markdown = render_markdown(bundle)

    assert "# Global Mobility AIOS MVP Release Bundle" in markdown
    assert "## Demo Counts" in markdown
    assert "## Audit Highlights" in markdown
    assert "## Required Release Tags" in markdown
    assert "## Safety Rules" in markdown
    assert "demo-release-v5.9" in markdown
    assert "/admin/agent-output-reviews" in markdown
    assert "No automatic email" in markdown


def test_mvp_release_bundle_paths_use_ignored_release_exports_folder() -> None:
    default_markdown = default_bundle_output_path("markdown")
    default_json = default_bundle_output_path("json")
    bare_markdown = resolve_bundle_output_path("handoff.md", "markdown")
    nested_json = resolve_bundle_output_path("custom_exports/handoff.json", "json")

    assert default_markdown.parts[-2:] == ("release_exports", "mvp-release-bundle-v6.1.md")
    assert default_json.parts[-2:] == ("release_exports", "mvp-release-bundle-v6.1.json")
    assert bare_markdown.parts[-2:] == ("release_exports", "handoff.md")
    assert nested_json.parts[-2:] == ("custom_exports", "handoff.json")
