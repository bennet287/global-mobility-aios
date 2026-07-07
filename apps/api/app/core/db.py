from collections.abc import Generator

from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)

def register_models() -> None:
    from app.models.domain import (  # noqa: F401
        AgentRun,
        ApplicationRecord,
        DocumentRecord,
        FollowUp,
        HumanReview,
        Lead,
        Profile,
        SourceReference,
        TruthClaim,
        VerificationAudit,
        VisaCheck,
        WorkflowRun,
    )

def create_db_and_tables() -> None:
    register_models()
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
