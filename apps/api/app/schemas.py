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


class EligibilityEvaluateRequest(BaseModel):
    lead_id: UUID
    profile: dict[str, Any] = Field(default_factory=dict)
    actor: str = "system"


class EligibilityAssessmentRead(BaseModel):
    id: UUID
    lead_id: UUID
    agent_run_id: Optional[UUID] = None
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
