from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, Column, Enum as SQLAlchemyEnum, ForeignKeyConstraint, Numeric, UniqueConstraint
from sqlalchemy import Index, text
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


class OrganizationActorType(str, Enum):
    human = "human"
    agent = "agent"
    worker = "worker"
    system = "system"
    external_human = "external_human"


class OrganizationActivityClass(str, Enum):
    domain = "domain"
    work = "work"
    decision = "decision"
    blocker = "blocker"
    human_action = "human_action"
    contribution = "contribution"
    operational = "operational"


class OrganizationContributionRecordKind(str, Enum):
    outcome = "outcome"
    supersession = "supersession"
    retraction = "retraction"


class OrganizationContributionVerificationMethod(str, Enum):
    domain_transition = "domain_transition"
    human_attestation = "human_attestation"
    deterministic_gate = "deterministic_gate"


class OrganizationContributionImpactKind(str, Enum):
    state_change = "state_change"
    risk_reduction = "risk_reduction"
    milestone = "milestone"
    delivery = "delivery"
    validation = "validation"
    knowledge = "knowledge"


class OrganizationWorkPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class OrganizationDependencyType(str, Enum):
    blocks = "blocks"
    requires = "requires"
    informs = "informs"


class OrganizationDependencyStatus(str, Enum):
    active = "active"
    satisfied = "satisfied"
    waived = "waived"
    superseded = "superseded"


class OrganizationDecisionType(str, Enum):
    operational = "operational"
    policy = "policy"
    risk = "risk"
    exception = "exception"
    board_reserved = "board_reserved"


class OrganizationBlockerType(str, Enum):
    evidence = "evidence"
    dependency = "dependency"
    authority = "authority"
    human_input = "human_input"
    external = "external"
    safety = "safety"
    technical = "technical"


class OrganizationBlockerStatus(str, Enum):
    open = "open"
    mitigated = "mitigated"
    resolved = "resolved"
    waived = "waived"
    superseded = "superseded"


class OrganizationHumanActionRequestType(str, Enum):
    review = "review"
    decision = "decision"
    attestation = "attestation"
    acknowledgement = "acknowledgement"
    provide_information = "provide_information"
    approval = "approval"
    exception = "exception"


class OrganizationHumanActionRequestStatus(str, Enum):
    required = "required"
    acknowledged = "acknowledged"
    in_progress = "in_progress"
    completed = "completed"
    declined = "declined"
    cancelled = "cancelled"
    expired = "expired"


class OrganizationHumanActionType(str, Enum):
    reviewed = "reviewed"
    approved = "approved"
    rejected = "rejected"
    requested_changes = "requested_changes"
    attested = "attested"
    acknowledged = "acknowledged"
    assigned = "assigned"
    reassigned = "reassigned"
    resolved = "resolved"
    declined = "declined"
    cancelled = "cancelled"


class OrganizationReferenceRole(str, Enum):
    authoritative_outcome = "authoritative_outcome"
    affected_subject = "affected_subject"
    evidence = "evidence"
    caused_by = "caused_by"
    supports = "supports"
    contradicts = "contradicts"


class OrganizationReferenceTargetType(str, Enum):
    lead = "lead"
    profile = "profile"
    application = "application"
    corporate_mobility_case = "corporate_mobility_case"
    pathway_comparison_assessment = "pathway_comparison_assessment"
    eligibility_assessment = "eligibility_assessment"
    source_snapshot = "source_snapshot"
    official_source = "official_source"
    external_validation_run = "external_validation_run"
    external_validation_finding = "external_validation_finding"
    agent_run = "agent_run"
    automation_event = "automation_event"
    audit_log = "audit_log"
    regulatory_change = "regulatory_change"
    verified_rule = "verified_rule"
    mobility_pathway_version = "mobility_pathway_version"
    agency_submission = "agency_submission"
    corporate_compliance_event = "corporate_compliance_event"
    mobility_timeline_milestone = "mobility_timeline_milestone"


def _string_enum(enum_type: type[Enum]) -> SQLAlchemyEnum:
    return SQLAlchemyEnum(
        enum_type,
        native_enum=False,
        create_constraint=False,
        values_callable=lambda members: [member.value for member in members],
    )

class Lead(SQLModel, table=True):
    __tablename__ = "leads"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    full_name: str
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = None
    source: str = "manual"
    intent: LeadIntent = LeadIntent.unknown
    target_country: Optional[str] = None
    nationality: Optional[str] = None
    current_country: Optional[str] = None
    occupation_title: Optional[str] = None
    years_experience: Optional[float] = None
    job_offer_status: Optional[str] = None
    qualification_recognition: Optional[str] = None
    german_level: Optional[str] = None
    employment_province: Optional[str] = None
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

    __table_args__ = (
        Index(
            "uq_jsc_primary_scope_version",
            "jurisdiction_id",
            "certification_scope",
            "certification_version",
            unique=True,
            sqlite_where=text(
                "certification_scope = 'primary_immigration'"
            ),
            postgresql_where=text(
                "certification_scope = 'primary_immigration'"
            ),
        ),
        Index(
            "uq_jsc_supplemental_source_scope_version",
            "jurisdiction_id",
            "official_source_id",
            "certification_scope",
            "certification_version",
            unique=True,
            sqlite_where=text(
                "certification_scope <> 'primary_immigration'"
            ),
            postgresql_where=text(
                "certification_scope <> 'primary_immigration'"
            ),
        ),
    )

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


class JurisdictionCoverageEvidenceBatch(SQLModel, table=True):
    __tablename__ = "jurisdiction_coverage_evidence_batches"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    registry_release_id: UUID = Field(index=True, foreign_key="jurisdiction_registry_releases.id")
    batch_key: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    notes: str
    item_count: int = 0
    immigration_assessment_count: int = 0
    source_certification_count: int = 0
    source_onboarding_count: int = 0
    status: str = Field(default="submitted_for_review", index=True)
    submitted_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class JurisdictionCoverageEvidenceBatchItem(SQLModel, table=True):
    __tablename__ = "jurisdiction_coverage_evidence_batch_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    batch_id: UUID = Field(index=True, foreign_key="jurisdiction_coverage_evidence_batches.id")
    row_number: int = Field(index=True)
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    registry_entry_id: UUID = Field(index=True, foreign_key="jurisdiction_registry_entries.id")
    alpha2_code: str = Field(index=True)
    immigration_assessment_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="jurisdiction_immigration_assessments.id",
    )
    source_certification_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="jurisdiction_source_certifications.id",
    )
    regulatory_authority_id: Optional[UUID] = Field(
        default=None,
        foreign_key="regulatory_authorities.id",
    )
    official_source_id: Optional[UUID] = Field(
        default=None,
        foreign_key="official_sources.id",
    )
    source_monitor_id: Optional[UUID] = Field(
        default=None,
        foreign_key="source_monitors.id",
    )
    payload_sha256: str = Field(index=True)
    payload_json: str
    created_at: datetime = Field(default_factory=now_utc, index=True)


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

class ShortageOccupationEntry(SQLModel, table=True):
    __tablename__ = "shortage_occupation_entries"
    __table_args__ = (
        UniqueConstraint(
            "source_snapshot_id",
            "year",
            "scope",
            "source_ordinal",
            name="uq_shortage_occupation_snapshot_scope_ordinal",
        ),
        UniqueConstraint(
            "entry_sha256",
            name="uq_shortage_occupation_entry_sha256",
        ),
        CheckConstraint(
            "scope IN ('national', 'regional')",
            name="ck_shortage_occupation_scope",
        ),
        CheckConstraint(
            "year BETWEEN 2000 AND 2200",
            name="ck_shortage_occupation_year",
        ),
        CheckConstraint(
            "source_ordinal > 0",
            name="ck_shortage_occupation_source_ordinal",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    year: int = Field(index=True)
    scope: str = Field(index=True)
    source_ordinal: int = Field(index=True)
    occupation_group: str
    normalized_occupation_group: str = Field(index=True)
    occupation_aliases_json: str = "[]"
    province_codes_json: str = "[]"
    province_names_json: str = "[]"
    extraction_version: str
    entry_sha256: str = Field(index=True)
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=now_utc)


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


class InitialRuleAssertion(SQLModel, table=True):
    __tablename__ = "initial_rule_assertions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assertion_sha256: str = Field(index=True, unique=True)
    coverage_batch_item_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="jurisdiction_coverage_evidence_batch_items.id",
    )
    jurisdiction_id: UUID = Field(index=True, foreign_key="jurisdictions.id")
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    domain: str = Field(default="visa", index=True)
    title: str
    rule_key: str = Field(index=True)
    statement: str
    rationale: str
    evidence_excerpt: str
    confidence: float = 0.0
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    status: str = Field(default="pending_review", index=True)
    proposed_by: str = Field(index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    published_rule_id: Optional[UUID] = Field(default=None, index=True)
    published_by: Optional[str] = Field(default=None, index=True)
    published_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)

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
    initial_rule_assertion_id: Optional[UUID] = Field(default=None, index=True, foreign_key="initial_rule_assertions.id")
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


