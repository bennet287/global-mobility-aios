from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlmodel import Session, select

from app.agents.registry import CONTROLLED_AGENT_REGISTRY
from app.core.config import settings
from app.models.domain import Lead
from app.schemas import InhouseConsultantDecision
from app.services.llm_client import LLMProviderError, LLMProviderFactory
from app.services.role_card_loader import load_role_card


# Decision schema sent to the LLM as a JSON response_format hint.
_CONSULTANT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["propose_action", "ask_clarification", "wait_for_human"],
            "description": "The consultant's routing decision.",
        },
        "agent_name": {
            "type": ["string", "null"],
            "description": "Canonical controlled agent name. Required for propose_action.",
        },
        "lead_id": {
            "type": ["string", "null"],
            "description": "UUID of the matched lead. Required for propose_action.",
        },
        "task_template": {
            "type": ["string", "null"],
            "description": "Concise task description sent to the agent. Required for propose_action.",
        },
        "summary": {
            "type": ["string", "null"],
            "description": "Human-readable explanation of the proposed action. Required for propose_action.",
        },
        "clarification_question": {
            "type": ["string", "null"],
            "description": "Question to ask the operator. Required for ask_clarification.",
        },
        "escalation_reason": {
            "type": ["string", "null"],
            "description": "Why human intervention is needed. Required for wait_for_human.",
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Confidence in the decision.",
        },
    },
    "required": ["decision", "confidence"],
}


def _available_agents_text() -> str:
    lines = ["Available controlled agents:"]
    for name, meta in CONTROLLED_AGENT_REGISTRY.items():
        lines.append(f"- {name}: {meta.get('role', '')}")
        for guardrail in meta.get("guardrails", []):
            lines.append(f"    • {guardrail}")
    return "\n".join(lines)


def _build_system_prompt() -> str:
    card = load_role_card("Inhouse_Consultant")
    parts = [
        f"# {card['title']}",
        "",
        "## Mission",
        card["mission"],
        "",
    ]
    for section in ["inputs", "outputs", "guardrails"]:
        value = card.get(section, "")
        if value:
            parts.extend([f"## {section.title()}", value, ""])

    parts.extend(
        [
            _available_agents_text(),
            "",
            "## Instructions",
            "You will receive the operator's message, optional conversation history, and a list of available leads.",
            "Return ONLY valid JSON matching the schema below. Do not wrap it in markdown.",
            "",
            "## Output Schema",
            json.dumps(_CONSULTANT_OUTPUT_SCHEMA, indent=2),
            "",
        ]
    )
    return "\n".join(parts).strip()


def _leads_for_prompt(leads: list[Lead]) -> str:
    if not leads:
        return "Available leads: none"
    lines = ["Available leads:"]
    for lead in leads:
        email = lead.email or "no-email"
        lines.append(f"- id={lead.id} name={lead.full_name} email={email} country={lead.target_country or 'unknown'} intent={lead.intent}")
    return "\n".join(lines)


def _build_user_message(
    message: str,
    conversation_history: list[dict[str, str]],
    leads: list[Lead],
    lead_hint: str | None,
) -> str:
    parts = [
        _leads_for_prompt(leads),
        "",
        f"Operator message: {message}",
    ]
    if lead_hint:
        parts.append(f"Lead hint from UI context: {lead_hint}")
    if conversation_history:
        parts.append("")
        parts.append("Conversation history:")
        for turn in conversation_history[-6:]:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            parts.append(f"{role}: {content}")
    return "\n".join(parts).strip()


def _match_lead(leads: list[Lead], hint: str | None) -> Lead | None:
    if not hint:
        return None
    hint_lower = hint.lower().strip()
    # Exact UUID match first.
    try:
        uuid_hint = UUID(hint_lower)
        for lead in leads:
            if lead.id == uuid_hint:
                return lead
    except ValueError:
        pass
    # Name/email substring match.
    for lead in leads:
        if hint_lower in (lead.full_name or "").lower():
            return lead
        if lead.email and hint_lower in lead.email.lower():
            return lead
    return None


def _extract_lead_hint(message: str, lead_hint: str | None) -> str | None:
    """Try to pull a lead identifier from the message if no explicit hint is given."""
    if lead_hint:
        return lead_hint
    # Very simple heuristic: look for quoted names or an email-like token.
    email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", message)
    if email_match:
        return email_match.group(0)
    # Quoted phrase.
    quote_match = re.search(r'"([^"]{3,80})"', message)
    if quote_match:
        return quote_match.group(1)
    return None


