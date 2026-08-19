from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.core.organization_constitution import ConsequenceClass, MaterialActionType
from app.models.domain import OrganizationActivity, OrganizationalWorkItem, now_utc
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    AuditMutation,
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
    require_mutation_role,
    snapshot,
    stage_mutations,
    tenant_record,
)
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayEvaluation,
    GatewayOutcome,
    MaterialAction,
    PolicyDisposition,
    evaluate_material_action,
    organization_activity_projection,
)
from app.services.organization_semantic_activity import stage_work_item_assignment_activity


GOVERNED_WORK_CAPABILITY = "operations.work"


@dataclass(frozen=True, slots=True)
class GovernedWorkAssignmentResult:
    evaluation: GatewayEvaluation
    work_item: OrganizationalWorkItem
    governance_activity: OrganizationActivity | None
    mutated: bool


def work_item_precondition_version(work_item: OrganizationalWorkItem) -> int:
    """Return a stable integer precondition token from the canonical updated_at value."""

    value = work_item.updated_at
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    normalized = value.astimezone(timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = normalized - epoch
    return ((delta.days * 86_400) + delta.seconds) * 1_000_000 + delta.microseconds


def _governance_activity(
    session: Session,
    *,
    tenant_key: str,
    idempotency_key: str,
) -> OrganizationActivity | None:
    return session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.activity_key == f"governance:{idempotency_key}",
        )
    ).first()


def _existing_action_fingerprint(activity: OrganizationActivity | None) -> str | None:
    if activity is None:
        return None
    try:
        payload = json.loads(activity.payload_json or "{}")
    except json.JSONDecodeError as exc:
        raise DependencyConflict("persisted governance activity payload is invalid") from exc
    fingerprint = payload.get("action_fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise DependencyConflict("persisted governance activity lacks an action fingerprint")
    return fingerprint


def _evaluate_persisted_action(
    context: OrganizationCommandContext,
    authority: CapabilityAuthority,
    action: MaterialAction,
    *,
    current_version: int,
    persisted_activity: OrganizationActivity | None,
    policy_disposition: PolicyDisposition,
) -> GatewayEvaluation:
    """Evaluate with durable idempotency taking precedence over aggregate staleness.

    A successful material command advances its aggregate precondition. An exact retry
    must therefore replay the durable prior result instead of failing only because the
    first execution changed the aggregate. Conflicting reuse of the same idempotency
    key still fails closed.
    """

    existing_fingerprint = _existing_action_fingerprint(persisted_activity)
    evaluation_version = (
        action.expected_version
        if existing_fingerprint is not None and action.expected_version is not None
        else current_version
    )
    return evaluate_material_action(
        context,
        authority,
        action,
        current_version=evaluation_version,
        existing_idempotency_fingerprint=existing_fingerprint,
        policy_disposition=policy_disposition,
    )


def _stage_assignment(
    session: Session,
    context: OrganizationCommandContext,
    work_item: OrganizationalWorkItem,
    *,
    assigned_position_key: str,
    reason: str,
) -> bool:
    """Stage the existing WorkItem assignment semantics without owning the transaction."""

    require_mutation_role(context)
    if work_item.status in {"completed", "cancelled", "failed", "rejected", "returned"}:
        raise InvalidTransition("terminal work cannot be reassigned")
    if work_item.assigned_position_key == assigned_position_key:
        return False

    before = snapshot(work_item)
    previous_position_key = work_item.assigned_position_key
    work_item.assigned_position_key = assigned_position_key
    work_item.updated_at = now_utc()
    session.add(work_item)

    stage_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.work.assign",
                "organizational_work_item",
                work_item.id,
                before,
                work_item,
                reason,
            )
        ],
        context=context,
    )
    stage_work_item_assignment_activity(
        session,
        context,
        work_item,
        previous_position_key=previous_position_key,
    )
    return True


def governed_assign_work_item(
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
) -> GovernedWorkAssignmentResult:
    """Route one real reversible R1 WorkItem assignment through the V1.3 gateway.

    AUTO_EXECUTE stages the existing assignment audit + semantic Activity together
    with the governance Activity and commits them atomically. BLOCK/REVIEW_REQUIRED
    does not mutate the WorkItem. An exact durable retry returns IDEMPOTENT_REPLAY.
    """

    work_item = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        context.tenant_key,
        label="work item",
    )
    current_version = work_item_precondition_version(work_item)
    action = MaterialAction(
        action_type=MaterialActionType.WORK_ITEM_ASSIGNMENT,
        capability=GOVERNED_WORK_CAPABILITY,
        subject_type="organizational_work_item",
        subject_id=str(work_item.id),
        idempotency_key=idempotency_key,
        expected_version=expected_version,
        proposed_change={"assigned_position_key": assigned_position_key},
        scope_key=work_item.department,
        rationale=reason,
        consequence_class=ConsequenceClass.REVERSIBLE,
    )

    persisted_activity = _governance_activity(
        session,
        tenant_key=context.tenant_key,
        idempotency_key=idempotency_key,
    )
    evaluation = _evaluate_persisted_action(
        context,
        authority,
        action,
        current_version=current_version,
        persisted_activity=persisted_activity,
        policy_disposition=policy_disposition,
    )

    if evaluation.outcome is GatewayOutcome.IDEMPOTENT_REPLAY:
        return GovernedWorkAssignmentResult(
            evaluation=evaluation,
            work_item=work_item,
            governance_activity=persisted_activity,
            mutated=False,
        )

    if evaluation.outcome is not GatewayOutcome.AUTO_EXECUTE:
        return GovernedWorkAssignmentResult(
            evaluation=evaluation,
            work_item=work_item,
            governance_activity=None,
            mutated=False,
        )

    projection = organization_activity_projection(context, action, evaluation)
    trace_context = replace(context, correlation_key=str(evaluation.trace_id))
    try:
        mutated = _stage_assignment(
            session,
            trace_context,
            work_item,
            assigned_position_key=assigned_position_key,
            reason=reason,
        )
        governance_activity = stage_activity(
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
            source_object_version=str(action.expected_version),
            work_item_id=work_item.id,
            occurred_at=action.requested_at,
            payload=projection.payload,
            correlation_key=projection.correlation_key,
        )
        session.commit()
        session.refresh(work_item)
        session.refresh(governance_activity)
    except Exception:
        session.rollback()
        raise

    return GovernedWorkAssignmentResult(
        evaluation=evaluation,
        work_item=work_item,
        governance_activity=governance_activity,
        mutated=mutated,
    )