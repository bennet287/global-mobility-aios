from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session, select

from app.agents.registry import AGENT_ALIASES, CONTROLLED_AGENT_REGISTRY
from app.core.config import settings
from app.models.domain import AgentRun, AgentRunStatus
from app.schemas import ControlledAgentRunRequest, ControlledAgentRunResponse
from app.services.audit_log import record_audit
from app.services.eligibility_coach import evaluate_eligibility_output
from app.services.eligibility_engine import evaluate_lead_eligibility
from app.services.llm_client import LLMProviderError, LLMProviderFactory, is_llm_enabled
from app.services.role_card_loader import build_system_prompt, get_agent_output_schema


PENDING_AGENT_OUTPUT_STATUSES = {
    AgentRunStatus.completed.value,
    AgentRunStatus.pending_review.value,
}
CLIENT_DRAFTING_AGENT = "client_drafting_agent"
CONTROLLED_AGENT_SAFETY_FIELDS = {
    "human_review_required": True,
    "client_facing": False,
    "deployment_allowed": False,
    "external_action_authorized": False,
    "infrastructure_mutation_allowed": False,
    "secrets_access_allowed": False,
}
TECHNOLOGY_AGENT_CONTROLLED_FIELDS = {
    "delivery_readiness",
    "evidence_basis",
    "evidence_gaps",
    "recommendation",
    "dissent",
    "dissent_reason",
    "material_risks",
    "escalation_required",
    "confidence",
    "blocked_actions",
}
PRODUCT_AGENT_CONTROLLED_FIELDS = {
    "product_fit",
    "design_assessment",
    "evidence_basis",
    "evidence_gaps",
    "recommendation",
    "dissent",
    "dissent_reason",
    "material_risks",
    "escalation_required",
    "confidence",
    "blocked_actions",
}
SECURITY_AGENT_CONTROLLED_FIELDS = {
    "summary",
    "security_assessment",
    "threat_assessment",
    "evidence_basis",
    "evidence_gaps",
    "recommendation",
    "dissent",
    "dissent_reason",
    "material_risks",
    "escalation_required",
    "confidence",
    "blocked_actions",
}
SOC_AGENT_CONTROLLED_FIELDS = {
    "summary",
    "soc_assessment",
    "anomaly_assessment",
    "evidence_basis",
    "evidence_gaps",
    "recommendation",
    "dissent",
    "dissent_reason",
    "material_risks",
    "escalation_required",
    "confidence",
    "blocked_actions",
}
MARKETING_AGENT_CONTROLLED_FIELDS = {
    "summary",
    "creative_assessment",
    "marketing_fit",
    "evidence_basis",
    "evidence_gaps",
    "recommendation",
    "dissent",
    "dissent_reason",
    "material_risks",
    "escalation_required",
    "confidence",
    "blocked_actions",
}
FINANCE_AGENT_CONTROLLED_FIELDS = {
    "summary",
    "financial_assessment",
    "accounting_assessment",
    "evidence_basis",
    "evidence_gaps",
    "recommendation",
    "dissent",
    "dissent_reason",
    "material_risks",
    "escalation_required",
    "confidence",
    "blocked_actions",
}


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
        **CONTROLLED_AGENT_SAFETY_FIELDS,
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