def _keyword_decision(message: str, leads: list[Lead], lead_hint: str | None) -> InhouseConsultantDecision:
    """Deterministic fallback when LLM is disabled or fails."""
    text = message.lower()
    hint = _extract_lead_hint(message, lead_hint)
    lead = _match_lead(leads, hint) if hint else None

    # If no explicit hint matched, try to find a lead whose full name appears in the message.
    if lead is None:
        text_for_name = message.lower()
        for candidate in leads:
            name = (candidate.full_name or "").lower().strip()
            if name and len(name) > 2 and name in text_for_name:
                lead = candidate
                break

    # Agent keyword mapping.
    agent_name: str | None = None
    task_template = ""
    if any(word in text for word in ["draft", "email", "message", "client update", "follow-up", "follow up"]):
        agent_name = "client_drafting_agent"
        task_template = "Draft a client update based on the current lead state."
    elif any(word in text for word in ["summary", "summarize", "sales summary", "lead summary", "overview"]):
        agent_name = "sales_summary_agent"
        task_template = "Create a sales-safe summary and next-step suggestions."
    elif any(word in text for word in ["document", "documents", "checklist", "missing doc"]):
        agent_name = "document_checklist_agent"
        task_template = "Summarize missing, received, and verified documents."
    elif any(word in text for word in ["truth", "claim", "verify", "check claim", "immigration claim"]):
        agent_name = "truth_explanation_agent"
        task_template = "Explain the current truth status for the lead."
    elif any(word in text for word in ["readiness", "ready", "application status", "application readiness"]):
        agent_name = "application_readiness_agent"
        task_template = "Explain application readiness blockers and safe next actions."

    if agent_name and lead:
        return InhouseConsultantDecision(
            decision="propose_action",
            agent_name=agent_name,
            lead_id=lead.id,
            task_template=task_template,
            summary=f"Fallback routing: run {agent_name} for lead {lead.full_name}.",
            confidence="medium",
        )

    if agent_name and not lead:
        return InhouseConsultantDecision(
            decision="ask_clarification",
            clarification_question=f"I can run the {agent_name} for you. Which lead should I use? Provide a name, email, or lead ID.",
            confidence="medium",
        )

    return InhouseConsultantDecision(
        decision="wait_for_human",
        escalation_reason="I couldn't confidently map your request to a controlled agent or lead. Please use the Agent Console to select the agent and lead manually, or rephrase your request.",
        confidence="low",
    )


def _reply_from_decision(decision: InhouseConsultantDecision) -> str:
    if decision.decision == "propose_action":
        return (
            f"I propose running **{decision.agent_name}** for the selected lead.\n\n"
            f"Task: {decision.task_template}\n\n"
            f"{decision.summary}"
        )
    if decision.decision == "ask_clarification":
        return decision.clarification_question or "Could you clarify what you'd like me to do?"
    return (
        decision.escalation_reason
        or "I'm not sure how to handle that. Please use the Agent Console or Review Queue."
    )


def consult(
    session: Session,
    message: str,
    conversation_history: list[dict[str, str]] | None = None,
    lead_hint: str | None = None,
) -> dict[str, Any]:
    """Run the in-house consultant agent and return a decision + human reply."""
    conversation_history = conversation_history or []
    leads = list(session.exec(select(Lead).order_by(Lead.created_at.desc())).all())

    # If no LLM configured, use deterministic fallback immediately.
    if not settings.llm_provider or not settings.llm_provider.strip():
        decision = _keyword_decision(message, leads, lead_hint)
        return {"decision": decision, "reply": _reply_from_decision(decision)}

    system_prompt = _build_system_prompt()
    user_message = _build_user_message(message, conversation_history, leads, lead_hint)

    try:
        provider = LLMProviderFactory.get_provider()
        response = provider.complete(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.content)
        decision = InhouseConsultantDecision(**parsed)
    except (LLMProviderError, json.JSONDecodeError, ValidationError, KeyError, TypeError):
        # On any LLM/parse failure, fall back to deterministic routing.
        decision = _keyword_decision(message, leads, lead_hint)

    # Enforce lead existence if an ID was returned.
    if decision.decision == "propose_action" and decision.lead_id:
        matched = next((lead for lead in leads if lead.id == decision.lead_id), None)
        if matched is None:
            decision = InhouseConsultantDecision(
                decision="ask_clarification",
                clarification_question=f"I couldn't find lead {decision.lead_id}. Please provide a valid lead name, email, or ID.",
                confidence="low",
            )

    # Enforce agent existence.
    if decision.decision == "propose_action" and decision.agent_name:
        if decision.agent_name not in CONTROLLED_AGENT_REGISTRY:
            decision = InhouseConsultantDecision(
                decision="wait_for_human",
                escalation_reason=f"The model suggested unknown agent '{decision.agent_name}'. Please use the Agent Console to select a valid agent.",
                confidence="low",
            )

    return {"decision": decision, "reply": _reply_from_decision(decision)}
