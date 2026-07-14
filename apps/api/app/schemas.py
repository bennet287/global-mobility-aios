from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

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
    storage_key: Optional[str]
    storage_provider: Optional[str] = None
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    uploaded_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

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
]


class PathwayVersionInput(BaseModel):
    official_source_id: Optional[UUID] = None
    source_snapshot_id: Optional[UUID] = None
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


class PathwayVersionRead(BaseModel):
    id: UUID
    pathway_id: UUID
    version_number: int
    lifecycle_status: str
    supersedes_version_id: Optional[UUID] = None
    official_source_id: Optional[UUID] = None
    source_snapshot_id: Optional[UUID] = None
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


class RegulatoryChangePublishRequest(BaseModel):
    rule_key: str = Field(min_length=2, max_length=200)
    statement: str = Field(min_length=5)
    reviewer: str = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    supersedes_rule_id: Optional[UUID] = None


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
    coverage_domains: List[str] = Field(min_length=1)
    evidence_notes: str = Field(min_length=10, max_length=5000)


class JurisdictionSourceCertificationReview(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=3, max_length=5000)
