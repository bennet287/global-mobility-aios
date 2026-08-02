from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth import auth_middleware
from app.core.config import settings
from app.core.db import create_db_and_tables
from app.routers import (
    agent_chat,
    agent_runs,
    agents,
    agency_submissions,
    application_engine,
    authority_appointments,
    authority_checklists,
    auth,
    automation,
    auto_communications,
    business_advisory,
    client_return,
    client_portal,
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
    documents,
    education,
    ecosystem_portal,
    eligibility,
    external_agencies,
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
    organization_governance,
    partner_api,
    pathways,
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Global Mobility AIOS API",
    version="0.1.0",
    description="Local-first AI operating system for study abroad, jobs, visa guidance, CRM and workflow automation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(auth_middleware)

@app.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "global-mobility-aios-api",
        "environment": settings.app_env,
    }

app.include_router(auth.router)
app.include_router(application_engine.router)
app.include_router(crm.router, prefix="/api/v1", tags=["crm"])
app.include_router(truth.router, prefix="/api/v1", tags=["truth-engine"])
app.include_router(education.router, prefix="/api/v1", tags=["education"])
app.include_router(recruitment.router, prefix="/api/v1", tags=["recruitment"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(document_operations.router, tags=["document-operations"])
app.include_router(document_uploads.router)
app.include_router(sales_engine.router, prefix="", tags=["sales-engine"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(controlled_agents.router, tags=["controlled-agents"])
app.include_router(corporate_mobility.router)
app.include_router(business_advisory.router)
app.include_router(investment_mobility.router)
app.include_router(investment_rule_review.router)
app.include_router(investment_suitability.router)
app.include_router(family_office_mobility.router)
app.include_router(tax_residency.router)
app.include_router(agent_runs.router, prefix="/api/v1", tags=["agent-runs"])
app.include_router(agent_chat.router, tags=["agent-chat"])
app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
app.include_router(reviews.router, prefix="/api/v1", tags=["human-reviews"])
app.include_router(followups.router, prefix="/api/v1", tags=["follow-ups"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(coaching.router)
app.include_router(training_cases.router)
app.include_router(eligibility.router)
app.include_router(client_return.router)
app.include_router(client_portal.router)
app.include_router(ecosystem_portal.router)
app.include_router(partner_api.router)
app.include_router(opportunities.router)
app.include_router(pathways.router)
app.include_router(mobility_timelines.router)
app.include_router(live_intelligence.router)
app.include_router(automation.router)
app.include_router(organization_governance.router)
app.include_router(auto_communications.router)
app.include_router(public_intake.router)
app.include_router(operations.router, prefix="/api/v1", tags=["operations"])
app.include_router(official_sources.router)
app.include_router(detail_views.router, tags=["lead-detail"])
app.include_router(document_engine.router, tags=["document-engine"])
app.include_router(document_ocr.router)
app.include_router(document_intelligence.router)
app.include_router(document_access.router)

app.include_router(truth_resolution.router)

# Document Verification Actions v1.2
from app.routers import document_verification as document_verification_router
app.include_router(document_verification_router.router)

# Application Lifecycle Engine v1.7
from app.routers import application_lifecycle as application_lifecycle_router
app.include_router(application_lifecycle_router.router)

# Application Draft Control v1.8
from app.routers import application_draft_control as application_draft_control_router
app.include_router(application_draft_control_router.router)

# Authority Decision Tracking v1.9
from app.routers import authority_decision as authority_decision_router
app.include_router(authority_decision_router.router)

# Authority Appointment Tracking v12.5
app.include_router(authority_appointments.router)

# Agency Submission Tracking v12.6
app.include_router(agency_submissions.router)

# External Agency Assignment Tracking v12.7
app.include_router(external_agencies.router)

# Authority Submission Checklist v12.8
app.include_router(authority_checklists.router)

# Admin UI Sync v2.0
from app.routers import admin_ui_sync as admin_ui_sync_router
app.include_router(admin_ui_sync_router.router)

# Post-Approval Onboarding v2.4
from app.routers import post_approval_onboarding as post_approval_onboarding_router
app.include_router(post_approval_onboarding_router.router)

# Client Communication Drafting v2.6
from app.routers import client_communications as client_communications_router
app.include_router(client_communications_router.router)

# Audit Log v2.8
from app.routers import audit_logs as audit_logs_router
app.include_router(audit_logs_router.router)
