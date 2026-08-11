from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.domain import (
    AgentRunStatus,
    CoachConfidence,
    CoachReviewStatus,
    FollowUpStatus,
    IntakeSessionStatus,
    LeadIntent,
    LeadStatus,
    ReviewStatus,
    VerificationStatus,
    WorkflowStatus,
    now_utc,
)

class LeadCreate(BaseModel):
    full_name: str = Field(..., examples=["Bennet Allryn"])
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: str = "manual"
    intent: LeadIntent = LeadIntent.unknown
    target_country: Optional[str] = None
    notes: Optional[str] = None

class LeadRead(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    source: str
    intent: LeadIntent
    target_country: Optional[str]
    status: LeadStatus
    notes: Optional[str]

class TruthRequest(BaseModel):
    claim: str
    domain: Literal["visa", "job", "study", "scholarship", "document", "general"] = "general"
    country: Optional[str] = None
    source_urls: List[str] = []

class TruthResponse(BaseModel):
    verdict: VerificationStatus
    confidence: float
    requires_human_review: bool
    explanation: str
    official_sources: List[str]
    red_flags: List[str]
    recommended_next_step: str


class DashboardSummary(BaseModel):
    leads_total: int
    leads_new: int
    leads_human_review: int
    leads_converted: int
    truth_queue_pending: int
    truth_queue_resolved: int
    recent_leads: List[LeadRead]
    recent_truth_audits: List["TruthClaimRead"]

class TruthClaimRead(BaseModel):
    id: UUID
    lead_id: Optional[UUID]
    workflow_run_id: Optional[UUID]
    claim: str
    domain: str
    country: Optional[str]
    verdict: VerificationStatus
    confidence: float
    requires_human_review: bool
    explanation: str
    red_flags_json: Optional[str]
    recommended_next_step: Optional[str]
    created_at: datetime

class SourceReferenceRead(BaseModel):
    id: UUID
    truth_claim_id: Optional[UUID]
    source_url: str
    source_type: str
    title: Optional[str]
    country: Optional[str]
    retrieved_at: datetime

class EducationProfile(BaseModel):
    lead_id: Optional[UUID] = None
    highest_qualification: Optional[str] = None
    field_of_study: Optional[str] = None
    target_country: Optional[str] = None
    budget_eur: Optional[float] = None
    english_test_score: Optional[str] = None

class RecommendationResponse(BaseModel):
    domain: str
    summary: str
    confidence: float
    risks: List[str]
    next_actions: List[str]
    requires_truth_check: bool = True

class JobProfile(BaseModel):
    lead_id: Optional[UUID] = None
    role: str
    years_experience: Optional[float] = None
    skills: List[str] = []
    target_country: Optional[str] = None
    visa_status: Optional[str] = None

class ProfileCreate(BaseModel):
    lead_id: UUID
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

class ProfileRead(ProfileCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class EducationEntry(BaseModel):
    qualification: str = Field(min_length=1, max_length=200)
    field_of_study: Optional[str] = Field(default=None, max_length=200)
    institution: Optional[str] = Field(default=None, max_length=250)
    country: Optional[str] = Field(default=None, max_length=100)
    completion_year: Optional[int] = Field(default=None, ge=1900, le=2200)


class EmploymentEntry(BaseModel):
    role: str = Field(min_length=1, max_length=200)
    employer: Optional[str] = Field(default=None, max_length=250)
    country: Optional[str] = Field(default=None, max_length=100)
    years: float = Field(default=0, ge=0, le=80)
    current: bool = False


class LanguageAbility(BaseModel):
    language: str = Field(min_length=1, max_length=100)
    level: Optional[str] = Field(default=None, max_length=100)
    test_name: Optional[str] = Field(default=None, max_length=100)
    test_score: Optional[str] = Field(default=None, max_length=100)


class MobilityGoal(BaseModel):
    domain: Literal["study", "work", "visa", "settlement", "family", "business"]
    target_country: str = Field(min_length=2, max_length=100)
    desired_role_or_program: Optional[str] = Field(default=None, max_length=250)
    target_date: Optional[datetime] = None
    priority: Literal["low", "medium", "high"] = "medium"


class UniversalMobilityProfileUpsert(BaseModel):
    current_country: Optional[str] = Field(default=None, max_length=100)
    education: List[EducationEntry] = Field(default_factory=list)
    employment: List[EmploymentEntry] = Field(default_factory=list)
    years_experience: Optional[float] = Field(default=None, ge=0, le=80)
    skills: List[str] = Field(default_factory=list)
    languages: List[LanguageAbility] = Field(default_factory=list)
    family_status: Literal["unknown", "single", "partnered", "dependants"] = "unknown"
    family: List[dict[str, Any]] = Field(default_factory=list)
    family_details_confirmed: bool = False
    finances: dict[str, Any] = Field(default_factory=dict)
    goals: List[MobilityGoal] = Field(default_factory=list)
    constraints: List[dict[str, Any]] = Field(default_factory=list)
    constraints_confirmed: bool = False
    consent_status: Literal["not_recorded", "granted", "withdrawn"] = "not_recorded"
    consent_purposes: List[str] = Field(default_factory=list)
    consent_expires_at: Optional[datetime] = None
    evidence_document_ids: List[UUID] = Field(default_factory=list)


class UniversalMobilityProfileRead(BaseModel):
    id: UUID
    lead_id: UUID
    profile_version: int
    lifecycle_status: str
    supersedes_profile_id: Optional[UUID] = None
    current_country: Optional[str] = None
    education: List[dict[str, Any]] = Field(default_factory=list)
    employment: List[dict[str, Any]] = Field(default_factory=list)
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    languages: List[dict[str, Any]] = Field(default_factory=list)
    family: dict[str, Any] = Field(default_factory=dict)
    finances: dict[str, Any] = Field(default_factory=dict)
    goals: List[dict[str, Any]] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    consent: dict[str, Any] = Field(default_factory=dict)
    evidence_document_ids: List[UUID] = Field(default_factory=list)
    completeness_score: float
    readiness_stage: str
    consent_status: str
    missing_sections: List[str] = Field(default_factory=list)
    activated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DocumentCreate(BaseModel):
    lead_id: Optional[UUID] = None
    document_type: str
    filename: str
    storage_key: Optional[str] = None

class DocumentRead(BaseModel):
    id: UUID
    lead_id: Optional[UUID]
    document_type: str
    filename: str
    storage_provider: Optional[str] = None
    storage_reference_present: bool = False
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    uploaded_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    signed_access_supported: bool = False
    storage_key_exposed: bool = False

class HumanReviewRead(BaseModel):
    id: UUID
    lead_id: Optional[UUID]
    truth_claim_id: Optional[UUID]
    workflow_run_id: Optional[UUID]
    review_type: str
    status: ReviewStatus
    priority: str
    reason: str
    reviewer_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class HumanReviewUpdate(BaseModel):
    status: Optional[ReviewStatus] = None
    reviewer_notes: Optional[str] = None

class FollowUpRead(BaseModel):
    id: UUID
    lead_id: UUID
    workflow_run_id: Optional[UUID]
    channel: str
    status: FollowUpStatus
    due_at: Optional[datetime]
    message: str
    created_at: datetime
    updated_at: datetime

class FollowUpUpdate(BaseModel):
    status: Optional[FollowUpStatus] = None
    message: Optional[str] = None
    due_at: Optional[datetime] = None

class WorkflowRunRead(BaseModel):
    id: UUID
    workflow_name: str
    lead_id: Optional[UUID]
    status: WorkflowStatus
    detected_intent: LeadIntent
    route: Optional[str]
    input_json: Optional[str]
    output_json: Optional[str]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

class AgentRunRead(BaseModel):
    id: UUID
    workflow_run_id: Optional[UUID]
    lead_id: Optional[UUID]
    agent_name: str
    task: str
    status: AgentRunStatus
    input_json: Optional[str]
    output_json: Optional[str]
    created_at: datetime

class LeadIntakeWorkflowRequest(BaseModel):
    full_name: str = Field(..., examples=["Sample Lead"])
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: str = "web_form"
    intent: LeadIntent = LeadIntent.unknown
    target_country: Optional[str] = None
    claim: Optional[str] = None
    notes: Optional[str] = None
    profile: dict[str, Any] = {}

class LeadIntakeWorkflowResponse(BaseModel):
    workflow_run_id: UUID
    lead_id: UUID
    profile_id: UUID
    detected_intent: LeadIntent
    route: str
    truth_claim_id: Optional[UUID]
    human_review_id: Optional[UUID]
    follow_up_id: Optional[UUID]
    status: WorkflowStatus
    next_actions: List[str]

class AgentRunRequest(BaseModel):
    agent_name: str
    task: str
    context: dict[str, Any] = Field(default_factory=dict)

class AgentRunResponse(BaseModel):
    agent_name: str
    status: str
    output: dict
    message: str = "Agent run completed."
    created_at: datetime = Field(default_factory=now_utc)

class ControlledAgentRunRequest(BaseModel):
    agent_name: str
    task: str
    lead_id: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None
    context: dict[str, Any] = Field(default_factory=dict)
    actor: str = "system"

class ControlledAgentRunResponse(BaseModel):
    run_id: UUID
    agent_name: str
    status: str
    output: dict[str, Any]
    guardrails: list[str]
    requires_human_review: bool
    persisted: bool = True
    message: str
    created_at: datetime


class ControlledAgentRunBatchRequest(BaseModel):
    agent_name: str
    lead_ids: List[UUID]
    task_template: str = "Execute agent task for lead."
    context_per_lead: dict[str, dict[str, Any]] = Field(default_factory=dict)
    actor: str = "system"


class ControlledAgentRunBatchResponse(BaseModel):
    batch_id: UUID
    agent_name: str
    queued: int
    run_ids: List[UUID]


class AgentRunBatchReviewRequest(BaseModel):
    run_ids: List[UUID]
    actor: str = "operator"
    note: Optional[str] = None


class InhouseConsultantDecision(BaseModel):
    decision: Literal["propose_action", "ask_clarification", "wait_for_human"]
    agent_name: Optional[str] = None
    lead_id: Optional[UUID] = None
    task_template: Optional[str] = None
    summary: Optional[str] = None
    clarification_question: Optional[str] = None
    escalation_reason: Optional[str] = None
    confidence: Literal["high", "medium", "low"] = "medium"


class AgentChatRequest(BaseModel):
    message: str
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    lead_hint: Optional[str] = None


class AgentChatResponse(BaseModel):
    decision: InhouseConsultantDecision
    reply: str


class AgentRunAuditEntry(BaseModel):
    id: UUID
    action: str
    actor: str
    created_at: datetime
    reason: Optional[str] = None


class AgentRunDetailResponse(BaseModel):
    run: AgentRunRead
    audit_history: List[AgentRunAuditEntry]
    latest_review_note: Optional[str] = None


class PublicIntakeCreate(BaseModel):
    full_name: str = Field(..., examples=["Aisha Patel"])
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    goal: str = Field(..., examples=["Work in Germany as a nurse"])
    nationality: str = Field(..., examples=["India"])
    profession: str = Field(..., examples=["Registered Nurse"])
    years_experience: Optional[float] = None
    target_country: str = Field(..., examples=["Germany"])
    notes: Optional[str] = None


class PublicIntakeResponse(BaseModel):
    session_token: str
    lead_id: Optional[UUID] = None
    status: LeadStatus
    checklist: List[str] = []
    message: str


class CoachReviewCreate(BaseModel):
    lead_id: Optional[UUID] = None
    agent_run_id: Optional[UUID] = None
    target_agent_name: str
    conclusion_valid: bool = False
    missing_facts: List[str] = []
    source_issues: List[str] = []
    corrected_summary: Optional[str] = None
    confidence: CoachConfidence = CoachConfidence.medium


class CoachReviewRead(BaseModel):
    id: UUID
    lead_id: Optional[UUID]
    agent_run_id: Optional[UUID]
    coach_agent_name: str
    target_agent_name: str
    conclusion_valid: bool
    missing_facts_json: Optional[str]
    source_issues_json: Optional[str]
    corrected_summary: Optional[str]
    confidence: CoachConfidence
    operator_feedback: Optional[str]
    operator_override_json: Optional[str]
    status: CoachReviewStatus
    created_at: datetime
    updated_at: datetime


class CoachReviewFeedback(BaseModel):
    operator_feedback: str
    override_decision: Optional[CoachReviewStatus] = None


class TrainingCaseCreate(BaseModel):
    title: str
    country: str
    profession: str
    scenario: dict[str, Any] = Field(default_factory=dict)
    expected_outcome: dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"


class TrainingCaseRead(BaseModel):
    id: UUID
    lead_id: Optional[UUID]
    title: str
    country: str
    profession: str
    scenario_json: Optional[str]
    expected_outcome_json: Optional[str]
    source: str
    times_run: int
    avg_score: Optional[float]
    created_at: datetime
    updated_at: datetime


class TrainingCaseGenerateRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=50)
    country: Optional[str] = None
    profession: Optional[str] = None


class IntakeSessionRead(BaseModel):
    id: UUID
    lead_id: Optional[UUID]
    session_token: str
    status: IntakeSessionStatus
    source: str
    answers_json: Optional[str]
    created_at: datetime
    updated_at: datetime


class DocumentOcrExtractRequest(BaseModel):
    lead_id: UUID
    document_type: str
    filename: str
    extracted_text: str
    language: str = "eng"
    confidence: Optional[float] = None


class DocumentOcrExtractResponse(BaseModel):
    document_id: UUID
    document_type: str
    extracted_text: str
    parsed_fields: dict[str, Any]
    message: str


class DocumentExtractionRequest(BaseModel):
    language: str = Field(default="eng", min_length=3, max_length=32, pattern=r"^[a-zA-Z_+\-]+$")


class DocumentExtractionReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=3, max_length=2000)


