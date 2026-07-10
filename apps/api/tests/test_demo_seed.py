from __future__ import annotations

import sys
from pathlib import Path

from sqlmodel import Session, select

from app.models.domain import AgentRun, AuditLog, Lead

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_demo_readiness import check_demo_readiness  # noqa: E402
from scripts.seed_demo_data import DEMO_SOURCE, seed_demo_data  # noqa: E402


def test_demo_seed_creates_exactly_four_demo_leads(db_session: Session) -> None:
    summary = seed_demo_data(db_session, reset_demo=True)

    demo_leads = db_session.exec(select(Lead).where(Lead.source == DEMO_SOURCE)).all()

    assert summary["status"] == "seeded"
    assert summary["demo_version"] == "v4.4"
    assert summary["demo_leads"] == 4
    assert summary["demo_agent_runs"] == 4
    assert {"completed", "approved", "rejected", "converted"} <= set(summary["agent_status_counts"])
    assert len(demo_leads) == 4
    assert {
        "Demo 1 - Blocked Visa Claim",
        "Demo 2 - Documents Pending",
        "Demo 3 - Ready For Application",
        "Demo 4 - Completed Journey",
    } == {lead.full_name for lead in demo_leads}

    agent_runs = db_session.exec(select(AgentRun)).all()
    audit_actions = {audit.action for audit in db_session.exec(select(AuditLog)).all()}

    assert {run.status for run in agent_runs} >= {"completed", "approved", "rejected", "converted"}
    assert "agent_output_approved" in audit_actions
    assert "agent_output_rejected" in audit_actions
    assert "agent_output_converted_to_client_draft" in audit_actions


def test_demo_readiness_check_passes_after_seed(db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    result = check_demo_readiness(db_session)

    assert result["status"] == "ready"
    assert result["demo_leads"] == 4
    assert set(result["agent_statuses"]) >= {"completed", "approved", "rejected", "converted"}
    assert result["missing_leads"] == []
    assert result["missing_agent_statuses"] == []
    assert result["missing_audit_actions"] == []
