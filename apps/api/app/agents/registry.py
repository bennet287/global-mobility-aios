from app.services.role_card_loader import AGENT_OUTPUT_SCHEMA, AGENT_ROLE_CARD_MAP


CONTROLLED_AGENT_REGISTRY = {
    "truth_explanation_agent": {
        "version": "v4.0",
        "department": "truth",
        "role": "Explains verified or rejected truth claims in plain operator language.",
        "guardrails": [
            "Cannot create new immigration facts.",
            "Must preserve official-source and confidence boundaries.",
            "Requires human review before client-facing use.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["truth_explanation_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["truth_explanation_agent"],
    },
    "document_checklist_agent": {
        "version": "v4.0",
        "department": "documents",
        "role": "Summarizes missing, received, and verified documents for an operator.",
        "guardrails": [
            "Cannot mark documents verified.",
            "Cannot fabricate or alter document metadata.",
            "Requires operator action for upload, expiry, or verification changes.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["document_checklist_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["document_checklist_agent"],
    },
    "client_drafting_agent": {
        "version": "v4.0",
        "department": "client_communications",
        "role": "Drafts internal client communication text from approved workflow state.",
        "guardrails": [
            "Automatic sending is disabled.",
            "Drafts must remain review-gated.",
            "Cannot promise outcomes, visas, admissions, jobs, or processing times.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["client_drafting_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["client_drafting_agent"],
    },
    "sales_summary_agent": {
        "version": "v4.0",
        "department": "sales",
        "role": "Creates sales-safe lead summaries and next-step suggestions.",
        "guardrails": [
            "Cannot convert a lead.",
            "Cannot bypass truth, readiness, or role guardrails.",
            "Cannot make guaranteed outcome claims.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["sales_summary_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["sales_summary_agent"],
    },
    "operations_coordination_agent": {
        "version": "v13.6",
        "department": "operations",
        "role": "Coordinates internal workflow state, dependencies, ownership, and service-level risks.",
        "guardrails": [
            "Cannot submit to an authority or change a case lifecycle state.",
            "Cannot contact clients, agencies, or external providers.",
            "Can recommend internal sequencing only from recorded workflow facts.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["operations_coordination_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["operations_coordination_agent"],
    },
    "business_intelligence_agent": {
        "version": "v13.6",
        "department": "business_intelligence",
        "role": "Produces evidence-backed internal operating signals and decision questions.",
        "guardrails": [
            "Cannot invent metrics, forecasts, or causal claims.",
            "Cannot change pricing, spending, client, or case state.",
            "Must expose missing evidence and uncertainty.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["business_intelligence_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["business_intelligence_agent"],
    },
    "application_readiness_agent": {
        "version": "v4.0",
        "department": "applications",
        "role": "Explains application readiness blockers and safe next actions.",
        "guardrails": [
            "Cannot draft, approve, or submit applications.",
            "Must respect truth and document readiness gates.",
            "Requires human approval for any application lifecycle action.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["application_readiness_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["application_readiness_agent"],
    },
    "eligibility_coach": {
        "version": "v7.3",
        "department": "coaching",
        "role": "Audits eligibility and pathway conclusions from operational agents for factual grounding and safety.",
        "guardrails": [
            "Cannot change lead data or case status directly.",
            "Must flag missing facts and source issues explicitly.",
            "Cannot approve client-facing output; only provides a review verdict.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["eligibility_coach"],
        "output_schema": AGENT_OUTPUT_SCHEMA["eligibility_coach"],
    },
    "eligibility_agent": {
        "version": "v7.4",
        "department": "eligibility",
        "role": "Produces an internal rule-based eligibility assessment, highlighting pathways, gaps, and required documents.",
        "guardrails": [
            "Cannot promise a specific immigration outcome.",
            "Output is internal and requires human review before client use.",
            "Cannot alter lead data or case status directly.",
        ],
        "role_card": AGENT_ROLE_CARD_MAP["eligibility_agent"],
        "output_schema": AGENT_OUTPUT_SCHEMA["eligibility_agent"],
    },
}

AGENT_ALIASES = {
    "visa_truth_agent": "truth_explanation_agent",
    "document_officer": "document_checklist_agent",
    "sales_followup_agent": "sales_summary_agent",
    "study_abroad_advisor": "application_readiness_agent",
    "recruitment_specialist": "sales_summary_agent",
}

# Backward-compatible public name used by the original /api/v1/agents endpoint.
AGENT_REGISTRY = {
    **CONTROLLED_AGENT_REGISTRY,
    **{
        alias: {
            **CONTROLLED_AGENT_REGISTRY[target],
            "alias_for": target,
        }
        for alias, target in AGENT_ALIASES.items()
    },
}
