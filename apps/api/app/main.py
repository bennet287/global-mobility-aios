from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.auth import auth_middleware
from app.core.config import settings
from app.core.db import create_db_and_tables
from app.core.router_registry import register_routers
from app.core.startup_safety import validate_production_settings
from app.services.document_storage import validate_document_storage_configuration


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail closed before touching the database or serving traffic when production
    # authentication or identity-document storage is insecure/incomplete.
    validate_production_settings()
    validate_document_storage_configuration()
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


register_routers(app)