class DocumentSchemaDefinitionRead(BaseModel):
    id: UUID
    schema_key: str
    document_type: str
    version_number: int
    lifecycle_status: str
    supersedes_schema_id: Optional[UUID] = None
    json_schema: dict[str, Any]
    extraction_rules: dict[str, Any]
    human_review_required: bool
    approved_by: Optional[str] = None
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class DocumentExtractionJobRead(BaseModel):
    id: UUID
    document_id: UUID
    lead_id: Optional[UUID] = None
    schema_definition_id: UUID
    schema_version: int
    schema_key: str
    document_type: str
    status: str
    engine: str
    language: str
    task_id: Optional[str] = None
    attempt_count: int
    input_file_hash: Optional[str] = None
    extracted_text: Optional[str] = None
    structured_data: dict[str, Any] = Field(default_factory=dict)
    field_confidence: dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    requested_by: str
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentConsistencyGenerateRequest(BaseModel):
    application_id: Optional[UUID] = None


class DocumentConsistencyReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=3, max_length=2000)


class DocumentConsistencyFinding(BaseModel):
    finding_key: str
    document_field: str
    source: Literal["lead", "profile", "application", "system"]
    source_path: str
    outcome: Literal["match", "mismatch", "missing_document_value", "missing_source_value", "not_comparable"]
    severity: Literal["info", "warning", "high"]
    extracted_value: Any = None
    source_value: Any = None
    explanation: str


class DocumentConsistencyAssessmentRead(BaseModel):
    id: UUID
    extraction_job_id: UUID
    document_id: UUID
    lead_id: UUID
    profile_id: UUID
    profile_version: int
    application_id: Optional[UUID] = None
    result_status: str
    review_status: str
    match_count: int
    mismatch_count: int
    missing_count: int
    findings: List[DocumentConsistencyFinding] = Field(default_factory=list)
    source_facts: dict[str, Any] = Field(default_factory=dict)
    summary: str
    human_review_required: bool
    generated_by: str
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentExpiryScanRequest(BaseModel):
    lead_id: Optional[UUID] = None


class DocumentExpiryScanResult(BaseModel):
    as_of: datetime
    lead_id: Optional[UUID] = None
    documents_scanned: int
    created: int
    existing: int
    superseded: int
    outside_window: int
    reminder_ids: List[str] = Field(default_factory=list)
    external_messages_sent: int = 0


class DocumentExpiryReminderReviewRequest(BaseModel):
    decision: Literal["acknowledged", "dismissed", "resolved"]
    notes: str = Field(min_length=3, max_length=2000)