def _operations_coordination(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    dependencies = facts.get("dependencies", [])
    service_level_risks = facts.get("service_level_risks", [])
    output.update(
        {
            "summary": "Internal operating sequence prepared from the recorded workflow context.",
            "workflow_status": str(facts.get("status") or "needs_review"),
            "dependencies": dependencies if isinstance(dependencies, list) else [],
            "service_level_risks": service_level_risks if isinstance(service_level_risks, list) else [],
            "safe_next_actions": [
                "Confirm the accountable owner for each unresolved dependency.",
                "Escalate material delay or client-impact risk to the COO.",
            ],
            "confidence": 0.6 if facts else 0.35,
            "blocked_actions": [
                "case_status_change",
                "authority_submission",
                "client_send",
                "external_provider_action",
            ],
        }
    )
    return output


def _business_intelligence(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    observed = [f"{key}={value}" for key, value in sorted(facts.items()) if value not in (None, "", [], {})]
    output.update(
        {
            "summary": "Evidence-backed operating signals prepared for internal COO review.",
            "observed_signals": observed,
            "evidence_gaps": [] if observed else ["No structured operating facts were supplied."],
            "recommended_questions": [
                "Which recorded signal materially changes the operating priority?",
                "What additional evidence is required before an executive decision?",
            ],
            "confidence": 0.55 if observed else 0.25,
            "blocked_actions": [
                "forecast_as_fact",
                "pricing_change",
                "payment_initiation",
                "client_send",
            ],
        }
    )
    return output


def _is_supplied(value: Any) -> bool:
    return value not in (None, "", [], {})


def _first_supplied(facts: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = facts.get(key)
        if _is_supplied(value):
            return value
    return None


def _technology_context(payload: ControlledAgentRunRequest) -> dict[str, Any]:
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    evidence = payload.context.get("evidence", {})
    if isinstance(evidence, dict):
        # Explicit work facts take precedence over the accompanying evidence map.
        return {**evidence, **facts}
    if isinstance(evidence, list) and evidence:
        return {**facts, "sources": evidence}
    return facts


def _bounded_evidence_confidence(evidence_basis: list[str], required_fields: tuple[str, ...]) -> float:
    supplied = len(set(evidence_basis).intersection(required_fields))
    return round(min(0.85, 0.2 + (0.1 * supplied)), 2)


def _technology_risk_signals(
    facts: dict[str, Any],
    *,
    role_prefix: str,
) -> tuple[str | None, list[str]]:
    dissent_reason = _first_supplied(
        facts,
        f"{role_prefix}_dissent_reason",
        "technology_dissent_reason",
    )
    material_risks = _first_supplied(
        facts,
        f"{role_prefix}_material_risks",
        "technology_material_risks",
    )
    if not isinstance(material_risks, list):
        material_risks = [str(material_risks)] if _is_supplied(material_risks) else []
    return str(dissent_reason) if _is_supplied(dissent_reason) else None, material_risks


def _vp_engineering(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _technology_context(payload)
    evidence = {
        "tests": _first_supplied(facts, "tests", "test_evidence", "test_results"),
        "reliability": _first_supplied(facts, "reliability", "reliability_evidence"),
        "observability": _first_supplied(facts, "observability", "observability_evidence"),
        "dependencies": _first_supplied(facts, "dependencies", "delivery_dependencies"),
        "rollback": _first_supplied(facts, "rollback", "rollback_plan", "rollback_evidence"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dependencies = evidence["dependencies"]
    if not isinstance(dependencies, list):
        dependencies = [str(dependencies)] if _is_supplied(dependencies) else []
    dissent_reason, material_risks = _technology_risk_signals(
        facts,
        role_prefix="engineering",
    )
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Engineering delivery evidence assessed for internal CTO review.",
            "delivery_readiness": (
                "evidence_complete_for_review" if not evidence_gaps else "evidence_incomplete"
            ),
            "test_evidence": evidence["tests"] or {},
            "reliability_evidence": evidence["reliability"] or {},
            "observability_evidence": evidence["observability"] or {},
            "dependencies": dependencies,
            "rollback_posture": evidence["rollback"] or {},
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cto_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded evidence gap before a delivery recommendation is accepted.",
                "Escalate production, security, reliability, spend, or contractual action to the CTO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "deployment.production",
                "production_mutation",
                "infrastructure_mutation",
                "secrets_access",
                "spend_initiation",
                "contract_signing",
                "external_action",
            ],
        }
    )
    return output


def _lead_architect(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _technology_context(payload)
    evidence = {
        "architecture": _first_supplied(facts, "architecture", "architecture_evidence"),
        "security": _first_supplied(facts, "security", "security_evidence"),
        "data_handling": _first_supplied(facts, "data_handling", "data_classification"),
        "integration": _first_supplied(facts, "integration", "integration_impact"),
        "reversibility": _first_supplied(
            facts,
            "reversibility",
            "rollback",
            "rollback_plan",
            "rollback_evidence",
        ),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _technology_risk_signals(
        facts,
        role_prefix="architecture",
    )
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Architecture and security evidence assessed for internal CTO review.",
            "architecture_assessment": evidence["architecture"] or {},
            "security_assessment": evidence["security"] or {},
            "data_handling_assessment": evidence["data_handling"] or {},
            "integration_impact": evidence["integration"] or {},
            "reversibility": evidence["reversibility"] or {},
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cto_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded architecture, security, data, integration, and provenance gap.",
                "Escalate irreversible production or material security risk to the CTO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "deployment.production",
                "architecture_mutation",
                "infrastructure_mutation",
                "secrets_access",
                "spend_initiation",
                "contract_signing",
                "external_action",
            ],
        }
    )
    return output


def _product_context(payload: ControlledAgentRunRequest) -> dict[str, Any]:
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    evidence = payload.context.get("evidence", {})
    if isinstance(evidence, dict):
        return {**evidence, **facts}
    if isinstance(evidence, list) and evidence:
        return {**facts, "sources": evidence}
    return facts


def _product_risk_signals(
    facts: dict[str, Any],
    *,
    role_prefix: str,
) -> tuple[str | None, list[str]]:
    dissent_reason = _first_supplied(
        facts,
        f"{role_prefix}_dissent_reason",
        "product_dissent_reason",
    )
    material_risks = _first_supplied(
        facts,
        f"{role_prefix}_material_risks",
        "product_material_risks",
    )
    if not isinstance(material_risks, list):
        material_risks = [str(material_risks)] if _is_supplied(material_risks) else []
    return str(dissent_reason) if _is_supplied(dissent_reason) else None, material_risks


def _product_manager(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _product_context(payload)
    evidence = {
        "user_evidence": _first_supplied(facts, "user_evidence", "user_research"),
        "market_evidence": _first_supplied(facts, "market_evidence", "market_signals"),
        "scope": _first_supplied(facts, "scope", "proposed_scope"),
        "dependencies": _first_supplied(facts, "dependencies", "product_dependencies"),
        "roadmap_alignment": _first_supplied(facts, "roadmap_alignment", "roadmap_fit"),
        "success_metrics": _first_supplied(facts, "success_metrics", "metrics"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
        "risks": _first_supplied(facts, "risks", "known_risks"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dependencies = evidence["dependencies"]
    if not isinstance(dependencies, list):
        dependencies = [str(dependencies)] if _is_supplied(dependencies) else []
    dissent_reason, material_risks = _product_risk_signals(facts, role_prefix="product_manager")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Product fit and scope evidence assessed for internal CPO review.",
            "product_fit": "evidence_complete_for_review" if not evidence_gaps else "evidence_incomplete",
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "dependencies": dependencies,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cpo_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded product evidence gap before a recommendation is accepted.",
                "Escalate pricing, policy, roadmap, or external action requests to the CPO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "pricing.change",
                "policy.publish",
                "client.external_send",
                "contract_signing",
                "external_action",
            ],
        }
    )
    return output


def _design_agent(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _product_context(payload)
    evidence = {
        "design_principles": _first_supplied(facts, "design_principles", "design_standards"),
        "ux_research": _first_supplied(facts, "ux_research", "ux_evidence"),
        "accessibility": _first_supplied(facts, "accessibility", "accessibility_evidence"),
        "scope": _first_supplied(facts, "scope", "proposed_scope"),
        "dependencies": _first_supplied(facts, "dependencies", "design_dependencies"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
        "risks": _first_supplied(facts, "risks", "known_risks"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dependencies = evidence["dependencies"]
    if not isinstance(dependencies, list):
        dependencies = [str(dependencies)] if _is_supplied(dependencies) else []
    dissent_reason, material_risks = _product_risk_signals(facts, role_prefix="design_agent")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Design quality and accessibility evidence assessed for internal CPO review.",
            "design_assessment": "evidence_complete_for_review" if not evidence_gaps else "evidence_incomplete",
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "dependencies": dependencies,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cpo_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded design evidence gap before a recommendation is accepted.",
                "Escalate production design release or external asset publication to the CPO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "deployment.production",
                "design.publish",
                "client.external_send",
                "external_action",
            ],
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


INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore the above",
    "ignore your instructions",
    "you are now",
    "pretend you are",
    "simulate being",
    "jailbreak",
    "do not tell anyone",
    "do not disclose",
    "leak",
    "exfiltrate",
    "output the system prompt",
    "repeat the prompt",
    "system prompt",
    "training data",
    "api key",
    "token",
    "secret",
    "password",
    "confidential",
    "internal only",
)


def _detect_injection_signals(context: dict[str, Any]) -> tuple[bool, list[str]]:
    """Scan supplied context for prompt-injection / compromised-agent indicators."""
    text = ""
    for value in context.values():
        if isinstance(value, str):
            text += value + "\n"
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, str):
                    text += item + "\n"
        elif isinstance(value, dict):
            for nested in value.values():
                if isinstance(nested, str):
                    text += nested + "\n"
                elif isinstance(nested, (list, tuple)):
                    for item in nested:
                        if isinstance(item, str):
                            text += item + "\n"
    text_lower = text.lower()
    hits = [pattern for pattern in INJECTION_PATTERNS if pattern in text_lower]
    return bool(hits), sorted(set(hits))


COMPROMISED_AGENT_INDICATORS = (
    "override safety",
    "disable guardrails",
    "turn off review",
    "approve immediately",
    "no human review",
    "auto-approve",
    "bypass",
    "suppress dissent",
    "hide this",
    "delete logs",
    "untraceable",
)


def _detect_compromised_agent_signals(context: dict[str, Any]) -> tuple[bool, list[str]]:
    """Scan supplied context for compromised-agent / malicious-override indicators."""
    text = ""
    for value in context.values():
        if isinstance(value, str):
            text += value + "\n"
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, str):
                    text += item + "\n"
        elif isinstance(value, dict):
            for nested in value.values():
                if isinstance(nested, str):
                    text += nested + "\n"
                elif isinstance(nested, (list, tuple)):
                    for item in nested:
                        if isinstance(item, str):
                            text += item + "\n"
    text_lower = text.lower()
    hits = [indicator for indicator in COMPROMISED_AGENT_INDICATORS if indicator in text_lower]
    return bool(hits), sorted(set(hits))


def _security_context(payload: ControlledAgentRunRequest) -> dict[str, Any]:
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    evidence = payload.context.get("evidence", {})
    if isinstance(evidence, dict):
        return {**evidence, **facts}
    if isinstance(evidence, list) and evidence:
        return {**facts, "sources": evidence}
    return facts


def _security_risk_signals(
    facts: dict[str, Any],
    *,
    role_prefix: str,
) -> tuple[str | None, list[str]]:
    dissent_reason = _first_supplied(
        facts,
        f"{role_prefix}_dissent_reason",
        "security_dissent_reason",
    )
    material_risks = _first_supplied(
        facts,
        f"{role_prefix}_material_risks",
        "security_material_risks",
    )
    if not isinstance(material_risks, list):
        material_risks = [str(material_risks)] if _is_supplied(material_risks) else []
    return str(dissent_reason) if _is_supplied(dissent_reason) else None, material_risks


def _security_lead(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _security_context(payload)
    evidence = {
        "controls": _first_supplied(facts, "controls", "security_controls", "control_evidence"),
        "attack_surface": _first_supplied(facts, "attack_surface", "attack_surface_evidence"),
        "policy_alignment": _first_supplied(facts, "policy_alignment", "policy_fit", "security_policy"),
        "impact": _first_supplied(facts, "impact", "security_impact", "impact_assessment"),
        "risks": _first_supplied(facts, "risks", "known_risks", "security_risks"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _security_risk_signals(facts, role_prefix="security_lead")
    injection_detected, injection_signals = _detect_injection_signals(payload.context)
    compromised_detected, compromised_signals = _detect_compromised_agent_signals(payload.context)
    if injection_detected:
        material_risks.append(f"prompt-injection signals detected: {', '.join(injection_signals)}")
    if compromised_detected:
        material_risks.append(f"compromised-agent indicators detected: {', '.join(compromised_signals)}")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks or injection_detected or compromised_detected)
    output.update(
        {
            "summary": "Security controls and attack-surface evidence assessed for internal CISO review.",
            "security_assessment": (
                "evidence_complete_for_review"
                if not (evidence_gaps or injection_detected or compromised_detected)
                else "evidence_incomplete"
            ),
            "injection_detected": injection_detected,
            "injection_signals": injection_signals,
            "compromised_agent_detected": compromised_detected,
            "compromised_agent_signals": compromised_signals,
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_ciso_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded security evidence gap before a recommendation is accepted.",
                "Escalate policy change, position suspension, secret access, or external action to the CISO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "position.suspend",
                "contract.sign",
                "policy.publish",
                "secrets.access",
                "deployment.production",
                "infrastructure.mutation",
                "payment.initiate",
                "client.external_send",
                "vendor.commit",
            ],
        }
    )
    return output


def _threat_analyst(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _security_context(payload)
    evidence = {
        "threat_evidence": _first_supplied(facts, "threat_evidence", "threats", "threat_intelligence"),
        "signals": _first_supplied(facts, "signals", "suspicious_signals", "security_signals"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _security_risk_signals(facts, role_prefix="threat_analyst")
    injection_detected, injection_signals = _detect_injection_signals(payload.context)
    compromised_detected, compromised_signals = _detect_compromised_agent_signals(payload.context)
    data_exfiltration_detected = any(
        signal in " ".join(str(v) for v in payload.context.values()).lower()
        for signal in ("exfiltrate", "leak", "output the system prompt", "repeat the prompt")
    )
    if injection_detected:
        material_risks.append(f"prompt-injection/jailbreak signals detected: {', '.join(injection_signals)}")
    if compromised_detected:
        material_risks.append(f"compromised-agent indicators detected: {', '.join(compromised_signals)}")
    if data_exfiltration_detected:
        material_risks.append("data-exfiltration indicator detected")
    must_hold = bool(
        evidence_gaps
        or dissent_reason
        or material_risks
        or injection_detected
        or compromised_detected
        or data_exfiltration_detected
    )
    output.update(
        {
            "summary": "Threat evidence and compromise indicators assessed for internal CISO review.",
            "threat_assessment": (
                "evidence_complete_for_review"
                if not (evidence_gaps or injection_detected or compromised_detected or data_exfiltration_detected)
                else "evidence_incomplete"
            ),
            "injection_detected": injection_detected,
            "injection_signals": injection_signals,
            "compromised_agent_detected": compromised_detected,
            "compromised_agent_signals": compromised_signals,
            "data_exfiltration_detected": data_exfiltration_detected,
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_ciso_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Treat every detected injection, jailbreak, or compromise indicator as escalation-worthy.",
                "Escalate confirmed indicators to the CISO; do not approve external action or policy change.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "position.suspend",
                "contract.sign",
                "policy.publish",
                "secrets.access",
                "deployment.production",
                "infrastructure.mutation",
                "payment.initiate",
                "client.external_send",
                "vendor.commit",
            ],
        }
    )
    return output


def _soc_context(payload: ControlledAgentRunRequest) -> dict[str, Any]:
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    evidence = payload.context.get("evidence", {})
    if isinstance(evidence, dict):
        return {**evidence, **facts}
    if isinstance(evidence, list) and evidence:
        return {**facts, "sources": evidence}
    return facts


def _soc_risk_signals(
    facts: dict[str, Any],
    *,
    role_prefix: str,
) -> tuple[str | None, list[str]]:
    dissent_reason = _first_supplied(
        facts,
        f"{role_prefix}_dissent_reason",
        "soc_dissent_reason",
    )
    material_risks = _first_supplied(
        facts,
        f"{role_prefix}_material_risks",
        "soc_material_risks",
    )
    if not isinstance(material_risks, list):
        material_risks = [str(material_risks)] if _is_supplied(material_risks) else []
    return str(dissent_reason) if _is_supplied(dissent_reason) else None, material_risks


def _marketing_context(payload: ControlledAgentRunRequest) -> dict[str, Any]:
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    evidence = payload.context.get("evidence", {})
    if isinstance(evidence, dict):
        return {**evidence, **facts}
    if isinstance(evidence, list) and evidence:
        return {**facts, "sources": evidence}
    return facts


def _marketing_risk_signals(
    facts: dict[str, Any],
    *,
    role_prefix: str,
) -> tuple[str | None, list[str]]:
    dissent_reason = _first_supplied(
        facts,
        f"{role_prefix}_dissent_reason",
        "marketing_dissent_reason",
    )
    material_risks = _first_supplied(
        facts,
        f"{role_prefix}_material_risks",
        "marketing_material_risks",
    )
    if not isinstance(material_risks, list):
        material_risks = [str(material_risks)] if _is_supplied(material_risks) else []
    return str(dissent_reason) if _is_supplied(dissent_reason) else None, material_risks


def _soc_lead(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _soc_context(payload)
    evidence = {
        "agent_activity": _first_supplied(facts, "agent_activity", "agent_behavior"),
        "audit_logs": _first_supplied(facts, "audit_logs", "logs"),
        "incident_history": _first_supplied(facts, "incident_history", "incidents"),
        "monitored_signals": _first_supplied(facts, "monitored_signals", "signals"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _soc_risk_signals(facts, role_prefix="soc_lead")
    injection_detected, injection_signals = _detect_injection_signals(payload.context)
    compromised_detected, compromised_signals = _detect_compromised_agent_signals(payload.context)
    if injection_detected:
        material_risks.append(f"prompt-injection signals detected: {', '.join(injection_signals)}")
    if compromised_detected:
        material_risks.append(f"compromised-agent indicators detected: {', '.join(compromised_signals)}")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks or injection_detected or compromised_detected)
    output.update(
        {
            "summary": "SOC posture and anomaly triage assessed for internal CISO review.",
            "soc_assessment": (
                "evidence_complete_for_review"
                if not (evidence_gaps or injection_detected or compromised_detected)
                else "evidence_incomplete"
            ),
            "injection_detected": injection_detected,
            "injection_signals": injection_signals,
            "compromised_agent_detected": compromised_detected,
            "compromised_agent_signals": compromised_signals,
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_ciso_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Correlate every detected anomaly with recorded audit logs before triage closure.",
                "Escalate confirmed injection, compromise, or incident indicators to the CISO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "position.suspend",
                "contract.sign",
                "policy.publish",
                "secrets.access",
                "deployment.production",
                "infrastructure.mutation",
                "payment.initiate",
                "client.external_send",
                "vendor.commit",
            ],
        }
    )
    return output


def _soc_analyst(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _soc_context(payload)
    evidence = {
        "agent_outputs": _first_supplied(facts, "agent_outputs", "outputs"),
        "audit_logs": _first_supplied(facts, "audit_logs", "logs"),
        "signals": _first_supplied(facts, "signals", "suspicious_signals", "security_signals"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _soc_risk_signals(facts, role_prefix="soc_analyst")
    injection_detected, injection_signals = _detect_injection_signals(payload.context)
    compromised_detected, compromised_signals = _detect_compromised_agent_signals(payload.context)
    data_exfiltration_detected = any(
        signal in " ".join(str(v) for v in payload.context.values()).lower()
        for signal in ("exfiltrate", "leak", "output the system prompt", "repeat the prompt")
    )
    if injection_detected:
        material_risks.append(f"prompt-injection/jailbreak signals detected: {', '.join(injection_signals)}")
    if compromised_detected:
        material_risks.append(f"compromised-agent indicators detected: {', '.join(compromised_signals)}")
    if data_exfiltration_detected:
        material_risks.append("data-exfiltration indicator detected")
    must_hold = bool(
        evidence_gaps
        or dissent_reason
        or material_risks
        or injection_detected
        or compromised_detected
        or data_exfiltration_detected
    )
    output.update(
        {
            "summary": "Agent-output and audit-log anomaly analysis assessed for internal CISO review.",
            "anomaly_assessment": (
                "evidence_complete_for_review"
                if not (evidence_gaps or injection_detected or compromised_detected or data_exfiltration_detected)
                else "evidence_incomplete"
            ),
            "injection_detected": injection_detected,
            "injection_signals": injection_signals,
            "compromised_agent_detected": compromised_detected,
            "compromised_agent_signals": compromised_signals,
            "data_exfiltration_detected": data_exfiltration_detected,
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_ciso_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Treat every detected injection, jailbreak, or compromise indicator as escalation-worthy.",
                "Correlate anomalies with audit-trail provenance before any disposition.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "position.suspend",
                "contract.sign",
                "policy.publish",
                "secrets.access",
                "deployment.production",
                "infrastructure.mutation",
                "payment.initiate",
                "client.external_send",
                "vendor.commit",
            ],
        }
    )
    return output


def _creative_director(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _marketing_context(payload)
    evidence = {
        "audience_evidence": _first_supplied(facts, "audience_evidence", "audience_research", "audience_signals"),
        "brand_guidelines": _first_supplied(facts, "brand_guidelines", "brand_standards", "brand_policy"),
        "creative_assets": _first_supplied(facts, "creative_assets", "assets", "creative"),
        "messaging": _first_supplied(facts, "messaging", "messaging_drafts", "copy"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _marketing_risk_signals(facts, role_prefix="creative_director")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Brand, creative, and messaging evidence assessed for internal CMO review.",
            "creative_assessment": "evidence_complete_for_review" if not evidence_gaps else "evidence_incomplete",
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cmo_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded creative evidence gap before a recommendation is accepted.",
                "Escalate creative-asset publication, external messaging, or brand-policy claims to the CMO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "pricing.change",
                "policy.publish",
                "client.external_send",
                "contract.sign",
                "deployment.production",
                "external_action",
                "campaign.launch",
            ],
        }
    )
    return output


def _marketing_manager(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _marketing_context(payload)
    evidence = {
        "budget_constraints": _first_supplied(facts, "budget_constraints", "budget", "budget_limit"),
        "campaign_plan": _first_supplied(facts, "campaign_plan", "campaign"),
        "channel_strategy": _first_supplied(facts, "channel_strategy", "channels"),
        "risks": _first_supplied(facts, "risks", "known_risks", "marketing_risks"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
        "success_metrics": _first_supplied(facts, "success_metrics", "metrics", "growth_metrics"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _marketing_risk_signals(facts, role_prefix="marketing_manager")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Channel, campaign, and growth evidence assessed for internal CMO review.",
            "marketing_fit": "evidence_complete_for_review" if not evidence_gaps else "evidence_incomplete",
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cmo_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded campaign and channel evidence gap before a recommendation is accepted.",
                "Escalate campaign launch, spend, pricing, or external messaging decisions to the CMO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "pricing.change",
                "policy.publish",
                "client.external_send",
                "contract.sign",
                "payment.initiate",
                "external_action",
                "campaign.launch",
            ],
        }
    )
    return output


def _finance_context(payload: ControlledAgentRunRequest) -> dict[str, Any]:
    facts = payload.context.get("facts", {})
    facts = facts if isinstance(facts, dict) else {}
    evidence = payload.context.get("evidence", {})
    if isinstance(evidence, dict):
        return {**evidence, **facts}
    if isinstance(evidence, list) and evidence:
        return {**facts, "sources": evidence}
    return facts


def _finance_risk_signals(
    facts: dict[str, Any],
    *,
    role_prefix: str,
) -> tuple[str | None, list[str]]:
    dissent_reason = _first_supplied(
        facts,
        f"{role_prefix}_dissent_reason",
        "finance_dissent_reason",
    )
    material_risks = _first_supplied(
        facts,
        f"{role_prefix}_material_risks",
        "finance_material_risks",
    )
    if not isinstance(material_risks, list):
        material_risks = [str(material_risks)] if _is_supplied(material_risks) else []
    return str(dissent_reason) if _is_supplied(dissent_reason) else None, material_risks


def _financial_analyst(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _finance_context(payload)
    evidence = {
        "cost_structure": _first_supplied(facts, "cost_structure", "costs"),
        "pricing_model": _first_supplied(facts, "pricing_model", "pricing"),
        "revenue_model": _first_supplied(facts, "revenue_model", "revenue", "fee_model"),
        "budget_constraints": _first_supplied(facts, "budget_constraints", "budget", "budget_limit"),
        "scenario_parameters": _first_supplied(facts, "scenario_parameters", "scenarios"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
        "risks": _first_supplied(facts, "risks", "known_risks", "finance_risks"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _finance_risk_signals(facts, role_prefix="financial_analyst")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Financial scenario and unit-economics evidence assessed for internal CFO review.",
            "financial_assessment": "evidence_complete_for_review" if not evidence_gaps else "evidence_incomplete",
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cfo_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded financial evidence gap before a recommendation is accepted.",
                "Escalate funds movement, pricing changes, spend commitments, contracts, or tax conclusions to the CFO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "payment.initiate",
                "pricing.change",
                "spend.above_threshold",
                "contract.sign",
                "client.external_send",
                "external_action",
            ],
        }
    )
    return output


def _accounting_lead(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    facts = _finance_context(payload)
    evidence = {
        "chart_of_accounts": _first_supplied(facts, "chart_of_accounts", "accounts"),
        "ap_ar_aging": _first_supplied(facts, "ap_ar_aging", "ap_ar", "receivables_payables"),
        "reconciliation": _first_supplied(facts, "reconciliation", "reconciliation_status"),
        "audit_trail": _first_supplied(facts, "audit_trail", "audit_evidence"),
        "tax_treaty_implications": _first_supplied(facts, "tax_treaty_implications", "tax_treaty"),
        "compliance_controls": _first_supplied(facts, "compliance_controls", "controls"),
        "sources": _first_supplied(facts, "sources", "source_provenance"),
        "risks": _first_supplied(facts, "risks", "known_risks", "accounting_risks"),
    }
    evidence_basis = [key for key, value in evidence.items() if _is_supplied(value)]
    evidence_gaps = [key for key, value in evidence.items() if not _is_supplied(value)]
    required = tuple(evidence)
    dissent_reason, material_risks = _finance_risk_signals(facts, role_prefix="accounting_lead")
    must_hold = bool(evidence_gaps or dissent_reason or material_risks)
    output.update(
        {
            "summary": "Accounting, audit-readiness, and compliance evidence assessed for internal CFO review.",
            "accounting_assessment": "evidence_complete_for_review" if not evidence_gaps else "evidence_incomplete",
            "evidence_basis": evidence_basis,
            "evidence_gaps": evidence_gaps,
            "recommendation": (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cfo_internal_review"
            ),
            "dissent": dissent_reason is not None,
            "dissent_reason": dissent_reason,
            "material_risks": material_risks,
            "escalation_required": must_hold,
            "safe_next_actions": [
                "Resolve every recorded accounting evidence gap before a recommendation is accepted.",
                "Escalate funds movement, journal entries, tax positions, audit representations, or contracts to the CFO.",
            ],
            "confidence": _bounded_evidence_confidence(evidence_basis, required),
            "blocked_actions": [
                "payment.initiate",
                "pricing.change",
                "spend.above_threshold",
                "contract.sign",
                "client.external_send",
                "external_action",
            ],
        }
    )
    return output


def _eligibility_coach(payload: ControlledAgentRunRequest, agent: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(payload, agent)
    lead_data = payload.context.get("lead", {})
    target_output = payload.context.get("target_output", {})
    evaluation = evaluate_eligibility_output(target_output, lead_data)
    output.update(evaluation)
    return output


def _eligibility_agent(payload: ControlledAgentRunRequest, agent: dict[str, Any]):
    output = _base_output(payload, agent)
    assessment = payload.context.get("assessment", {})
    if not assessment:
        output.update({
            "overall_score": 0.0,
            "confidence": 0.0,
            "status": "insufficient_profile",
            "summary": "Cannot assess eligibility: no assessment result provided in context.",
            "risks": ["Eligibility engine result missing."],
            "required_documents": [],
            "pathways": [],
            "factors": {},
        })
    else:
        output.update(assessment)
    output["blocked_actions"] = ["client_send", "lead_conversion", "guarantee_claim"]
    return output


DETERMINISTIC_HANDLERS = {
    "truth_explanation_agent": _truth_explanation,
    "document_checklist_agent": _document_checklist,
    "client_drafting_agent": _client_drafting,
    "sales_summary_agent": _sales_summary,
    "operations_coordination_agent": _operations_coordination,
    "business_intelligence_agent": _business_intelligence,
    "vp_engineering_agent": _vp_engineering,
    "lead_architect_agent": _lead_architect,
    "product_manager_agent": _product_manager,
    "design_agent_agent": _design_agent,
    "security_lead_agent": _security_lead,
    "threat_analyst_agent": _threat_analyst,
    "soc_lead_agent": _soc_lead,
    "soc_analyst_agent": _soc_analyst,
    "creative_director_agent": _creative_director,
    "marketing_manager_agent": _marketing_manager,
    "financial_analyst_agent": _financial_analyst,
    "accounting_lead_agent": _accounting_lead,
    "application_readiness_agent": _application_readiness,
    "eligibility_coach": _eligibility_coach,
    "eligibility_agent": _eligibility_agent,
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
    immutable_fields = {*CONTROLLED_AGENT_SAFETY_FIELDS, "workflow_position"}
    for key, value in output.items():
        if key not in immutable_fields:
            merged[key] = value
    merged.update(CONTROLLED_AGENT_SAFETY_FIELDS)
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
        if resolved_name in {"vp_engineering_agent", "lead_architect_agent"}:
            deterministic = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)
            for key in TECHNOLOGY_AGENT_CONTROLLED_FIELDS:
                if key in deterministic:
                    output[key] = deterministic[key]
            model_gaps = parsed.get("evidence_gaps")
            model_gaps = model_gaps if isinstance(model_gaps, list) else []
            output["evidence_gaps"] = sorted(
                {
                    str(item)
                    for item in [*output.get("evidence_gaps", []), *model_gaps]
                    if str(item).strip()
                }
            )
            model_risks = parsed.get("material_risks")
            model_risks = model_risks if isinstance(model_risks, list) else []
            output["material_risks"] = sorted(
                {
                    str(item)
                    for item in [*output.get("material_risks", []), *model_risks]
                    if str(item).strip()
                }
            )
            model_dissent = parsed.get("dissent") is True
            if model_dissent:
                output["dissent"] = True
                model_reason = parsed.get("dissent_reason")
                if isinstance(model_reason, str) and model_reason.strip():
                    output["dissent_reason"] = model_reason.strip()
            model_confidence = parsed.get("confidence")
            if isinstance(model_confidence, (int, float)) and not isinstance(model_confidence, bool):
                output["confidence"] = round(
                    max(0.0, min(float(output["confidence"]), float(model_confidence))),
                    2,
                )
            must_hold = bool(
                output["evidence_gaps"]
                or output["material_risks"]
                or output.get("dissent") is True
                or parsed.get("escalation_required") is True
                or parsed.get("recommendation") == "hold_for_evidence_or_risk"
            )
            output["escalation_required"] = must_hold
            output["recommendation"] = (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cto_internal_review"
            )
            if resolved_name == "vp_engineering_agent" and must_hold:
                output["delivery_readiness"] = "evidence_incomplete"
        elif resolved_name in {"product_manager_agent", "design_agent_agent"}:
            deterministic = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)
            for key in PRODUCT_AGENT_CONTROLLED_FIELDS:
                if key in deterministic:
                    output[key] = deterministic[key]
            model_gaps = parsed.get("evidence_gaps")
            model_gaps = model_gaps if isinstance(model_gaps, list) else []
            output["evidence_gaps"] = sorted(
                {
                    str(item)
                    for item in [*output.get("evidence_gaps", []), *model_gaps]
                    if str(item).strip()
                }
            )
            model_risks = parsed.get("material_risks")
            model_risks = model_risks if isinstance(model_risks, list) else []
            output["material_risks"] = sorted(
                {
                    str(item)
                    for item in [*output.get("material_risks", []), *model_risks]
                    if str(item).strip()
                }
            )
            model_dissent = parsed.get("dissent") is True
            if model_dissent:
                output["dissent"] = True
                model_reason = parsed.get("dissent_reason")
                if isinstance(model_reason, str) and model_reason.strip():
                    output["dissent_reason"] = model_reason.strip()
            model_confidence = parsed.get("confidence")
            if isinstance(model_confidence, (int, float)) and not isinstance(model_confidence, bool):
                output["confidence"] = round(
                    max(0.0, min(float(output["confidence"]), float(model_confidence))),
                    2,
                )
            must_hold = bool(
                output["evidence_gaps"]
                or output["material_risks"]
                or output.get("dissent") is True
                or parsed.get("escalation_required") is True
                or parsed.get("recommendation") == "hold_for_evidence_or_risk"
            )
            output["escalation_required"] = must_hold
            output["recommendation"] = (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cpo_internal_review"
            )
            if resolved_name == "product_manager_agent" and must_hold:
                output["product_fit"] = "evidence_incomplete"
            if resolved_name == "design_agent_agent" and must_hold:
                output["design_assessment"] = "evidence_incomplete"
        elif resolved_name in {"security_lead_agent", "threat_analyst_agent"}:
            deterministic = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)
            for key in SECURITY_AGENT_CONTROLLED_FIELDS:
                if key in deterministic:
                    output[key] = deterministic[key]
            model_gaps = parsed.get("evidence_gaps")
            model_gaps = model_gaps if isinstance(model_gaps, list) else []
            output["evidence_gaps"] = sorted(
                {
                    str(item)
                    for item in [*output.get("evidence_gaps", []), *model_gaps]
                    if str(item).strip()
                }
            )
            model_risks = parsed.get("material_risks")
            model_risks = model_risks if isinstance(model_risks, list) else []
            output["material_risks"] = sorted(
                {
                    str(item)
                    for item in [*output.get("material_risks", []), *model_risks]
                    if str(item).strip()
                }
            )
            model_dissent = parsed.get("dissent") is True
            if model_dissent:
                output["dissent"] = True
                model_reason = parsed.get("dissent_reason")
                if isinstance(model_reason, str) and model_reason.strip():
                    output["dissent_reason"] = model_reason.strip()
            model_confidence = parsed.get("confidence")
            if isinstance(model_confidence, (int, float)) and not isinstance(model_confidence, bool):
                output["confidence"] = round(
                    max(0.0, min(float(output["confidence"]), float(model_confidence))),
                    2,
                )
            must_hold = bool(
                output["evidence_gaps"]
                or output["material_risks"]
                or output.get("dissent") is True
                or parsed.get("escalation_required") is True
                or parsed.get("recommendation") == "hold_for_evidence_or_risk"
                or output.get("injection_detected") is True
                or output.get("compromised_agent_detected") is True
                or output.get("data_exfiltration_detected") is True
            )
            output["escalation_required"] = must_hold
            output["recommendation"] = (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_ciso_internal_review"
            )
            if resolved_name == "security_lead_agent" and must_hold:
                output["security_assessment"] = "evidence_incomplete"
            if resolved_name == "threat_analyst_agent" and must_hold:
                output["threat_assessment"] = "evidence_incomplete"
        elif resolved_name in {"soc_lead_agent", "soc_analyst_agent"}:
            deterministic = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)
            for key in SOC_AGENT_CONTROLLED_FIELDS:
                if key in deterministic:
                    output[key] = deterministic[key]
            model_gaps = parsed.get("evidence_gaps")
            model_gaps = model_gaps if isinstance(model_gaps, list) else []
            output["evidence_gaps"] = sorted(
                {
                    str(item)
                    for item in [*output.get("evidence_gaps", []), *model_gaps]
                    if str(item).strip()
                }
            )
            model_risks = parsed.get("material_risks")
            model_risks = model_risks if isinstance(model_risks, list) else []
            output["material_risks"] = sorted(
                {
                    str(item)
                    for item in [*output.get("material_risks", []), *model_risks]
                    if str(item).strip()
                }
            )
            model_dissent = parsed.get("dissent") is True
            if model_dissent:
                output["dissent"] = True
                model_reason = parsed.get("dissent_reason")
                if isinstance(model_reason, str) and model_reason.strip():
                    output["dissent_reason"] = model_reason.strip()
            model_confidence = parsed.get("confidence")
            if isinstance(model_confidence, (int, float)) and not isinstance(model_confidence, bool):
                output["confidence"] = round(
                    max(0.0, min(float(output["confidence"]), float(model_confidence))),
                    2,
                )
            must_hold = bool(
                output["evidence_gaps"]
                or output["material_risks"]
                or output.get("dissent") is True
                or parsed.get("escalation_required") is True
                or parsed.get("recommendation") == "hold_for_evidence_or_risk"
            )
            output["escalation_required"] = must_hold
            output["recommendation"] = (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_ciso_internal_review"
            )
            if resolved_name == "soc_lead_agent" and must_hold:
                output["soc_assessment"] = "evidence_incomplete"
            if resolved_name == "soc_analyst_agent" and must_hold:
                output["anomaly_assessment"] = "evidence_incomplete"
        elif resolved_name in {"creative_director_agent", "marketing_manager_agent"}:
            deterministic = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)
            for key in MARKETING_AGENT_CONTROLLED_FIELDS:
                if key in deterministic:
                    output[key] = deterministic[key]
            model_gaps = parsed.get("evidence_gaps")
            model_gaps = model_gaps if isinstance(model_gaps, list) else []
            output["evidence_gaps"] = sorted(
                {
                    str(item)
                    for item in [*output.get("evidence_gaps", []), *model_gaps]
                    if str(item).strip()
                }
            )
            model_risks = parsed.get("material_risks")
            model_risks = model_risks if isinstance(model_risks, list) else []
            output["material_risks"] = sorted(
                {
                    str(item)
                    for item in [*output.get("material_risks", []), *model_risks]
                    if str(item).strip()
                }
            )
            model_dissent = parsed.get("dissent") is True
            if model_dissent:
                output["dissent"] = True
                model_reason = parsed.get("dissent_reason")
                if isinstance(model_reason, str) and model_reason.strip():
                    output["dissent_reason"] = model_reason.strip()
            model_confidence = parsed.get("confidence")
            if isinstance(model_confidence, (int, float)) and not isinstance(model_confidence, bool):
                output["confidence"] = round(
                    max(0.0, min(float(output["confidence"]), float(model_confidence))),
                    2,
                )
            must_hold = bool(
                output["evidence_gaps"]
                or output["material_risks"]
                or output.get("dissent") is True
                or parsed.get("escalation_required") is True
                or parsed.get("recommendation") == "hold_for_evidence_or_risk"
            )
            output["escalation_required"] = must_hold
            output["recommendation"] = (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cmo_internal_review"
            )
            if resolved_name == "creative_director_agent" and must_hold:
                output["creative_assessment"] = "evidence_incomplete"
            if resolved_name == "marketing_manager_agent" and must_hold:
                output["marketing_fit"] = "evidence_incomplete"
        elif resolved_name in {"financial_analyst_agent", "accounting_lead_agent"}:
            deterministic = DETERMINISTIC_HANDLERS[resolved_name](payload, agent)
            for key in FINANCE_AGENT_CONTROLLED_FIELDS:
                if key in deterministic:
                    output[key] = deterministic[key]
            model_gaps = parsed.get("evidence_gaps")
            model_gaps = model_gaps if isinstance(model_gaps, list) else []
            output["evidence_gaps"] = sorted(
                {
                    str(item)
                    for item in [*output.get("evidence_gaps", []), *model_gaps]
                    if str(item).strip()
                }
            )
            model_risks = parsed.get("material_risks")
            model_risks = model_risks if isinstance(model_risks, list) else []
            output["material_risks"] = sorted(
                {
                    str(item)
                    for item in [*output.get("material_risks", []), *model_risks]
                    if str(item).strip()
                }
            )
            model_dissent = parsed.get("dissent") is True
            if model_dissent:
                output["dissent"] = True
                model_reason = parsed.get("dissent_reason")
                if isinstance(model_reason, str) and model_reason.strip():
                    output["dissent_reason"] = model_reason.strip()
            model_confidence = parsed.get("confidence")
            if isinstance(model_confidence, (int, float)) and not isinstance(model_confidence, bool):
                output["confidence"] = round(
                    max(0.0, min(float(output["confidence"]), float(model_confidence))),
                    2,
                )
            must_hold = bool(
                output["evidence_gaps"]
                or output["material_risks"]
                or output.get("dissent") is True
                or parsed.get("escalation_required") is True
                or parsed.get("recommendation") == "hold_for_evidence_or_risk"
            )
            output["escalation_required"] = must_hold
            output["recommendation"] = (
                "hold_for_evidence_or_risk"
                if must_hold
                else "proceed_to_cfo_internal_review"
            )
            if resolved_name == "financial_analyst_agent" and must_hold:
                output["financial_assessment"] = "evidence_incomplete"
            if resolved_name == "accounting_lead_agent" and must_hold:
                output["accounting_assessment"] = "evidence_incomplete"
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
    "operations_coordination_agent": _llm_agent_handler,
    "business_intelligence_agent": _llm_agent_handler,
    "vp_engineering_agent": _llm_agent_handler,
    "lead_architect_agent": _llm_agent_handler,
    "product_manager_agent": _llm_agent_handler,
    "design_agent_agent": _llm_agent_handler,
    "security_lead_agent": _llm_agent_handler,
    "threat_analyst_agent": _llm_agent_handler,
    "soc_lead_agent": _llm_agent_handler,
    "soc_analyst_agent": _llm_agent_handler,
    "creative_director_agent": _llm_agent_handler,
    "marketing_manager_agent": _llm_agent_handler,
    "financial_analyst_agent": _llm_agent_handler,
    "accounting_lead_agent": _llm_agent_handler,
    "application_readiness_agent": _llm_agent_handler,
    "eligibility_coach": _llm_agent_handler,
    "eligibility_agent": _eligibility_agent,
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
