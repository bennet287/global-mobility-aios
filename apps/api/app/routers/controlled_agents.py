from __future__ import annotations

import html
import json
from typing import Any
from uuid import UUID
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import AgentRun, ApplicationRecord, AuditLog, DocumentRecord, FollowUp, Lead, TruthClaim
from app.schemas import ControlledAgentRunRequest, ControlledAgentRunResponse
from app.services.audit_log import record_audit
from app.services.controlled_agents import list_controlled_agents, run_controlled_agent

router = APIRouter()


LEAD_AGENT_ACTIONS = {
    "sales_summary_agent": "Generate Sales Summary",
    "application_readiness_agent": "Explain Readiness",
    "document_checklist_agent": "Summarize Documents",
    "truth_explanation_agent": "Explain Truth Status",
    "client_drafting_agent": "Draft Client Update",
}

PENDING_AGENT_OUTPUT_STATUS = "completed"
APPROVED_AGENT_OUTPUT_STATUS = "approved"
REJECTED_AGENT_OUTPUT_STATUS = "rejected"
CONVERTED_AGENT_OUTPUT_STATUS = "converted"
CLIENT_COMMUNICATION_DRAFT_PREFIX = "[client_communication_draft:v2.6]"
REVIEW_STATUSES = {
    "pending": PENDING_AGENT_OUTPUT_STATUS,
    "completed": PENDING_AGENT_OUTPUT_STATUS,
    "approved": APPROVED_AGENT_OUTPUT_STATUS,
    "rejected": REJECTED_AGENT_OUTPUT_STATUS,
    "converted": CONVERTED_AGENT_OUTPUT_STATUS,
    "all": "all",
}


class AgentOutputReviewRequest(BaseModel):
    actor: str = "operator"
    note: str | None = None


def _escape(value: Any) -> str:
    if value is None:
        return "-"
    return html.escape(str(value))


def _json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {"value": data}
    except Exception:
        return {"raw": value}


def _agent_runs_for_lead(session: Session, lead_id: UUID, limit: int = 10) -> list[AgentRun]:
    rows = session.exec(select(AgentRun).order_by(AgentRun.created_at.desc())).all()
    return [row for row in rows if str(row.lead_id) == str(lead_id)][:limit]


def _lead_context(session: Session, lead: Lead) -> dict[str, Any]:
    documents = [
        doc for doc in session.exec(select(DocumentRecord)).all()
        if str(doc.lead_id) == str(lead.id)
    ]
    claims = [
        claim for claim in session.exec(select(TruthClaim)).all()
        if str(claim.lead_id) == str(lead.id)
    ]
    applications = [
        app for app in session.exec(select(ApplicationRecord)).all()
        if str(app.lead_id) == str(lead.id)
    ]
    missing_documents = [
        doc.document_type for doc in documents
        if str(getattr(doc, "status", "")).lower() in {"missing", "needs_review", "rejected", "expired"}
    ]
    verified_documents = [
        doc.document_type for doc in documents
        if str(getattr(doc, "status", "")).lower() == "verified"
    ]
    rejected_claims = [
        claim for claim in claims
        if str(getattr(claim.verdict, "value", claim.verdict)).lower() == "rejected"
    ]
    review_claims = [
        claim for claim in claims
        if bool(claim.requires_human_review)
        or str(getattr(claim.verdict, "value", claim.verdict)).lower() == "needs_review"
    ]
    latest_application = sorted(applications, key=lambda app: str(app.created_at or ""))[-1] if applications else None

    return {
        "lead": {
            "id": str(lead.id),
            "full_name": lead.full_name,
            "email": lead.email,
            "intent": getattr(lead.intent, "value", lead.intent),
            "target_country": lead.target_country,
            "status": getattr(lead.status, "value", lead.status),
        },
        "truth_clear": not rejected_claims and not review_claims,
        "documents_verified": bool(documents) and len(verified_documents) == len(documents),
        "missing_documents": missing_documents,
        "verified_documents": verified_documents,
        "rejected_truth_claims": len(rejected_claims),
        "truth_claims_needing_review": len(review_claims),
        "latest_application_status": getattr(latest_application, "status", "no_application"),
        "subject": f"Update for {lead.full_name}",
    }