class DocumentExpiryReminderRead(BaseModel):
    id: UUID
    reminder_key: str
    document_id: UUID
    lead_id: Optional[UUID] = None
    document_type: str
    filename: str
    expiry_date: datetime
    reminder_type: str
    threshold_days: int
    due_at: datetime
    status: str
    priority: str
    source: str
    human_review_required: bool
    external_delivery_status: str
    external_message_sent: bool = False
    generated_by: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    superseded_by_id: Optional[UUID] = None
    days_until_expiry: int
    created_at: datetime
    updated_at: datetime


class DocumentRequirementAssessmentGenerateRequest(BaseModel):
    lead_id: UUID
    application_id: Optional[UUID] = None
    pathway_version_id: Optional[UUID] = None


class DocumentRequirementAssessmentReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=3, max_length=2000)


class DocumentRequirementScanRequest(BaseModel):
    lead_id: Optional[UUID] = None


class DocumentRequirementScanResult(BaseModel):
    lead_id: Optional[UUID] = None
    leads_scanned: int
    created: int
    existing: int
    skipped: int
    assessment_ids: List[str] = Field(default_factory=list)
    documents_created: int = 0
    external_messages_sent: int = 0


class DocumentRequirementFinding(BaseModel):
    finding_key: str
    finding_type: Literal["requirement_coverage", "cross_document_inconsistency"]
    requirement_key: str
    requirement_label: str
    expected_document_types: List[str] = Field(default_factory=list)
    optional: bool = False
    outcome: Literal[
        "satisfied",
        "missing",
        "optional_missing",
        "rejected",
        "expired",
        "present_unverified",
        "fact_inconsistency",
        "duplicate_conflict",
    ]
    severity: Literal["info", "warning", "high"]
    document_ids: List[UUID] = Field(default_factory=list)
    document_names: List[str] = Field(default_factory=list)
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class DocumentRequirementAssessmentRead(BaseModel):
    id: UUID
    assessment_key: str
    lead_id: UUID
    application_id: Optional[UUID] = None
    pathway_id: Optional[UUID] = None
    pathway_version_id: Optional[UUID] = None
    eligibility_assessment_id: Optional[UUID] = None
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    requirement_source: str
    result_status: str
    review_status: str
    required_count: int
    satisfied_count: int
    missing_count: int
    inconsistency_count: int
    requirements: List[dict[str, Any]] = Field(default_factory=list)
    findings: List[DocumentRequirementFinding] = Field(default_factory=list)
    source_snapshot: dict[str, Any] = Field(default_factory=dict)
    document_snapshot: List[dict[str, Any]] = Field(default_factory=list)
    summary: str
    human_review_required: bool
    generated_by: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    source_records_unchanged: bool = True
    documents_created: int = 0
    eligibility_changed: bool = False
    created_at: datetime
    updated_at: datetime


class DocumentFraudRiskAssessmentGenerateRequest(BaseModel):
    lead_id: UUID


class DocumentFraudRiskAssessmentReviewRequest(BaseModel):
    decision: Literal["cleared", "specialist_review_required", "dismissed"]
    notes: str = Field(min_length=3, max_length=2000)


class DocumentFraudRiskScanRequest(BaseModel):
    lead_id: Optional[UUID] = None


class DocumentFraudRiskScanResult(BaseModel):
    lead_id: Optional[UUID] = None
    leads_scanned: int
    created: int
    existing: int
    skipped: int
    assessment_ids: List[str] = Field(default_factory=list)
    fraud_determinations: int = 0
    documents_rejected: int = 0
    eligibility_changed: bool = False
    external_actions_triggered: int = 0


class DocumentFraudRiskIndicator(BaseModel):
    indicator_key: str
    indicator_type: Literal[
        "exact_file_reuse_across_leads",
        "same_file_multiple_document_types",
        "approved_identity_mismatch",
        "approved_material_fact_mismatch",
        "conflicting_duplicate_evidence",
        "approved_cross_document_inconsistency",
        "rejected_or_invalid_evidence",
        "extraction_integrity_failure",
        "approved_identifier_reuse_across_leads",
    ]
    severity: Literal["warning", "high"]
    document_ids: List[UUID] = Field(default_factory=list)
    document_names: List[str] = Field(default_factory=list)
    source_record_type: str
    source_record_ids: List[str] = Field(default_factory=list)
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    human_review_required: bool = True


class DocumentFraudRiskAssessmentRead(BaseModel):
    id: UUID
    assessment_key: str
    lead_id: UUID
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    application_id: Optional[UUID] = None
    result_status: str
    review_status: str
    risk_band: str
    indicator_count: int
    high_indicator_count: int
    warning_indicator_count: int
    indicators: List[DocumentFraudRiskIndicator] = Field(default_factory=list)
    source_snapshot: dict[str, Any] = Field(default_factory=dict)
    summary: str
    human_review_required: bool
    automated_fraud_determination: bool
    adverse_action_taken: bool
    generated_by: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    fraud_determined: bool = False
    documents_rejected: int = 0
    eligibility_changed: bool = False
    external_actions_triggered: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentAccessGrantCreateRequest(BaseModel):
    lead_id: UUID
    purpose: Literal[
        "operator_review",
        "document_verification",
        "consistency_review",
        "application_preparation",
        "client_request_fulfilment",
        "legal_compliance_export",
    ] = "operator_review"
    ttl_seconds: Optional[int] = Field(default=None, ge=30, le=900)
    max_uses: Optional[int] = Field(default=None, ge=1, le=5)
    recipient_username: Optional[str] = Field(default=None, min_length=1, max_length=200)
    recipient_role: Optional[Literal["admin", "operator", "reviewer", "sales", "read_only"]] = None


class DocumentAccessGrantRead(BaseModel):
    id: UUID
    document_id: UUID
    lead_id: UUID
    issued_to: str
    issued_role: str
    purpose: str
    status: str
    expires_at: datetime
    max_uses: int
    use_count: int
    remaining_uses: int
    storage_provider: str
    filename: str
    created_by: str
    last_accessed_by: Optional[str] = None
    last_accessed_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expired: bool
    token_returned: bool = False
    storage_key_exposed: bool = False


class DocumentAccessGrantIssued(BaseModel):
    grant: DocumentAccessGrantRead
    token: str
    token_type: Literal["gmai_document_access"] = "gmai_document_access"
    direct_object_url: Optional[str] = None
    storage_credentials_exposed: bool = False
    storage_key_exposed: bool = False


class DocumentAccessTokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=4096)


class DocumentAccessGrantRevokeRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class DocumentAccessExpiryResult(BaseModel):
    expired: int
    grant_ids: List[str] = Field(default_factory=list)
    external_messages_sent: int = 0


class DocumentStoragePostureRead(BaseModel):
    environment: str
    backend: str
    strict_mode: bool
    signed_access_secret_configured: bool
    signed_access_ttl_seconds: int
    signed_access_max_ttl_seconds: int
    minio_tls_enabled: bool
    minio_default_credentials: bool
    bucket_auto_create: bool
    server_side_encryption_enabled: bool
    retention_days: int
    backup_strategy_configured: bool
    recovery_test_recorded: bool
    local_storage_allowed_in_production: bool
    failures: List[str] = Field(default_factory=list)
    ready: bool
    signed_access_enabled: bool
    direct_object_urls_enabled: bool
    storage_credentials_exposed: bool
    unrestricted_object_keys_exposed: bool
    allowed_purposes: List[str] = Field(default_factory=list)


class EligibilityEvaluateRequest(BaseModel):
    lead_id: UUID
    profile: dict[str, Any] = Field(default_factory=dict)
    actor: str = "system"


