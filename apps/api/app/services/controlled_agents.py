from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session

from app.agents.registry import AGENT_ALIASES, CONTROLLED_AGENT_REGISTRY
from app.models.domain import AgentRun
from app.schemas import ControlledAgentRunRequest, ControlledAgentRunResponse
from app.services.audit_log import record_audit


def resolve_agent_name(agent_name: str) -> str:
    return AGENT_ALIASES.get(agent_name, agent_name)


def list_controlled_agents() -> dict[str, dict[str, Any]]:
    return CONTROLLED_AGENT_REGISTRY


def _json_dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _base_output(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_received": payload.task,
        "department": agent["department"],
        "role": agent["role"],
        "context_keys": sorted(payload.context.keys()),
        "workflow_position": "assistant_worker",
        "human_review_required": True,
        "client_facing": False,
    }


def _truth_explanation(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    verdict = payload.context.get("verdict", "needs_review")
    confidence = payload.context.get("confidence", "unknown")
    output.update(
        {
            "summary": f"Truth claim is currently {verdict} with confidence {confidence}.",
            "safe_next_actions": [
                "Keep official-source evidence attached.",
                "Escalate to a reviewer before using the explanation with a client.",
            ],
            "blocked_actions": ["new_policy_claims", "legal_advice", "client_send"],
        }
    )
    return output


def _document_checklist(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    missing = payload.context.get("missing_documents", [])
    verified = payload.context.get("verified_documents", [])
    output.update(
        {
            "missing_documents": missing,
            "verified_documents": verified,
            "summary": "Document status summarized for operator review.",
            "safe_next_actions": [
                "Request missing documents from the client.",
                "Verify uploaded documents through the document verification workflow.",
            ],
            "blocked_actions": ["document_verification", "metadata_changes", "file_mutation"],
        }
    )
    return output


def _client_drafting(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    output.update(
        {
            "draft_subject": payload.context.get("subject", "Update on your application"),
            "draft_body": (
                "Thank you for your patience. We are reviewing your case details and will share the "
                "next safe step after internal review is complete."
            ),
            "send_allowed": False,
            "review_status": "draft_requires_human_review",
            "blocked_actions": ["email_send", "whatsapp_send", "client_portal_send"],
        }
    )
    return output


def _sales_summary(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    output.update(
        {
            "summary": "Lead summary prepared for sales-safe follow-up.",
            "safe_next_actions": [
                "Confirm truth status before discussing outcomes.",
                "Use approved follow-up templates only.",
            ],
            "prohibited_claims": ["guaranteed visa", "guaranteed admission", "guaranteed job"],
            "blocked_actions": ["lead_conversion", "guarantee_claims", "payment_pressure"],
        }
    )
    return output


def _application_readiness(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    truth_clear = bool(payload.context.get("truth_clear", False))
    documents_verified = bool(payload.context.get("documents_verified", False))
    output.update(
        {
            "truth_clear": truth_clear,
            "documents_verified": documents_verified,
            "ready_for_operator_review": truth_clear and documents_verified,
            "ready_for_submission": False,
            "safe_next_actions": [
                "Resolve truth blockers." if not truth_clear else "Truth gate appears clear.",
                "Verify required documents." if not documents_verified else "Document gate appears clear.",
                "Use the application workflow for any draft, approval, or submission action.",
            ],
            "blocked_actions": ["application_draft", "application_approval", "application_submission"],
        }
    )
    return output


AGENT_HANDLERS = {
    "truth_explanation_agent": _truth_explanation,
    "document_checklist_agent": _document_checklist,
    "client_drafting_agent": _client_drafting,
    "sales_summary_agent": _sales_summary,
    "application_readiness_agent": _application_readiness,
}


def run_controlled_agent(session: Session, payload: ControlledAgentRunRequest) -> ControlledAgentRunResponse:
    resolved_name = resolve_agent_name(payload.agent_name)
    if resolved_name not in CONTROLLED_AGENT_REGISTRY:
        raise ValueError(f"Unknown controlled agent: {payload.agent_name}")

    agent = CONTROLLED_AGENT_REGISTRY[resolved_name]
    output = AGENT_HANDLERS[resolved_name](payload, agent)
    if resolved_name != payload.agent_name:
        output["requested_agent_name"] = payload.agent_name
        output["resolved_agent_name"] = resolved_name

    run = AgentRun(
        workflow_run_id=payload.workflow_run_id,
        lead_id=payload.lead_id,
        agent_name=resolved_name,
        task=payload.task,
        status="completed",
        input_json=_json_dump(
            {
                "agent_name": payload.agent_name,
                "task": payload.task,
                "context": payload.context,
                "actor": payload.actor,
            }
        ),
        output_json=_json_dump(output),
    )
    session.add(run)
    session.flush()

    record_audit(
        session,
        actor=payload.actor,
        action="controlled_agent_run",
        entity_type="agent_run",
        entity_id=run.id,
        after_state={
            "agent_name": resolved_name,
            "lead_id": payload.lead_id,
            "workflow_run_id": payload.workflow_run_id,
            "guardrails": agent["guardrails"],
            "requires_human_review": True,
        },
        reason="Controlled AI agent executed as an internal workflow assistant.",
        source="controlled_agents_v4.0",
    )
    session.commit()
    session.refresh(run)

    return ControlledAgentRunResponse(
        run_id=run.id,
        agent_name=resolved_name,
        status=run.status,
        output=output,
        guardrails=agent["guardrails"],
        requires_human_review=True,
        message="Controlled agent output generated for internal review only.",
        created_at=run.created_at,
    )