def _agent_task(agent_name: str, lead: Lead) -> str:
    return {
        "sales_summary_agent": f"Prepare a sales-safe summary for {lead.full_name}.",
        "application_readiness_agent": f"Explain application readiness for {lead.full_name}.",
        "document_checklist_agent": f"Summarize document checklist status for {lead.full_name}.",
        "truth_explanation_agent": f"Explain truth and verification status for {lead.full_name}.",
        "client_drafting_agent": f"Draft a review-gated client update for {lead.full_name}.",
    }.get(agent_name, f"Run controlled agent for {lead.full_name}.")


def _reviewable_agent_runs(session: Session) -> list[AgentRun]:
    return list(
        session.exec(
            select(AgentRun)
            .where(AgentRun.status == PENDING_AGENT_OUTPUT_STATUS)
            .order_by(AgentRun.created_at.desc())
        ).all()
    )


def _reviewed_agent_runs(session: Session, limit: int = 50) -> list[AgentRun]:
    rows = session.exec(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)).all()
    return [
        row for row in rows
        if row.status in {APPROVED_AGENT_OUTPUT_STATUS, REJECTED_AGENT_OUTPUT_STATUS, CONVERTED_AGENT_OUTPUT_STATUS}
    ]


def _all_agent_runs(session: Session) -> list[AgentRun]:
    return list(session.exec(select(AgentRun).order_by(AgentRun.created_at.desc())).all())


def _normal_review_status(status: str | None) -> str:
    return REVIEW_STATUSES.get(str(status or "all").strip().lower(), "all")


def _filter_agent_runs(
    runs: list[AgentRun],
    *,
    status: str | None = None,
    agent_name: str | None = None,
    lead_id: str | None = None,
) -> list[AgentRun]:
    wanted_status = _normal_review_status(status)
    filtered = runs
    if wanted_status != "all":
        filtered = [run for run in filtered if run.status == wanted_status]
    if agent_name:
        filtered = [run for run in filtered if run.agent_name == agent_name]
    if lead_id:
        filtered = [run for run in filtered if str(run.lead_id) == str(lead_id)]
    return filtered


def _review_dashboard_counts(runs: list[AgentRun]) -> dict[str, int]:
    counts = {"pending": 0, "approved": 0, "rejected": 0, "converted": 0, "all": len(runs)}
    for run in runs:
        if run.status == PENDING_AGENT_OUTPUT_STATUS:
            counts["pending"] += 1
        elif run.status in counts:
            counts[run.status] += 1
    return counts


def _conversion_target(run: AgentRun) -> str:
    if run.agent_name == "client_drafting_agent":
        return "client communication draft"
    if run.agent_name == "sales_summary_agent":
        return "internal lead note"
    return "no conversion target"


def _status_label(status: str) -> str:
    if status == PENDING_AGENT_OUTPUT_STATUS:
        return "pending review"
    return status


def _status_badge(status: str) -> str:
    kind = {
        PENDING_AGENT_OUTPUT_STATUS: "blocked",
        APPROVED_AGENT_OUTPUT_STATUS: "safe",
        REJECTED_AGENT_OUTPUT_STATUS: "blocked",
        CONVERTED_AGENT_OUTPUT_STATUS: "safe",
    }.get(status, "")
    return f'<span class="badge {kind}">{_escape(_status_label(status))}</span>'


def _lead_link(session: Session, lead_id: UUID | None) -> str:
    if not lead_id:
        return "-"
    lead = session.get(Lead, lead_id)
    label = lead.full_name if lead else str(lead_id)
    return f'<a href="/admin/controlled-agents/leads/{lead_id}">{_escape(label)}</a><br><small>{_escape(lead_id)}</small>'


def _review_audits_for_run(session: Session, run: AgentRun) -> list[AuditLog]:
    logs = session.exec(select(AuditLog).order_by(AuditLog.created_at.desc())).all()
    run_id = str(run.id)
    review_actions = {
        "agent_output_approved",
        "agent_output_rejected",
        "agent_output_converted_to_client_draft",
        "agent_output_converted_to_internal_note",
    }
    matches = []
    for log in logs:
        if log.action not in review_actions:
            continue
        if log.entity_type == "agent_run" and log.entity_id == run_id:
            matches.append(log)
            continue
        if run_id in (log.after_state_json or ""):
            matches.append(log)
    return matches


def _latest_review_note(session: Session, run: AgentRun) -> str:
    logs = _review_audits_for_run(session, run)
    if not logs:
        return "-"
    latest = logs[0]
    return latest.reason or "-"