class EligibilityAssessmentRead(BaseModel):
    id: UUID
    lead_id: UUID
    agent_run_id: Optional[UUID] = None
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    target_country: Optional[str] = None
    domain: str = "general"
    overall_score: float
    confidence: float
    status: str
    summary: Optional[str] = None
    risks: List[str] = []
    required_documents: List[str] = []
    pathways: List[str] = []
    factors: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, assessment: Any) -> "EligibilityAssessmentRead":
        import json

        def _load(value: str | None) -> list[str]:
            if not value:
                return []
            try:
                data = json.loads(value)
                return data if isinstance(data, list) else []
            except Exception:
                return []

        def _load_dict(value: str | None) -> dict[str, Any]:
            if not value:
                return {}
            try:
                data = json.loads(value)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}

        return cls(
            id=assessment.id,
            lead_id=assessment.lead_id,
            agent_run_id=assessment.agent_run_id,
            profile_id=assessment.profile_id,
            profile_version=assessment.profile_version,
            target_country=assessment.target_country,
            domain=assessment.domain,
            overall_score=assessment.overall_score,
            confidence=assessment.confidence,
            status=assessment.status,
            summary=assessment.summary,
            risks=_load(assessment.risks_json),
            required_documents=_load(assessment.required_documents_json),
            pathways=_load(assessment.pathways_json),
            factors=_load_dict(assessment.assessment_json).get("factors", {}),
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )


class ClientLookupRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    session_token: Optional[str] = None


class ClientLookupResult(BaseModel):
    lead_id: UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    target_country: Optional[str] = None
    status: str
    updated_at: datetime


class ClientDashboardDocument(BaseModel):
    id: UUID
    document_type: str
    filename: str
    status: str
    uploaded_at: Optional[datetime] = None


class ClientDashboardFollowUp(BaseModel):
    id: UUID
    channel: str
    status: str
    message: str
    due_at: Optional[datetime] = None


class ClientReturnDashboard(BaseModel):
    lead_id: UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    target_country: Optional[str] = None
    status: str
    intent: str
    checklist: List[str] = []
    session_token: Optional[str] = None
    eligibility: Optional[EligibilityAssessmentRead] = None
    documents: List[ClientDashboardDocument] = []
    follow_ups: List[ClientDashboardFollowUp] = []
    application_stage: Optional[str] = None
    next_action: str
    updated_at: datetime


class OpportunityCreate(BaseModel):
    title: str
    organization: Optional[str] = None
    country: str
    domain: str = "work"
    profession_tags: List[str] = []
    field_tags: List[str] = []
    required_years_experience: Optional[float] = None
    language_requirement: Optional[str] = None
    salary_eur: Optional[float] = None
    budget_eur: Optional[float] = None
    description: Optional[str] = None
    source: str = "manual"
    active: bool = True


class OpportunityRead(BaseModel):
    id: UUID
    title: str
    organization: Optional[str] = None
    country: str
    domain: str
    profession_tags: List[str] = []
    field_tags: List[str] = []
    required_years_experience: Optional[float] = None
    language_requirement: Optional[str] = None
    salary_eur: Optional[float] = None
    budget_eur: Optional[float] = None
    description: Optional[str] = None
    source: str
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, opp: Any) -> "OpportunityRead":
        import json

        def _load(value: str | None) -> list[str]:
            if not value:
                return []
            try:
                data = json.loads(value)
                return data if isinstance(data, list) else []
            except Exception:
                return []

        return cls(
            id=opp.id,
            title=opp.title,
            organization=opp.organization,
            country=opp.country,
            domain=opp.domain,
            profession_tags=_load(opp.profession_tags_json),
            field_tags=_load(opp.field_tags_json),
            required_years_experience=opp.required_years_experience,
            language_requirement=opp.language_requirement,
            salary_eur=opp.salary_eur,
            budget_eur=opp.budget_eur,
            description=opp.description,
            source=opp.source,
            active=opp.active,
            created_at=opp.created_at,
            updated_at=opp.updated_at,
        )


class OpportunityMatchResult(BaseModel):
    opportunity: OpportunityRead
    match_score: float
    confidence: float
    reasons: List[str]
    risks: List[str]


class OpportunityMatchResponse(BaseModel):
    lead_id: UUID
    matches: List[OpportunityMatchResult]
    top_opportunity_id: Optional[UUID] = None
    summary: str
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    profile_completeness: Optional[float] = None


PathwayDomain = Literal[
    "study",
    "work",
    "visa",
    "scholarship",
    "settlement",
    "family",
    "digital_nomad",
    "business",
    "entrepreneur",
    "startup",
    "investment",
    "wealth",
    "tax",
    "corporate",
]


