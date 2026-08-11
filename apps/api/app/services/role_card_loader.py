from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ROLE_CARDS_DIR = Path(__file__).parents[3] / "agents" / "role_cards"

# Maps canonical agent names to role-card filenames.
# Canonical runtime mappings intentionally use the position-specific Phase 13
# cards where available; legacy cards remain loadable for compatibility.
AGENT_ROLE_CARD_MAP = {
    "truth_explanation_agent": "Visa_Truth_Agent",
    "document_checklist_agent": "Document_Officer",
    "client_drafting_agent": "Sales_Followup_Agent",
    "sales_summary_agent": "Sales_Summary_Agent",
    "operations_coordination_agent": "Operations_Coordination_Agent",
    "business_intelligence_agent": "Business_Intelligence_Agent",
    "vp_engineering_agent": "VP_Engineering",
    "lead_architect_agent": "Lead_Architect",
    "product_manager_agent": "Product_Manager",
    "design_agent_agent": "Design_Agent",
    "security_lead_agent": "Security_Lead",
    "threat_analyst_agent": "Threat_Analyst",
    "soc_lead_agent": "SOC_Lead",
    "soc_analyst_agent": "SOC_Analyst",
    "creative_director_agent": "Creative_Director",
    "marketing_manager_agent": "Marketing_Manager",
    "financial_analyst_agent": "Financial_Analyst",
    "accounting_lead_agent": "Accounting_Lead",
    "pr_comms_lead_agent": "PR_Comms_Lead",
    "government_relations_lead_agent": "Government_Relations_Lead",
    "application_readiness_agent": "Application_Readiness_Agent",
    "eligibility_coach": "Eligibility_Coach",
    "eligibility_agent": "Eligibility_Agent",
}

