from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ROLE_CARDS_DIR = Path(__file__).parents[3] / "agents" / "role_cards"

# Maps canonical agent names to role-card filenames.
# Cards currently in agents/role_cards/:
#   AI_CEO, Document_Officer, Recruitment_Specialist,
#   Sales_Followup_Agent, Study_Abroad_Advisor, Visa_Truth_Agent
AGENT_ROLE_CARD_MAP = {
    "truth_explanation_agent": "Visa_Truth_Agent",
    "document_checklist_agent": "Document_Officer",
    "client_drafting_agent": "Sales_Followup_Agent",
    "sales_summary_agent": "Recruitment_Specialist",
    "application_readiness_agent": "AI_CEO",
    "eligibility_coach": "Eligibility_Coach",
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
