#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from sqlmodel import Session, select  # noqa: E402

from app.core.db import create_db_and_tables, engine  # noqa: E402
from app.models.domain import AgentRun, AuditLog, FollowUp, Lead  # noqa: E402
from scripts.check_demo_readiness import check_demo_readiness  # noqa: E402
from scripts.print_demo_runbook import DEFAULT_BASE_URL, DEMO_URLS  # noqa: E402
from scripts.seed_demo_data import CLIENT_DRAFT_PREFIX, DEMO_SOURCE  # noqa: E402


SNAPSHOT_VERSION = "v5.2"
DEMO_AUDIT_ACTIONS = (
    "controlled_agent_run",
    "agent_output_approved",
    "agent_output_rejected",
    "agent_output_converted_to_client_draft",
    "client_draft_reviewed",
)
SAFETY_RULES = (
    "Controlled agents create internal operator outputs only.",
    "Agent output conversion creates reviewable client communication drafts only.",
    "Client communication drafts require human review before any manual send/export.",
    "No automatic email, WhatsApp, portal message, application submission, or lead conversion is performed by the local MVP.",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _same_id(a: Any, b: Any) -> bool:
    return str(a or "").replace("-", "").lower() == str(b or "").replace("-", "").lower()


def _count_values(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(_value(value)) for value in values).items()))


def _public_draft_status(status: Any) -> str:
    value = str(_value(status))
    if value == "pending":
        return "draft"
    if value == "completed":
        return "reviewed"
    return value


def _is_demo_related(row: Any, ids: set[str]) -> bool:
    entity_id = str(getattr(row, "entity_id", "") or "")
    source = getattr(row, "source", None)
    return source == DEMO_SOURCE or any(_same_id(entity_id, item_id) for item_id in ids)


def _demo_leads(session: Session) -> list[Lead]:
    leads = session.exec(select(Lead).where(Lead.source == DEMO_SOURCE)).all()
    return sorted(leads, key=lambda lead: str(getattr(lead, "full_name", "")))


def _demo_agent_runs(session: Session, lead_ids: set[str]) -> list[AgentRun]:
    runs = session.exec(select(AgentRun)).all()
    return [
        run for run in runs
        if any(_same_id(getattr(run, "lead_id", None), lead_id) for lead_id in lead_ids)
    ]


def _demo_client_drafts(session: Session, lead_ids: set[str]) -> list[FollowUp]:
    drafts = [
        follow_up for follow_up in session.exec(select(FollowUp)).all()
        if CLIENT_DRAFT_PREFIX in str(getattr(follow_up, "message", "") or "")
        and any(_same_id(getattr(follow_up, "lead_id", None), lead_id) for lead_id in lead_ids)
    ]
    return sorted(drafts, key=lambda row: str(getattr(row, "created_at", "")))


def _lead_summary(lead: Lead, drafts: list[FollowUp], runs: list[AgentRun]) -> dict[str, Any]:
    lead_id = str(getattr(lead, "id", ""))
    lead_drafts = [
        draft for draft in drafts
        if _same_id(getattr(draft, "lead_id", None), lead_id)
    ]
    lead_runs = [
        run for run in runs
        if _same_id(getattr(run, "lead_id", None), lead_id)
    ]
    return {
        "id": lead_id,
        "name": getattr(lead, "full_name", ""),
        "email": getattr(lead, "email", None),
        "intent": str(_value(getattr(lead, "intent", ""))),
        "target_country": getattr(lead, "target_country", None),
        "status": str(_value(getattr(lead, "status", ""))),
        "client_drafts": len(lead_drafts),
        "agent_runs": len(lead_runs),
        "agent_statuses": _count_values(getattr(run, "status", "") for run in lead_runs),
        "draft_statuses": _count_values(_public_draft_status(getattr(draft, "status", "")) for draft in lead_drafts),
    }