class PathwayVersionEvidenceInput(BaseModel):
    evidence_role: str = Field(
        min_length=3,
        max_length=80,
        pattern=r"^[a-z0-9][a-z0-9_-]+$",
    )
    official_source_id: UUID
    source_snapshot_id: UUID
    required_for_publication: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class PathwayVersionInput(BaseModel):
    official_source_id: Optional[UUID] = None
    source_snapshot_id: Optional[UUID] = None
    evidence_links: List[PathwayVersionEvidenceInput] = Field(default_factory=list)
    verified_rule_ids: List[UUID] = Field(default_factory=list)
    eligibility_criteria: dict[str, Any] = Field(default_factory=dict)
    required_documents: List[str] = Field(default_factory=list)
    costs: dict[str, Any] = Field(default_factory=dict)
    processing_time: dict[str, Any] = Field(default_factory=dict)
    benefits: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class PathwayCreate(PathwayVersionInput):
    pathway_key: str = Field(min_length=3, max_length=160, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    name: str = Field(min_length=3, max_length=250)
    country: str = Field(min_length=2, max_length=100)
    domain: PathwayDomain
    jurisdiction_id: Optional[UUID] = None
    description: Optional[str] = Field(default=None, max_length=2000)


class PathwayPublishRequest(BaseModel):
    review_notes: str = Field(min_length=3, max_length=2000)


class PathwayRetireRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class PathwayRegulatoryImpactReviewRequest(BaseModel):
    decision: Literal[
        "acknowledged",
        "no_change_required",
        "new_version_required",
        "resolved",
    ]
    notes: str = Field(min_length=3, max_length=5000)
    replacement_pathway_version_id: Optional[UUID] = None


class PathwayRegulatoryImpactRead(BaseModel):
    id: UUID
    impact_type: str
    status: str
    materiality: str
    event_at: datetime
    pathway_id: UUID
    pathway_key: str
    pathway_name: str
    pathway_country: str
    pathway_domain: str
    pathway_version_id: UUID
    pathway_version_number: int
    pathway_version_lifecycle_status: str
    verified_rule_id: UUID
    rule_key: str
    rule_active: bool
    superseded_rule_id: Optional[UUID] = None
    regulatory_change_id: UUID
    change_type: str
    source_snapshot_id: UUID
    graph_rule_node_id: Optional[UUID] = None
    graph_projection_version: str
    match_basis: List[str] = Field(default_factory=list)
    impact_context: dict[str, Any] = Field(default_factory=dict)
    client_assessment_count_at_detection: int
    timeline_count_at_detection: int
    client_assessments_unchanged: bool = True
    human_review_required: bool
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    replacement_pathway_version_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class PathwayRegulatoryImpactList(BaseModel):
    total_returned: int
    counts_by_status: dict[str, int] = Field(default_factory=dict)
    pending_review: int
    client_assessments_unchanged: bool = True
    impacts: List[PathwayRegulatoryImpactRead] = Field(default_factory=list)


class PathwayVersionEvidenceRead(BaseModel):
    id: UUID
    pathway_version_id: UUID
    evidence_role: str
    official_source_id: UUID
    source_snapshot_id: UUID
    required_for_publication: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PathwayVersionRead(BaseModel):
    id: UUID
    pathway_id: UUID
    version_number: int
    lifecycle_status: str
    supersedes_version_id: Optional[UUID] = None
    official_source_id: Optional[UUID] = None
    source_snapshot_id: Optional[UUID] = None
    evidence_links: List[PathwayVersionEvidenceRead] = Field(default_factory=list)
    verified_rule_ids: List[UUID] = Field(default_factory=list)
    eligibility_criteria: dict[str, Any] = Field(default_factory=dict)
    required_documents: List[str] = Field(default_factory=list)
    costs: dict[str, Any] = Field(default_factory=dict)
    processing_time: dict[str, Any] = Field(default_factory=dict)
    benefits: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    human_review_required: bool
    approved_by: Optional[str] = None
    review_notes: Optional[str] = None
    published_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class PathwayStructuredOccupationIntegrationRequest(BaseModel):
    source_version_id: UUID
    year: int = Field(ge=2000, le=2200)
    national_source_snapshot_id: UUID
    regional_source_snapshot_id: UUID
    expected_national_entry_count: int = Field(ge=1, le=500)
    expected_regional_entry_count: int = Field(ge=1, le=500)
    expected_national_entry_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_regional_entry_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_national_snapshot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_regional_snapshot_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class PathwayPublicationReadinessRead(BaseModel):
    pathway_id: UUID
    pathway_version_id: UUID
    lifecycle_status: str
    ready: bool
    blockers: List[str] = Field(default_factory=list)
    requires_independent_reviewer: bool = True
    evidence_certification_statuses: dict[str, str] = Field(default_factory=dict)
    structured_occupation_evidence: dict[str, Any] = Field(default_factory=dict)


class PathwayStructuredOccupationIntegrationRead(BaseModel):
    created: bool
    pathway_version: PathwayVersionRead
    publication_readiness: PathwayPublicationReadinessRead


class PathwayRead(BaseModel):
    id: UUID
    pathway_key: str
    name: str
    country: str
    domain: str
    jurisdiction_id: Optional[UUID] = None
    description: Optional[str] = None
    catalogue_status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    current_version: Optional[PathwayVersionRead] = None


class PathwayDetail(PathwayRead):
    versions: List[PathwayVersionRead] = Field(default_factory=list)


class PathwayMatchItem(BaseModel):
    pathway: PathwayRead
    match_score: float
    confidence: float
    reasons: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    verified_rule_ids: List[UUID] = Field(default_factory=list)


class PathwayMatchResponse(BaseModel):
    lead_id: UUID
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    consent_status: str
    matches: List[PathwayMatchItem] = Field(default_factory=list)
    summary: str


class PathwayCostExplanation(BaseModel):
    currency: str = "EUR"
    one_time_total: Optional[float] = None
    monthly_total: Optional[float] = None
    annual_total: Optional[float] = None
    minimum_funds: Optional[float] = None
    components: dict[str, float] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class PathwayRiskExplanation(BaseModel):
    level: Literal["low", "medium", "high"]
    score: float
    declared_risks: List[str] = Field(default_factory=list)
    evidence_risks: List[str] = Field(default_factory=list)
    regulatory_risks: List[str] = Field(default_factory=list)


class PathwayComparisonItem(BaseModel):
    pathway: PathwayRead
    match_score: float
    confidence: float
    reasons: List[str] = Field(default_factory=list)
    cost: PathwayCostExplanation
    risk: PathwayRiskExplanation
    missing_evidence: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    explanation: str
    verified_rule_ids: List[UUID] = Field(default_factory=list)


class PathwayComparisonRead(BaseModel):
    assessment_id: Optional[UUID] = None
    lead_id: UUID
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    status: str
    consent_status: str
    primary: Optional[PathwayComparisonItem] = None
    alternatives: List[PathwayComparisonItem] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    summary: str
    human_review_required: bool = True
    generated_by: str
    generated_at: datetime


class CountryRankingCreate(BaseModel):
    explicit_user_acceptance: bool = True
    user_attestation: str = Field(min_length=10, max_length=2000)
    notes: str = Field(min_length=3, max_length=4000)
    limit_countries: int = Field(default=20, ge=1, le=100)


class CountryLongTermDependencyRead(BaseModel):
    stage: Literal["permanent_residence", "citizenship"]
    status: Literal["recorded", "not_recorded", "not_applicable"]
    summary: str
    minimum_years: Optional[float] = None
    dependencies: List[str] = Field(default_factory=list)
    pathway_version_id: Optional[UUID] = None
    verified_rule_ids: List[UUID] = Field(default_factory=list)
    human_reviewed_source: bool = False


class CountryRankingUncertaintyRead(BaseModel):
    level: Literal["low", "medium", "high"]
    score: float
    factors: List[str] = Field(default_factory=list)
    global_coverage_boundary: bool = True


class CountryRankingScopeRead(BaseModel):
    ranking_scope: Literal["complete_global_catalogue", "reviewed_published_catalogue_only"]
    global_coverage_claim_ready: bool
    complete_global_ranking_claim_allowed: bool
    registry_release_version: Optional[str] = None
    registry_entries: int = 0
    coverage_required: int = 0
    coverage_ready: int = 0
    published_catalogue_countries: int = 0
    published_pathway_versions: int = 0
    message: str


class CountryRankingItemRead(BaseModel):
    rank: int
    country: str
    ranking_score: float
    profile_match_score: float
    confidence: float
    reviewed_coverage_ready: bool
    pathway_count: int
    primary_pathway: PathwayComparisonItem
    alternative_pathways: List[PathwayComparisonItem] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    long_term_dependencies: List[CountryLongTermDependencyRead] = Field(default_factory=list)
    uncertainty: CountryRankingUncertaintyRead
    explanation: str


class CountryRankingRead(BaseModel):
    assessment_id: Optional[UUID] = None
    lead_id: UUID
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    status: str
    consent_status: str
    scope: CountryRankingScopeRead
    countries: List[CountryRankingItemRead] = Field(default_factory=list)
    explicit_user_acceptance: bool = True
    user_attestation: str
    notes: str
    summary: str
    human_review_required: bool = True
    generated_by: str
    generated_at: datetime


class ReassessmentRegulatoryChangeRead(BaseModel):
    impact_id: UUID
    pathway_id: UUID
    pathway_name: str
    affected_pathway_version_id: UUID
    affected_pathway_version_number: int
    replacement_pathway_version_id: UUID
    replacement_pathway_version_number: int
    verified_rule_id: UUID
    materiality: str
    reviewed_by: str
    reviewed_at: datetime
    review_notes: str


class ReassessmentCandidateRead(BaseModel):
    lead_id: UUID
    baseline_assessment_id: UUID
    baseline_profile_id: Optional[UUID] = None
    baseline_profile_version: Optional[int] = None
    current_profile_id: Optional[UUID] = None
    current_profile_version: Optional[int] = None
    profile_update_available: bool
    regulatory_changes: List[ReassessmentRegulatoryChangeRead] = Field(default_factory=list)
    requires_acceptance: bool
    pinned_assessment_unchanged: bool = True
    summary: str


class ReassessmentAcceptanceCreate(BaseModel):
    baseline_assessment_id: UUID
    accept_profile_version: bool = False
    regulatory_impact_ids: List[UUID] = Field(default_factory=list)
    explicit_user_acceptance: bool
    user_attestation: str = Field(min_length=10, max_length=2000)
    notes: str = Field(min_length=3, max_length=5000)


class ReassessmentAcceptanceRead(BaseModel):
    id: UUID
    lead_id: UUID
    baseline_assessment_id: UUID
    accepted_profile_id: Optional[UUID] = None
    accepted_profile_version: Optional[int] = None
    regulatory_impact_ids: List[UUID] = Field(default_factory=list)
    accepted_pathway_version_ids: List[UUID] = Field(default_factory=list)
    explicit_user_acceptance: bool
    user_attestation: str
    notes: str
    status: str
    recorded_by: str
    accepted_at: datetime
    consumed_at: Optional[datetime] = None
    generated_assessment_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class MobilityTimelineGenerateRequest(BaseModel):
    target_date: Optional[datetime] = None


class MobilityTimelineTransitionRequest(BaseModel):
    action: Literal["start", "complete", "block", "unblock"]
    note: Optional[str] = Field(default=None, max_length=2000)


class MobilityTimelineMilestoneRead(BaseModel):
    id: UUID
    timeline_id: UUID
    stage_order: int
    stage_key: str
    title: str
    description: Optional[str] = None
    status: str
    dependencies: List[str] = Field(default_factory=list)
    required_evidence: List[str] = Field(default_factory=list)
    owner_role: str
    due_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    blockers: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    requires_human_approval: bool
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MobilityTimelineRead(BaseModel):
    id: UUID
    lead_id: UUID
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    comparison_assessment_id: UUID
    primary_pathway_id: UUID
    primary_pathway_version_id: UUID
    title: str
    status: str
    current_stage_key: Optional[str] = None
    target_date: Optional[datetime] = None
    schedule: dict[str, Any] = Field(default_factory=dict)
    generated_by: str
    activated_by: Optional[str] = None
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    milestones: List[MobilityTimelineMilestoneRead] = Field(default_factory=list)


class MobilityScenarioStageCreate(BaseModel):
    stage_type: Literal[
        "study",
        "graduate_rights",
        "work_permit",
        "skilled_migration",
        "settlement",
        "permanent_residence",
        "citizenship_review",
    ]
    pathway_version_id: UUID
    duration_months: int = Field(ge=1, le=240)
    gap_months_before: int = Field(default=0, ge=0, le=120)
    title: Optional[str] = Field(default=None, min_length=3, max_length=250)


class MobilityScenarioCreate(BaseModel):
    lead_id: UUID
    title: str = Field(min_length=3, max_length=250)
    start_date: datetime
    baseline_timeline_id: Optional[UUID] = None
    stages: List[MobilityScenarioStageCreate] = Field(min_length=2, max_length=20)
    explicit_user_acceptance: bool
    user_attestation: str = Field(min_length=10, max_length=2000)
    review_notes: str = Field(min_length=3, max_length=5000)


class MobilityScenarioRecalculateRequest(BaseModel):
    regulatory_impact_ids: List[UUID] = Field(min_length=1, max_length=50)
    explicit_user_acceptance: bool
    user_attestation: str = Field(min_length=10, max_length=2000)
    review_notes: str = Field(min_length=3, max_length=5000)


class MobilityScenarioStageRead(BaseModel):
    id: UUID
    scenario_id: UUID
    stage_order: int
    stage_type: str
    title: str
    country: str
    domain: str
    pathway_id: UUID
    pathway_version_id: UUID
    planned_start: datetime
    planned_end: datetime
    duration_months: int
    gap_months_before: int
    dependencies: List[str] = Field(default_factory=list)
    verified_rule_ids: List[UUID] = Field(default_factory=list)
    source_snapshot_ids: List[UUID] = Field(default_factory=list)
    timing_basis: dict[str, Any] = Field(default_factory=dict)
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    human_confirmation_required: bool
    created_at: datetime


class MobilityScenarioRead(BaseModel):
    id: UUID
    lead_id: UUID
    profile_id: Optional[UUID] = None
    profile_version: Optional[int] = None
    baseline_timeline_id: Optional[UUID] = None
    scenario_version: int
    supersedes_scenario_id: Optional[UUID] = None
    title: str
    status: str
    start_date: datetime
    countries: List[str] = Field(default_factory=list)
    pathway_version_ids: List[UUID] = Field(default_factory=list)
    verified_rule_ids: List[UUID] = Field(default_factory=list)
    regulatory_impact_ids: List[UUID] = Field(default_factory=list)
    explicit_user_acceptance: bool
    user_attestation: str
    review_notes: str
    human_confirmation_required: bool
    original_scenario_preserved: bool
    global_coverage_claim_ready: bool
    warning: str
    reviewed_by: str
    reviewed_at: datetime
    created_at: datetime
    stages: List[MobilityScenarioStageRead] = Field(default_factory=list)


class MobilityScenarioImpactRead(BaseModel):
    impact_id: UUID
    pathway_version_id: UUID
    replacement_pathway_version_id: UUID
    impact_type: str
    materiality: str
    review_notes: Optional[str] = None
    affected_stage_orders: List[int] = Field(default_factory=list)
    event_at: datetime


class MobilityScenarioRecalculationCandidateRead(BaseModel):
    scenario_id: UUID
    scenario_version: int
    available: bool
    impacts: List[MobilityScenarioImpactRead] = Field(default_factory=list)
    message: str
    original_scenario_preserved: bool = True
    automatic_recalculation_performed: bool = False


class JurisdictionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    jurisdiction_type: Literal["country", "territory", "autonomous_jurisdiction"] = "country"
    parent_code: Optional[str] = None
    region: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegulatoryAuthorityCreate(BaseModel):
    jurisdiction_id: UUID
    name: str = Field(min_length=2, max_length=250)
    authority_type: str = "immigration_authority"
    website_url: Optional[str] = None
    domains: List[str] = Field(default_factory=lambda: ["visa"])
    official_source_ids: List[UUID] = Field(default_factory=list)


class RegulatorySourceAuthorityReassignmentRequest(BaseModel):
    target_regulatory_authority_id: UUID
    reason: str = Field(min_length=10, max_length=2000)


class SourceMonitorCreate(BaseModel):
    official_source_id: UUID
    schedule_minutes: int = Field(default=1440, ge=15, le=525600)
    fetch_method: Literal["http", "browser", "api", "manual"] = "http"
    allowed_domains: List[str] = Field(default_factory=list)
    max_redirects: int = Field(default=3, ge=0, le=10)
    parser_profile: Literal["generic", "gazette_html_v1", "structured_program_catalog_v1"] = "generic"
    parser_config: dict[str, Any] = Field(default_factory=dict)


class RegulatorySourceOnboardingRequest(BaseModel):
    jurisdiction_code: str = Field(min_length=2, max_length=32)
    jurisdiction_name: str = Field(min_length=2, max_length=200)
    jurisdiction_type: Literal["country", "territory", "autonomous_jurisdiction"] = "country"
    parent_code: Optional[str] = None
    region: Optional[str] = None
    authority_name: str = Field(min_length=2, max_length=250)
    authority_type: str = Field(default="immigration_authority", min_length=2, max_length=100)
    authority_website_url: Optional[str] = None
    authority_domains: List[str] = Field(default_factory=lambda: ["visa"])
    source_name: str = Field(min_length=2, max_length=250)
    source_url: str = Field(min_length=8, max_length=2000)
    source_domain: str = Field(default="visa", min_length=2, max_length=100)
    source_type: Literal[
        "government",
        "official",
        "official_portal",
        "official_agency",
        "gazette",
    ] = "official"
    schedule_minutes: int = Field(default=1440, ge=15, le=525600)
    fetch_method: Literal["http", "browser", "api", "manual"] = "http"
    allowed_domains: List[str] = Field(default_factory=list)
    max_redirects: int = Field(default=3, ge=0, le=10)
    parser_profile: Literal["generic", "gazette_html_v1", "structured_program_catalog_v1"] = "generic"
    parser_config: dict[str, Any] = Field(default_factory=dict)


ShortageOccupationScope = Literal["national", "regional"]


class ShortageOccupationMaterializeRequest(BaseModel):
    source_snapshot_id: UUID
    year: int = Field(ge=2000, le=2200)
    scope: ShortageOccupationScope
    expected_group_count: int = Field(ge=1, le=500)
    parser_profile: Literal["austria_migration_shortage_v1"] = "austria_migration_shortage_v1"


class ShortageOccupationEntryRead(BaseModel):
    id: UUID
    jurisdiction_id: UUID
    official_source_id: UUID
    source_snapshot_id: UUID
    source_snapshot_content_hash: Optional[str] = None
    source_url: Optional[str] = None
    year: int
    scope: ShortageOccupationScope
    source_ordinal: int
    occupation_group: str
    normalized_occupation_group: str
    occupation_aliases: List[str] = Field(default_factory=list)
    province_codes: List[str] = Field(default_factory=list)
    province_names: List[str] = Field(default_factory=list)
    extraction_version: str
    entry_sha256: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ShortageOccupationMaterializationRead(BaseModel):
    jurisdiction_id: UUID
    official_source_id: UUID
    source_snapshot_id: UUID
    source_snapshot_content_hash: Optional[str] = None
    year: int
    scope: ShortageOccupationScope
    extraction_version: str
    entry_set_sha256: str
    created_count: int
    existing_count: int
    entry_count: int
    entries: List[ShortageOccupationEntryRead] = Field(default_factory=list)


class ShortageOccupationLookupRead(BaseModel):
    jurisdiction_id: UUID
    year: int
    occupation: str
    normalized_occupation: str
    province_code: Optional[str] = None
    status: Literal[
        "matched",
        "not_found",
        "province_required",
        "not_applicable_in_province",
        "ambiguous",
    ]
    list_applicability: Optional[bool] = None
    governance_ready: bool = False
    certification_statuses: dict[str, str] = Field(default_factory=dict)
    match_count: int = 0
    matches: List[ShortageOccupationEntryRead] = Field(default_factory=list)
    warning: str


class SourceSnapshotCaptureRequest(BaseModel):
    content_text: str = Field(min_length=1)
    http_status: int = Field(default=200, ge=100, le=599)
    retrieval_method: Literal["http", "browser", "api", "manual"] = "manual"
    parser_version: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    change_type: Optional[Literal[
        "new_program",
        "rule_change",
        "program_removed",
        "processing_time_change",
        "salary_threshold_change",
        "investment_threshold_change",
        "age_limit_change",
        "occupation_list_change",
        "quota_change",
        "policy_change",
    ]] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    materiality: Literal["informational", "material", "critical"] = "material"
    effective_at: Optional[datetime] = None
    actor: str = "source-monitor"


class RegulatoryChangeReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(min_length=1)
    notes: str = Field(min_length=1)


class RegulatoryClassificationProposalGenerateRequest(BaseModel):
    use_model: bool = False
    actor: str = Field(default="regulatory-operator", min_length=1, max_length=200)


class RegulatoryClassificationProposalReviewRequest(BaseModel):
    decision: Literal["accepted", "rejected"]
    reviewer: str = Field(min_length=1, max_length=200)
    notes: str = Field(min_length=3, max_length=5000)


class RegulatoryKnowledgeGraphSyncRequest(BaseModel):
    actor: str = Field(default="regulatory-graph-operator", min_length=1, max_length=200)


class RegulatoryChangePublishRequest(BaseModel):
    rule_key: str = Field(min_length=2, max_length=200)
    statement: str = Field(min_length=5)
    reviewer: str = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    supersedes_rule_id: Optional[UUID] = None


class InitialRuleAssertionCreateRequest(BaseModel):
    alpha2_code: str = Field(min_length=2, max_length=2)
    domain: str = Field(default="visa", min_length=2, max_length=100)
    title: str = Field(min_length=5, max_length=300)
    rule_key: str = Field(min_length=2, max_length=200)
    statement: str = Field(min_length=10, max_length=10000)
    rationale: str = Field(min_length=10, max_length=5000)
    evidence_excerpt: str = Field(min_length=10, max_length=5000)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class InitialRuleAssertionReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=3, max_length=5000)


