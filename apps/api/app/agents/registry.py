AGENT_REGISTRY = {
    "ai_ceo": {
        "role": "Top-level orchestrator that routes work to departments.",
        "guardrail": "Cannot provide visa/job claims directly; must call Truth Engine.",
    },
    "study_abroad_advisor": {
        "role": "Builds education pathways from verified requirements and student profile.",
        "guardrail": "Must cite official university or admissions sources before recommendation is finalized.",
    },
    "visa_truth_agent": {
        "role": "Checks visa and immigration claims against official sources.",
        "guardrail": "Rejects unverifiable claims and requires human review for sensitive advice.",
    },
    "recruitment_specialist": {
        "role": "Matches candidates to overseas job opportunities and employer requirements.",
        "guardrail": "Must not promise jobs, sponsorship, or visas.",
    },
    "document_officer": {
        "role": "Checks document completeness, metadata, and expiry risks.",
        "guardrail": "Does not fabricate missing documents or alter official records.",
    },
    "sales_followup_agent": {
        "role": "Creates follow-up messages and moves leads through CRM pipeline.",
        "guardrail": "Cannot make guaranteed outcome claims.",
    },
}
