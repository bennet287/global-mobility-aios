from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, FastAPI

from app.routers import (
    admin_ui_sync,
    agent_chat,
    agent_runs,
    agents,
    agency_submissions,
    application_draft_control,
    application_engine,
    application_lifecycle,
    audit_logs,
    authority_appointments,
    authority_checklists,
    authority_decision,
    auth,
    automation,
    auto_communications,
    business_advisory,
    client_communications,
    client_portal,
    client_return,
    coaching,
    controlled_agents,
    corporate_mobility,
    crm,
    dashboard,
    detail_views,
    document_access,
    document_engine,
    document_intelligence,
    document_ocr,
    document_operations,
    document_uploads,
    document_verification,
    documents,
    ecosystem_portal,
    education,
    eligibility,
    external_agencies,
    external_validation,
    family_office_mobility,
    followups,
    investment_mobility,
    investment_rule_review,
    investment_suitability,
    live_intelligence,
    mobility_timelines,
    official_sources,
    opportunities,
    operations,
    organization_autonomy_evidence_evaluation_transparency,
    organization_autonomy_promotion_transparency,
    organization_eligibility,
    organization_governance,
    organization_records,
    organization_transparency,
    partner_api,
    pathways,
    post_approval_onboarding,
    profiles,
    public_intake,
    recruitment,
    reviews,
    sales_engine,
    tax_residency,
    training_cases,
    truth,
    truth_resolution,
    workflows,
)


@dataclass(frozen=True)
class RouterSpec:
    """Declarative FastAPI router registration contract."""

    router: APIRouter
    prefix: str | None = None
    tags: tuple[str, ...] = ()
    feature: str = ""

    def include(self, app: FastAPI) -> None:
        kwargs: dict[str, object] = {}
        if self.prefix is not None:
            kwargs["prefix"] = self.prefix
        if self.tags:
            kwargs["tags"] = list(self.tags)
        app.include_router(self.router, **kwargs)