class InitialRuleAssertionPublishRequest(BaseModel):
    attestation: bool
    publication_notes: str = Field(min_length=3, max_length=5000)


class VerifiedRuleRetireRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    effective_to: Optional[datetime] = None


class JurisdictionImmigrationAssessmentProposal(BaseModel):
    rule_relationship: Literal[
        "independent",
        "parent_inherited",
        "shared_or_coordinated",
        "not_applicable",
        "unclear",
    ]
    parent_code: Optional[str] = Field(default=None, min_length=2, max_length=12)
    evidence_url: str = Field(min_length=8, max_length=2000)
    evidence_title: str = Field(min_length=3, max_length=300)
    rationale: str = Field(min_length=10, max_length=5000)
    official_source_id: Optional[UUID] = None
    source_snapshot_id: Optional[UUID] = None


class JurisdictionImmigrationAssessmentReview(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=3, max_length=5000)


class JurisdictionSourceCertificationProposal(BaseModel):
    regulatory_authority_id: UUID
    official_source_id: UUID
    certification_scope: str = Field(
        default="primary_immigration",
        pattern=r"^(primary_immigration|supplemental_[a-z0-9_]+)$",
        max_length=100,
    )
    coverage_domains: List[str] = Field(min_length=1)
    evidence_notes: str = Field(min_length=10, max_length=5000)


