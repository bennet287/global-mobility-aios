from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.domain import (
    FollowUpStatus,
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
    status: str
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
