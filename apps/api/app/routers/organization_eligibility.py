from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session

from app.core.db import get_session
from app.routers.organization_records import organization_command_context
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_eligibility_orchestration import (
    GovernedEligibilityExecutionPlan,
    GovernedEligibilityOrchestrationIntegrityError,
    GovernedEligibilityOrchestrationResult,
    orchestrate_governed_eligibility,
)


router = APIRouter(
    prefix="/api/v1/organization",
    tags=["organization-governed-eligibility"],
    responses={
        401: {"description": "Authentication required."},
        403: {"description": "Organization action is not permitted."},
        409: {"description": "Governed eligibility orchestration conflicts with current state."},
        503: {"description": "Governed eligibility execution policy is not configured."},
    },
)


class GovernedEligibilityOrchestrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_work_item_id: UUID
    verification_work_item_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=200)


class GovernedEligibilityOrchestrationRead(BaseModel):
    schema_version: str
    state: str
    trace_id: UUID
    proposal_activity_id: UUID
    readiness_state: str | None
    verification_activity_id: UUID | None
    verification_disposition: str | None
    verification_floor_activity_id: UUID | None
    gateway_outcome: str
    assessment_id: UUID | None
    revision_id: UUID | None
    semantic_activity_id: UUID | None
    canonical_effect_committed: bool
    replayed: bool

    @classmethod
    def from_result(
        cls,
        result: GovernedEligibilityOrchestrationResult,
    ) -> "GovernedEligibilityOrchestrationRead":
        return cls(
            schema_version=result.schema_version,
            state=result.state.value,
            trace_id=result.trace_id,
            proposal_activity_id=result.proposal_activity_id,
            readiness_state=result.readiness_state,
            verification_activity_id=result.verification_activity_id,
            verification_disposition=result.verification_disposition,
            verification_floor_activity_id=result.verification_floor_activity_id,
            gateway_outcome=result.gateway_outcome,
            assessment_id=result.assessment_id,
            revision_id=result.revision_id,
            semantic_activity_id=result.semantic_activity_id,
            canonical_effect_committed=result.canonical_effect_committed,
            replayed=result.replayed,
        )


def governed_eligibility_execution_plan() -> GovernedEligibilityExecutionPlan:
    """Resolve trusted runtime/provider/authority policy for governed eligibility.

    The default is deliberately fail-closed. Provider/model/position/autonomy/authority
    are not accepted from request JSON and are not inferred from the legacy global LLM
    provider switch. A production deployment must bind this dependency to a governed
    server-side execution/egress policy before the route can execute.
    """

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Governed eligibility execution policy is not configured.",
    )


def governed_eligibility_initiator(
    context: OrganizationCommandContext = Depends(organization_command_context),
) -> OrganizationCommandContext:
    """Authorize a human initiator before resolving any execution/provider policy."""

    if context.actor_type.value != "human" or context.role not in {"admin", "operator"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization action is not permitted.",
        )
    return context


@router.post(
    "/eligibility/orchestrate",
    response_model=GovernedEligibilityOrchestrationRead,
)
def run_governed_eligibility_orchestration(
    payload: GovernedEligibilityOrchestrationRequest,
    session: Session = Depends(get_session),
    initiator: OrganizationCommandContext = Depends(governed_eligibility_initiator),
    execution_plan: GovernedEligibilityExecutionPlan = Depends(governed_eligibility_execution_plan),
) -> GovernedEligibilityOrchestrationRead:
    """Run the accepted governed eligibility vertical through a trusted server plan.

    The authenticated human initiates work but never becomes the material-action actor.
    E.2/G.2/G.3 continue to execute under the producer OrganizationPosition carried by
    the trusted execution plan and governed ContextBundle.
    """

    try:
        result = orchestrate_governed_eligibility(
            session,
            tenant_key=initiator.tenant_key,
            proposal_work_item_id=payload.proposal_work_item_id,
            verification_work_item_id=payload.verification_work_item_id,
            idempotency_key=payload.idempotency_key,
            execution_plan=execution_plan,
        )
    except GovernedEligibilityOrchestrationIntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Governed eligibility orchestration could not proceed with current canonical state.",
        ) from exc
    return GovernedEligibilityOrchestrationRead.from_result(result)
