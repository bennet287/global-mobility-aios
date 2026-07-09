from __future__ import annotations

import html
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import AgentRun, ApplicationRecord, DocumentRecord, Lead, TruthClaim
from app.schemas import ControlledAgentRunRequest, ControlledAgentRunResponse
from app.services.controlled_agents import list_controlled_agents, run_controlled_agent

router = APIRouter()


LEAD_AGENT_ACTIONS = {
    "sales_summary_agent": "Generate Sales Summary",
    "application_readiness_agent": "Explain Readiness",
    "document_checklist_agent": "Summarize Documents",
    "truth_explanation_agent": "Explain Truth Status",
    "client_drafting_agent": "Draft Client Update",
}


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
        "version": "v4.1",
        "send_actions_enabled": False,
        "external_llm_required": False,
        "agent_count": len(list_controlled_agents()),
        "operator_console": "GET /admin/controlled-agents",
    }


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
