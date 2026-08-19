from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from sqlmodel import Session

from app.models.domain import OrganizationActivity
from app.services.organization_activity import stage_activity
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayOutcome,
    PolicyDisposition,
    organization_activity_projection,
)
from app.services.organization_governed_work import (
    GovernedWorkAssignmentResult,
    governed_assign_work_item,
)


@dataclass(frozen=True, slots=True)
class TransparentGovernedWorkAssignmentResult:
    assignment: GovernedWorkAssignmentResult
    attempt_activity: OrganizationActivity | None

    @property
    def mutated(self) -> bool:
        return self.assignment.mutated


def _persist_non_execution_attempt(
    session: Session,
    context: OrganizationCommandContext,
    result: GovernedWorkAssignmentResult,
    *,
    idempotency_key: str,
) -> OrganizationActivity:
    evaluation = result.evaluation
    if evaluation.outcome not in {GatewayOutcome.BLOCK, GatewayOutcome.REVIEW_REQUIRED}:
        raise ValueError("attempt persistence requires BLOCK or REVIEW_REQUIRED")

    # Reconstruct the governance projection from the durable result metadata without
    # changing B.2 successful-command idempotency semantics. The attempt record uses
    # a trace-scoped key, not governance:<idempotency_key>, so a denied/reviewed attempt
    # cannot later masquerade as a successful-command replay record.
    from app.core.organization_constitution import ConsequenceClass, MaterialActionType
    from app.services.organization_governance_kernel import MaterialAction

    work_item = result.work_item
    action = MaterialAction(
        action_type=MaterialActionType.WORK_ITEM_ASSIGNMENT,
        capability="operations.work",
        subject_type="organizational_work_item",
        subject_id=str(work_item.id),
        idempotency_key=idempotency_key,
        expected_version=None if result.evaluation.reason.value == "EXPECTED_VERSION_REQUIRED" else None,
        proposed_change={},
        scope_key=work_item.department,
        rationale="",
        consequence_class=ConsequenceClass.REVERSIBLE,
        trace_id=evaluation.trace_id,
    )
    projection = organization_activity_projection(context, action, evaluation)
    projection = replace(
        projection,
        activity_key=f"governance:attempt:{evaluation.trace_id}",
        payload={
            **dict(projection.payload),
            "governance_record_kind": "attempt",
            "requested_idempotency_key": idempotency_key,
        },
    )
    trace_context = replace(context, correlation_key=str(evaluation.trace_id))
    activity = stage_activity(
        session,
        trace_context,
        activity_key=projection.activity_key,
        stream_key=projection.stream_key,
        activity_class=projection.activity_class,
        activity_type=projection.activity_type,
        title=projection.title,
        summary=projection.summary,
        source_object_type=projection.source_object_type,
        source_object_id=projection.source_object_id,
        source_object_version=projection.source_object_version,
        work_item_id=work_item.id,
        occurred_at=work_item.updated_at,
        payload=projection.payload,
        correlation_key=projection.correlation_key,
    )
    session.commit()
    session.refresh(activity)
    return activity


def transparent_governed_assign_work_item(
    session: Session,
    context: OrganizationCommandContext,
    authority: CapabilityAuthority,
    *,
    work_item_id: UUID,
    assigned_position_key: str,
    expected_version: int,
    idempotency_key: str,
    reason: str,
    policy_disposition: PolicyDisposition = PolicyDisposition.ALLOW,
) -> TransparentGovernedWorkAssignmentResult:
    """Execute B.2 assignment semantics and persist non-executing material attempts.

    Successful execution and successful-command replay remain owned by the sealed B.2
    service. C.2 only adds a trace-scoped durable governance Activity for BLOCK and
    REVIEW_REQUIRED outcomes so those material attempts are Board-inspectable.
    """

    assignment = governed_assign_work_item(
        session,
        context,
        authority,
        work_item_id=work_item_id,
        assigned_position_key=assigned_position_key,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
        reason=reason,
        policy_disposition=policy_disposition,
    )

    if assignment.evaluation.outcome not in {
        GatewayOutcome.BLOCK,
        GatewayOutcome.REVIEW_REQUIRED,
    }:
        return TransparentGovernedWorkAssignmentResult(
            assignment=assignment,
            attempt_activity=None,
        )

    try:
        attempt_activity = _persist_non_execution_attempt(
            session,
            context,
            assignment,
            idempotency_key=idempotency_key,
        )
    except Exception:
        session.rollback()
        raise

    return TransparentGovernedWorkAssignmentResult(
        assignment=assignment,
        attempt_activity=attempt_activity,
    )
