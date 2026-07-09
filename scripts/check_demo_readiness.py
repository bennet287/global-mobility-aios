#!/usr/bin/env python3
from __future__ import annotations

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

from sqlmodel import Session, select  # noqa: E402

from app.core.db import create_db_and_tables, engine  # noqa: E402
from app.models.domain import AgentRun, AuditLog, Lead  # noqa: E402
from scripts.seed_demo_data import DEMO_SOURCE  # noqa: E402


REQUIRED_LEADS = {
    "Demo 1 - Blocked Visa Claim",
    "Demo 2 - Documents Pending",
    "Demo 3 - Ready For Application",
    "Demo 4 - Completed Journey",
}
REQUIRED_AGENT_STATUSES = {"completed", "approved", "rejected", "converted"}
REQUIRED_AUDIT_ACTIONS = {
    "controlled_agent_run",
    "agent_output_approved",
    "agent_output_rejected",
    "agent_output_converted_to_client_draft",
}


def _same_id(a: Any, b: Any) -> bool:
    return str(a or "").replace("-", "").lower() == str(b or "").replace("-", "").lower()


def check_demo_readiness(session: Session) -> dict[str, Any]:
    leads = session.exec(select(Lead).where(Lead.source == DEMO_SOURCE)).all()
    lead_ids = {lead.id for lead in leads}
    agent_runs = [
        run for run in session.exec(select(AgentRun)).all()
        if any(_same_id(run.lead_id, lead_id) for lead_id in lead_ids)
    ]
    audits = session.exec(select(AuditLog)).all()

    lead_names = {lead.full_name for lead in leads}
    agent_statuses = {run.status for run in agent_runs}
    audit_actions = {audit.action for audit in audits if audit.source == DEMO_SOURCE}

    missing_leads = sorted(REQUIRED_LEADS - lead_names)
    missing_statuses = sorted(REQUIRED_AGENT_STATUSES - agent_statuses)
    missing_audits = sorted(REQUIRED_AUDIT_ACTIONS - audit_actions)
    ok = not missing_leads and not missing_statuses and not missing_audits

    return {
        "status": "ready" if ok else "not_ready",
        "demo_source": DEMO_SOURCE,
        "demo_leads": len(leads),
        "demo_agent_runs": len(agent_runs),
        "agent_statuses": sorted(agent_statuses),
        "audit_actions_present": sorted(audit_actions),
        "missing_leads": missing_leads,
        "missing_agent_statuses": missing_statuses,
        "missing_audit_actions": missing_audits,
        "admin_entrypoints": [
            "/admin/v2",
            "/admin/controlled-agents",
            "/admin/agent-output-reviews",
            "/admin/client-communications",
            "/admin/audit-logs",
        ],
    }


def main() -> int:
    create_db_and_tables()
    with Session(engine) as session:
        result = check_demo_readiness(session)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
