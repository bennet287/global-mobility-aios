from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

class LeadIntent(str, Enum):
    study_abroad = "study_abroad"
    overseas_job = "overseas_job"
    visa = "visa"
    document = "document"
    unknown = "unknown"

class LeadStatus(str, Enum):
    new = "new"
    qualified = "qualified"
    needs_documents = "needs_documents"
    human_review = "human_review"
    converted = "converted"
    closed = "closed"

class VerificationStatus(str, Enum):
    verified = "VERIFIED"
    rejected = "REJECTED"
    needs_review = "NEEDS_REVIEW"

class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    resolved = "resolved"


class ReviewDecision(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    resolved = "resolved"

class FollowUpStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"

class WorkflowStatus(str, Enum):
    started = "started"
    completed = "completed"
    failed = "failed"
    waiting_for_review = "waiting_for_review"


class AgentRunStatus(str, Enum):
    queued = "queued"
    running = "running"
    pending_review = "pending_review"
    completed = "completed"  # legacy synchronous runs
    approved = "approved"
    rejected = "rejected"
    converted = "converted"
    failed = "failed"

class Lead(SQLModel, table=True):
    __tablename__ = "leads"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    full_name: str
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = None
    source: str = "manual"
    intent: LeadIntent = LeadIntent.unknown
    target_country: Optional[str] = None
    status: LeadStatus = LeadStatus.new
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_type: str = "mobility"
    highest_qualification: Optional[str] = None
    field_of_study: Optional[str] = None
    current_country: Optional[str] = None
    target_country: Optional[str] = None
    desired_role: Optional[str] = None
    years_experience: Optional[float] = None
    budget_eur: Optional[float] = None
    language_scores_json: Optional[str] = None
    skills_json: Optional[str] = None
    missing_fields_json: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class VerificationAudit(SQLModel, table=True):
    __tablename__ = "verification_audits"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    claim: str
    domain: str
    country: Optional[str] = None
    verdict: VerificationStatus
    confidence: float
    official_sources_found: int = 0
    requires_human_review: bool = True
    explanation: str
    created_at: datetime = Field(default_factory=now_utc)

class TruthClaim(SQLModel, table=True):
    __tablename__ = "truth_claims"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    workflow_run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="workflow_runs.id")
    claim: str
    domain: str = "general"
    country: Optional[str] = None
    verdict: VerificationStatus = VerificationStatus.needs_review
    confidence: float = 0.0
    requires_human_review: bool = True
    explanation: str = ""
    red_flags_json: Optional[str] = None
    recommended_next_step: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)

class SourceReference(SQLModel, table=True):
    __tablename__ = "source_references"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    truth_claim_id: Optional[UUID] = Field(default=None, index=True, foreign_key="truth_claims.id")
    source_url: str
    source_type: str = "official"
    title: Optional[str] = None
    country: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=now_utc)

class OfficialSource(SQLModel, table=True):
    __tablename__ = "official_sources"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    country: str = Field(index=True)
    domain: str = Field(default="visa", index=True)
    name: str
    url: str = Field(index=True)
    source_type: str = Field(default="official", index=True)
    authority: Optional[str] = None
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class SourceSnapshot(SQLModel, table=True):
    __tablename__ = "source_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    official_source_id: Optional[UUID] = Field(default=None, index=True, foreign_key="official_sources.id")
    url: str = Field(index=True)
    content_hash: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="referenced", index=True)
    metadata_json: Optional[str] = None
    captured_at: datetime = Field(default_factory=now_utc, index=True)

class SourceCheckRun(SQLModel, table=True):
    __tablename__ = "source_check_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    truth_claim_id: Optional[UUID] = Field(default=None, index=True, foreign_key="truth_claims.id")
    country: Optional[str] = Field(default=None, index=True)
    domain: str = Field(default="general", index=True)
    claim: str
    verdict: str = Field(default="needs_review", index=True)
    confidence: float = 0.0
    evidence_count: int = 0
    matched_sources_json: Optional[str] = None
    corrected_statement: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)

class VerifiedRule(SQLModel, table=True):
    __tablename__ = "verified_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    country: str = Field(index=True)
    domain: str = Field(default="visa", index=True)
    rule_key: str = Field(index=True)
    statement: str
    official_source_id: Optional[UUID] = Field(default=None, index=True, foreign_key="official_sources.id")
    confidence: float = 0.0
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class CountryPolicy(SQLModel, table=True):
    __tablename__ = "country_policies"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    country: str = Field(index=True)
    domain: str = Field(default="visa", index=True)
    policy_json: str = "{}"
    status: str = Field(default="active", index=True)
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class HumanReview(SQLModel, table=True):
    __tablename__ = "human_reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    truth_claim_id: Optional[UUID] = Field(default=None, index=True, foreign_key="truth_claims.id")
    workflow_run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="workflow_runs.id")
    review_type: str = "truth_check"
    status: ReviewStatus = ReviewStatus.pending
    priority: str = "medium"
    reason: str
    reviewer_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class WorkflowRun(SQLModel, table=True):
    __tablename__ = "workflow_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    workflow_name: str
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    status: WorkflowStatus = WorkflowStatus.started
    detected_intent: LeadIntent = LeadIntent.unknown
    route: Optional[str] = None
    input_json: Optional[str] = None
    output_json: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=now_utc)
    completed_at: Optional[datetime] = None

class AgentRun(SQLModel, table=True):
    __tablename__ = "agent_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    workflow_run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="workflow_runs.id")
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    agent_name: str
    task: str
    status: str = Field(default=AgentRunStatus.completed.value, sa_column_kwargs={"index": True})
    input_json: Optional[str] = None
    output_json: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)

class FollowUp(SQLModel, table=True):
    __tablename__ = "follow_ups"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    workflow_run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="workflow_runs.id")
    channel: str = "email"
    status: FollowUpStatus = FollowUpStatus.pending
    due_at: Optional[datetime] = None
    message: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class VisaCheck(SQLModel, table=True):
    __tablename__ = "visa_checks"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    target_country: Optional[str] = None
    visa_type: Optional[str] = None
    eligibility_status: str = "unknown"
    risk_score: float = 0.5
    missing_requirements_json: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)

class DocumentRecord(SQLModel, table=True):
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    document_type: str
    filename: str
    storage_key: Optional[str] = None
    storage_provider: Optional[str] = Field(default=None, index=True)
    file_hash: Optional[str] = Field(default=None, index=True)
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str = "received"
    extracted_metadata_json: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class ApplicationRecord(SQLModel, table=True):
    __tablename__ = "applications"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    domain: str
    target_country: Optional[str] = None
    target_institution_or_employer: Optional[str] = None
    status: str = "draft"
    risk_score: float = 0.5
    created_at: datetime = Field(default_factory=now_utc)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    actor: str = Field(default="system", index=True)
    action: str = Field(index=True)
    entity_type: str = Field(index=True)
    entity_id: Optional[str] = Field(default=None, index=True)
    before_state_json: Optional[str] = None
    after_state_json: Optional[str] = None
    reason: Optional[str] = None
    source: str = Field(default="api", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
