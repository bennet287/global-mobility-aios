from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.core.organization_constitution import ConsequenceClass, MaterialActionType
from app.models.domain import (
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    AuditMutation,
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
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
from app.services.organization_semantic_activity import SEMANTIC_ACTIVITY_CONTRACT_VERSION


GOVERNED_WORK_CAPABILITY = "operations.work"


@dataclass(frozen=True, slots=True)
class GovernedWorkAssignmentResult:
    evaluation: GatewayEvaluation
    work_item: OrganizationalWorkItem
    governance_activity: OrganizationActivity | None
    mutated: bool


def _normalized_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def work_item_precondition_version(work_item: OrganizationalWorkItem) -> int:
    """Return a stable integer precondition token from the canonical updated_at value."""

    normalized = _normalized_utc(work_item.updated_at)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = normalized - epoch
    return ((delta.days * 86_400) + delta.seconds) * 1_000_000 + delta.microseconds


def _next_work_item_updated_at(previous: datetime) -> datetime:
    """Return a timestamp that strictly advances the optimistic precondition token."""

    previous_utc = _normalized_utc(previous)
    candidate = _normalized_utc(now_utc())
    if candidate <= previous_utc:
        return previous_utc + timedelta(microseconds=1)
    return candidate


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


def _stage_assignment_activity_with_causation(
    session: Session,
    context: OrganizationCommandContext,
    work_item: OrganizationalWorkItem,
    *,
    previous_position_key: str,
    causation_activity_id: UUID,
) -> OrganizationActivity:
    """Stage the accepted assignment semantic with an explicit governance cause.

    This preserves the existing semantic event key/version contract while ensuring the
    Activity record fingerprint also covers the causal governance Activity reference.
    """

    payload = {
        "previous_position_key": previous_position_key,
        "assigned_position_key": work_item.assigned_position_key,
        "status": work_item.status,
    }
    activity_type = "organization.work.assigned.v1"
    source_version = canonical_fingerprint(
        {
            "contract": SEMANTIC_ACTIVITY_CONTRACT_VERSION,
            "source_type": "organizational_work_item",
            "source_id": str(work_item.id),
            "activity_type": activity_type,
            "occurred_at": work_item.updated_at,
            "payload": payload,
        }
    )
    return stage_activity(
        session,
        context,
        activity_key=(
            f"semantic:organizational_work_item:{work_item.id}:{activity_type}:{source_version}"
        ),
        stream_key=f"work:{work_item.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type=activity_type,
        title="Work item assignment changed",
        summary="Governed work assignment changed without implying completion or impact.",
        source_object_type="organizational_work_item",
        source_object_id=str(work_item.id),
        source_object_version=source_version,
        occurred_at=work_item.updated_at,
        work_item_id=work_item.id,
        causation_activity_id=causation_activity_id,
        payload=payload,
    )


def _stage_assignment(
    session: Session,
    context: OrganizationCommandContext,
    work_item: OrganizationalWorkItem,
    *,
    assigned_position_key: str,
    reason: str,
    causation_activity_id: UUID,
) -> bool:
    """Stage the existing WorkItem assignment semantics without owning the transaction."""

    require_mutation_role(context)
    if work_item.status in {"completed", "cancelled", "failed", "rejected", "returned"}:
        raise InvalidTransition("terminal work cannot be reassigned")
    if work_item.assigned_position_key == assigned_position_key:
        return False

    before = snapshot(work_item)
    previous_position_key = work_item.assigned_position_key
    previous_updated_at = work_item.updated_at
    work_item.assigned_position_key = assigned_position_key
    work_item.updated_at = _next_work_item_updated_at(previous_updated_at)
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
    _stage_assignment_activity_with_causation(
        session,
        context,
        work_item,
        previous_position_key=previous_position_key,
        causation_activity_id=causation_activity_id,
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

    AUTO_EXECUTE stages governance authorization first, then the existing assignment
    mutation/audit plus a semantic Activity explicitly caused by that authorization.
    The entire unit commits atomically. BLOCK/REVIEW_REQUIRED does not mutate the
    WorkItem. An exact durable retry returns IDEMPOTENT_REPLAY.
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
        mutated = _stage_assignment(
            session,
            trace_context,
            work_item,
            assigned_position_key=assigned_position_key,
            reason=reason,
            causation_activity_id=governance_activity.id,
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
