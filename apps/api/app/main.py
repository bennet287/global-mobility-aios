from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import create_db_and_tables
from app.routers import (
    truth_resolution,
    application_engine,
    sales_engine,
    document_operations,
    document_engine,
    detail_views,
    operations,
    dashboard,
    agent_runs,
    agents,
    crm,
    documents,
    education,
    followups,
    profiles,
    recruitment,
    reviews,
    truth,
    workflows,
)

app = FastAPI(
    title="Global Mobility AIOS API",
    version="0.1.0",
    description="Local-first AI operating system for study abroad, jobs, visa guidance, CRM and workflow automation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()

@app.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "global-mobility-aios-api",
        "environment": settings.app_env,
    }

app.include_router(application_engine.router)
app.include_router(crm.router, prefix="/api/v1", tags=["crm"])
app.include_router(truth.router, prefix="/api/v1", tags=["truth-engine"])
app.include_router(education.router, prefix="/api/v1", tags=["education"])
app.include_router(recruitment.router, prefix="/api/v1", tags=["recruitment"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(document_operations.router, tags=["document-operations"])
app.include_router(sales_engine.router, prefix="", tags=["sales-engine"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(agent_runs.router, prefix="/api/v1", tags=["agent-runs"])
app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
app.include_router(reviews.router, prefix="/api/v1", tags=["human-reviews"])
app.include_router(followups.router, prefix="/api/v1", tags=["follow-ups"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(operations.router, prefix="/api/v1", tags=["operations"])
app.include_router(detail_views.router, tags=["lead-detail"])
app.include_router(document_engine.router, tags=["document-engine"])

app.include_router(truth_resolution.router)

# Document Verification Actions v1.2
from app.routers import document_verification as document_verification_router
app.include_router(document_verification_router.router)

