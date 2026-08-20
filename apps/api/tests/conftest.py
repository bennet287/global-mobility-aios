from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

PROJECT_ROOT = API_ROOT.parents[1] if len(API_ROOT.parents) > 1 else API_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core import db as db_module  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.db import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models.domain import ApplicationRecord, DocumentRecord, Lead, LeadIntent, TruthClaim  # noqa: E402
from app.models.domain import VerificationStatus  # noqa: E402


def _test_engine():
    """Return the default SQLite engine or an explicitly requested isolated DB engine.

    Normal developer and broad regression runs remain fast and hermetic on SQLite.
    The production-proof CI lane sets ``GMAI_TEST_DATABASE_URL`` to an isolated
    PostgreSQL database so the same domain tests exercise real transaction/constraint
    semantics without maintaining a second test framework.
    """

    database_url = os.getenv("GMAI_TEST_DATABASE_URL", "").strip()
    if database_url:
        return create_engine(database_url, pool_pre_ping=True), True
    return (
        create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        ),
        False,
    )


@pytest.fixture()
def db_session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    engine, external_database = _test_engine()
    monkeypatch.setattr(db_module, "engine", engine)
    db_module.register_models()

    # The external database is explicitly test-only. Reset the SQLModel schema around
    # every focused test so no state leaks between concurrency/idempotency scenarios.
    # Migration correctness is verified independently before this fixture is used.
    if external_database:
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            yield session
    finally:
        SQLModel.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def raw_client(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    def override_get_session() -> Generator[Session, None, None]:
        yield db_session

    # Header-role auth is an explicit test/local shortcut; production defaults
    # fail closed and never trust these headers.
    monkeypatch.setattr(settings, "auth_allow_header_role", True)
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def client(raw_client: TestClient) -> Generator[TestClient, None, None]:
    raw_client.headers.update({
        "X-GMAI-Role": "admin",
        "X-GMAI-User": "pytest-admin",
    })
    yield raw_client


def enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def create_lead(
    session: Session,
    *,
    name: str = "Test Lead",
    intent: LeadIntent = LeadIntent.visa,
    target_country: str = "Germany",
) -> Lead:
    lead = Lead(
        full_name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
        intent=intent,
        target_country=target_country,
        source="pytest",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def create_document(session: Session, lead: Lead, *, status: str = "verified", document_type: str = "passport") -> DocumentRecord:
    doc = DocumentRecord(
        lead_id=lead.id,
        document_type=document_type,
        filename=f"{document_type}.pdf",
        status=status,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def create_application(session: Session, lead: Lead, *, status: str = "draft") -> ApplicationRecord:
    app_record = ApplicationRecord(
        lead_id=lead.id,
        domain="visa",
        target_country=lead.target_country,
        status=status,
        risk_score=0.2,
    )
    session.add(app_record)
    session.commit()
    session.refresh(app_record)
    return app_record


def create_truth_claim(
    session: Session,
    lead: Lead,
    *,
    verdict: str = "rejected",
    requires_review: bool = False,
) -> TruthClaim:
    verdict_value = {
        "verified": VerificationStatus.verified,
        "rejected": VerificationStatus.rejected,
        "needs_review": VerificationStatus.needs_review,
    }.get(verdict, verdict)
    claim = TruthClaim(
        lead_id=lead.id,
        claim="Germany student visa is guaranteed without financial proof.",
        domain="visa",
        country=lead.target_country,
        verdict=verdict_value,
        confidence=0.95,
        requires_human_review=requires_review,
        explanation="Pytest high-risk visa claim.",
    )
    session.add(claim)
    session.commit()
    session.refresh(claim)
    return claim