class RegulatoryClassificationProposal(SQLModel, table=True):
    __tablename__ = "regulatory_classification_proposals"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    regulatory_change_id: UUID = Field(index=True, foreign_key="regulatory_changes.id")
    previous_snapshot_id: Optional[UUID] = Field(default=None, index=True, foreign_key="source_snapshots.id")
    current_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    proposed_change_type: str = Field(index=True)
    proposed_materiality: str = Field(index=True)
    proposed_summary: str
    rationale: str
    evidence_json: str = "[]"
    confidence: float = 0.0
    method: str = Field(default="deterministic", index=True)
    provider: Optional[str] = Field(default=None, index=True)
    model: Optional[str] = None
    prompt_version: str = "regulatory-classifier-v1"
    model_metadata_json: Optional[str] = None
    fallback_reason: Optional[str] = None
    status: str = Field(default="pending_review", index=True)
    created_by: str = Field(default="source-monitor", index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class RegulatoryKnowledgeNode(SQLModel, table=True):
    __tablename__ = "regulatory_knowledge_nodes"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    node_key: str = Field(index=True, unique=True)
    node_type: str = Field(index=True)
    label: str
    properties_json: str = "{}"
    active: bool = Field(default=True, index=True)
    created_from_verified_rule_id: UUID = Field(index=True, foreign_key="verified_rules.id")
    last_verified_rule_id: UUID = Field(index=True, foreign_key="verified_rules.id")
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class RegulatoryKnowledgeEdge(SQLModel, table=True):
    __tablename__ = "regulatory_knowledge_edges"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    edge_key: str = Field(index=True, unique=True)
    source_node_id: UUID = Field(index=True, foreign_key="regulatory_knowledge_nodes.id")
    target_node_id: UUID = Field(index=True, foreign_key="regulatory_knowledge_nodes.id")
    relation_type: str = Field(index=True)
    verified_rule_id: UUID = Field(index=True, foreign_key="verified_rules.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    regulatory_change_id: Optional[UUID] = Field(default=None, index=True, foreign_key="regulatory_changes.id")
    initial_rule_assertion_id: Optional[UUID] = Field(default=None, index=True, foreign_key="initial_rule_assertions.id")
    projection_version: str = Field(default="regulatory-graph-v1", index=True)
    active: bool = Field(default=True, index=True)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    retired_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class PathwayRegulatoryImpact(SQLModel, table=True):
    __tablename__ = "pathway_regulatory_impacts"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    impact_key: str = Field(index=True, unique=True)
    pathway_id: UUID = Field(index=True, foreign_key="mobility_pathways.id")
    pathway_version_id: UUID = Field(index=True, foreign_key="mobility_pathway_versions.id")
    verified_rule_id: UUID = Field(index=True, foreign_key="verified_rules.id")
    superseded_rule_id: Optional[UUID] = Field(default=None, index=True, foreign_key="verified_rules.id")
    regulatory_change_id: UUID = Field(index=True, foreign_key="regulatory_changes.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    graph_rule_node_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="regulatory_knowledge_nodes.id",
    )
    graph_projection_version: str = Field(default="regulatory-graph-v1", index=True)
    impact_type: str = Field(index=True)
    status: str = Field(default="pending_review", index=True)
    materiality: str = Field(default="material", index=True)
    match_basis_json: str = "[]"
    impact_context_json: str = "{}"
    client_assessment_count_at_detection: int = 0
    timeline_count_at_detection: int = 0
    human_review_required: bool = True
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    replacement_pathway_version_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="mobility_pathway_versions.id",
    )
    event_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
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

class DocumentExpiryReminderTask(SQLModel, table=True):
    __tablename__ = "document_expiry_reminder_tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    reminder_key: str = Field(index=True, unique=True)
    document_id: UUID = Field(index=True, foreign_key="documents.id")
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    document_type: str = Field(index=True)
    filename: str
    expiry_date: datetime = Field(index=True)
    reminder_type: str = Field(index=True)
    threshold_days: int
    due_at: datetime = Field(index=True)
    status: str = Field(default="pending", index=True)
    priority: str = Field(default="normal", index=True)
    source: str = Field(default="document_record_expiry_date", index=True)
    human_review_required: bool = True
    external_delivery_status: str = Field(default="not_sent", index=True)
    generated_by: str = "document-expiry-monitor"
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    superseded_by_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="document_expiry_reminder_tasks.id",
    )
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class DocumentRequirementAssessment(SQLModel, table=True):
    __tablename__ = "document_requirement_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assessment_key: str = Field(index=True, unique=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    pathway_id: Optional[UUID] = Field(default=None, index=True, foreign_key="mobility_pathways.id")
    pathway_version_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="mobility_pathway_versions.id",
    )
    eligibility_assessment_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="eligibility_assessments.id",
    )
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    profile_version: Optional[int] = Field(default=None, index=True)
    requirement_source: str = Field(index=True)
    result_status: str = Field(default="insufficient_context", index=True)
    review_status: str = Field(default="pending", index=True)
    required_count: int = 0
    satisfied_count: int = 0
    missing_count: int = 0
    inconsistency_count: int = 0
    requirements_json: str
    findings_json: str
    source_snapshot_json: str
    document_snapshot_json: str
    summary: str
    human_review_required: bool = True
    generated_by: str = "system"
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class DocumentFraudRiskAssessment(SQLModel, table=True):
    __tablename__ = "document_fraud_risk_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assessment_key: str = Field(index=True, unique=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    profile_version: Optional[int] = Field(default=None, index=True)
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    result_status: str = Field(default="no_indicators", index=True)
    review_status: str = Field(default="not_required", index=True)
    risk_band: str = Field(default="none", index=True)
    indicator_count: int = 0
    high_indicator_count: int = 0
    warning_indicator_count: int = 0
    indicators_json: str
    source_snapshot_json: str
    summary: str
    human_review_required: bool = False
    automated_fraud_determination: bool = False
    adverse_action_taken: bool = False
    generated_by: str = "system"
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class DocumentAccessGrant(SQLModel, table=True):
    __tablename__ = "document_access_grants"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    token_hash: str = Field(index=True, unique=True)
    document_id: UUID = Field(index=True, foreign_key="documents.id")
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    issued_to: str = Field(index=True)
    issued_role: str = Field(index=True)
    purpose: str = Field(index=True)
    status: str = Field(default="active", index=True)
    expires_at: datetime = Field(index=True)
    max_uses: int = 1
    use_count: int = 0
    document_file_hash: str
    document_file_size_bytes: int
    storage_provider: str = Field(index=True)
    storage_key_hash: str
    mime_type: Optional[str] = None
    filename: str
    created_by: str = Field(index=True)
    last_accessed_by: Optional[str] = Field(default=None, index=True)
    last_accessed_at: Optional[datetime] = Field(default=None, index=True)
    revoked_by: Optional[str] = Field(default=None, index=True)
    revoked_at: Optional[datetime] = Field(default=None, index=True)
    revocation_reason: Optional[str] = None
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


class AuthorityAppointment(SQLModel, table=True):
    __tablename__ = "authority_appointments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    application_id: UUID = Field(index=True, foreign_key="applications.id")
    appointment_type: str = Field(index=True)
    authority_name: str
    location: Optional[str] = None
    scheduled_at: datetime = Field(index=True)
    timezone: Optional[str] = Field(default="UTC")
    status: str = Field(default="scheduled", index=True)
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class AgencySubmission(SQLModel, table=True):
    __tablename__ = "agency_submissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    application_id: UUID = Field(index=True, foreign_key="applications.id")
    authority_name: str
    submission_channel: str = Field(index=True)
    submitted_at: datetime = Field(index=True)
    reference_number: Optional[str] = None
    tracking_url: Optional[str] = None
    status: str = Field(default="submitted", index=True)
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ExternalAgency(SQLModel, table=True):
    __tablename__ = "external_agencies"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    country: Optional[str] = None
    city: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    status: str = Field(default="active", index=True)
    sla_due_hours: Optional[int] = Field(default=72, index=True)
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ExternalAgencyAssignment(SQLModel, table=True):
    __tablename__ = "external_agency_assignments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    application_id: UUID = Field(index=True, foreign_key="applications.id")
    external_agency_id: UUID = Field(index=True, foreign_key="external_agencies.id")
    status: str = Field(default="assigned", index=True)
    agency_reference_number: Optional[str] = None
    handoff_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sla_due_at: Optional[datetime] = None
    sla_status: str = Field(default="on_track", index=True)
    sla_breached_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class AuthorityChecklistTemplate(SQLModel, table=True):
    __tablename__ = "authority_checklist_templates"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    authority_name: str = Field(index=True)
    country: Optional[str] = None
    item_key: str = Field(index=True)
    item_label: str
    category: str = Field(index=True)
    is_required: bool = True
    sort_order: int = 0
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ApplicationAuthorityChecklistItem(SQLModel, table=True):
    __tablename__ = "application_authority_checklist_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    application_id: UUID = Field(index=True, foreign_key="applications.id")
    template_item_id: Optional[UUID] = Field(default=None, index=True, foreign_key="authority_checklist_templates.id")
    authority_name: str = Field(index=True)
    item_key: str = Field(index=True)
    item_label: str
    category: str = Field(index=True)
    is_required: bool = True
    status: str = Field(default="pending", index=True)
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


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


