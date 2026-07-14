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
    profile_version: int = Field(default=1, index=True)
    lifecycle_status: str = Field(default="active", index=True)
    supersedes_profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
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
    education_json: Optional[str] = None
    employment_json: Optional[str] = None
    family_json: Optional[str] = None
    finances_json: Optional[str] = None
    goals_json: Optional[str] = None
    constraints_json: Optional[str] = None
    consent_json: Optional[str] = None
    evidence_json: Optional[str] = None
    completeness_score: float = 0.0
    readiness_stage: str = Field(default="foundation", index=True)
    consent_status: str = Field(default="not_recorded", index=True)
    activated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
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
    jurisdiction_id: Optional[UUID] = Field(default=None, index=True, foreign_key="jurisdictions.id")
    regulatory_authority_id: Optional[UUID] = Field(default=None, index=True, foreign_key="regulatory_authorities.id")
    country: str = Field(index=True)
    domain: str = Field(default="visa", index=True)
    name: str
    url: str = Field(index=True)
    source_type: str = Field(default="official", index=True)
    authority: Optional[str] = None
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Jurisdiction(SQLModel, table=True):
    __tablename__ = "jurisdictions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    code: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    jurisdiction_type: str = Field(default="country", index=True)
    parent_code: Optional[str] = Field(default=None, index=True)
    region: Optional[str] = Field(default=None, index=True)
    active: bool = Field(default=True, index=True)
    metadata_json: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class JurisdictionRegistryRelease(SQLModel, table=True):
    __tablename__ = "jurisdiction_registry_releases"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    version: str = Field(index=True, unique=True)
    source_name: str = "United Nations M49"
    source_url: str
    source_sha256: str = Field(index=True, unique=True)
    source_retrieved_at: datetime = Field(default_factory=now_utc)
    expected_entries: int
    imported_entries: int
    status: str = Field(default="active", index=True)
    released_by: str
    released_at: datetime = Field(default_factory=now_utc, index=True)
    created_at: datetime = Field(default_factory=now_utc)


class JurisdictionRegistryEntry(SQLModel, table=True):
    __tablename__ = "jurisdiction_registry_entries"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    registry_release_id: UUID = Field(index=True, foreign_key="jurisdiction_registry_releases.id")
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    alpha2_code: str = Field(index=True)
    alpha3_code: str = Field(index=True)
    m49_code: str = Field(index=True)
    canonical_name: str = Field(index=True)
    jurisdiction_type: str = Field(default="territory", index=True)
    membership_status: str = Field(default="territory_or_area", index=True)
    parent_code: Optional[str] = Field(default=None, index=True)
    region: Optional[str] = Field(default=None, index=True)
    subregion: Optional[str] = Field(default=None, index=True)
    immigration_rule_status: str = Field(default="unassessed", index=True)
    coverage_required: bool = Field(default=True, index=True)
    payload_sha256: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc)