class JurisdictionSourceCertificationReview(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=3, max_length=5000)
    evidence_pack_sha256: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9a-fA-F]{64}$",
    )
    source_snapshot_id: Optional[UUID] = None
    independent_human_attestation: bool = False


class SourceCertificationReviewPackRead(BaseModel):
    pack_version: str
    evidence_pack_sha256: str
    certification_id: UUID
    certification_status: str
    proposed_by: str
    jurisdiction: dict[str, Any]
    regulatory_authority: dict[str, Any]
    official_source: dict[str, Any]
    source_snapshot: dict[str, Any]
    source_content_text: str
    structured_projection: dict[str, Any]
    structured_entries: List[dict[str, Any]] = Field(default_factory=list)
    review_checklist: List[str] = Field(default_factory=list)


class SourceCertificationReviewProjectionOption(BaseModel):
    source_snapshot_id: UUID
    year: int
    scope: str
    entry_count: int
    entry_set_sha256: str
    extraction_version: str
    source_snapshot_content_hash: str


class SourceCertificationReviewQueueItem(BaseModel):
    certification: dict[str, Any]
    jurisdiction: dict[str, Any]
    regulatory_authority: dict[str, Any]
    official_source: dict[str, Any]
    review_pack_state: Literal["ready", "snapshot_pin_required", "unavailable"]
    available_projections: List[SourceCertificationReviewProjectionOption] = Field(default_factory=list)
    evidence_pack_sha256: Optional[str] = None
    selected_source_snapshot_id: Optional[UUID] = None
    reviewer_identity_conflict: bool = False
    can_submit_review: bool = False


class SourceCertificationReviewQueueRead(BaseModel):
    reviewer_identity: str
    reviewer_role: str
    total: int
    items: List[SourceCertificationReviewQueueItem] = Field(default_factory=list)
    safety_message: str


class SourceCertificationReviewHistoryEntry(BaseModel):
    id: UUID
    actor: str
    decision: Optional[str] = None
    notes: Optional[str] = None
    evidence_pack_sha256: Optional[str] = None
    pack_version: Optional[str] = None
    source_snapshot_id: Optional[UUID] = None
    independent_human_attestation: bool = False
    structured_projection: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SourceCertificationReviewWorkspaceRead(BaseModel):
    certification: dict[str, Any]
    reviewer_identity: str
    reviewer_role: str
    reviewer_identity_conflict: bool
    review_pack_state: Literal["ready", "snapshot_pin_required", "unavailable"]
    can_submit_review: bool
    submission_requirements: List[str] = Field(default_factory=list)
    available_projections: List[SourceCertificationReviewProjectionOption] = Field(default_factory=list)
    review_pack: Optional[SourceCertificationReviewPackRead] = None
    review_history: List[SourceCertificationReviewHistoryEntry] = Field(default_factory=list)


class JurisdictionSourceOnboardingProposal(BaseModel):
    authority_name: str = Field(min_length=2, max_length=250)
    authority_type: str = Field(default="immigration_authority", min_length=2, max_length=100)
    authority_website_url: Optional[str] = None
    authority_domains: List[str] = Field(default_factory=lambda: ["visa"])
    source_name: str = Field(min_length=2, max_length=250)
    source_url: str = Field(min_length=8, max_length=2000)
    source_domain: str = Field(default="visa", min_length=2, max_length=100)
    source_type: Literal[
        "government",
        "official",
        "official_portal",
        "official_agency",
        "gazette",
    ] = "official"
    schedule_minutes: int = Field(default=1440, ge=15, le=525600)
    fetch_method: Literal["http", "browser", "api", "manual"] = "http"
    allowed_domains: List[str] = Field(default_factory=list)
    max_redirects: int = Field(default=3, ge=0, le=10)
    parser_profile: Literal["generic", "gazette_html_v1", "structured_program_catalog_v1"] = "generic"
    parser_config: dict[str, Any] = Field(default_factory=dict)
    certification_scope: str = Field(
        default="primary_immigration",
        pattern=r"^(primary_immigration|supplemental_[a-z0-9_]+)$",
        max_length=100,
    )
    certification_domains: List[str] = Field(min_length=1)
    evidence_notes: str = Field(min_length=10, max_length=5000)


class JurisdictionCoverageEvidenceBatchItemProposal(BaseModel):
    alpha2_code: str = Field(min_length=2, max_length=2)
    immigration_assessment: Optional[JurisdictionImmigrationAssessmentProposal] = None
    source_certification: Optional[JurisdictionSourceCertificationProposal] = None
    source_onboarding: Optional[JurisdictionSourceOnboardingProposal] = None

    @model_validator(mode="after")
    def require_evidence_operation(self):
        if (
            self.immigration_assessment is None
            and self.source_certification is None
            and self.source_onboarding is None
        ):
            raise ValueError(
                "Each coverage batch item must include an immigration assessment, source certification, or source onboarding"
            )
        if self.source_certification is not None and self.source_onboarding is not None:
            raise ValueError(
                "Use source_onboarding to create its pending certification; do not also provide source_certification"
            )
        return self


class JurisdictionCoverageEvidenceBatchCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    notes: str = Field(min_length=10, max_length=5000)
    items: List[JurisdictionCoverageEvidenceBatchItemProposal] = Field(min_length=1, max_length=50)


class CoverageTrancheAssistantPrepareRequest(BaseModel):
    alpha2_codes: List[str] = Field(min_length=1, max_length=25)
    dry_run: bool = True
    queue_eligible_baselines: bool = False
    include_candidate_assertions: bool = True
    max_candidate_lines: int = Field(default=8, ge=1, le=12)

    @model_validator(mode="after")
    def normalize_codes(self):
        normalized: list[str] = []
        for value in self.alpha2_codes:
            code = value.strip().upper()
            if len(code) != 2 or not code.isalpha():
                raise ValueError("Coverage tranche assistant alpha2_codes must contain two-letter codes")
            if code not in normalized:
                normalized.append(code)
        self.alpha2_codes = normalized
        return self


ExternalValidationReviewerType = Literal["mobility_user", "professional_operator"]
ExternalValidationSeverity = Literal["critical", "high", "medium", "low"]
ExternalValidationFindingStatus = Literal["open", "triaged", "resolved", "accepted_risk"]
ExternalValidationEvidenceType = Literal[
    "truth_claim",
    "verified_rule",
    "official_source",
    "source_snapshot",
    "pathway",
    "pathway_version",
    "pathway_comparison",
    "document",
    "operator_note",
]


class ExternalValidationScenarioCreate(BaseModel):
    scenario_key: str = Field(min_length=3, max_length=160, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    title: str = Field(min_length=3, max_length=250)
    jurisdiction_code: str = Field(min_length=2, max_length=12)
    domain: str = Field(min_length=2, max_length=100)
    persona: dict[str, Any] = Field(default_factory=dict)
    objectives: List[str] = Field(default_factory=list, min_length=1, max_length=25)
    required_evidence_types: List[ExternalValidationEvidenceType] = Field(
        default_factory=lambda: [
            "truth_claim",
            "verified_rule",
            "official_source",
            "source_snapshot",
            "pathway_version",
            "pathway_comparison",
        ]
    )


class ExternalValidationScenarioRead(BaseModel):
    id: UUID
    scenario_key: str
    title: str
    jurisdiction_code: str
    domain: str
    persona: dict[str, Any] = Field(default_factory=dict)
    objectives: List[str] = Field(default_factory=list)
    required_evidence_types: List[str] = Field(default_factory=list)
    status: str
    source_fixture: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class ExternalValidationRunCreate(BaseModel):
    run_key: Optional[str] = Field(default=None, min_length=3, max_length=180, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]+$")
    scenario_id: UUID
    lead_id: UUID
    pathway_comparison_assessment_id: UUID
    founder_intervention_count: int = Field(default=0, ge=0, le=10000)
    workflow_started_at: Optional[datetime] = None


class ExternalValidationRunUpdate(BaseModel):
    founder_intervention_count: Optional[int] = Field(default=None, ge=0, le=10000)
    workflow_completed_at: Optional[datetime] = None


class ExternalValidationReviewCreate(BaseModel):
    reviewer_type: ExternalValidationReviewerType
    reviewer_name: str = Field(min_length=2, max_length=200)
    reviewer_organization: Optional[str] = Field(default=None, max_length=250)
    reviewer_origin: Literal["external_human"] = "external_human"
    external_human_attestation: bool
    workflow_completed: bool
    understanding_rating: Optional[int] = Field(default=None, ge=1, le=5)
    usefulness_rating: int = Field(ge=1, le=5)
    jurisdiction_pathway_correct: Optional[bool] = None
    material_rule_traceability_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    unsupported_legal_certainty_count: Optional[int] = Field(default=None, ge=0)
    missing_critical_document_count: Optional[int] = Field(default=None, ge=0)
    feedback: str = Field(min_length=3, max_length=10000)

    @model_validator(mode="after")
    def validate_reviewer_specific_metrics(self):
        if not self.external_human_attestation:
            raise ValueError("External human attestation is required")
        if self.reviewer_type == "mobility_user" and self.understanding_rating is None:
            raise ValueError("Mobility-user review requires understanding_rating")
        if self.reviewer_type == "professional_operator":
            required = {
                "jurisdiction_pathway_correct": self.jurisdiction_pathway_correct,
                "material_rule_traceability_percent": self.material_rule_traceability_percent,
                "unsupported_legal_certainty_count": self.unsupported_legal_certainty_count,
                "missing_critical_document_count": self.missing_critical_document_count,
            }
            missing = [key for key, value in required.items() if value is None]
            if missing:
                raise ValueError(
                    "Professional/operator review requires: " + ", ".join(sorted(missing))
                )
        return self


class ExternalValidationReviewRead(BaseModel):
    id: UUID
    run_id: UUID
    reviewer_type: str
    reviewer_name: str
    reviewer_organization: Optional[str] = None
    reviewer_origin: str
    external_human_attestation: bool
    workflow_completed: bool
    understanding_rating: Optional[int] = None
    usefulness_rating: Optional[int] = None
    jurisdiction_pathway_correct: Optional[bool] = None
    material_rule_traceability_percent: Optional[float] = None
    unsupported_legal_certainty_count: Optional[int] = None
    missing_critical_document_count: Optional[int] = None
    feedback: str
    submitted_by: str
    submitted_at: datetime


class ExternalValidationFindingCreate(BaseModel):
    review_id: Optional[UUID] = None
    severity: ExternalValidationSeverity
    category: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=3, max_length=250)
    description: str = Field(min_length=3, max_length=10000)


class ExternalValidationFindingTriage(BaseModel):
    status: Literal["triaged", "resolved"]
    remediation_notes: str = Field(min_length=3, max_length=10000)


class ExternalValidationBoardAcceptance(BaseModel):
    attestation: bool
    reason: str = Field(min_length=10, max_length=10000)


class ExternalValidationFindingRead(BaseModel):
    id: UUID
    run_id: UUID
    review_id: Optional[UUID] = None
    severity: str
    category: str
    title: str
    description: str
    status: str
    remediation_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    board_acceptance_reason: Optional[str] = None
    board_accepted_by: Optional[str] = None
    board_accepted_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class ExternalValidationEvidenceCreate(BaseModel):
    finding_id: Optional[UUID] = None
    evidence_type: ExternalValidationEvidenceType
    entity_id: Optional[UUID] = None
    label: str = Field(min_length=2, max_length=300)
    source_url: Optional[str] = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_entity_for_governed_evidence(self):
        if self.evidence_type != "operator_note" and self.entity_id is None:
            raise ValueError(f"{self.evidence_type} evidence requires entity_id")
        return self


class ExternalValidationEvidenceRead(BaseModel):
    id: UUID
    run_id: UUID
    finding_id: Optional[UUID] = None
    evidence_type: str
    entity_id: Optional[UUID] = None
    label: str
    source_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    added_by: str
    created_at: datetime


class ExternalValidationGateRead(BaseModel):
    status: Literal["held", "failed", "passed"]
    reasons: List[str] = Field(default_factory=list)
    required_reviewer_types: List[str] = Field(default_factory=lambda: ["mobility_user", "professional_operator"])
    completed_reviewer_types: List[str] = Field(default_factory=list)
    required_evidence_types: List[str] = Field(default_factory=list)
    captured_evidence_types: List[str] = Field(default_factory=list)
    founder_intervention_count: int
    critical_open: int = 0
    high_open: int = 0
    medium_low_untriaged: int = 0


class ExternalValidationRunRead(BaseModel):
    id: UUID
    run_key: str
    scenario_id: UUID
    lead_id: Optional[UUID] = None
    pathway_comparison_assessment_id: Optional[UUID] = None
    status: str
    gate_status: str
    gate_reasons: List[str] = Field(default_factory=list)
    founder_intervention_count: int
    workflow_started_at: Optional[datetime] = None
    workflow_completed_at: Optional[datetime] = None
    evaluated_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    scenario: ExternalValidationScenarioRead
    reviews: List[ExternalValidationReviewRead] = Field(default_factory=list)
    findings: List[ExternalValidationFindingRead] = Field(default_factory=list)
    evidence: List[ExternalValidationEvidenceRead] = Field(default_factory=list)
    gate: ExternalValidationGateRead
