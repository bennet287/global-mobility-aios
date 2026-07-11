from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session, select

from app.agents.registry import AGENT_ALIASES, CONTROLLED_AGENT_REGISTRY
from app.core.config import settings
from app.models.domain import AgentRun, AgentRunStatus
from app.schemas import ControlledAgentRunRequest, ControlledAgentRunResponse
from app.services.audit_log import record_audit
from app.services.llm_client import LLMProviderError, LLMProviderFactory, is_llm_enabled
from app.services.role_card_loader import build_system_prompt, get_agent_output_schema


PENDING_AGENT_OUTPUT_STATUSES = {
    AgentRunStatus.completed.value,
    AgentRunStatus.pending_review.value,
}
CLIENT_DRAFTING_AGENT = "client_drafting_agent"


class DuplicatePendingControlledAgentOutput(Exception):
    def __init__(self, existing_run: AgentRun):
        self.existing_run = existing_run
        super().__init__(
            "A pending client drafting output already exists for this lead. "
            "Review, reject, or convert that output before generating another client draft."
        )


def resolve_agent_name(agent_name: str) -> str:
    return AGENT_ALIASES.get(agent_name, agent_name)


def list_controlled_agents() -> dict[str, dict[str, Any]]:
    return CONTROLLED_AGENT_REGISTRY


def _json_dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _pending_client_drafting_run(session: Session, payload: ControlledAgentRunRequest) -> AgentRun | None:
    if not payload.lead_id:
        return None
    return session.exec(
        select(AgentRun)
        .where(AgentRun.lead_id == payload.lead_id)
        .where(AgentRun.agent_name == CLIENT_DRAFTING_AGENT)
        .where(AgentRun.status.in_(PENDING_AGENT_OUTPUT_STATUSES))
        .order_by(AgentRun.created_at.desc())
    ).first()


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


# ---------------------------------------------------------------------------
# Deterministic fallback handlers (preserved for tests and when LLM is disabled)
# ---------------------------------------------------------------------------


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


DETERMINISTIC_HANDLERS = {
    "truth_explanation_agent": _truth_explanation,
    "document_checklist_agent": _document_checklist,
    "client_drafting_agent": _client_drafting,
    "sales_summary_agent": _sales_summary,
    "application_readiness_agent": _application_readiness,
}


# ---------------------------------------------------------------------------
# LLM-powered handler
# ---------------------------------------------------------------------------


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _safe_llm_json(content: str) -> dict[str, Any] | None:
    content = _strip_json_fences(content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _merge_with_safety(output: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    """Ensure every LLM output respects the hard safety invariants."""
    merged = {**base}
    # Allow LLM to add/override agent-specific keys, but never safety-critical keys.
    for key, value in output.items():
        if key not in {"human_review_required", "client_facing", "workflow_position"}:
            merged[key] = value
    merged["human_review_required"] = True
    merged["client_facing"] = False
    merged["workflow_position"] = "assistant_worker"
    return merged


def _llm_agent_handler(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    base = _base_output(payload, agent)
    resolved_name = resolve_agent_name(payload.agent_name)

    try:
        system_prompt = build_system_prompt(resolved_name)
        provider = LLMProviderFactory.get_provider()
        schema = get_agent_output_schema(resolved_name)
        response_format = {"type": "json_object"} if provider.name in {"deepseek", "moonshot"} else None

        user_content = {
            "task": payload.task,
            "context": payload.context,
            "required_output_schema": schema,
        }

        llm_response = provider.complete(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": _json_dump(user_content)}],
            response_format=response_format,
        )

        parsed = _safe_llm_json(llm_response.content)
        if parsed is None:
            raise LLMProviderError("LLM returned non-JSON or malformed JSON.")

        output = _merge_with_safety(parsed, base)
        output["_llm_meta"] = {
            "provider": llm_response.provider,
            "model": llm_response.model,
            "finish_reason": llm_response.finish_reason,
            "prompt_tokens": llm_response.prompt_tokens,
            "completion_tokens": llm_response.completion_tokens,
            "total_tokens": llm_response.total_tokens,
            "estimated_cost_usd": llm_response.estimated_cost_usd,
        }
        return output

    except Exception as exc:
        if not settings.llm_fallback_to_template:
            raise
        # Fall back to deterministic template and annotate the failure.
        fallback = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)
        fallback["_llm_meta"] = {
            "provider": settings.llm_provider or "unknown",
            "fallback_reason": f"{type(exc).__name__}: {exc}",
            "fallback_to_template": True,
        }
        return fallback


def _should_use_llm() -> bool:
    return is_llm_enabled() and settings.llm_fallback_to_template is not None


AGENT_HANDLERS = {
    "truth_explanation_agent": _llm_agent_handler,
    "document_checklist_agent": _llm_agent_handler,
    "client_drafting_agent": _llm_agent_handler,
    "sales_summary_agent": _llm_agent_handler,
    "application_readiness_agent": _llm_agent_handler,
}


def run_controlled_agent(
    session: Session,
    payload: ControlledAgentRunRequest,
    existing_run: AgentRun | None = None,
) -> ControlledAgentRunResponse:
    resolved_name = resolve_agent_name(payload.agent_name)
    if resolved_name not in CONTROLLED_AGENT_REGISTRY:
        raise ValueError(f"Unknown controlled agent: {payload.agent_name}")

    is_async = existing_run is not None
    if not is_async and resolved_name == CLIENT_DRAFTING_AGENT:
        existing_pending_run = _pending_client_drafting_run(session, payload)
        if existing_pending_run:
            raise DuplicatePendingControlledAgentOutput(existing_pending_run)

    agent = CONTROLLED_AGENT_REGISTRY[resolved_name]

    if _should_use_llm():
        output = AGENT_HANDLERS[resolved_name](payload, agent)
    else:
        output = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)

    if resolved_name != payload.agent_name:
        output["requested_agent_name"] = payload.agent_name
        output["resolved_agent_name"] = resolved_name

    input_data = {
        "agent_name": payload.agent_name,
        "task": payload.task,
        "context": payload.context,
        "actor": payload.actor,
        "llm_provider": settings.llm_provider or None,
        "llm_model": _active_model_for_audit(),
    }

    if existing_run is not None:
        run = existing_run
        run.agent_name = resolved_name
        run.task = payload.task
        run.lead_id = payload.lead_id
        run.workflow_run_id = payload.workflow_run_id
        run.status = AgentRunStatus.pending_review.value
        run.input_json = _json_dump(input_data)
        run.output_json = _json_dump(output)
        session.add(run)
    else:
        run = AgentRun(
            workflow_run_id=payload.workflow_run_id,
            lead_id=payload.lead_id,
            agent_name=resolved_name,
            task=payload.task,
            status=AgentRunStatus.completed.value,
            input_json=_json_dump(input_data),
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
            "llm_provider": settings.llm_provider or None,
            "llm_model": _active_model_for_audit(),
            "async": is_async,
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


def _active_model_for_audit() -> str | None:
    provider = (settings.llm_provider or "").lower().strip()
    if provider == "deepseek":
        return settings.deepseek_model
    if provider == "moonshot":
        return settings.moonshot_model
    return None