def _agent_run_summary(run: AgentRun) -> dict[str, Any]:
    output = _json_loads(run.output_json)
    return {
        "id": str(run.id),
        "lead_id": str(run.lead_id) if run.lead_id else None,
        "workflow_run_id": str(run.workflow_run_id) if run.workflow_run_id else None,
        "agent_name": run.agent_name,
        "task": run.task,
        "status": run.status,
        "summary": output.get("summary") or output.get("draft_subject") or output.get("role") or "Output captured",
        "conversion_target": _conversion_target(run),
        "requires_human_review": True,
        "created_at": run.created_at,
    }


def _get_agent_run_or_404(session: Session, run_id: UUID) -> AgentRun:
    run = session.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


def _update_agent_run_review_status(
    session: Session,
    run: AgentRun,
    *,
    status: str,
    action: str,
    actor: str,
    note: str | None,
) -> AgentRun:
    before = {"status": run.status}
    run.status = status
    record_audit(
        session,
        actor=actor,
        action=action,
        entity_type="agent_run",
        entity_id=run.id,
        before_state=before,
        after_state={"status": run.status, "agent_name": run.agent_name, "note": note},
        reason=note or f"Agent output {status}.",
        source="agent_output_review_v4.2",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def _require_approved(run: AgentRun) -> None:
    if run.status != APPROVED_AGENT_OUTPUT_STATUS:
        raise HTTPException(status_code=409, detail="Agent output must be approved before conversion")


def _convert_client_draft(session: Session, run: AgentRun, *, actor: str, note: str | None) -> dict[str, Any]:
    if not run.lead_id:
        raise HTTPException(status_code=409, detail="Cannot convert client draft without lead_id")
    output = _json_loads(run.output_json)
    subject = output.get("draft_subject") or "Client update"
    body = output.get("draft_body") or output.get("summary") or "Approved agent output."
    message = (
        f"{CLIENT_COMMUNICATION_DRAFT_PREFIX} template=agent_client_update "
        f"title=Agent drafted client update subject={subject} "
        f"body={body} note={note or 'Converted from approved client drafting agent output.'}"
    )
    follow_up = FollowUp(
        lead_id=run.lead_id,
        channel="email_draft",
        status="pending",
        message=message,
    )
    session.add(follow_up)
    session.flush()
    run.status = CONVERTED_AGENT_OUTPUT_STATUS
    record_audit(
        session,
        actor=actor,
        action="agent_output_converted_to_client_draft",
        entity_type="follow_up",
        entity_id=follow_up.id,
        before_state={"agent_run_status": APPROVED_AGENT_OUTPUT_STATUS},
        after_state={
            "agent_run_id": run.id,
            "agent_run_status": run.status,
            "follow_up_id": follow_up.id,
            "follow_up_status": "pending",
            "note": note,
        },
        reason=note or "Approved client drafting agent output converted into a review-gated communication draft.",
        source="agent_output_review_v4.2",
    )
    session.add(run)
    session.commit()
    session.refresh(follow_up)
    session.refresh(run)
    return {"converted_to": "client_communication_draft", "follow_up_id": str(follow_up.id), "status": run.status}


def _convert_sales_summary(session: Session, run: AgentRun, *, actor: str, note: str | None) -> dict[str, Any]:
    if not run.lead_id:
        raise HTTPException(status_code=409, detail="Cannot convert sales summary without lead_id")
    lead = session.get(Lead, run.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    output = _json_loads(run.output_json)
    summary = output.get("summary") or "Approved sales summary agent output."
    before_notes = lead.notes or ""
    addition = f"[agent_output_review:v4.2] {summary}"
    if note:
        addition = f"{addition}\nReviewer note: {note}"
    lead.notes = f"{before_notes}\n\n{addition}".strip()
    run.status = CONVERTED_AGENT_OUTPUT_STATUS
    record_audit(
        session,
        actor=actor,
        action="agent_output_converted_to_internal_note",
        entity_type="lead",
        entity_id=lead.id,
        before_state={"notes": before_notes, "agent_run_status": APPROVED_AGENT_OUTPUT_STATUS},
        after_state={"notes": lead.notes, "agent_run_id": run.id, "agent_run_status": run.status},
        reason=note or "Approved sales summary agent output converted into an internal lead note.",
        source="agent_output_review_v4.2",
    )
    session.add(lead)
    session.add(run)
    session.commit()
    session.refresh(lead)
    session.refresh(run)
    return {"converted_to": "internal_lead_note", "lead_id": str(lead.id), "status": run.status}


async def _form_review_request(request: Request) -> AgentOutputReviewRequest:
    body = (await request.body()).decode("utf-8")
    fields = parse_qs(body, keep_blank_values=True)
    return AgentOutputReviewRequest(
        actor=(fields.get("actor") or ["operator"])[0] or "operator",
        note=(fields.get("note") or [None])[0] or None,
    )


def _page_shell(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""
        <!doctype html>
        <html>
          <head>
            <title>{_escape(title)}</title>
            <style>
              body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
              .nav a {{ margin-right: 12px; }}
              .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0; }}
              table {{ border-collapse: collapse; width: 100%; background: white; }}
              th, td {{ border: 1px solid #e2e8f0; padding: 8px; vertical-align: top; font-size: 14px; }}
              th {{ background: #eef2f7; }}
              button {{ padding: 6px 10px; border: 1px solid #94a3b8; border-radius: 6px; background: #f8fafc; cursor: pointer; margin: 2px 0; }}
              .badge {{ display: inline-block; padding: 2px 7px; border-radius: 999px; font-size: 12px; font-weight: 600; background: #e2e8f0; color: #334155; }}
              .safe {{ background: #dcfce7; color: #166534; }}
              .blocked {{ background: #fee2e2; color: #991b1b; }}
              small {{ color: #64748b; }}
              pre {{ background: #020617; color: #e2e8f0; padding: 12px; overflow-x: auto; border-radius: 8px; white-space: pre-wrap; }}
            </style>
          </head>
          <body>
            <div class="nav">
              <a href="/admin/v2">Admin v2</a>
              <a href="/admin/controlled-agents">Agent Console</a>
              <a href="/admin/agent-output-reviews">Agent Review Queue</a>
              <a href="/api/v1/controlled-agents">Agents JSON</a>
              <a href="/api/v1/agent-runs">Runs JSON</a>
              <a href="/debug/controlled-agents">Debug</a>
            </div>
            {body}
          </body>
        </html>
        """
    )


def _run_rows(runs: list[AgentRun]) -> str:
    if not runs:
        return "<tr><td colspan='5'>No controlled agent runs yet.</td></tr>"
    rows = []
    for run in runs:
        output = _json_loads(run.output_json)
        summary = output.get("summary") or output.get("draft_subject") or output.get("role") or "Output captured"
        rows.append(
            f"""
            <tr>
              <td><a href="/admin/controlled-agents/runs/{run.id}">{run.id}</a></td>
              <td>{_escape(run.agent_name)}</td>
              <td>{_escape(run.status)}</td>
              <td>{_escape(summary)}</td>
              <td>{_escape(run.created_at)}</td>
            </tr>
            """
        )
    return "".join(rows)


def _review_action_forms(run: AgentRun) -> str:
    if run.status == PENDING_AGENT_OUTPUT_STATUS:
        return f"""
        <form method="post" action="/admin/agent-output-reviews/runs/{run.id}/approve">
          <input type="hidden" name="actor" value="operator_console">
          <textarea name="note" rows="2" style="width:95%" placeholder="Reviewer approval note"></textarea><br>
          <button type="submit">Approve Output</button>
        </form>
        <form method="post" action="/admin/agent-output-reviews/runs/{run.id}/reject">
          <input type="hidden" name="actor" value="operator_console">
          <textarea name="note" rows="2" style="width:95%" placeholder="Reviewer rejection note"></textarea><br>
          <button type="submit">Reject Output</button>
        </form>
        """
    if run.status == APPROVED_AGENT_OUTPUT_STATUS and run.agent_name in {"client_drafting_agent", "sales_summary_agent"}:
        return f"""
        <form method="post" action="/admin/agent-output-reviews/runs/{run.id}/convert">
          <input type="hidden" name="actor" value="operator_console">
          <textarea name="note" rows="2" style="width:95%" placeholder="Conversion note"></textarea><br>
          <button type="submit">Convert Approved Output</button>
        </form>
        """
    if run.status == APPROVED_AGENT_OUTPUT_STATUS:
        return '<span class="badge safe">Approved - no conversion target in v4.2</span>'
    return f'<span class="badge">{_escape(run.status)}</span>'


def _review_rows(session: Session, runs: list[AgentRun]) -> str:
    if not runs:
        return "<tr><td colspan='8'>No agent outputs match these filters.</td></tr>"
    rows = []
    for run in runs:
        summary = _agent_run_summary(run)
        rows.append(
            f"""
            <tr>
              <td><a href="/admin/agent-output-reviews/runs/{run.id}">{run.id}</a></td>
              <td>{_escape(run.agent_name)}</td>
              <td>{_lead_link(session, run.lead_id)}</td>
              <td>{_status_badge(run.status)}</td>
              <td>{_escape(summary["conversion_target"])}</td>
              <td>{_escape(summary["summary"])}</td>
              <td>{_escape(_latest_review_note(session, run))}</td>
              <td>{_review_action_forms(run)}</td>
            </tr>
            """
        )
    return "".join(rows)


def _audit_history_rows(logs: list[AuditLog]) -> str:
    if not logs:
        return "<tr><td colspan='4'>No review decisions recorded yet.</td></tr>"
    return "".join(
        f"""
        <tr>
          <td>{_escape(log.action)}</td>
          <td>{_escape(log.actor)}</td>
          <td>{_escape(log.reason)}</td>
          <td>{_escape(log.created_at)}</td>
        </tr>
        """
        for log in logs
    )


def _lead_action_forms(lead: Lead) -> str:
    forms = []
    for agent_name, label in LEAD_AGENT_ACTIONS.items():
        forms.append(
            f"""
            <form method="post" action="/admin/controlled-agents/leads/{lead.id}/run/{agent_name}" style="display:inline-block">
              <button type="submit">{_escape(label)}</button>
            </form>
            """
        )
    return "".join(forms)


@router.get("/api/v1/controlled-agents")
def get_controlled_agents() -> dict:
    return {
        "version": "v4.0",
        "mode": "workflow_assistant_only",
        "automatic_actions_enabled": False,
        "agents": list_controlled_agents(),
    }


@router.post("/api/v1/controlled-agents/run", response_model=ControlledAgentRunResponse)
def run_controlled_agent_endpoint(
    payload: ControlledAgentRunRequest,
    session: Session = Depends(get_session),
) -> ControlledAgentRunResponse:
    try:
        return run_controlled_agent(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/debug/controlled-agents")
def debug_controlled_agents() -> dict:
    return {
        "module": "controlled_ai_agents",
        "version": "v4.3",
        "send_actions_enabled": False,
        "external_llm_required": False,
        "agent_count": len(list_controlled_agents()),
        "operator_console": "GET /admin/controlled-agents",
        "review_queue": "GET /admin/agent-output-reviews",
        "dashboard_filters": ["status", "agent_name", "lead_id"],
    }


@router.get("/api/v1/agent-output-reviews/queue")
def agent_output_review_queue(
    agent_name: str | None = None,
    lead_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict:
    items = _filter_agent_runs(_reviewable_agent_runs(session), agent_name=agent_name, lead_id=lead_id)
    return {
        "version": "v4.3",
        "review_required": True,
        "filters": {"status": "pending", "agent_name": agent_name, "lead_id": lead_id},
        "items": [_agent_run_summary(run) for run in items],
    }


@router.get("/api/v1/agent-output-reviews/reviewed")
def agent_output_reviewed(
    status: str = "all",
    agent_name: str | None = None,
    lead_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict:
    items = _filter_agent_runs(_reviewed_agent_runs(session), status=status, agent_name=agent_name, lead_id=lead_id)
    return {
        "version": "v4.3",
        "filters": {"status": status, "agent_name": agent_name, "lead_id": lead_id},
        "items": [_agent_run_summary(run) for run in items],
    }


@router.get("/api/v1/agent-output-reviews/dashboard")
def agent_output_review_dashboard(
    status: str = "all",
    agent_name: str | None = None,
    lead_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict:
    runs = _all_agent_runs(session)
    filtered = _filter_agent_runs(runs, status=status, agent_name=agent_name, lead_id=lead_id)
    return {
        "version": "v4.3",
        "filters": {"status": status, "agent_name": agent_name, "lead_id": lead_id},
        "counts": _review_dashboard_counts(runs),
        "items": [_agent_run_summary(run) for run in filtered],
    }


@router.post("/api/v1/agent-output-reviews/runs/{run_id}/approve")
def approve_agent_output(
    run_id: UUID,
    payload: AgentOutputReviewRequest,
    session: Session = Depends(get_session),
) -> dict:
    run = _get_agent_run_or_404(session, run_id)
    if run.status != PENDING_AGENT_OUTPUT_STATUS:
        raise HTTPException(status_code=409, detail="Only pending agent outputs can be approved")
    run = _update_agent_run_review_status(
        session,
        run,
        status=APPROVED_AGENT_OUTPUT_STATUS,
        action="agent_output_approved",
        actor=payload.actor,
        note=payload.note,
    )
    return {"status": run.status, "run": _agent_run_summary(run)}


@router.post("/api/v1/agent-output-reviews/runs/{run_id}/reject")
def reject_agent_output(
    run_id: UUID,
    payload: AgentOutputReviewRequest,
    session: Session = Depends(get_session),
) -> dict:
    run = _get_agent_run_or_404(session, run_id)
    if run.status != PENDING_AGENT_OUTPUT_STATUS:
        raise HTTPException(status_code=409, detail="Only pending agent outputs can be rejected")
    run = _update_agent_run_review_status(
        session,
        run,
        status=REJECTED_AGENT_OUTPUT_STATUS,
        action="agent_output_rejected",
        actor=payload.actor,
        note=payload.note,
    )
    return {"status": run.status, "run": _agent_run_summary(run)}


@router.post("/api/v1/agent-output-reviews/runs/{run_id}/convert")
def convert_approved_agent_output(
    run_id: UUID,
    payload: AgentOutputReviewRequest,
    session: Session = Depends(get_session),
) -> dict:
    run = _get_agent_run_or_404(session, run_id)
    _require_approved(run)
    if run.agent_name == "client_drafting_agent":
        return _convert_client_draft(session, run, actor=payload.actor, note=payload.note)
    if run.agent_name == "sales_summary_agent":
        return _convert_sales_summary(session, run, actor=payload.actor, note=payload.note)
    raise HTTPException(status_code=409, detail="This agent output type has no conversion target in v4.2")


@router.get("/admin/controlled-agents", response_class=HTMLResponse)
def admin_controlled_agents(session: Session = Depends(get_session)) -> HTMLResponse:
    leads = session.exec(select(Lead)).all()
    recent_runs = list(session.exec(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(15)).all())
    lead_rows = "".join(
        f"""
        <tr>
          <td><a href="/admin/controlled-agents/leads/{lead.id}">{_escape(lead.full_name)}</a><br><small>{lead.id}</small></td>
          <td>{_escape(getattr(lead.intent, "value", lead.intent))}<br>{_escape(lead.target_country)}</td>
          <td>{_escape(getattr(lead.status, "value", lead.status))}</td>
          <td>{_lead_action_forms(lead)}</td>
        </tr>
        """
        for lead in leads
    )
    if not lead_rows:
        lead_rows = "<tr><td colspan='4'>No leads available.</td></tr>"

    body = f"""
      <h1>Agent Operator Console v4.1</h1>
      <div class="card">
        <h2>Safety Mode</h2>
        <p>{'<span class="badge safe">Review-gated</span>'} {'<span class="badge blocked">Auto-send disabled</span>'} {'<span class="badge blocked">Auto-submit disabled</span>'}</p>
        <p>Controlled agents create internal operator outputs only. They do not verify documents, convert leads, approve applications, submit applications, or send client messages.</p>
      </div>
      <div class="card">
        <h2>Lead Agent Actions</h2>
        <table>
          <thead><tr><th>Lead</th><th>Intent / Country</th><th>Status</th><th>Controlled Actions</th></tr></thead>
          <tbody>{lead_rows}</tbody>
        </table>
      </div>
      <div class="card">
        <h2>Recent Agent Runs</h2>
        <table>
          <thead><tr><th>Run</th><th>Agent</th><th>Status</th><th>Summary</th><th>Created</th></tr></thead>
          <tbody>{_run_rows(recent_runs)}</tbody>
        </table>
      </div>
    """
    return _page_shell("Agent Operator Console v4.1", body)


@router.get("/admin/agent-output-reviews", response_class=HTMLResponse)
def admin_agent_output_reviews(
    status: str = "pending",
    agent_name: str = "",
    lead_id: str = "",
    session: Session = Depends(get_session),
) -> HTMLResponse:
    all_runs = _all_agent_runs(session)
    counts = _review_dashboard_counts(all_runs)
    selected_status = _normal_review_status(status)
    selected_status_label = status if status in REVIEW_STATUSES else "all"
    filtered_runs = _filter_agent_runs(
        all_runs,
        status=selected_status_label,
        agent_name=agent_name or None,
        lead_id=lead_id or None,
    )
    status_links = " ".join(
        f'<a href="/admin/agent-output-reviews?status={label}">{_escape(label)} ({counts.get(label if label != "pending" else "pending", 0)})</a>'
        for label in ["pending", "approved", "rejected", "converted", "all"]
    )
    agent_options = "".join(
        f'<option value="{_escape(name)}" {"selected" if name == agent_name else ""}>{_escape(name)}</option>'
        for name in ["", *list(list_controlled_agents().keys())]
    )
    body = f"""
      <h1>Agent Output Review Dashboard v4.3</h1>
      <div class="card">
        <h2>Safety Mode</h2>
        <p><span class="badge safe">Human review required</span> <span class="badge blocked">Unapproved output blocked</span></p>
        <p>Only approved outputs can be converted. Conversion is limited to client drafting outputs and sales summaries.</p>
      </div>
      <div class="card">
        <h2>Filters</h2>
        <p>{status_links}</p>
        <form method="get" action="/admin/agent-output-reviews">
          <label>Status
            <select name="status">
              <option value="pending" {"selected" if selected_status == PENDING_AGENT_OUTPUT_STATUS else ""}>pending</option>
              <option value="approved" {"selected" if selected_status == APPROVED_AGENT_OUTPUT_STATUS else ""}>approved</option>
              <option value="rejected" {"selected" if selected_status == REJECTED_AGENT_OUTPUT_STATUS else ""}>rejected</option>
              <option value="converted" {"selected" if selected_status == CONVERTED_AGENT_OUTPUT_STATUS else ""}>converted</option>
              <option value="all" {"selected" if selected_status == "all" else ""}>all</option>
            </select>
          </label>
          <label> Agent
            <select name="agent_name">{agent_options}</select>
          </label>
          <label> Lead ID
            <input name="lead_id" value="{_escape(lead_id)}" placeholder="optional lead id">
          </label>
          <button type="submit">Apply Filters</button>
        </form>
      </div>
      <div class="card">
        <h2>Summary</h2>
        <p>
          <span class="badge blocked">pending {counts["pending"]}</span>
          <span class="badge safe">approved {counts["approved"]}</span>
          <span class="badge blocked">rejected {counts["rejected"]}</span>
          <span class="badge safe">converted {counts["converted"]}</span>
          <span class="badge">all {counts["all"]}</span>
        </p>
      </div>
      <div class="card">
        <h2>Filtered Outputs</h2>
        <table>
          <thead><tr><th>Run</th><th>Agent</th><th>Lead</th><th>Status</th><th>Conversion Target</th><th>Summary</th><th>Reviewer Note</th><th>Action</th></tr></thead>
          <tbody>{_review_rows(session, filtered_runs)}</tbody>
        </table>
      </div>
    """
    return _page_shell("Agent Output Review Dashboard v4.3", body)


@router.get("/admin/agent-output-reviews/runs/{run_id}", response_class=HTMLResponse)
def admin_agent_output_review_detail(run_id: UUID, session: Session = Depends(get_session)) -> HTMLResponse:
    run = _get_agent_run_or_404(session, run_id)
    input_data = _json_loads(run.input_json)
    output_data = _json_loads(run.output_json)
    audit_rows = _audit_history_rows(_review_audits_for_run(session, run))
    body = f"""
      <h1>Agent Output Review Detail</h1>
      <div class="card">
        <p><strong>Run:</strong> {_escape(run.id)}</p>
        <p><strong>Agent:</strong> {_escape(run.agent_name)}</p>
        <p><strong>Status:</strong> {_status_badge(run.status)}</p>
        <p><strong>Lead:</strong> {_lead_link(session, run.lead_id)}</p>
        <p><strong>Conversion target:</strong> {_escape(_conversion_target(run))}</p>
        <p><strong>Latest reviewer note:</strong> {_escape(_latest_review_note(session, run))}</p>
        {_review_action_forms(run)}
      </div>
      <div class="card">
        <h2>Review History</h2>
        <table>
          <thead><tr><th>Action</th><th>Actor</th><th>Note</th><th>Created</th></tr></thead>
          <tbody>{audit_rows}</tbody>
        </table>
      </div>
      <div class="card">
        <h2>Input</h2>
        <pre>{_escape(json.dumps(input_data, indent=2, default=str))}</pre>
      </div>
      <div class="card">
        <h2>Output</h2>
        <pre>{_escape(json.dumps(output_data, indent=2, default=str))}</pre>
      </div>
    """
    return _page_shell("Agent Output Review Detail", body)


@router.post("/admin/agent-output-reviews/runs/{run_id}/approve")
async def admin_approve_agent_output(
    run_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    payload = await _form_review_request(request)
    approve_agent_output(run_id, payload, session)
    return RedirectResponse(url=f"/admin/agent-output-reviews/runs/{run_id}", status_code=303)


@router.post("/admin/agent-output-reviews/runs/{run_id}/reject")
async def admin_reject_agent_output(
    run_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    payload = await _form_review_request(request)
    reject_agent_output(run_id, payload, session)
    return RedirectResponse(url=f"/admin/agent-output-reviews/runs/{run_id}", status_code=303)


@router.post("/admin/agent-output-reviews/runs/{run_id}/convert")
async def admin_convert_agent_output(
    run_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    payload = await _form_review_request(request)
    convert_approved_agent_output(run_id, payload, session)
    return RedirectResponse(url=f"/admin/agent-output-reviews/runs/{run_id}", status_code=303)


@router.get("/admin/controlled-agents/leads/{lead_id}", response_class=HTMLResponse)
def admin_controlled_agents_lead(lead_id: UUID, session: Session = Depends(get_session)) -> HTMLResponse:
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    context = _lead_context(session, lead)
    runs = _agent_runs_for_lead(session, lead.id)
    body = f"""
      <h1>Controlled Agents for {_escape(lead.full_name)}</h1>
      <div class="card">
        <h2>Actions</h2>
        {_lead_action_forms(lead)}
      </div>
      <div class="card">
        <h2>Generated Context</h2>
        <pre>{_escape(json.dumps(context, indent=2, default=str))}</pre>
      </div>
      <div class="card">
        <h2>Lead Agent Runs</h2>
        <table>
          <thead><tr><th>Run</th><th>Agent</th><th>Status</th><th>Summary</th><th>Created</th></tr></thead>
          <tbody>{_run_rows(runs)}</tbody>
        </table>
      </div>
    """
    return _page_shell(f"Controlled Agents - {lead.full_name}", body)


@router.post("/admin/controlled-agents/leads/{lead_id}/run/{agent_name}")
def admin_run_controlled_agent_for_lead(
    lead_id: UUID,
    agent_name: str,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if agent_name not in LEAD_AGENT_ACTIONS:
        raise HTTPException(status_code=404, detail="Unsupported operator agent action")

    response = run_controlled_agent(
        session,
        ControlledAgentRunRequest(
            agent_name=agent_name,
            task=_agent_task(agent_name, lead),
            lead_id=lead.id,
            context=_lead_context(session, lead),
            actor="operator_console",
        ),
    )
    return RedirectResponse(url=f"/admin/controlled-agents/runs/{response.run_id}", status_code=303)


@router.get("/admin/controlled-agents/runs/{run_id}", response_class=HTMLResponse)
def admin_controlled_agent_run_detail(run_id: UUID, session: Session = Depends(get_session)) -> HTMLResponse:
    run = session.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    input_data = _json_loads(run.input_json)
    output_data = _json_loads(run.output_json)
    lead_link = ""
    if run.lead_id:
        lead_link = f'<p><a href="/admin/controlled-agents/leads/{run.lead_id}">Back to lead agent console</a></p>'

    body = f"""
      <h1>Controlled Agent Run</h1>
      <div class="card">
        <p><strong>Run:</strong> {_escape(run.id)}</p>
        <p><strong>Agent:</strong> {_escape(run.agent_name)}</p>
        <p><strong>Status:</strong> {_escape(run.status)}</p>
        <p><strong>Created:</strong> {_escape(run.created_at)}</p>
        <p><span class="badge safe">Internal output</span> <span class="badge blocked">Requires human review</span></p>
        {lead_link}
      </div>
      <div class="card">
        <h2>Input</h2>
        <pre>{_escape(json.dumps(input_data, indent=2, default=str))}</pre>
      </div>
      <div class="card">
        <h2>Output</h2>
        <pre>{_escape(json.dumps(output_data, indent=2, default=str))}</pre>
      </div>
    """
    return _page_shell("Controlled Agent Run", body)