class JurisdictionImmigrationAssessment(SQLModel, table=True):
    __tablename__ = "jurisdiction_immigration_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    registry_entry_id: UUID = Field(index=True, foreign_key="jurisdiction_registry_entries.id")
    assessment_version: int = Field(default=1, index=True)
    rule_relationship: str = Field(default="unclear", index=True)
    parent_code: Optional[str] = Field(default=None, index=True)
    evidence_url: str
    evidence_title: str
    official_source_id: Optional[UUID] = Field(default=None, index=True, foreign_key="official_sources.id")
    source_snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="source_snapshots.id")
    rationale: str
    status: str = Field(default="pending_review", index=True)
    proposed_by: str
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    supersedes_assessment_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="jurisdiction_immigration_assessments.id",
    )
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class JurisdictionSourceCertification(SQLModel, table=True):
    __tablename__ = "jurisdiction_source_certifications"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    registry_entry_id: UUID = Field(index=True, foreign_key="jurisdiction_registry_entries.id")
    regulatory_authority_id: UUID = Field(index=True, foreign_key="regulatory_authorities.id")
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    certification_version: int = Field(default=1, index=True)
    certification_scope: str = Field(default="primary_immigration", index=True)
    coverage_domains_json: str
    evidence_notes: str
    status: str = Field(default="pending_review", index=True)
    proposed_by: str
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    supersedes_certification_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="jurisdiction_source_certifications.id",
    )
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class RegulatoryAuthority(SQLModel, table=True):
    __tablename__ = "regulatory_authorities"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    name: str = Field(index=True)
    authority_type: str = Field(default="immigration_authority", index=True)
    website_url: Optional[str] = None
    domains_json: Optional[str] = None
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class SourceMonitor(SQLModel, table=True):
    __tablename__ = "source_monitors"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    official_source_id: UUID = Field(index=True, unique=True, foreign_key="official_sources.id")
    schedule_minutes: int = 1440
    fetch_method: str = "http"
    allowed_domains_json: Optional[str] = None
    max_redirects: int = 3
    parser_profile: str = Field(default="generic", index=True)
    parser_config_json: Optional[str] = None
    status: str = Field(default="active", index=True)
    last_checked_at: Optional[datetime] = Field(default=None, index=True)
    next_check_at: Optional[datetime] = Field(default=None, index=True)
    last_http_status: Optional[int] = None
    last_error: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class SourceRetrievalRun(SQLModel, table=True):
    __tablename__ = "source_retrieval_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    monitor_id: UUID = Field(index=True, foreign_key="source_monitors.id")
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    status: str = Field(default="queued", index=True)
    attempt: int = 1
    requested_url: str
    final_url: Optional[str] = None
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    bytes_received: int = 0
    snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="source_snapshots.id")
    regulatory_change_id: Optional[UUID] = Field(default=None, index=True, foreign_key="regulatory_changes.id")
    error_code: Optional[str] = Field(default=None, index=True)
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=now_utc, index=True)
    completed_at: Optional[datetime] = Field(default=None, index=True)

class SourceSnapshot(SQLModel, table=True):
    __tablename__ = "source_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    official_source_id: Optional[UUID] = Field(default=None, index=True, foreign_key="official_sources.id")
    previous_snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="source_snapshots.id")
    url: str = Field(index=True)
    content_hash: Optional[str] = Field(default=None, index=True)
    content_text: Optional[str] = None
    http_status: Optional[int] = None
    retrieval_method: str = "reference"
    parser_version: Optional[str] = None
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
    jurisdiction_id: Optional[UUID] = Field(default=None, index=True, foreign_key="jurisdictions.id")
    regulatory_change_id: Optional[UUID] = Field(default=None, index=True, foreign_key="regulatory_changes.id")
    source_snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="source_snapshots.id")
    supersedes_rule_id: Optional[UUID] = Field(default=None, index=True, foreign_key="verified_rules.id")
    confidence: float = 0.0
    active: bool = Field(default=True, index=True)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    approved_by: Optional[str] = None
    published_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None
    retired_by: Optional[str] = None
    retirement_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class RegulatoryChange(SQLModel, table=True):
    __tablename__ = "regulatory_changes"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    previous_snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="source_snapshots.id")
    current_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    domain: str = Field(default="visa", index=True)
    change_type: str = Field(default="rule_change", index=True)
    title: str
    summary: str
    diff_json: Optional[str] = None
    materiality: str = Field(default="material", index=True)
    status: str = Field(default="pending_review", index=True)
    effective_at: Optional[datetime] = None
    detected_at: datetime = Field(default_factory=now_utc, index=True)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = None

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
    regulatory_change_id: Optional[UUID] = Field(default=None, index=True, foreign_key="regulatory_changes.id")
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


