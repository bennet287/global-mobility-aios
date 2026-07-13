from collections.abc import Generator

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings
from app.core.database_url import is_sqlite_url, normalize_database_url, should_auto_create_tables

DATABASE_URL = normalize_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if is_sqlite_url(DATABASE_URL) else {}
engine = create_engine(
    DATABASE_URL,
    echo=settings.database_echo,
    connect_args=connect_args,
    pool_pre_ping=not is_sqlite_url(DATABASE_URL),
)

def register_models() -> None:
    from app.models.domain import (  # noqa: F401
        AgentRun,
        AuditLog,
        ApplicationRecord,
        CoachReview,
        CountryPolicy,
        DocumentRecord,
        EligibilityAssessment,
        FollowUp,
        HumanReview,
        IntakeSession,
        Lead,
        OfficialSource,
        Opportunity,
        Profile,
        SourceCheckRun,
        SourceReference,
        SourceSnapshot,
        TrainingCase,
        TruthClaim,
        VerificationAudit,
        VerifiedRule,
        VisaCheck,
        WorkflowRun,
    )

def create_db_and_tables() -> None:
    register_models()
    if should_auto_create_tables(DATABASE_URL, settings.database_auto_create_tables):
        SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
