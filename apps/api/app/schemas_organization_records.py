from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import (
    OrganizationActivityClass,
    OrganizationActorType,
    OrganizationBlockerStatus,
    OrganizationBlockerType,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    OrganizationDecisionType,
    OrganizationDependencyStatus,
    OrganizationDependencyType,
    OrganizationHumanActionRequestStatus,
    OrganizationHumanActionRequestType,
    OrganizationHumanActionType,
    OrganizationReferenceRole,
    OrganizationReferenceTargetType,
    OrganizationWorkPriority,
)


class OrganizationInput(BaseModel):
    """Business input only; trusted identity/tenant/authority fields are forbidden."""

    model_config = ConfigDict(extra="forbid")


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)


ItemT = TypeVar("ItemT")


class OrganizationPage(BaseModel, Generic[ItemT]):
    data: list[ItemT]
    page: int
    page_size: int
    total: int
    total_pages: int


class ActivityCreate(OrganizationInput):
    activity_key: str = Field(min_length=1, max_length=255)
    stream_key: str = Field(min_length=1, max_length=255)
    activity_class: OrganizationActivityClass
    activity_type: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1, max_length=4000)
    source_object_type: str = Field(min_length=1, max_length=255)
    source_object_id: str = Field(min_length=1, max_length=255)
    source_object_version: str | None = Field(default=None, max_length=255)
    occurred_at: datetime
    work_item_id: UUID | None = None
    execution_attempt_id: UUID | None = None
    agent_run_id: UUID | None = None
    automation_event_id: UUID | None = None
    lead_id: UUID | None = None
    profile_id: UUID | None = None
    application_id: UUID | None = None
    corporate_account_id: UUID | None = None
    corporate_mobility_case_id: UUID | None = None
    causation_activity_id: UUID | None = None
    supersedes_activity_id: UUID | None = None
    correlation_key: str | None = Field(default=None, max_length=255)
    payload: dict[str, Any] = Field(default_factory=dict)


class ActivityRead(OrganizationRead):
    id: UUID
    activity_key: str
    stream_sequence: int
    activity_class: OrganizationActivityClass
    activity_type: str
    title: str
    summary: str
    department: str | None
    position_key: str | None
    actor_type: OrganizationActorType
    actor_id: str
    work_item_id: UUID | None
    source_object_type: str
    source_object_id: str
    source_object_version: str | None
    correlation_key: str | None
    occurred_at: datetime
    created_at: datetime


class ContributionCreate(OrganizationInput):
    contribution_key: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=255)
    source_id: UUID
    source_version: str = Field(min_length=1, max_length=255)
    outcome_type: str = Field(min_length=1, max_length=255)
    verification_basis: str = Field(min_length=1, max_length=2000)
    contribution_type: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    outcome_summary: str = Field(min_length=1, max_length=4000)
    department: str = Field(min_length=1, max_length=255)
    accountable_position_key: str = Field(min_length=1, max_length=255)
    impact_kind: OrganizationContributionImpactKind
    effective_at: datetime
    work_item_id: UUID | None = None
    decision_id: UUID | None = None
    objective_key: str | None = Field(default=None, max_length=255)
    phase_key: str | None = Field(default=None, max_length=255)
    measured_value: Decimal | None = None
    baseline_value: Decimal | None = None
    target_value: Decimal | None = None
    measurement_unit: str | None = Field(default=None, max_length=100)
    impact: dict[str, Any] = Field(default_factory=dict)
    evidence_summary: list[Any] = Field(default_factory=list, max_length=100)
    human_action_required: bool = False


class ContributionCorrectionCreate(OrganizationInput):
    contribution_key: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=255)
    source_id: UUID
    source_version: str = Field(min_length=1, max_length=255)
    outcome_type: str = Field(min_length=1, max_length=255)
    verification_basis: str = Field(min_length=1, max_length=2000)
    record_kind: OrganizationContributionRecordKind
    title: str = Field(min_length=1, max_length=500)
    outcome_summary: str = Field(min_length=1, max_length=4000)
    effective_at: datetime
    retraction_reason: str | None = Field(default=None, max_length=2000)


class ContributionRead(OrganizationRead):
    id: UUID
    contribution_key: str
    contribution_type: str
    title: str
    outcome_summary: str
    actor_type: OrganizationActorType
    actor_id: str
    department: str
    accountable_position_key: str
    authority_level: str
    work_item_id: UUID | None
    decision_id: UUID | None
    source_object_type: str
    source_object_id: str
    source_object_version: str
    source_state: str
    verification_method: OrganizationContributionVerificationMethod
    record_kind: OrganizationContributionRecordKind
    impact_kind: OrganizationContributionImpactKind
    effective_at: datetime
    supersedes_contribution_id: UUID | None
    retraction_reason: str | None
    created_at: datetime


