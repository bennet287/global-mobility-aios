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
    },
}

AGENT_ALIASES = {
    "visa_truth_agent": "truth_explanation_agent",
    "document_officer": "document_checklist_agent",
    "sales_followup_agent": "sales_summary_agent",
    "study_abroad_advisor": "application_readiness_agent",
    "ai_ceo": "application_readiness_agent",
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
