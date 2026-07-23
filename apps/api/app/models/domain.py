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
    status: IntakeSessionStatus = IntakeSessionStatus.started
    source: str = "public_intake"
    answers_json: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
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