class DocumentSchemaDefinition(SQLModel, table=True):
    __tablename__ = "document_schema_definitions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    schema_key: str = Field(index=True)
    document_type: str = Field(index=True)
    version_number: int = Field(default=1, index=True)
    lifecycle_status: str = Field(default="draft", index=True)
    supersedes_schema_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="document_schema_definitions.id",
    )
    json_schema_json: str
    extraction_rules_json: str
    human_review_required: bool = True
    approved_by: Optional[str] = None
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = None
    created_by: str = "system"
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class DocumentExtractionJob(SQLModel, table=True):
    __tablename__ = "document_extraction_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    document_id: UUID = Field(index=True, foreign_key="documents.id")
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    schema_definition_id: UUID = Field(index=True, foreign_key="document_schema_definitions.id")
    schema_version: int
    status: str = Field(default="queued", index=True)
    engine: str = Field(default="server_tesseract_pypdf_v1", index=True)
    language: str = "eng"
    task_id: Optional[str] = Field(default=None, index=True)
    attempt_count: int = 0
    input_file_hash: Optional[str] = None
    extracted_text: Optional[str] = None
    structured_data_json: Optional[str] = None
    field_confidence_json: Optional[str] = None
    warnings_json: Optional[str] = None
    error_code: Optional[str] = Field(default=None, index=True)
    error_message: Optional[str] = None
    requested_by: str = "system"
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    queued_at: datetime = Field(default_factory=now_utc, index=True)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class DocumentConsistencyAssessment(SQLModel, table=True):
    __tablename__ = "document_consistency_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    extraction_job_id: UUID = Field(index=True, foreign_key="document_extraction_jobs.id")
    document_id: UUID = Field(index=True, foreign_key="documents.id")
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_id: UUID = Field(index=True, foreign_key="profiles.id")
    profile_version: int = Field(index=True)
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    result_status: str = Field(default="insufficient_context", index=True)
    review_status: str = Field(default="pending", index=True)
    match_count: int = 0
    mismatch_count: int = 0
    missing_count: int = 0
    findings_json: str
    source_facts_json: str
    summary: str
    human_review_required: bool = True
    generated_by: str = "system"
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
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


class CoachReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    overridden = "overridden"


class CoachConfidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class CoachReview(SQLModel, table=True):
    __tablename__ = "coach_reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    agent_run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="agent_runs.id")
    coach_agent_name: str = "eligibility_coach"
    target_agent_name: str
    conclusion_valid: bool = False
    missing_facts_json: Optional[str] = None
    source_issues_json: Optional[str] = None
    corrected_summary: Optional[str] = None
    confidence: CoachConfidence = CoachConfidence.medium
    operator_feedback: Optional[str] = None
    operator_override_json: Optional[str] = None
    status: CoachReviewStatus = CoachReviewStatus.pending
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class TrainingCase(SQLModel, table=True):
    __tablename__ = "training_cases"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    title: str
    country: str = Field(index=True)
    profession: str = Field(index=True)
    scenario_json: Optional[str] = None
    expected_outcome_json: Optional[str] = None
    source: str = "synthetic"
    times_run: int = 0
    avg_score: Optional[float] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class EligibilityAssessment(SQLModel, table=True):
    __tablename__ = "eligibility_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    agent_run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="agent_runs.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    profile_version: Optional[int] = None
    target_country: Optional[str] = Field(default=None, index=True)
    domain: str = Field(default="general", index=True)
    overall_score: float = Field(default=0.0)
    confidence: float = Field(default=0.0)
    status: str = Field(default="insufficient_profile", index=True)
    summary: Optional[str] = None
    assessment_json: Optional[str] = None
    risks_json: Optional[str] = None
    required_documents_json: Optional[str] = None
    pathways_json: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Opportunity(SQLModel, table=True):
    __tablename__ = "opportunities"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    title: str
    organization: Optional[str] = None
    country: str = Field(index=True)
    domain: str = Field(default="work", index=True)
    profession_tags_json: Optional[str] = None
    field_tags_json: Optional[str] = None
    required_years_experience: Optional[float] = None
    language_requirement: Optional[str] = None
    salary_eur: Optional[float] = None
    budget_eur: Optional[float] = None
    description: Optional[str] = None
    source: str = "manual"
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class MobilityPathway(SQLModel, table=True):
    __tablename__ = "mobility_pathways"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    pathway_key: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    country: str = Field(index=True)
    domain: str = Field(index=True)
    jurisdiction_id: Optional[UUID] = Field(default=None, index=True, foreign_key="jurisdictions.id")
    description: Optional[str] = None
    catalogue_status: str = Field(default="draft", index=True)
    created_by: str = "system"
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class MobilityPathwayVersion(SQLModel, table=True):
    __tablename__ = "mobility_pathway_versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    pathway_id: UUID = Field(index=True, foreign_key="mobility_pathways.id")
    version_number: int = Field(default=1, index=True)
    lifecycle_status: str = Field(default="draft", index=True)
    supersedes_version_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="mobility_pathway_versions.id",
    )
    official_source_id: Optional[UUID] = Field(default=None, index=True, foreign_key="official_sources.id")
    source_snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="source_snapshots.id")
    verified_rule_ids_json: Optional[str] = None
    eligibility_criteria_json: Optional[str] = None
    required_documents_json: Optional[str] = None
    costs_json: Optional[str] = None
    processing_time_json: Optional[str] = None
    benefits_json: Optional[str] = None
    risks_json: Optional[str] = None
    metadata_json: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    human_review_required: bool = True
    approved_by: Optional[str] = None
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = None
    created_by: str = "system"
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class PathwayComparisonAssessment(SQLModel, table=True):
    __tablename__ = "pathway_comparison_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    profile_version: Optional[int] = None
    primary_pathway_id: Optional[UUID] = Field(default=None, index=True, foreign_key="mobility_pathways.id")
    primary_pathway_version_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="mobility_pathway_versions.id",
    )
    status: str = Field(default="insufficient_pathways", index=True)
    comparison_json: Optional[str] = None
    cost_summary_json: Optional[str] = None
    risk_summary_json: Optional[str] = None
    alternative_pathways_json: Optional[str] = None
    missing_evidence_json: Optional[str] = None
    summary: Optional[str] = None
    human_review_required: bool = True
    generated_by: str = "system"
    created_at: datetime = Field(default_factory=now_utc, index=True)


class MobilityTimeline(SQLModel, table=True):
    __tablename__ = "mobility_timelines"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    profile_version: Optional[int] = None
    comparison_assessment_id: UUID = Field(
        index=True,
        unique=True,
        foreign_key="pathway_comparison_assessments.id",
    )
    primary_pathway_id: UUID = Field(index=True, foreign_key="mobility_pathways.id")
    primary_pathway_version_id: UUID = Field(index=True, foreign_key="mobility_pathway_versions.id")
    title: str
    status: str = Field(default="draft", index=True)
    current_stage_key: Optional[str] = Field(default=None, index=True)
    target_date: Optional[datetime] = None
    schedule_json: Optional[str] = None
    generated_by: str = "system"
    activated_by: Optional[str] = None
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class MobilityTimelineMilestone(SQLModel, table=True):
    __tablename__ = "mobility_timeline_milestones"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    timeline_id: UUID = Field(index=True, foreign_key="mobility_timelines.id")
    stage_order: int = Field(index=True)
    stage_key: str = Field(index=True)
    title: str
    description: Optional[str] = None
    status: str = Field(default="pending", index=True)
    dependencies_json: Optional[str] = None
    required_evidence_json: Optional[str] = None
    owner_role: str = "mobility_operator"
    due_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    blockers_json: Optional[str] = None
    notes: Optional[str] = None
    requires_human_approval: bool = False
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class IntakeSessionStatus(str, Enum):
    started = "started"
    completed = "completed"
    converted = "converted"


class IntakeSession(SQLModel, table=True):
    __tablename__ = "intake_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    session_token: str = Field(index=True, unique=True)
    status: IntakeSessionStatus = IntakeSessionStatus.started
    source: str = "public_intake"
    answers_json: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


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