def build_demo_snapshot(session: Session, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    leads = _demo_leads(session)
    lead_ids = {str(getattr(lead, "id", "")) for lead in leads}
    agent_runs = _demo_agent_runs(session, lead_ids)
    client_drafts = _demo_client_drafts(session, lead_ids)
    related_ids = lead_ids | {str(getattr(run, "id", "")) for run in agent_runs} | {str(getattr(draft, "id", "")) for draft in client_drafts}
    audit_logs = [
        audit for audit in session.exec(select(AuditLog)).all()
        if _is_demo_related(audit, related_ids)
    ]
    audit_counts = _count_values(getattr(audit, "action", "") for audit in audit_logs)
    readiness = check_demo_readiness(session)

    return {
        "status": readiness["status"],
        "snapshot_version": SNAPSHOT_VERSION,
        "generated_at": _utcnow_iso(),
        "base_url": base_url.rstrip("/"),
        "demo_source": DEMO_SOURCE,
        "counts": {
            "demo_leads": len(leads),
            "demo_agent_runs": len(agent_runs),
            "demo_client_drafts": len(client_drafts),
            "demo_audit_logs": len(audit_logs),
        },
        "readiness": readiness,
        "lead_summaries": [_lead_summary(lead, client_drafts, agent_runs) for lead in leads],
        "agent_status_counts": _count_values(getattr(run, "status", "") for run in agent_runs),
        "client_draft_status_counts": _count_values(_public_draft_status(getattr(draft, "status", "")) for draft in client_drafts),
        "audit_action_counts": audit_counts,
        "audit_highlights": {
            action: audit_counts.get(action, 0)
            for action in DEMO_AUDIT_ACTIONS
        },
        "key_urls": [
            url.with_base_url(base_url)
            for url in DEMO_URLS
            if url.label in {"Admin v2", "Agent Console", "Agent Review Queue", "Communication Drafts", "Audit Logs"}
        ],
        "safety_rules": list(SAFETY_RULES),
    }


def render_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Global Mobility AIOS Demo Snapshot",
        "",
        f"- Status: `{snapshot['status']}`",
        f"- Snapshot version: `{snapshot['snapshot_version']}`",
        f"- Generated at: `{snapshot['generated_at']}`",
        f"- Base URL: `{snapshot['base_url']}`",
        f"- Demo source: `{snapshot['demo_source']}`",
        "",
        "## Counts",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in snapshot["counts"].items():
        lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## Lead Summary",
        "",
        "| Lead | Country | Status | Agent Runs | Client Drafts |",
        "|---|---|---|---:|---:|",
    ])
    for lead in snapshot["lead_summaries"]:
        lines.append(
            f"| {lead['name']} | {lead.get('target_country') or ''} | {lead['status']} | "
            f"{lead['agent_runs']} | {lead['client_drafts']} |"
        )

    lines.extend([
        "",
        "## Agent Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ])
    for status, count in snapshot["agent_status_counts"].items():
        lines.append(f"| {status} | {count} |")

    lines.extend([
        "",
        "## Client Draft Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ])
    for status, count in snapshot["client_draft_status_counts"].items():
        lines.append(f"| {status} | {count} |")

    lines.extend([
        "",
        "## Audit Highlights",
        "",
        "| Action | Count |",
        "|---|---:|",
    ])
    for action, count in snapshot["audit_highlights"].items():
        lines.append(f"| {action} | {count} |")

    lines.extend([
        "",
        "## Key URLs",
        "",
    ])
    for item in snapshot["key_urls"]:
        lines.append(f"- [{item['label']}]({item['url']}) - {item['purpose']}")

    lines.extend([
        "",
        "## Safety Rules",
        "",
    ])
    for rule in snapshot["safety_rules"]:
        lines.append(f"- {rule}")

    lines.append("")
    return "\n".join(lines)


def _write_or_print(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(f"Demo snapshot written to {output}")
    else:
        print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a current local demo snapshot for Global Mobility AIOS.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Local API base URL.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format.")
    parser.add_argument("--output", help="Optional output file path.")
    args = parser.parse_args()

    create_db_and_tables()
    with Session(engine) as session:
        snapshot = build_demo_snapshot(session, args.base_url)

    if args.format == "markdown":
        _write_or_print(render_markdown(snapshot), args.output)
    else:
        _write_or_print(json.dumps(snapshot, indent=2, sort_keys=True), args.output)
    return 0 if snapshot["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