# Output schema hints that the LLM must produce for each canonical agent.
AGENT_OUTPUT_SCHEMA = {
    "truth_explanation_agent": {
        "summary": "string",
        "verdict": "string",
        "confidence": "string",
        "source_urls": ["string"],
        "conditions": ["string"],
        "safe_next_actions": ["string"],
        "blocked_actions": ["string"],
    },
    "document_checklist_agent": {
        "summary": "string",
        "missing_documents": ["string"],
        "verified_documents": ["string"],
        "safe_next_actions": ["string"],
        "blocked_actions": ["string"],
    },
    "client_drafting_agent": {
        "draft_subject": "string",
        "draft_body": "string",
        "send_allowed": False,
        "review_status": "draft_requires_human_review",
        "safe_next_actions": ["string"],
        "blocked_actions": ["string"],
    },
    "sales_summary_agent": {
        "summary": "string",
        "safe_next_actions": ["string"],
        "prohibited_claims": ["string"],
        "blocked_actions": ["string"],
    },
    "operations_coordination_agent": {
        "summary": "string",
        "workflow_status": "string",
        "dependencies": ["string"],
        "service_level_risks": ["string"],
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "blocked_actions": ["string"],
    },
    "business_intelligence_agent": {
        "summary": "string",
        "observed_signals": ["string"],
        "evidence_gaps": ["string"],
        "recommended_questions": ["string"],
        "confidence": 0.0,
        "blocked_actions": ["string"],
    },
    "vp_engineering_agent": {
        "summary": "string",
        "delivery_readiness": "evidence_complete_for_review | evidence_incomplete",
        "test_evidence": {},
        "reliability_evidence": {},
        "observability_evidence": {},
        "dependencies": ["string"],
        "rollback_posture": {},
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cto_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "deployment_allowed": False,
        "external_action_authorized": False,
        "infrastructure_mutation_allowed": False,
        "secrets_access_allowed": False,
        "blocked_actions": ["string"],
    },
    "lead_architect_agent": {
        "summary": "string",
        "architecture_assessment": {},
        "security_assessment": {},
        "data_handling_assessment": {},
        "integration_impact": {},
        "reversibility": {},
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cto_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "deployment_allowed": False,
        "external_action_authorized": False,
        "infrastructure_mutation_allowed": False,
        "secrets_access_allowed": False,
        "blocked_actions": ["string"],
    },
    "product_manager_agent": {
        "summary": "string",
        "product_fit": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cpo_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "design_agent_agent": {
        "summary": "string",
        "design_assessment": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cpo_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "security_lead_agent": {
        "summary": "string",
        "security_assessment": "evidence_complete_for_review | evidence_incomplete",
        "injection_detected": False,
        "injection_signals": ["string"],
        "compromised_agent_detected": False,
        "compromised_agent_signals": ["string"],
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_ciso_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "threat_analyst_agent": {
        "summary": "string",
        "threat_assessment": "evidence_complete_for_review | evidence_incomplete",
        "injection_detected": False,
        "injection_signals": ["string"],
        "compromised_agent_detected": False,
        "compromised_agent_signals": ["string"],
        "data_exfiltration_detected": False,
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_ciso_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "soc_lead_agent": {
        "summary": "string",
        "soc_assessment": "evidence_complete_for_review | evidence_incomplete",
        "injection_detected": False,
        "injection_signals": ["string"],
        "compromised_agent_detected": False,
        "compromised_agent_signals": ["string"],
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_ciso_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "soc_analyst_agent": {
        "summary": "string",
        "anomaly_assessment": "evidence_complete_for_review | evidence_incomplete",
        "injection_detected": False,
        "injection_signals": ["string"],
        "compromised_agent_detected": False,
        "compromised_agent_signals": ["string"],
        "data_exfiltration_detected": False,
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_ciso_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "creative_director_agent": {
        "summary": "string",
        "creative_assessment": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cmo_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "marketing_manager_agent": {
        "summary": "string",
        "marketing_fit": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cmo_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "financial_analyst_agent": {
        "summary": "string",
        "financial_assessment": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cfo_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "accounting_lead_agent": {
        "summary": "string",
        "accounting_assessment": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cfo_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "pr_comms_lead_agent": {
        "summary": "string",
        "communications_assessment": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cco_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "government_relations_lead_agent": {
        "summary": "string",
        "government_relations_assessment": "evidence_complete_for_review | evidence_incomplete",
        "evidence_basis": ["string"],
        "evidence_gaps": ["string"],
        "recommendation": "proceed_to_cco_internal_review | hold_for_evidence_or_risk",
        "dissent": False,
        "dissent_reason": "string | null",
        "material_risks": ["string"],
        "escalation_required": False,
        "safe_next_actions": ["string"],
        "confidence": 0.0,
        "human_review_required": True,
        "client_facing": False,
        "external_action_authorized": False,
        "blocked_actions": ["string"],
    },
    "application_readiness_agent": {
        "truth_clear": True,
        "documents_verified": True,
        "ready_for_operator_review": True,
        "ready_for_submission": False,
        "safe_next_actions": ["string"],
        "blocked_actions": ["string"],
    },
    "eligibility_coach": {
        "conclusion_valid": False,
        "missing_facts": ["string"],
        "source_issues": ["string"],
        "corrected_summary": "string",
        "confidence": "low | medium | high",
        "human_review_required": True,
        "safe_next_actions": ["string"],
        "blocked_actions": ["string"],
    },
    "eligibility_agent": {
        "overall_score": 0.0,
        "confidence": 0.0,
        "status": "eligible | likely_eligible | needs_documents | insufficient_profile | ineligible",
        "summary": "string",
        "risks": ["string"],
        "required_documents": ["string"],
        "pathways": ["string"],
        "factors": {},
        "human_review_required": True,
        "client_facing": False,
        "blocked_actions": ["string"],
    },
}


def _find_role_cards_dir() -> Path:
    # When running from apps/api, the cards live three levels up under agents/role_cards.
    candidate = ROLE_CARDS_DIR
    if candidate.exists():
        return candidate
    # Fallback: search upward from CWD.
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        fallback = parent / "agents" / "role_cards"
        if fallback.exists():
            return fallback
    raise FileNotFoundError(f"Could not locate agents/role_cards directory (tried {candidate})")


def list_role_cards() -> dict[str, Path]:
    directory = _find_role_cards_dir()
    return {p.stem: p for p in directory.glob("*.md")}


def _parse_sections(text: str) -> dict[str, str]:
    """Split markdown text by ## headings."""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        match = re.match(r"^##\s+(.*)$", line)
        if match:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1).strip().lower()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _extract_title(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    match = re.match(r"^#\s+(.*)$", first_line)
    return match.group(1).strip() if match else first_line.lstrip("# ").strip()


def load_role_card(name: str) -> dict[str, Any]:
    """Load a role card by its file stem (e.g. 'Visa_Truth_Agent')."""
    cards = list_role_cards()
    path = cards.get(name)
    if path is None:
        available = ", ".join(sorted(cards.keys()))
        raise FileNotFoundError(f"Role card '{name}' not found. Available: {available}")

    text = path.read_text(encoding="utf-8")
    sections = _parse_sections(text)
    title = _extract_title(text)

    return {
        "name": name,
        "title": title,
        "path": str(path),
        "mission": sections.get("mission", ""),
        "inputs": sections.get("inputs", ""),
        "outputs": sections.get("outputs", ""),
        "guardrails": sections.get("guardrails", ""),
        "allowed_sources": sections.get("allowed sources", ""),
        "reject_immediately": sections.get("reject immediately", ""),
        "output_contract": sections.get("output contract", ""),
        "raw_sections": sections,
    }


def build_system_prompt(agent_name: str) -> str:
    """Build the system prompt for a canonical controlled agent."""
    card_name = AGENT_ROLE_CARD_MAP.get(agent_name)
    if card_name is None:
        raise ValueError(f"No role-card mapping for agent '{agent_name}'")

    card = load_role_card(card_name)
    schema = AGENT_OUTPUT_SCHEMA.get(agent_name, {})
    schema_json = __import__("json").dumps(schema, indent=2, default=str)

    parts = [
        f"# {card['title']}",
        "",
        "## Mission",
        card["mission"],
        "",
    ]

    for section in ["allowed_sources", "reject_immediately", "output_contract", "guardrails"]:
        value = card.get(section, "")
        if value:
            heading = section.replace("_", " ").title()
            parts.extend([f"## {heading}", value, ""])

    parts.extend(
        [
            "## Universal Safety Rules",
            "- You are an internal assistant. Your output is reviewed by a human before any client sees it.",
            "- Never promise a specific immigration outcome (e.g., 'guaranteed visa', 'guaranteed admission').",
            "- Never suggest illegal or deceptive actions.",
            "- Always cite official sources when making factual claims.",
            "- Always set human_review_required to true and client_facing to false.",
            "- Always set deployment_allowed, external_action_authorized, infrastructure_mutation_allowed, and secrets_access_allowed to false.",
            "",
            "## Output Format",
            "Return ONLY valid JSON matching this schema (no markdown fences, no extra commentary):",
            "```json",
            schema_json,
            "```",
            "",
        ]
    )

    return "\n".join(parts).strip()


def get_agent_output_schema(agent_name: str) -> dict[str, Any]:
    return AGENT_OUTPUT_SCHEMA.get(agent_name, {})