class WorkItemCreate(OrganizationInput):
    idempotency_key: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    objective: str = Field(min_length=1, max_length=4000)
    department: str = Field(min_length=1, max_length=255)
    assigned_position_key: str = Field(min_length=1, max_length=255)
    work_type: str = Field(default="organizational", min_length=1, max_length=255)
    priority: OrganizationWorkPriority = OrganizationWorkPriority.normal
    parent_work_item_id: UUID | None = None
    objective_key: str | None = Field(default=None, max_length=255)
    phase_key: str | None = Field(default=None, max_length=255)
    risk_level: str = Field(default="routine", min_length=1, max_length=100)
    is_emergency: bool = False
    due_at: datetime | None = None
    source_object_type: str | None = Field(default=None, max_length=255)
    source_object_id: str | None = Field(default=None, max_length=255)
    source_object_version: str | None = Field(default=None, max_length=255)
    context: dict[str, Any] = Field(default_factory=dict)


class WorkItemRead(OrganizationRead):
    id: UUID
    idempotency_key: str
    work_type: str
    objective_key: str | None
    phase_key: str | None
    priority: OrganizationWorkPriority
    parent_work_item_id: UUID | None
    title: str
    objective: str
    department: str
    authority_level: str
    status: str
    assigned_position_key: str
    risk_level: str
    is_emergency: bool
    due_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class ReasonCommand(OrganizationInput):
    reason: str = Field(min_length=1, max_length=2000)


class WorkAssignCommand(ReasonCommand):
    assigned_position_key: str = Field(min_length=1, max_length=255)


class DependencyCreate(OrganizationInput):
    dependency_key: str = Field(min_length=1, max_length=255)
    work_item_id: UUID
    depends_on_work_item_id: UUID
    dependency_type: OrganizationDependencyType


class DependencySatisfyCommand(ReasonCommand):
    contribution_id: UUID


class DependencyRead(OrganizationRead):
    id: UUID
    dependency_key: str
    work_item_id: UUID
    depends_on_work_item_id: UUID
    dependency_type: OrganizationDependencyType
    status: OrganizationDependencyStatus
    satisfied_by_contribution_id: UUID | None
    waived_by_human_id: str | None
    waiver_reason: str | None
    waived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BlockerFields(OrganizationInput):
    blocker_key: str = Field(min_length=1, max_length=255)
    blocker_type: OrganizationBlockerType
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=4000)
    work_item_id: UUID | None = None
    decision_id: UUID | None = None
    contribution_id: UUID | None = None
    lead_id: UUID | None = None
    profile_id: UUID | None = None
    application_id: UUID | None = None
    corporate_account_id: UUID | None = None
    corporate_mobility_case_id: UUID | None = None
    requires_human_action: bool = False
    due_at: datetime | None = None
    source_object_type: str | None = Field(default=None, max_length=255)
    source_object_id: str | None = Field(default=None, max_length=255)
    source_object_version: str | None = Field(default=None, max_length=255)


class BlockerCreate(BlockerFields):
    supersedes_blocker_id: UUID | None = None


class BlockerSupersedeCreate(BlockerFields):
    pass


class BlockerRead(OrganizationRead):
    id: UUID
    blocker_key: str
    blocker_type: OrganizationBlockerType
    severity: str
    title: str
    description: str
    status: OrganizationBlockerStatus
    department: str | None
    accountable_position_key: str | None
    work_item_id: UUID | None
    decision_id: UUID | None
    contribution_id: UUID | None
    requires_human_action: bool
    due_at: datetime | None
    mitigated_at: datetime | None
    resolved_at: datetime | None
    resolution_summary: str | None
    resolving_actor_type: OrganizationActorType | None
    resolving_actor_id: str | None
    supersedes_blocker_id: UUID | None
    created_at: datetime
    updated_at: datetime


class HumanActionRequestCreate(OrganizationInput):
    request_key: str = Field(min_length=1, max_length=255)
    request_type: OrganizationHumanActionRequestType
    title: str = Field(min_length=1, max_length=500)
    instructions: str = Field(min_length=1, max_length=4000)
    required_role: str = Field(min_length=1, max_length=255)
    priority: OrganizationWorkPriority = OrganizationWorkPriority.normal
    assigned_human_id: str | None = Field(default=None, max_length=255)
    work_item_id: UUID | None = None
    decision_id: UUID | None = None
    blocker_id: UUID | None = None
    contribution_id: UUID | None = None
    lead_id: UUID | None = None
    profile_id: UUID | None = None
    application_id: UUID | None = None
    corporate_account_id: UUID | None = None
    corporate_mobility_case_id: UUID | None = None
    source_object_type: str | None = Field(default=None, max_length=255)
    source_object_id: str | None = Field(default=None, max_length=255)
    source_object_version: str | None = Field(default=None, max_length=255)
    due_at: datetime | None = None


class HumanActionRequestRead(OrganizationRead):
    id: UUID
    request_key: str
    request_type: OrganizationHumanActionRequestType
    title: str
    instructions: str
    status: OrganizationHumanActionRequestStatus
    priority: OrganizationWorkPriority
    required_role: str
    assigned_human_id: str | None
    requested_by_type: OrganizationActorType
    requested_by_id: str
    work_item_id: UUID | None
    decision_id: UUID | None
    blocker_id: UUID | None
    contribution_id: UUID | None
    due_at: datetime | None
    outcome: str | None
    completed_at: datetime | None
    completed_by_human_id: str | None
    created_at: datetime
    updated_at: datetime


