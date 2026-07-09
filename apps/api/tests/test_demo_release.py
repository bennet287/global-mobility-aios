from __future__ import annotations

from sqlmodel import Session

from scripts.check_demo_release import build_demo_release_status
from scripts.seed_demo_data import seed_demo_data


def test_demo_release_status_is_ready_after_seed(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    result = build_demo_release_status(db_session, quality_results=[{"label": "static", "returncode": 0}])

    assert result["status"] == "ready"
    assert result["release_version"] == "v5.5"
    assert result["quality_status"] == "passed"
    assert result["missing_files"] == []
    assert result["demo_readiness"]["status"] == "ready"
    assert result["snapshot"]["status"] == "ready"
    assert result["runbook"]["status"] == "ready"


def test_demo_release_reports_quality_failure(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    result = build_demo_release_status(db_session, quality_results=[{"label": "static", "returncode": 1}])

    assert result["status"] == "not_ready"
    assert result["quality_status"] == "failed"


def test_demo_release_keeps_safety_state_explicit(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    result = build_demo_release_status(db_session, quality_results=[{"label": "static", "returncode": 0}])

    assert result["safety"]["auto_send"] == "disabled"
    assert result["safety"]["human_review_required"] is True
    assert result["runbook"]["missing_safety_terms"] == []