# Keep this ordered: a route can intentionally be registered more than once
# (for example dashboard with and without /api/v1) to preserve compatibility.
ROUTER_SPECS: tuple[RouterSpec, ...] = (
    RouterSpec(auth.router, feature="auth"),
    RouterSpec(application_engine.router, feature="application-engine"),
    RouterSpec(crm.router, prefix="/api/v1", tags=("crm",), feature="crm"),
    RouterSpec(truth.router, prefix="/api/v1", tags=("truth-engine",), feature="truth-engine"),
    RouterSpec(education.router, prefix="/api/v1", tags=("education",), feature="education"),
    RouterSpec(recruitment.router, prefix="/api/v1", tags=("recruitment",), feature="recruitment"),
    RouterSpec(documents.router, prefix="/api/v1", tags=("documents",), feature="documents"),
    RouterSpec(document_operations.router, tags=("document-operations",), feature="document-operations"),
    RouterSpec(document_uploads.router, feature="document-uploads"),
    RouterSpec(sales_engine.router, prefix="", tags=("sales-engine",), feature="sales-engine"),
    RouterSpec(agents.router, prefix="/api/v1", tags=("agents",), feature="agents"),
    RouterSpec(controlled_agents.router, tags=("controlled-agents",), feature="controlled-agents"),
    RouterSpec(corporate_mobility.router, feature="corporate-mobility"),
    RouterSpec(business_advisory.router, feature="business-advisory"),
    RouterSpec(investment_mobility.router, feature="investment-mobility"),
    RouterSpec(investment_rule_review.router, feature="investment-rule-review"),
    RouterSpec(investment_suitability.router, feature="investment-suitability"),
    RouterSpec(family_office_mobility.router, feature="family-office-mobility"),
    RouterSpec(tax_residency.router, feature="tax-residency"),
    RouterSpec(agent_runs.router, prefix="/api/v1", tags=("agent-runs",), feature="agent-runs"),
    RouterSpec(agent_chat.router, tags=("agent-chat",), feature="agent-chat"),
    RouterSpec(profiles.router, prefix="/api/v1", tags=("profiles",), feature="profiles"),
    RouterSpec(reviews.router, prefix="/api/v1", tags=("human-reviews",), feature="reviews"),
    RouterSpec(followups.router, prefix="/api/v1", tags=("follow-ups",), feature="followups"),
    RouterSpec(workflows.router, prefix="/api/v1", tags=("workflows",), feature="workflows"),
    RouterSpec(dashboard.router, prefix="/api/v1", tags=("dashboard",), feature="dashboard-api"),
    RouterSpec(dashboard.router, tags=("dashboard",), feature="dashboard-compat"),
    RouterSpec(coaching.router, feature="coaching"),
    RouterSpec(training_cases.router, feature="training-cases"),
    RouterSpec(eligibility.router, feature="eligibility"),
    RouterSpec(client_return.router, feature="client-return"),
    RouterSpec(client_portal.router, feature="client-portal"),
    RouterSpec(ecosystem_portal.router, feature="ecosystem-portal"),
    RouterSpec(partner_api.router, feature="partner-api"),
    RouterSpec(opportunities.router, feature="opportunities"),
    RouterSpec(pathways.router, feature="pathways"),
    RouterSpec(mobility_timelines.router, feature="mobility-timelines"),
    RouterSpec(live_intelligence.router, feature="live-intelligence"),
    RouterSpec(automation.router, feature="automation"),
    RouterSpec(organization_governance.router, feature="organization-governance"),
    RouterSpec(organization_records.router, feature="organization-records"),
    RouterSpec(organization_eligibility.router, feature="organization-governed-eligibility"),
    RouterSpec(organization_transparency.router, feature="organization-transparency"),
    RouterSpec(
        organization_autonomy_promotion_transparency.router,
        feature="organization-autonomy-promotion-transparency",
    ),
    RouterSpec(
        organization_autonomy_evidence_evaluation_transparency.router,
        feature="organization-autonomy-evidence-evaluation-transparency",
    ),
    RouterSpec(auto_communications.router, feature="auto-communications"),
    RouterSpec(public_intake.router, feature="public-intake"),
    RouterSpec(operations.router, prefix="/api/v1", tags=("operations",), feature="operations"),
    RouterSpec(official_sources.router, feature="official-sources"),
    RouterSpec(detail_views.router, tags=("lead-detail",), feature="detail-views"),
    RouterSpec(document_engine.router, tags=("document-engine",), feature="document-engine"),
    RouterSpec(document_ocr.router, feature="document-ocr"),
    RouterSpec(document_intelligence.router, feature="document-intelligence"),
    RouterSpec(document_access.router, feature="document-access"),
    RouterSpec(truth_resolution.router, feature="truth-resolution"),
    RouterSpec(document_verification.router, feature="document-verification"),
    RouterSpec(application_lifecycle.router, feature="application-lifecycle"),
    RouterSpec(application_draft_control.router, feature="application-draft-control"),
    RouterSpec(authority_decision.router, feature="authority-decision"),
    RouterSpec(authority_appointments.router, feature="authority-appointments"),
    RouterSpec(agency_submissions.router, feature="agency-submissions"),
    RouterSpec(external_agencies.router, feature="external-agencies"),
    RouterSpec(external_validation.router, feature="external-validation"),
    RouterSpec(authority_checklists.router, feature="authority-checklists"),
    RouterSpec(admin_ui_sync.router, feature="admin-ui-sync"),
    RouterSpec(post_approval_onboarding.router, feature="post-approval-onboarding"),
    RouterSpec(client_communications.router, feature="client-communications"),
    RouterSpec(audit_logs.router, feature="audit-logs"),
)


def register_routers(app: FastAPI) -> None:
    for spec in ROUTER_SPECS:
        spec.include(app)