class HumanActionRequestAssign(ReasonCommand):
    assigned_human_id: str = Field(min_length=1, max_length=255)


class HumanActionFields(OrganizationInput):
    action_key: str = Field(min_length=1, max_length=255)
    action_type: OrganizationHumanActionType
    outcome: str = Field(min_length=1, max_length=4000)
    occurred_at: datetime
    reason: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HumanActionComplete(HumanActionFields):
    completion_notes: str | None = Field(default=None, max_length=4000)


class HumanActionCreate(HumanActionFields):
    human_action_request_id: UUID | None = None
    work_item_id: UUID | None = None
    decision_id: UUID | None = None
    blocker_id: UUID | None = None
    contribution_id: UUID | None = None
    lead_id: UUID | None = None
    profile_id: UUID | None = None
    application_id: UUID | None = None
    corporate_account_id: UUID | None = None
    corporate_mobility_case_id: UUID | None = None
    source_object_type: str | None = Field(default=None, max_length=255)
    source_object_id: str | None = Field(default=None, max_length=255)
    source_object_version: str | None = Field(default=None, max_length=255)


class HumanActionRead(OrganizationRead):
    id: UUID
    action_key: str
    human_action_request_id: UUID | None
    action_type: OrganizationHumanActionType
    actor_type: OrganizationActorType
    human_actor_id: str
    actor_role: str | None
    actor_position_key: str | None
    actor_department: str | None
    work_item_id: UUID | None
    decision_id: UUID | None
    blocker_id: UUID | None
    contribution_id: UUID | None
    outcome: str
    reason: str | None
    occurred_at: datetime
    created_at: datetime


class HumanActionCompletionRead(BaseModel):
    request: HumanActionRequestRead
    action: HumanActionRead


class DecisionCreate(OrganizationInput):
    decision_key: str = Field(min_length=1, max_length=255)
    decision_type: OrganizationDecisionType
    title: str = Field(min_length=1, max_length=500)
    question: str = Field(min_length=1, max_length=4000)
    recommendation: str = Field(min_length=1, max_length=4000)
    alternatives: list[Any] = Field(default_factory=list, max_length=100)
    evidence: list[Any] = Field(default_factory=list, max_length=100)
    impact: dict[str, Any] = Field(default_factory=dict)
    conditions: list[Any] = Field(default_factory=list, max_length=100)
    work_item_id: UUID | None = None
    source_object_type: str | None = Field(default=None, max_length=255)
    source_object_id: str | None = Field(default=None, max_length=255)
    source_object_version: str | None = Field(default=None, max_length=255)
    due_at: datetime | None = None
    expires_at: datetime | None = None


class DecisionOutcome(ReasonCommand):
    outcome: str = Field(pattern="^(approved|rejected)$")
    effect_summary: str | None = Field(default=None, max_length=4000)


class DecisionSupersede(ReasonCommand):
    new_decision_key: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    question: str = Field(min_length=1, max_length=4000)
    recommendation: str = Field(min_length=1, max_length=4000)


class DecisionRead(OrganizationRead):
    id: UUID
    decision_key: str
    decision_type: OrganizationDecisionType
    work_item_id: UUID | None
    supersedes_decision_id: UUID | None
    authority_level: str
    requested_by_position: str
    decision_owner_position: str
    title: str
    question: str
    recommendation: str
    effect_summary: str | None
    status: str
    decided_by: str | None
    decision_reason: str | None
    decided_at: datetime | None
    due_at: datetime | None
    expires_at: datetime | None
    source_version: str | None = Field(validation_alias="record_fingerprint")
    created_at: datetime
    updated_at: datetime


class ReferenceCreate(OrganizationInput):
    reference_key: str = Field(min_length=1, max_length=255)
    reference_role: OrganizationReferenceRole
    target_type: OrganizationReferenceTargetType
    target_id: UUID
    activity_id: UUID | None = None
    contribution_id: UUID | None = None
    work_item_id: UUID | None = None
    decision_id: UUID | None = None
    blocker_id: UUID | None = None
    human_action_request_id: UUID | None = None
    human_action_id: UUID | None = None
    target_version: str | None = Field(default=None, max_length=255)
    target_state: str | None = Field(default=None, max_length=255)
    content_hash: str | None = Field(default=None, max_length=255)
    label: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    supersedes_reference_id: UUID | None = None


class ReferenceRead(OrganizationRead):
    id: UUID
    reference_key: str
    activity_id: UUID | None
    contribution_id: UUID | None
    work_item_id: UUID | None
    decision_id: UUID | None
    blocker_id: UUID | None
    human_action_request_id: UUID | None
    human_action_id: UUID | None
    reference_role: OrganizationReferenceRole
    target_type: OrganizationReferenceTargetType
    target_id: str
    target_version: str | None
    target_state: str | None
    label: str | None
    source_url: str | None
    supersedes_reference_id: UUID | None
    created_at: datetime
