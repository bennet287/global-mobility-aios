from __future__ import annotations

from sqlmodel import Session

from scripts.check_mvp_release import build_mvp_release_status
from scripts.seed_demo_data import seed_demo_data


def _ready_git_status() -> dict:
    return {
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
        "tag_count": 4,
        "git_commands_ok": True,
    }


def test_mvp_release_status_is_ready_after_seed(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    result = build_mvp_release_status(
        db_session,
        git_status=_ready_git_status(),
        quality_results=[{"label": "static", "returncode": 0}],
    )

    assert result["status"] == "ready"
    assert result["mvp_release_version"] == "v6.0"
    assert result["quality_status"] == "passed"
    assert result["git"]["status"] == "ready"
    assert result["demo_release"]["status"] == "ready"
    assert result["demo_release"]["release_version"] == "v5.8"
    assert result["missing_files"] == []


def test_mvp_release_blocks_dirty_worktree(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)
    git_status = _ready_git_status()
    git_status["status"] = "not_ready"
    git_status["working_tree_clean"] = False

    result = build_mvp_release_status(
        db_session,
        git_status=git_status,
        quality_results=[{"label": "static", "returncode": 0}],
    )

    assert result["status"] == "not_ready"
    assert result["git"]["working_tree_clean"] is False


def test_mvp_release_blocks_missing_release_tags(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)
    git_status = _ready_git_status()
    git_status["status"] = "not_ready"
    git_status["missing_release_tags"] = ["demo-release-v5.9"]

    result = build_mvp_release_status(
        db_session,
        git_status=git_status,
        quality_results=[{"label": "static", "returncode": 0}],
    )

    assert result["status"] == "not_ready"
    assert result["git"]["missing_release_tags"] == ["demo-release-v5.9"]


def test_mvp_release_keeps_safety_state_explicit(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    result = build_mvp_release_status(
        db_session,
        git_status=_ready_git_status(),
        quality_results=[{"label": "static", "returncode": 0}],
    )

    assert result["safety"]["auto_send"] == "disabled"
    assert result["safety"]["human_review_required"] is True
    assert result["safety"]["automatic_submission"] == "disabled"
    assert result["safety"]["automatic_lead_conversion"] == "disabled"