class MobilityPathwayVersionEvidence(SQLModel, table=True):
    __tablename__ = "mobility_pathway_version_evidence"
    __table_args__ = (
        UniqueConstraint(
            "pathway_version_id",
            "evidence_role",
            "official_source_id",
            "source_snapshot_id",
            name="uq_pathway_version_evidence_identity",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    pathway_version_id: UUID = Field(
        index=True,
        foreign_key="mobility_pathway_versions.id",
    )
    evidence_role: str = Field(default="supporting", index=True)
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    required_for_publication: bool = Field(default=True, index=True)
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=now_utc)


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


class ReassessmentAcceptance(SQLModel, table=True):
    __tablename__ = "reassessment_acceptances"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    acceptance_key: str = Field(index=True, unique=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    baseline_assessment_id: UUID = Field(index=True, foreign_key="pathway_comparison_assessments.id")
    accepted_profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    accepted_profile_version: Optional[int] = Field(default=None, index=True)
    regulatory_impact_ids_json: str = "[]"
    accepted_pathway_version_ids_json: str = "[]"
    explicit_user_acceptance: bool = True
    user_attestation: str
    notes: str
    status: str = Field(default="accepted", index=True)
    recorded_by: str = Field(index=True)
    accepted_at: datetime = Field(default_factory=now_utc, index=True)
    consumed_at: Optional[datetime] = Field(default=None, index=True)
    generated_assessment_id: Optional[UUID] = Field(default=None, index=True, foreign_key="pathway_comparison_assessments.id")
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CountryRankingAssessment(SQLModel, table=True):
    __tablename__ = "country_ranking_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    ranking_key: str = Field(index=True, unique=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    profile_version: Optional[int] = Field(default=None, index=True)
    status: str = Field(default="reviewed_catalogue_only", index=True)
    input_sha256: str = Field(index=True)
    catalogue_version_ids_json: str = "[]"
    scope_json: str = "{}"
    ranking_json: str = "[]"
    explicit_user_acceptance: bool = True
    user_attestation: str
    notes: str
    global_coverage_claim_ready: bool = Field(default=False, index=True)
    human_review_required: bool = True
    generated_by: str = Field(index=True)
    summary: str
    created_at: datetime = Field(default_factory=now_utc, index=True)


class MobilityScenario(SQLModel, table=True):
    __tablename__ = "mobility_scenarios"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    scenario_key: str = Field(index=True, unique=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    profile_version: Optional[int] = Field(default=None, index=True)
    baseline_timeline_id: Optional[UUID] = Field(default=None, index=True, foreign_key="mobility_timelines.id")
    scenario_version: int = Field(default=1, index=True)
    supersedes_scenario_id: Optional[UUID] = Field(default=None, index=True, foreign_key="mobility_scenarios.id")
    title: str
    status: str = Field(default="human_confirmed", index=True)
    start_date: datetime = Field(index=True)
    input_sha256: str = Field(index=True)
    countries_json: str = "[]"
    pathway_version_ids_json: str = "[]"
    verified_rule_ids_json: str = "[]"
    regulatory_impact_ids_json: str = "[]"
    explicit_user_acceptance: bool = True
    user_attestation: str
    review_notes: str
    human_confirmation_required: bool = True
    original_scenario_preserved: bool = True
    global_coverage_claim_ready: bool = Field(default=False, index=True)
    warning: str
    reviewed_by: str = Field(index=True)
    reviewed_at: datetime = Field(default_factory=now_utc, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class MobilityScenarioStage(SQLModel, table=True):
    __tablename__ = "mobility_scenario_stages"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    scenario_id: UUID = Field(index=True, foreign_key="mobility_scenarios.id")
    stage_order: int = Field(index=True)
    stage_type: str = Field(index=True)
    title: str
    country: str = Field(index=True)
    domain: str = Field(index=True)
    pathway_id: UUID = Field(index=True, foreign_key="mobility_pathways.id")
    pathway_version_id: UUID = Field(index=True, foreign_key="mobility_pathway_versions.id")
    planned_start: datetime = Field(index=True)
    planned_end: datetime = Field(index=True)
    duration_months: int
    gap_months_before: int = 0
    dependencies_json: str = "[]"
    verified_rule_ids_json: str = "[]"
    source_snapshot_ids_json: str = "[]"
    timing_basis_json: str = "{}"
    uncertainty_json: str = "{}"
    human_confirmation_required: bool = True
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
    submission_key: Optional[str] = Field(default=None, index=True, unique=True)
    submission_fingerprint: Optional[str] = None
    status: IntakeSessionStatus = IntakeSessionStatus.started
    source: str = "public_intake"
    answers_json: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class ClientPortalAccessGrant(SQLModel, table=True):
    __tablename__ = "client_portal_access_grants"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    token_hash: str = Field(index=True, unique=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    label: str = "Client portal"
    status: str = Field(default="active", index=True)
    expires_at: datetime = Field(index=True)
    created_by: str = Field(index=True)
    access_count: int = 0
    last_accessed_at: Optional[datetime] = Field(default=None, index=True)
    device_fingerprint: Optional[str] = Field(default=None, index=True)
    device_label: Optional[str] = None
    user_agent: Optional[str] = None
    revoked_by: Optional[str] = Field(default=None, index=True)
    revoked_at: Optional[datetime] = Field(default=None, index=True)
    revocation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class EcosystemPortalAccessGrant(SQLModel, table=True):
    __tablename__ = "ecosystem_portal_access_grants"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    token_hash: str = Field(index=True, unique=True)
    corporate_account_id: UUID = Field(index=True, foreign_key="corporate_accounts.id")
    audience_type: str = Field(index=True)
    label: str
    status: str = Field(default="active", index=True)
    expires_at: datetime = Field(index=True)
    created_by: str = Field(index=True)
    access_count: int = 0
    last_accessed_at: Optional[datetime] = Field(default=None, index=True)
    revoked_by: Optional[str] = Field(default=None, index=True)
    revoked_at: Optional[datetime] = Field(default=None, index=True)
    revocation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class PartnerApiCredential(SQLModel, table=True):
    __tablename__ = "partner_api_credentials"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    key_hash: str = Field(index=True, unique=True)
    key_prefix: str = Field(index=True)
    corporate_account_id: UUID = Field(index=True, foreign_key="corporate_accounts.id")
    label: str
    scopes: str
    status: str = Field(default="active", index=True)
    expires_at: datetime = Field(index=True)
    created_by: str = Field(index=True)
    access_count: int = 0
    last_used_at: Optional[datetime] = Field(default=None, index=True)
    revoked_by: Optional[str] = Field(default=None, index=True)
    revoked_at: Optional[datetime] = Field(default=None, index=True)
    revocation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class AutomationRule(SQLModel, table=True):
    __tablename__ = "automation_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_account_id: UUID = Field(index=True, foreign_key="corporate_accounts.id")
    name: str
    event_type: str = Field(index=True)
    channels: str
    destinations_json: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    requires_human_approval: bool = True
    status: str = Field(default="active", index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class AutomationEvent(SQLModel, table=True):
    __tablename__ = "automation_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    idempotency_key: str = Field(index=True, unique=True)
    corporate_account_id: UUID = Field(index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(
        default=None, index=True, foreign_key="corporate_mobility_cases.id"
    )
    event_type: str = Field(index=True)
    entity_type: str = Field(index=True)
    entity_id: str = Field(index=True)
    source: str = Field(default="domain", index=True)
    payload_json: str
    status: str = Field(default="recorded", index=True)
    occurred_at: datetime = Field(default_factory=now_utc, index=True)
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class AutomationDelivery(SQLModel, table=True):
    __tablename__ = "automation_deliveries"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    automation_event_id: UUID = Field(index=True, foreign_key="automation_events.id")
    automation_rule_id: UUID = Field(index=True, foreign_key="automation_rules.id")
    connector_config_id: Optional[UUID] = Field(default=None, index=True, foreign_key="automation_connector_configs.id")
    channel: str = Field(index=True)
    destination: Optional[str] = None
    subject: Optional[str] = None
    payload_json: str
    status: str = Field(default="pending_review", index=True)
    requires_human_approval: bool = True
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_reason: Optional[str] = None
    dispatched_by: Optional[str] = Field(default=None, index=True)
    dispatched_at: Optional[datetime] = Field(default=None, index=True)
    provider_message_id: Optional[str] = Field(default=None, index=True)
    attempt_count: int = 0
    next_attempt_at: Optional[datetime] = Field(default=None, index=True)
    last_error: Optional[str] = None
    reconciled: bool = Field(default=False, index=True)
    reconciled_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class AutomationConnectorConfig(SQLModel, table=True):
    __tablename__ = "automation_connector_configs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_account_id: UUID = Field(index=True, foreign_key="corporate_accounts.id")
    channel: str = Field(index=True)
    provider_type: str = Field(index=True)
    credentials_json: str
    from_address: Optional[str] = Field(default=None, index=True)
    sender_label: Optional[str] = None
    status: str = Field(default="active", index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateAccount(SQLModel, table=True):
    __tablename__ = "corporate_accounts"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    legal_name: str = Field(index=True)
    display_name: Optional[str] = None
    account_status: str = Field(default="active", index=True)
    primary_country: str = Field(index=True)
    registration_number: Optional[str] = Field(default=None, index=True)
    contact_name: Optional[str] = None
    contact_email: Optional[str] = Field(default=None, index=True)
    compliance_owner: Optional[str] = None
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateMobilityCase(SQLModel, table=True):
    __tablename__ = "corporate_mobility_cases"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_account_id: UUID = Field(index=True, foreign_key="corporate_accounts.id")
    employee_lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    case_reference: str = Field(index=True, unique=True)
    case_type: str = Field(default="employee_relocation", index=True)
    status: str = Field(default="draft", index=True)
    origin_country: Optional[str] = Field(default=None, index=True)
    destination_country: str = Field(index=True)
    sponsor_name: Optional[str] = None
    target_start_date: Optional[datetime] = Field(default=None, index=True)
    compliance_due_date: Optional[datetime] = Field(default=None, index=True)
    human_review_required: bool = True
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateSponsorEntity(SQLModel, table=True):
    __tablename__ = "corporate_sponsor_entities"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_account_id: UUID = Field(index=True, foreign_key="corporate_accounts.id")
    legal_name: str = Field(index=True)
    sponsor_type: str = Field(index=True)
    country: str = Field(index=True)
    registration_number: Optional[str] = Field(default=None, index=True)
    contact_name: Optional[str] = None
    contact_email: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="active", index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateCaseSponsorAssignment(SQLModel, table=True):
    __tablename__ = "corporate_case_sponsor_assignments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_mobility_case_id: UUID = Field(index=True, foreign_key="corporate_mobility_cases.id")
    sponsor_entity_id: UUID = Field(index=True, foreign_key="corporate_sponsor_entities.id")
    status: str = Field(default="active", index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateCaseDependant(SQLModel, table=True):
    __tablename__ = "corporate_case_dependants"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_mobility_case_id: UUID = Field(index=True, foreign_key="corporate_mobility_cases.id")
    dependant_lead_id: UUID = Field(index=True, foreign_key="leads.id")
    relationship_to_employee: str = Field(index=True)
    sponsorship_required: bool = False
    status: str = Field(default="active", index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateComplianceEvent(SQLModel, table=True):
    __tablename__ = "corporate_compliance_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_mobility_case_id: UUID = Field(index=True, foreign_key="corporate_mobility_cases.id")
    event_type: str = Field(index=True)
    title: str
    due_at: datetime = Field(index=True)
    status: str = Field(default="open", index=True)
    evidence_required: bool = True
    human_review_required: bool = True
    completion_notes: Optional[str] = None
    completed_by: Optional[str] = Field(default=None, index=True)
    completed_at: Optional[datetime] = Field(default=None, index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateRelocationTask(SQLModel, table=True):
    __tablename__ = "corporate_relocation_tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_mobility_case_id: UUID = Field(index=True, foreign_key="corporate_mobility_cases.id")
    depends_on_task_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_relocation_tasks.id")
    title: str
    category: str = Field(index=True)
    status: str = Field(default="planned", index=True)
    owner_role: str = Field(default="mobility_operator", index=True)
    due_at: Optional[datetime] = Field(default=None, index=True)
    requires_human_approval: bool = False
    approval_status: str = Field(default="not_required", index=True)
    work_notes: Optional[str] = None
    submitted_by: Optional[str] = Field(default=None, index=True)
    submitted_at: Optional[datetime] = Field(default=None, index=True)
    completed_by: Optional[str] = Field(default=None, index=True)
    completed_at: Optional[datetime] = Field(default=None, index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class CorporateRelocationTaskDecision(SQLModel, table=True):
    __tablename__ = "corporate_relocation_task_decisions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_relocation_task_id: UUID = Field(index=True, foreign_key="corporate_relocation_tasks.id")
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class EntrepreneurVentureProfile(SQLModel, table=True):
    __tablename__ = "entrepreneur_venture_profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    corporate_mobility_case_id: UUID = Field(index=True, unique=True, foreign_key="corporate_mobility_cases.id")
    founder_lead_id: UUID = Field(index=True, foreign_key="leads.id")
    venture_name: str = Field(index=True)
    venture_stage: str = Field(index=True)
    sector: str = Field(index=True)
    target_country: str = Field(index=True)
    incorporation_country: Optional[str] = Field(default=None, index=True)
    founder_role: str
    business_model_summary: str
    status: str = Field(default="draft", index=True)
    human_review_required: bool = True
    submitted_by: Optional[str] = Field(default=None, index=True)
    submitted_at: Optional[datetime] = Field(default=None, index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class VentureEvidenceItem(SQLModel, table=True):
    __tablename__ = "venture_evidence_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    venture_profile_id: UUID = Field(index=True, foreign_key="entrepreneur_venture_profiles.id")
    evidence_type: str = Field(index=True)
    title: str
    declared_amount_minor: Optional[int] = None
    currency: Optional[str] = Field(default=None, index=True)
    document_record_id: Optional[UUID] = Field(default=None, index=True, foreign_key="documents.id")
    notes: Optional[str] = None
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class VentureReviewDecision(SQLModel, table=True):
    __tablename__ = "venture_review_decisions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    venture_profile_id: UUID = Field(index=True, foreign_key="entrepreneur_venture_profiles.id")
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class BusinessMobilityAdvisoryAssessment(SQLModel, table=True):
    __tablename__ = "business_mobility_advisory_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    corporate_mobility_case_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_mobility_cases.id")
    primary_intent: str = Field(index=True)
    situation_text: str
    input_json: str
    feasibility_score: float
    feasibility_band: str = Field(index=True)
    information_score: float
    evidence_score: float
    commercial_fit_score: float
    pathway_grounding_score: float
    strategy_options_json: str
    blockers_json: str
    next_actions_json: str
    evidence_basis_json: str
    risk_flags_json: str
    strategic_memo: Optional[str] = None
    escalation_required: bool = True
    status: str = Field(default="pending_review", index=True)
    human_review_required: bool = True
    generated_by: str = Field(index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class BusinessMobilityAdvisoryReview(SQLModel, table=True):
    __tablename__ = "business_mobility_advisory_reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assessment_id: UUID = Field(index=True, foreign_key="business_mobility_advisory_assessments.id")
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class InvestmentMobilityProgram(SQLModel, table=True):
    __tablename__ = "investment_mobility_programs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    program_key: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    country: str = Field(index=True)
    program_type: str = Field(index=True)
    pathway_id: UUID = Field(index=True, foreign_key="mobility_pathways.id")
    description: Optional[str] = None
    catalogue_status: str = Field(default="draft", index=True)
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class InvestmentMobilityProgramVersion(SQLModel, table=True):
    __tablename__ = "investment_mobility_program_versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    program_id: UUID = Field(index=True, foreign_key="investment_mobility_programs.id")
    version_number: int = Field(default=1, index=True)
    lifecycle_status: str = Field(default="draft", index=True)
    supersedes_version_id: Optional[UUID] = Field(default=None, index=True, foreign_key="investment_mobility_program_versions.id")
    pathway_version_id: UUID = Field(index=True, foreign_key="mobility_pathway_versions.id")
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    minimum_commitment_minor: int
    currency: str
    investment_options_json: str
    holding_period_text: Optional[str] = None
    physical_presence_text: Optional[str] = None
    family_scope_json: str
    due_diligence_json: str
    fees_json: str
    benefits_json: str
    risks_json: str
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    human_review_required: bool = True
    created_by: str = Field(index=True)
    approved_by: Optional[str] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class InvestmentMobilitySuitabilityAssessment(SQLModel, table=True):
    __tablename__ = "investment_mobility_suitability_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    business_advisory_assessment_id: Optional[UUID] = Field(default=None, index=True, foreign_key="business_mobility_advisory_assessments.id")
    input_json: str
    candidate_program_version_ids_json: str
    ranked_programs_json: str
    blockers_json: str
    next_actions_json: str
    evidence_basis_json: str
    overall_readiness_score: float
    readiness_band: str = Field(index=True)
    status: str = Field(default="pending_review", index=True)
    human_review_required: bool = True
    generated_by: str = Field(index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class InvestmentMobilitySuitabilityReview(SQLModel, table=True):
    __tablename__ = "investment_mobility_suitability_reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assessment_id: UUID = Field(index=True, foreign_key="investment_mobility_suitability_assessments.id")
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class FamilyOfficeMobilityAssessment(SQLModel, table=True):
    __tablename__ = "family_office_mobility_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    business_advisory_assessment_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="business_mobility_advisory_assessments.id",
    )
    family_office_name: Optional[str] = Field(default=None, index=True)
    input_json: str
    readiness_score: float
    readiness_band: str = Field(index=True)
    identity_score: float
    wealth_evidence_score: float
    ownership_transparency_score: float
    governance_score: float
    mobility_grounding_score: float
    workstreams_json: str
    blockers_json: str
    next_actions_json: str
    evidence_basis_json: str
    grounded_pathway_versions_json: str
    grounded_program_versions_json: str
    escalation_flags_json: str
    status: str = Field(default="pending_review", index=True)
    human_review_required: bool = True
    generated_by: str = Field(index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class FamilyOfficeMobilityReview(SQLModel, table=True):
    __tablename__ = "family_office_mobility_reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assessment_id: UUID = Field(
        index=True,
        foreign_key="family_office_mobility_assessments.id",
    )
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class TaxTreatyEvidence(SQLModel, table=True):
    __tablename__ = "tax_treaty_evidence"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    evidence_key: str = Field(index=True, unique=True)
    jurisdiction_a: str = Field(index=True)
    jurisdiction_b: str = Field(index=True)
    topic: str = Field(index=True)
    title: str
    statement: str
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    effective_from: Optional[datetime] = Field(default=None, index=True)
    effective_to: Optional[datetime] = Field(default=None, index=True)
    status: str = Field(default="pending_review", index=True)
    proposed_by: str = Field(index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class TaxTreatyEvidenceDecision(SQLModel, table=True):
    __tablename__ = "tax_treaty_evidence_decisions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    tax_treaty_evidence_id: UUID = Field(
        index=True,
        foreign_key="tax_treaty_evidence.id",
    )
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class TaxResidencyAssessment(SQLModel, table=True):
    __tablename__ = "tax_residency_assessments"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    family_office_assessment_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="family_office_mobility_assessments.id",
    )
    business_advisory_assessment_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="business_mobility_advisory_assessments.id",
    )
    tax_year: int = Field(index=True)
    input_json: str
    readiness_score: float
    readiness_band: str = Field(index=True)
    fact_completeness_score: float
    controlled_evidence_score: float
    treaty_grounding_score: float
    specialist_coordination_score: float
    issue_matrix_json: str
    workstreams_json: str
    blockers_json: str
    next_actions_json: str
    evidence_basis_json: str
    treaty_evidence_ids_json: str
    escalation_flags_json: str
    status: str = Field(default="specialist_review_required", index=True)
    human_review_required: bool = True
    generated_by: str = Field(index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class TaxResidencyAssessmentReview(SQLModel, table=True):
    __tablename__ = "tax_residency_assessment_reviews"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    assessment_id: UUID = Field(
        index=True,
        foreign_key="tax_residency_assessments.id",
    )
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class InvestmentMobilityRuleProposal(SQLModel, table=True):
    __tablename__ = "investment_mobility_rule_proposals"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    pathway_version_id: UUID = Field(index=True, foreign_key="mobility_pathway_versions.id")
    official_source_id: UUID = Field(index=True, foreign_key="official_sources.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    proposed_rules_json: str
    status: str = Field(default="pending_review", index=True)
    proposed_by: str = Field(index=True)
    reviewed_by: Optional[str] = Field(default=None, index=True)
    reviewed_at: Optional[datetime] = Field(default=None, index=True)
    review_notes: Optional[str] = None
    created_verified_rule_ids_json: str = "[]"
    replacement_pathway_version_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="mobility_pathway_versions.id",
    )
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class InvestmentMobilityRuleDecision(SQLModel, table=True):
    __tablename__ = "investment_mobility_rule_decisions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    proposal_id: UUID = Field(index=True, foreign_key="investment_mobility_rule_proposals.id")
    decision: str = Field(index=True)
    reason: str
    reviewer: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


class OrganizationPosition(SQLModel, table=True):
    __tablename__ = "organization_positions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    position_key: str = Field(index=True)
    title: str
    department: str = Field(index=True)
    reports_to_position_key: Optional[str] = Field(default=None, index=True)
    role_card_name: Optional[str] = None
    authority_level: str = Field(index=True)
    contract_json: str = "{}"
    status: str = Field(default="active", index=True)
    version: int = 1
    created_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)
    suspended_at: Optional[datetime] = Field(default=None, index=True)
    suspended_by: Optional[str] = Field(default=None, index=True)
    suspended_reason: Optional[str] = None


class OrganizationalWorkItem(SQLModel, table=True):
    __tablename__ = "organizational_work_items"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_org_work_idempotency"),
        UniqueConstraint("tenant_key", "id", name="uq_org_work_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_key", "parent_work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_work_parent_tenant",
        ),
        CheckConstraint("priority IN ('low','normal','high','critical')", name="ck_org_work_priority"),
        CheckConstraint("parent_work_item_id IS NULL OR parent_work_item_id <> id", name="ck_org_work_not_self_parent"),
        Index("ix_org_work_tenant_status_due", "tenant_key", "status", "due_at"),
        Index("ix_org_work_tenant_department_status", "tenant_key", "department", "status"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    idempotency_key: str = Field(index=True)
    idempotency_fingerprint: Optional[str] = Field(default=None, max_length=64, index=True)
    tenant_key: str = Field(default="default", index=True)
    work_type: str = Field(default="organizational", index=True)
    objective_key: Optional[str] = Field(default=None, index=True)
    phase_key: Optional[str] = Field(default=None, index=True)
    priority: OrganizationWorkPriority = Field(
        default=OrganizationWorkPriority.normal,
        sa_column=Column(_string_enum(OrganizationWorkPriority), nullable=False, index=True),
    )
    parent_work_item_id: Optional[UUID] = Field(default=None, index=True)
    automation_event_id: Optional[UUID] = Field(default=None, index=True, foreign_key="automation_events.id")
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    corporate_account_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_mobility_cases.id")
    source_object_type: Optional[str] = Field(default=None, index=True)
    source_object_id: Optional[str] = Field(default=None, index=True)
    source_object_version: Optional[str] = None
    requested_by_type: Optional[OrganizationActorType] = Field(
        default=None,
        sa_column=Column(_string_enum(OrganizationActorType), nullable=True, index=True),
    )
    requested_by_id: Optional[str] = Field(default=None, index=True)
    title: str
    objective: str
    department: str = Field(index=True)
    authority_level: str = Field(index=True)
    status: str = Field(default="queued", index=True)
    assigned_position_key: str = Field(index=True)
    risk_level: str = Field(default="routine", index=True)
    is_emergency: bool = Field(default=False, index=True)
    due_at: Optional[datetime] = Field(default=None, index=True)
    reminded_at: Optional[datetime] = Field(default=None, index=True)
    escalated_at: Optional[datetime] = Field(default=None, index=True)
    execution_attempts: int = Field(default=0, ge=0)
    max_execution_attempts: int = Field(default=3, ge=1, le=5)
    execution_token: Optional[str] = Field(default=None, index=True)
    execution_started_at: Optional[datetime] = Field(default=None, index=True)
    next_retry_at: Optional[datetime] = Field(default=None, index=True)
    last_error: Optional[str] = None
    cancel_requested_at: Optional[datetime] = Field(default=None, index=True)
    cancelled_at: Optional[datetime] = Field(default=None, index=True)
    cancelled_by: Optional[str] = Field(default=None, index=True)
    cancellation_reason: Optional[str] = None
    context_json: str = "{}"
    output_json: str = "{}"
    created_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)
    completed_at: Optional[datetime] = Field(default=None, index=True)


class OrganizationExecutionAttempt(SQLModel, table=True):
    __tablename__ = "organization_execution_attempts"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    attempt_key: str = Field(index=True)
    work_item_id: UUID = Field(index=True, foreign_key="organizational_work_items.id")
    attempt_number: int = Field(ge=1)
    execution_token: str = Field(index=True)
    status: str = Field(default="running", index=True)
    actor: str = Field(default="organization-worker", index=True)
    started_at: datetime = Field(default_factory=now_utc, index=True)
    completed_at: Optional[datetime] = Field(default=None, index=True)
    error: Optional[str] = None


class DelegationRecord(SQLModel, table=True):
    __tablename__ = "delegation_records"
    __table_args__ = (
        UniqueConstraint(
            "work_item_id",
            "delegate_position_key",
            name="uq_delegation_work_delegate",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    work_item_id: UUID = Field(index=True, foreign_key="organizational_work_items.id")
    delegator_position_key: str = Field(index=True)
    delegate_position_key: str = Field(index=True)
    task: str
    authority_basis: str
    status: str = Field(default="queued", index=True)
    result_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    completed_at: Optional[datetime] = Field(default=None, index=True)


class OrganizationalActionOutput(SQLModel, table=True):
    __tablename__ = "organizational_action_outputs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    output_key: str = Field(index=True)
    work_item_id: UUID = Field(index=True, foreign_key="organizational_work_items.id")
    delegation_record_id: Optional[UUID] = Field(default=None, index=True, foreign_key="delegation_records.id")
    accountable_position_key: str = Field(index=True)
    authority_basis: str
    evidence_json: str = "[]"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_basis: str
    impact_json: str = "{}"
    rollback_posture: str
    output_json: str = "{}"
    status: str = Field(default="completed", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ExecutiveDecision(SQLModel, table=True):
    __tablename__ = "executive_decisions"
    __table_args__ = (
        UniqueConstraint("decision_key", name="uq_executive_decision_key"),
        UniqueConstraint("tenant_key", "id", name="uq_exec_decision_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_exec_decision_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_exec_decision_supersedes_tenant",
        ),
        CheckConstraint(
            "decision_type IN ('operational','policy','risk','exception','board_reserved')",
            name="ck_exec_decision_type",
        ),
        CheckConstraint(
            "supersedes_decision_id IS NULL OR supersedes_decision_id <> id",
            name="ck_exec_decision_not_self_superseding",
        ),
        Index("ix_exec_decision_tenant_status_due", "tenant_key", "status", "due_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    decision_key: str = Field(index=True)
    tenant_key: str = Field(default="default", index=True)
    decision_type: OrganizationDecisionType = Field(
        default=OrganizationDecisionType.operational,
        sa_column=Column(_string_enum(OrganizationDecisionType), nullable=False, index=True),
    )
    record_fingerprint: Optional[str] = Field(default=None, max_length=64, index=True)
    work_item_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organizational_work_items.id")
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    corporate_account_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_mobility_cases.id")
    source_object_type: Optional[str] = Field(default=None, index=True)
    source_object_id: Optional[str] = Field(default=None, index=True)
    source_object_version: Optional[str] = None
    supersedes_decision_id: Optional[UUID] = Field(default=None, index=True)
    authority_level: str = Field(index=True)
    requested_by_position: str = Field(index=True)
    decision_owner_position: str = Field(index=True)
    title: str
    question: str
    recommendation: str
    alternatives_json: str = "[]"
    evidence_json: str = "[]"
    impact_json: str = "{}"
    conditions_json: str = "[]"
    effect_summary: Optional[str] = None
    status: str = Field(default="pending_ceo", index=True)
    coordination_token: Optional[str] = Field(default=None, index=True)
    coordination_claimed_at: Optional[datetime] = Field(default=None, index=True)
    decided_by: Optional[str] = Field(default=None, index=True)
    decision_reason: Optional[str] = None
    decided_at: Optional[datetime] = Field(default=None, index=True)
    due_at: Optional[datetime] = Field(default=None, index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)
    reminded_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class OrganizationActivityStream(SQLModel, table=True):
    __tablename__ = "organization_activity_streams"
    __table_args__ = (
        UniqueConstraint("tenant_key", "stream_key", name="uq_org_activity_stream_tenant_key"),
        UniqueConstraint("tenant_key", "id", name="uq_org_activity_stream_tenant_id"),
        CheckConstraint("last_sequence >= 0", name="ck_org_activity_stream_sequence_nonnegative"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str = Field(index=True)
    stream_key: str = Field(index=True)
    last_sequence: int = Field(default=0, sa_column=Column(BigInteger(), nullable=False))
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class OrganizationActivity(SQLModel, table=True):
    __tablename__ = "organization_activities"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_activity_tenant_id"),
        UniqueConstraint("tenant_key", "activity_key", name="uq_org_activity_tenant_key"),
        UniqueConstraint("activity_stream_id", "stream_sequence", name="uq_org_activity_stream_sequence"),
        ForeignKeyConstraint(
            ["tenant_key", "activity_stream_id"],
            ["organization_activity_streams.tenant_key", "organization_activity_streams.id"],
            name="fk_org_activity_stream_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_activity_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "causation_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_org_activity_causation_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_org_activity_supersedes_tenant",
        ),
        CheckConstraint("stream_sequence >= 1", name="ck_org_activity_sequence_positive"),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_activity_fingerprint_length"),
        CheckConstraint(
            "activity_class IN ('domain','work','decision','blocker','human_action','contribution','operational')",
            name="ck_org_activity_class",
        ),
        CheckConstraint(
            "actor_type IN ('human','agent','worker','system','external_human')",
            name="ck_org_activity_actor_type",
        ),
        CheckConstraint("authority_level IS NULL OR authority_level <> ''", name="ck_org_activity_authority"),
        CheckConstraint(
            "causation_activity_id IS NULL OR causation_activity_id <> id",
            name="ck_org_activity_not_self_caused",
        ),
        CheckConstraint(
            "supersedes_activity_id IS NULL OR supersedes_activity_id <> id",
            name="ck_org_activity_not_self_superseding",
        ),
        Index("ix_org_activity_tenant_occurred", "tenant_key", "occurred_at"),
        Index("ix_org_activity_tenant_department_occurred", "tenant_key", "department", "occurred_at"),
        Index("ix_org_activity_tenant_type_occurred", "tenant_key", "activity_type", "occurred_at"),
        Index("ix_org_activity_tenant_source", "tenant_key", "source_object_type", "source_object_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    activity_key: str
    record_fingerprint: str = Field(max_length=64)
    tenant_key: str = Field(index=True)
    activity_stream_id: UUID
    stream_sequence: int = Field(sa_column=Column(BigInteger(), nullable=False))
    activity_class: OrganizationActivityClass = Field(
        sa_column=Column(_string_enum(OrganizationActivityClass), nullable=False)
    )
    activity_type: str = Field(index=True)
    title: str
    summary: str
    department: Optional[str] = Field(default=None, index=True)
    position_key: Optional[str] = None
    authority_level: Optional[str] = None
    actor_type: OrganizationActorType = Field(
        sa_column=Column(_string_enum(OrganizationActorType), nullable=False)
    )
    actor_id: str = Field(index=True)
    work_item_id: Optional[UUID] = Field(default=None, index=True)
    execution_attempt_id: Optional[UUID] = Field(
        default=None, index=True, foreign_key="organization_execution_attempts.id"
    )
    agent_run_id: Optional[UUID] = Field(default=None, index=True, foreign_key="agent_runs.id")
    automation_event_id: Optional[UUID] = Field(default=None, index=True, foreign_key="automation_events.id")
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    corporate_account_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(
        default=None, index=True, foreign_key="corporate_mobility_cases.id"
    )
    source_object_type: str = Field(index=True)
    source_object_id: str = Field(index=True)
    source_object_version: Optional[str] = None
    correlation_key: Optional[str] = Field(default=None, index=True)
    causation_activity_id: Optional[UUID] = Field(default=None, index=True)
    supersedes_activity_id: Optional[UUID] = Field(default=None, index=True)
    payload_json: str = "{}"
    occurred_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc)
    created_by: str


class OrganizationContribution(SQLModel, table=True):
    __tablename__ = "organization_contributions"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_contribution_tenant_id"),
        UniqueConstraint("tenant_key", "contribution_key", name="uq_org_contribution_tenant_key"),
        UniqueConstraint(
            "tenant_key", "supersedes_contribution_id", "record_kind", name="uq_org_contribution_correction"
        ),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_contribution_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_org_contribution_decision_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_contribution_supersedes_tenant",
        ),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_contribution_fingerprint_length"),
        CheckConstraint(
            "actor_type IN ('human','agent','worker','system','external_human')",
            name="ck_org_contribution_actor_type",
        ),
        CheckConstraint(
            "verification_method IN ('domain_transition','human_attestation','deterministic_gate')",
            name="ck_org_contribution_verification_method",
        ),
        CheckConstraint(
            "record_kind IN ('outcome','supersession','retraction')",
            name="ck_org_contribution_record_kind",
        ),
        CheckConstraint(
            "impact_kind IN ('state_change','risk_reduction','milestone','delivery','validation','knowledge')",
            name="ck_org_contribution_impact_kind",
        ),
        CheckConstraint(
            "human_review_state IN ('not_required','completed')",
            name="ck_org_contribution_human_review_state",
        ),
        CheckConstraint(
            "source_object_type NOT IN ('agent_run','workflow_run','organization_execution_attempt',"
            "'organizational_action_output','audit_log','tool_call','message')",
            name="ck_org_contribution_authoritative_source",
        ),
        CheckConstraint(
            "(measured_value IS NULL AND baseline_value IS NULL AND target_value IS NULL) "
            "OR measurement_unit IS NOT NULL",
            name="ck_org_contribution_measurement_unit",
        ),
        CheckConstraint(
            "(record_kind = 'outcome' AND supersedes_contribution_id IS NULL AND retraction_reason IS NULL) OR "
            "(record_kind = 'supersession' AND supersedes_contribution_id IS NOT NULL AND retraction_reason IS NULL) OR "
            "(record_kind = 'retraction' AND supersedes_contribution_id IS NOT NULL AND retraction_reason IS NOT NULL)",
            name="ck_org_contribution_correction_shape",
        ),
        CheckConstraint(
            "supersedes_contribution_id IS NULL OR supersedes_contribution_id <> id",
            name="ck_org_contribution_not_self_superseding",
        ),
        Index("ix_org_contribution_tenant_kind_effective", "tenant_key", "record_kind", "effective_at"),
        Index("ix_org_contribution_tenant_department_effective", "tenant_key", "department", "effective_at"),
        Index("ix_org_contribution_tenant_type_effective", "tenant_key", "contribution_type", "effective_at"),
        Index(
            "ix_org_contribution_tenant_source",
            "tenant_key",
            "source_object_type",
            "source_object_id",
            "source_object_version",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    contribution_key: str
    record_fingerprint: str = Field(max_length=64)
    tenant_key: str = Field(index=True)
    contribution_type: str = Field(index=True)
    title: str
    outcome_summary: str
    actor_type: OrganizationActorType = Field(
        sa_column=Column(_string_enum(OrganizationActorType), nullable=False)
    )
    actor_id: str = Field(index=True)
    department: str = Field(index=True)
    accountable_position_key: str
    authority_level: str
    objective_key: Optional[str] = Field(default=None, index=True)
    phase_key: Optional[str] = Field(default=None, index=True)
    work_item_id: Optional[UUID] = Field(default=None, index=True)
    decision_id: Optional[UUID] = Field(default=None, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    corporate_account_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(
        default=None, index=True, foreign_key="corporate_mobility_cases.id"
    )
    source_object_type: str = Field(index=True)
    source_object_id: str = Field(index=True)
    source_object_version: str
    source_state: str
    verification_method: OrganizationContributionVerificationMethod = Field(
        sa_column=Column(_string_enum(OrganizationContributionVerificationMethod), nullable=False)
    )
    record_kind: OrganizationContributionRecordKind = Field(
        default=OrganizationContributionRecordKind.outcome,
        sa_column=Column(_string_enum(OrganizationContributionRecordKind), nullable=False),
    )
    verified_by: str
    verified_at: datetime
    human_review_state: str
    impact_kind: OrganizationContributionImpactKind = Field(
        sa_column=Column(_string_enum(OrganizationContributionImpactKind), nullable=False)
    )
    measured_value: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 4), nullable=True))
    baseline_value: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 4), nullable=True))
    target_value: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 4), nullable=True))
    measurement_unit: Optional[str] = None
    impact_json: str = "{}"
    evidence_summary_json: str = "[]"
    human_action_required: bool = False
    effective_at: datetime = Field(index=True)
    supersedes_contribution_id: Optional[UUID] = Field(default=None, index=True)
    retraction_reason: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)


class OrganizationWorkItemDependency(SQLModel, table=True):
    __tablename__ = "organization_work_item_dependencies"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_work_dependency_tenant_id"),
        UniqueConstraint("tenant_key", "dependency_key", name="uq_org_work_dependency_tenant_key"),
        UniqueConstraint(
            "tenant_key", "work_item_id", "depends_on_work_item_id", "dependency_type",
            name="uq_org_work_dependency_edge",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_work_dependency_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "depends_on_work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_work_dependency_depends_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "satisfied_by_contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_work_dependency_contribution_tenant",
        ),
        CheckConstraint("work_item_id <> depends_on_work_item_id", name="ck_org_work_dependency_not_self"),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_work_dependency_fingerprint_length"),
        CheckConstraint("dependency_type IN ('blocks','requires','informs')", name="ck_org_work_dependency_type"),
        CheckConstraint(
            "status IN ('active','satisfied','waived','superseded')", name="ck_org_work_dependency_status"
        ),
        CheckConstraint(
            "status <> 'waived' OR (waived_by_human_id IS NOT NULL AND waiver_reason IS NOT NULL AND waived_at IS NOT NULL)",
            name="ck_org_work_dependency_waiver",
        ),
        Index("ix_org_work_dependency_tenant_status", "tenant_key", "status"),
        Index("ix_org_work_dependency_forward", "tenant_key", "work_item_id"),
        Index("ix_org_work_dependency_reverse", "tenant_key", "depends_on_work_item_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    dependency_key: str
    record_fingerprint: str = Field(max_length=64)
    tenant_key: str
    work_item_id: UUID
    depends_on_work_item_id: UUID
    dependency_type: OrganizationDependencyType = Field(
        sa_column=Column(_string_enum(OrganizationDependencyType), nullable=False)
    )
    status: OrganizationDependencyStatus = Field(
        default=OrganizationDependencyStatus.active,
        sa_column=Column(_string_enum(OrganizationDependencyStatus), nullable=False),
    )
    satisfied_by_contribution_id: Optional[UUID] = None
    waived_by_human_id: Optional[str] = None
    waiver_reason: Optional[str] = None
    waived_at: Optional[datetime] = None
    created_by: str
    updated_by: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class OrganizationBlocker(SQLModel, table=True):
    __tablename__ = "organization_blockers"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_blocker_tenant_id"),
        UniqueConstraint("tenant_key", "blocker_key", name="uq_org_blocker_tenant_key"),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_blocker_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_org_blocker_decision_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_blocker_contribution_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_blocker_id"],
            ["organization_blockers.tenant_key", "organization_blockers.id"],
            name="fk_org_blocker_supersedes_tenant",
        ),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_blocker_fingerprint_length"),
        CheckConstraint(
            "blocker_type IN ('evidence','dependency','authority','human_input','external','safety','technical')",
            name="ck_org_blocker_type",
        ),
        CheckConstraint("severity IN ('low','medium','high','critical')", name="ck_org_blocker_severity"),
        CheckConstraint(
            "status IN ('open','mitigated','resolved','waived','superseded')", name="ck_org_blocker_status"
        ),
        CheckConstraint(
            "work_item_id IS NOT NULL OR decision_id IS NOT NULL OR contribution_id IS NOT NULL OR lead_id IS NOT NULL "
            "OR profile_id IS NOT NULL OR application_id IS NOT NULL OR corporate_account_id IS NOT NULL "
            "OR corporate_mobility_case_id IS NOT NULL",
            name="ck_org_blocker_has_target",
        ),
        CheckConstraint(
            "status <> 'resolved' OR (resolved_at IS NOT NULL AND resolution_summary IS NOT NULL "
            "AND resolving_actor_type IS NOT NULL AND resolving_actor_id IS NOT NULL)",
            name="ck_org_blocker_resolution",
        ),
        CheckConstraint(
            "status <> 'waived' OR (waived_by_human_id IS NOT NULL AND waiver_reason IS NOT NULL AND waived_at IS NOT NULL)",
            name="ck_org_blocker_waiver",
        ),
        CheckConstraint("supersedes_blocker_id IS NULL OR supersedes_blocker_id <> id", name="ck_org_blocker_not_self"),
        Index("ix_org_blocker_tenant_status_severity_due", "tenant_key", "status", "severity", "due_at"),
        Index("ix_org_blocker_tenant_department_status", "tenant_key", "department", "status"),
        Index("ix_org_blocker_tenant_source", "tenant_key", "source_object_type", "source_object_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    blocker_key: str
    record_fingerprint: str = Field(max_length=64)
    tenant_key: str = Field(index=True)
    blocker_type: OrganizationBlockerType = Field(
        sa_column=Column(_string_enum(OrganizationBlockerType), nullable=False)
    )
    severity: str = Field(index=True)
    title: str
    description: str
    status: OrganizationBlockerStatus = Field(
        default=OrganizationBlockerStatus.open,
        sa_column=Column(_string_enum(OrganizationBlockerStatus), nullable=False, index=True),
    )
    department: Optional[str] = Field(default=None, index=True)
    accountable_position_key: Optional[str] = None
    authority_level: Optional[str] = None
    work_item_id: Optional[UUID] = Field(default=None, index=True)
    decision_id: Optional[UUID] = Field(default=None, index=True)
    contribution_id: Optional[UUID] = Field(default=None, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    corporate_account_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(
        default=None, index=True, foreign_key="corporate_mobility_cases.id"
    )
    risk_escalation_id: Optional[UUID] = Field(default=None, index=True, foreign_key="risk_escalations.id")
    external_validation_finding_id: Optional[UUID] = Field(
        default=None, index=True, foreign_key="external_validation_findings.id"
    )
    source_object_type: Optional[str] = Field(default=None, index=True)
    source_object_id: Optional[str] = Field(default=None, index=True)
    source_object_version: Optional[str] = None
    requires_human_action: bool = False
    opened_at: datetime = Field(default_factory=now_utc)
    due_at: Optional[datetime] = Field(default=None, index=True)
    mitigated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_summary: Optional[str] = None
    resolving_actor_type: Optional[OrganizationActorType] = Field(
        default=None,
        sa_column=Column(_string_enum(OrganizationActorType), nullable=True),
    )
    resolving_actor_id: Optional[str] = None
    waived_by_human_id: Optional[str] = None
    waiver_reason: Optional[str] = None
    waived_at: Optional[datetime] = None
    supersedes_blocker_id: Optional[UUID] = Field(default=None, index=True)
    created_by: str
    updated_by: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class OrganizationHumanActionRequest(SQLModel, table=True):
    __tablename__ = "organization_human_action_requests"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_human_request_tenant_id"),
        UniqueConstraint("tenant_key", "request_key", name="uq_org_human_request_tenant_key"),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_human_request_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_org_human_request_decision_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "blocker_id"],
            ["organization_blockers.tenant_key", "organization_blockers.id"],
            name="fk_org_human_request_blocker_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_human_request_contribution_tenant",
        ),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_human_request_fingerprint_length"),
        CheckConstraint(
            "request_type IN ('review','decision','attestation','acknowledgement','provide_information','approval','exception')",
            name="ck_org_human_request_type",
        ),
        CheckConstraint(
            "status IN ('required','acknowledged','in_progress','completed','declined','cancelled','expired')",
            name="ck_org_human_request_status",
        ),
        CheckConstraint("priority IN ('low','normal','high','critical')", name="ck_org_human_request_priority"),
        CheckConstraint(
            "work_item_id IS NOT NULL OR decision_id IS NOT NULL OR blocker_id IS NOT NULL OR contribution_id IS NOT NULL "
            "OR lead_id IS NOT NULL OR profile_id IS NOT NULL OR application_id IS NOT NULL "
            "OR corporate_account_id IS NOT NULL OR corporate_mobility_case_id IS NOT NULL",
            name="ck_org_human_request_has_target",
        ),
        CheckConstraint(
            "status <> 'completed' OR (completed_at IS NOT NULL AND completed_by_human_id IS NOT NULL AND outcome IS NOT NULL)",
            name="ck_org_human_request_completed",
        ),
        CheckConstraint(
            "status <> 'declined' OR (declined_at IS NOT NULL AND declined_by_human_id IS NOT NULL AND outcome IS NOT NULL)",
            name="ck_org_human_request_declined",
        ),
        CheckConstraint(
            "status <> 'cancelled' OR (cancelled_at IS NOT NULL AND cancelled_by_actor_id IS NOT NULL AND outcome IS NOT NULL)",
            name="ck_org_human_request_cancelled",
        ),
        CheckConstraint("status <> 'expired' OR expired_at IS NOT NULL", name="ck_org_human_request_expired"),
        Index("ix_org_human_request_tenant_status_priority_due", "tenant_key", "status", "priority", "due_at"),
        Index("ix_org_human_request_assignee_status_due", "assigned_human_id", "status", "due_at"),
        Index("ix_org_human_request_tenant_source", "tenant_key", "source_object_type", "source_object_id"),
        Index("ix_org_human_request_corporate_case", "corporate_mobility_case_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    request_key: str
    record_fingerprint: str = Field(max_length=64)
    tenant_key: str = Field(index=True)
    request_type: OrganizationHumanActionRequestType = Field(
        sa_column=Column(_string_enum(OrganizationHumanActionRequestType), nullable=False)
    )
    title: str
    instructions: str
    status: OrganizationHumanActionRequestStatus = Field(
        default=OrganizationHumanActionRequestStatus.required,
        sa_column=Column(_string_enum(OrganizationHumanActionRequestStatus), nullable=False, index=True),
    )
    priority: OrganizationWorkPriority = Field(
        default=OrganizationWorkPriority.normal,
        sa_column=Column(_string_enum(OrganizationWorkPriority), nullable=False, index=True),
    )
    required_role: str = Field(index=True)
    assigned_human_id: Optional[str] = Field(default=None, index=True)
    requested_by_type: OrganizationActorType = Field(
        sa_column=Column(_string_enum(OrganizationActorType), nullable=False)
    )
    requested_by_id: str
    authority_level: Optional[str] = None
    work_item_id: Optional[UUID] = Field(default=None, index=True)
    decision_id: Optional[UUID] = Field(default=None, index=True)
    blocker_id: Optional[UUID] = Field(default=None, index=True)
    contribution_id: Optional[UUID] = Field(default=None, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    corporate_account_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(
        default=None, foreign_key="corporate_mobility_cases.id"
    )
    source_object_type: Optional[str] = Field(default=None, index=True)
    source_object_id: Optional[str] = Field(default=None, index=True)
    source_object_version: Optional[str] = None
    requested_at: datetime = Field(default_factory=now_utc)
    due_at: Optional[datetime] = Field(default=None, index=True)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_human_id: Optional[str] = None
    started_at: Optional[datetime] = None
    started_by_human_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    completed_by_human_id: Optional[str] = None
    declined_at: Optional[datetime] = None
    declined_by_human_id: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by_actor_id: Optional[str] = None
    expired_at: Optional[datetime] = None
    outcome: Optional[str] = None
    completion_notes: Optional[str] = None
    created_by: str
    updated_by: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class OrganizationHumanAction(SQLModel, table=True):
    __tablename__ = "organization_human_actions"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_human_action_tenant_id"),
        UniqueConstraint("tenant_key", "action_key", name="uq_org_human_action_tenant_key"),
        ForeignKeyConstraint(
            ["tenant_key", "human_action_request_id"],
            ["organization_human_action_requests.tenant_key", "organization_human_action_requests.id"],
            name="fk_org_human_action_request_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_human_action_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_org_human_action_decision_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "blocker_id"],
            ["organization_blockers.tenant_key", "organization_blockers.id"],
            name="fk_org_human_action_blocker_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_human_action_contribution_tenant",
        ),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_human_action_fingerprint_length"),
        CheckConstraint("actor_type = 'human'", name="ck_org_human_action_actor_human"),
        CheckConstraint(
            "action_type IN ('reviewed','approved','rejected','requested_changes','attested','acknowledged',"
            "'assigned','reassigned','resolved','declined','cancelled')",
            name="ck_org_human_action_type",
        ),
        CheckConstraint(
            "human_action_request_id IS NOT NULL OR work_item_id IS NOT NULL OR decision_id IS NOT NULL "
            "OR blocker_id IS NOT NULL OR contribution_id IS NOT NULL OR lead_id IS NOT NULL OR profile_id IS NOT NULL "
            "OR application_id IS NOT NULL OR corporate_account_id IS NOT NULL OR corporate_mobility_case_id IS NOT NULL",
            name="ck_org_human_action_has_target",
        ),
        Index("ix_org_human_action_tenant_occurred", "tenant_key", "occurred_at"),
        Index("ix_org_human_action_actor_occurred", "human_actor_id", "occurred_at"),
        Index("ix_org_human_action_type_occurred", "action_type", "occurred_at"),
        Index("ix_org_human_action_tenant_source", "tenant_key", "source_object_type", "source_object_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    action_key: str
    record_fingerprint: str = Field(max_length=64)
    tenant_key: str = Field(index=True)
    human_action_request_id: Optional[UUID] = Field(default=None, index=True)
    action_type: OrganizationHumanActionType = Field(
        sa_column=Column(_string_enum(OrganizationHumanActionType), nullable=False)
    )
    actor_type: OrganizationActorType = Field(
        default=OrganizationActorType.human,
        sa_column=Column(_string_enum(OrganizationActorType), nullable=False),
    )
    human_actor_id: str = Field(index=True)
    actor_role: Optional[str] = None
    actor_position_key: Optional[str] = None
    actor_department: Optional[str] = None
    authority_level: Optional[str] = None
    work_item_id: Optional[UUID] = Field(default=None, index=True)
    decision_id: Optional[UUID] = Field(default=None, index=True)
    blocker_id: Optional[UUID] = Field(default=None, index=True)
    contribution_id: Optional[UUID] = Field(default=None, index=True)
    lead_id: Optional[UUID] = Field(default=None, index=True, foreign_key="leads.id")
    profile_id: Optional[UUID] = Field(default=None, index=True, foreign_key="profiles.id")
    application_id: Optional[UUID] = Field(default=None, index=True, foreign_key="applications.id")
    corporate_account_id: Optional[UUID] = Field(default=None, index=True, foreign_key="corporate_accounts.id")
    corporate_mobility_case_id: Optional[UUID] = Field(
        default=None, index=True, foreign_key="corporate_mobility_cases.id"
    )
    source_object_type: Optional[str] = Field(default=None, index=True)
    source_object_id: Optional[str] = Field(default=None, index=True)
    source_object_version: Optional[str] = None
    outcome: str
    reason: Optional[str] = None
    metadata_json: str = "{}"
    occurred_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc)
    created_by: str


class OrganizationRecordReference(SQLModel, table=True):
    __tablename__ = "organization_record_references"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_org_record_reference_tenant_id"),
        UniqueConstraint("tenant_key", "reference_key", name="uq_org_record_reference_tenant_key"),
        ForeignKeyConstraint(
            ["tenant_key", "activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_org_reference_activity_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_reference_contribution_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_reference_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_org_reference_decision_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "blocker_id"],
            ["organization_blockers.tenant_key", "organization_blockers.id"],
            name="fk_org_reference_blocker_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "human_action_request_id"],
            ["organization_human_action_requests.tenant_key", "organization_human_action_requests.id"],
            name="fk_org_reference_human_request_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "human_action_id"],
            ["organization_human_actions.tenant_key", "organization_human_actions.id"],
            name="fk_org_reference_human_action_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "supersedes_reference_id"],
            ["organization_record_references.tenant_key", "organization_record_references.id"],
            name="fk_org_reference_supersedes_tenant",
        ),
        CheckConstraint("length(record_fingerprint) = 64", name="ck_org_record_reference_fingerprint_length"),
        CheckConstraint(
            "reference_role IN ('authoritative_outcome','affected_subject','evidence','caused_by','supports','contradicts')",
            name="ck_org_record_reference_role",
        ),
        CheckConstraint(
            "target_type IN ('lead','profile','application','corporate_mobility_case','pathway_comparison_assessment',"
            "'eligibility_assessment','source_snapshot','official_source','external_validation_run',"
            "'external_validation_finding','agent_run','automation_event','audit_log','regulatory_change','verified_rule',"
            "'mobility_pathway_version','agency_submission','corporate_compliance_event','mobility_timeline_milestone')",
            name="ck_org_record_reference_target_type",
        ),
        CheckConstraint(
            "(CASE WHEN activity_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN contribution_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN work_item_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN decision_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN blocker_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN human_action_request_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN human_action_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_org_record_reference_one_owner",
        ),
        CheckConstraint(
            "supersedes_reference_id IS NULL OR supersedes_reference_id <> id",
            name="ck_org_record_reference_not_self",
        ),
        Index("ix_org_record_reference_tenant_target", "tenant_key", "target_type", "target_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    reference_key: str
    record_fingerprint: str = Field(max_length=64)
    tenant_key: str = Field(index=True)
    activity_id: Optional[UUID] = Field(default=None, index=True)
    contribution_id: Optional[UUID] = Field(default=None, index=True)
    work_item_id: Optional[UUID] = Field(default=None, index=True)
    decision_id: Optional[UUID] = Field(default=None, index=True)
    blocker_id: Optional[UUID] = Field(default=None, index=True)
    human_action_request_id: Optional[UUID] = Field(default=None, index=True)
    human_action_id: Optional[UUID] = Field(default=None, index=True)
    reference_role: OrganizationReferenceRole = Field(
        sa_column=Column(_string_enum(OrganizationReferenceRole), nullable=False)
    )
    target_type: OrganizationReferenceTargetType = Field(
        sa_column=Column(_string_enum(OrganizationReferenceTargetType), nullable=False, index=True)
    )
    target_id: str = Field(index=True)
    target_version: Optional[str] = None
    target_state: Optional[str] = None
    content_hash: Optional[str] = None
    label: Optional[str] = None
    source_url: Optional[str] = None
    metadata_json: str = "{}"
    supersedes_reference_id: Optional[UUID] = Field(default=None, index=True)
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)


class ExecutiveCouncilConsultation(SQLModel, table=True):
    __tablename__ = "executive_council_consultations"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    consultation_key: str = Field(index=True, unique=True)
    decision_id: UUID = Field(index=True, foreign_key="executive_decisions.id")
    work_item_id: UUID = Field(index=True, foreign_key="organizational_work_items.id")
    requested_by_position: str = Field(index=True)
    consulted_position: str = Field(index=True)
    domain: str = Field(index=True)
    evidence_json: str = "[]"
    recommendation: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    dissent: bool = Field(default=False, index=True)
    status: str = Field(default="pending", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)
    completed_at: Optional[datetime] = Field(default=None, index=True)


class RiskEscalation(SQLModel, table=True):
    __tablename__ = "risk_escalations"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    risk_key: str = Field(index=True)
    work_item_id: Optional[UUID] = Field(default=None, index=True, foreign_key="organizational_work_items.id")
    category: str = Field(index=True)
    severity: str = Field(index=True)
    title: str
    description: str
    evidence_json: str = "[]"
    containment_json: str = "[]"
    accountable_position_key: str = Field(index=True)
    escalated_to_position_key: str = Field(index=True)
    status: str = Field(default="open", index=True)
    requires_board_attention: bool = Field(default=False, index=True)
    is_emergency: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)
    resolved_at: Optional[datetime] = Field(default=None, index=True)


class BoardPacket(SQLModel, table=True):
    __tablename__ = "board_packets"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    packet_key: str = Field(index=True)
    packet_type: str = Field(default="on_demand", index=True)
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
    ceo_summary: str
    content_json: str = "{}"
    status: str = Field(default="draft", index=True)
    prepared_by_position: str = Field(default="ceo", index=True)
    published_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class OrganizationControl(SQLModel, table=True):
    __tablename__ = "organization_controls"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    control_key: str = Field(default="global", index=True)
    status: str = Field(default="active", index=True)
    reason: Optional[str] = None
    changed_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ExternalValidationScenario(SQLModel, table=True):
    __tablename__ = "external_validation_scenarios"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    scenario_key: str = Field(index=True, unique=True)
    title: str
    jurisdiction_code: str = Field(index=True)
    domain: str = Field(index=True)
    persona_json: str = "{}"
    objectives_json: str = "[]"
    required_evidence_types_json: str = "[]"
    status: str = Field(default="active", index=True)
    source_fixture: Optional[str] = None
    created_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ExternalValidationRun(SQLModel, table=True):
    __tablename__ = "external_validation_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    run_key: str = Field(index=True, unique=True)
    scenario_id: UUID = Field(index=True, foreign_key="external_validation_scenarios.id")
    lead_id: UUID = Field(index=True, foreign_key="leads.id")
    pathway_comparison_assessment_id: UUID = Field(
        index=True,
        foreign_key="pathway_comparison_assessments.id",
    )
    status: str = Field(default="draft", index=True)
    gate_status: str = Field(default="held", index=True)
    gate_reasons_json: str = "[]"
    founder_intervention_count: int = Field(default=0, ge=0)
    workflow_started_at: Optional[datetime] = Field(default=None, index=True)
    workflow_completed_at: Optional[datetime] = Field(default=None, index=True)
    evaluated_at: Optional[datetime] = Field(default=None, index=True)
    created_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ExternalValidationReview(SQLModel, table=True):
    __tablename__ = "external_validation_reviews"
    __table_args__ = (
        UniqueConstraint("run_id", "reviewer_type", name="uq_external_validation_run_reviewer_type"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    run_id: UUID = Field(index=True, foreign_key="external_validation_runs.id")
    reviewer_type: str = Field(index=True)
    reviewer_name: str = Field(index=True)
    reviewer_organization: Optional[str] = None
    reviewer_origin: str = Field(default="external_human", index=True)
    external_human_attestation: bool = False
    workflow_completed: bool = False
    understanding_rating: Optional[int] = Field(default=None, ge=1, le=5)
    usefulness_rating: Optional[int] = Field(default=None, ge=1, le=5)
    jurisdiction_pathway_correct: Optional[bool] = None
    material_rule_traceability_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    unsupported_legal_certainty_count: Optional[int] = Field(default=None, ge=0)
    missing_critical_document_count: Optional[int] = Field(default=None, ge=0)
    feedback: str
    submitted_by: str = Field(index=True)
    submitted_at: datetime = Field(default_factory=now_utc, index=True)


class ExternalValidationFinding(SQLModel, table=True):
    __tablename__ = "external_validation_findings"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    run_id: UUID = Field(index=True, foreign_key="external_validation_runs.id")
    review_id: Optional[UUID] = Field(default=None, index=True, foreign_key="external_validation_reviews.id")
    severity: str = Field(index=True)
    category: str = Field(index=True)
    title: str
    description: str
    status: str = Field(default="open", index=True)
    remediation_notes: Optional[str] = None
    resolved_by: Optional[str] = Field(default=None, index=True)
    resolved_at: Optional[datetime] = Field(default=None, index=True)
    board_acceptance_reason: Optional[str] = None
    board_accepted_by: Optional[str] = Field(default=None, index=True)
    board_accepted_at: Optional[datetime] = Field(default=None, index=True)
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class ExternalValidationEvidence(SQLModel, table=True):
    __tablename__ = "external_validation_evidence"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    run_id: UUID = Field(index=True, foreign_key="external_validation_runs.id")
    finding_id: Optional[UUID] = Field(default=None, index=True, foreign_key="external_validation_findings.id")
    evidence_type: str = Field(index=True)
    entity_id: Optional[UUID] = Field(default=None, index=True)
    label: str
    source_url: Optional[str] = None
    metadata_json: str = "{}"
    added_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)


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
