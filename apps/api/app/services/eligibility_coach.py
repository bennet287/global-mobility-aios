from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import AgentRun, CoachConfidence, CoachReview, CoachReviewStatus, Lead

GUARANTEED_TERMS = {"guaranteed", "guarantee", "100% visa", "sure approval", "certain"}


def _json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {"value": data}
    except Exception:
        return {"raw": value}


def _has_guarantee_language(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in GUARANTEED_TERMS)


def _find_target_run(session: Session, lead_id: UUID, agent_run_id: UUID | None = None, target_agent_name: str | None = None) -> AgentRun | None:
    if agent_run_id is not None:
        return session.get(AgentRun, agent_run_id)

    target_agents = [target_agent_name] if target_agent_name else ["application_readiness_agent", "sales_summary_agent"]
    rows = session.exec(
        select(AgentRun)
        .where(AgentRun.lead_id == lead_id)
        .where(AgentRun.agent_name.in_(target_agents))
        .order_by(AgentRun.created_at.desc())
    ).all()
    return rows[0] if rows else None


def evaluate_eligibility_output(output: dict[str, Any], lead_data: dict[str, Any]) -> dict[str, Any]:
    """Deterministic coach evaluation of an eligibility/pathway output."""
    text = json.dumps(output, default=str, sort_keys=True)
    missing_facts: list[str] = []
    source_issues: list[str] = []

    # Guardrail checks
    if _has_guarantee_language(text):
        source_issues.append("Output contains guarantee-like language that must be removed before client review.")

    # Fact checks against lead
    if not lead_data.get("target_country"):
        missing_facts.append("Target country is missing; eligibility cannot be assessed without it.")
    if not lead_data.get("intent") or lead_data.get("intent") == "unknown":
        missing_facts.append("Client goal/intent is unknown; a pathway cannot be chosen safely.")

    # Source grounding check
    if not output.get("source_urls") and not output.get("official_sources"):
        source_issues.append("No official sources attached to factual eligibility claims.")

    # Confidence scoring
    if source_issues or missing_facts:
        confidence = CoachConfidence.low
        conclusion_valid = False
    elif output.get("confidence") in {"low", CoachConfidence.low}:
        confidence = CoachConfidence.medium
        conclusion_valid = False
    else:
        confidence = CoachConfidence.high
        conclusion_valid = True

    # Build corrected summary
    if conclusion_valid:
        corrected_summary = output.get("summary", "Eligibility conclusion appears factually grounded and safe for human review.")
    else:
        corrected_summary = (
            "Eligibility conclusion requires review. "
            f"Missing facts: {len(missing_facts)}. Source issues: {len(source_issues)}. "
            "Do not share with the client until resolved."
        )

    return {
        "conclusion_valid": conclusion_valid,
        "missing_facts": missing_facts,
        "source_issues": source_issues,
        "corrected_summary": corrected_summary,
        "confidence": confidence.value,
        "human_review_required": True,
        "safe_next_actions": [
            "Address missing facts before client communication." if missing_facts else "Facts appear complete.",
            "Attach official sources to all eligibility claims." if source_issues else "Sources attached.",
            "Escalate to a consultant if the conclusion changes materially.",
        ],
        "blocked_actions": ["client_send", "lead_conversion", "guarantee_claim"],
    }


def run_eligibility_coach_review(
    session: Session,
    lead_id: UUID,
    agent_run_id: UUID | None = None,
    target_agent_name: str | None = None,
    actor: str = "system",
) -> CoachReview:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError(f"Lead {lead_id} not found")

    target_run = _find_target_run(session, lead_id, agent_run_id, target_agent_name)
    target_output: dict[str, Any] = _json_loads(target_run.output_json) if target_run else {}
    target_agent = target_run.agent_name if target_run else (target_agent_name or "unknown")

    lead_data = {
        "id": str(lead.id),
        "target_country": lead.target_country,
        "intent": getattr(lead.intent, "value", lead.intent),
    }
    evaluation = evaluate_eligibility_output(target_output, lead_data)

    review = CoachReview(
        lead_id=lead_id,
        agent_run_id=target_run.id if target_run else None,
        coach_agent_name="eligibility_coach",
        target_agent_name=target_agent,
        conclusion_valid=evaluation["conclusion_valid"],
        missing_facts_json=json.dumps(evaluation["missing_facts"]),
        source_issues_json=json.dumps(evaluation["source_issues"]),
        corrected_summary=evaluation["corrected_summary"],
        confidence=CoachConfidence(evaluation["confidence"]),
        status=CoachReviewStatus.pending,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review
