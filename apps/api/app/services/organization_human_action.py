from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from sqlmodel import Session, select

from app.core.auth_policy import ROLES
from app.models.domain import (
    ExecutiveDecision,
    OrganizationBlocker,
    OrganizationContribution,
    OrganizationHumanAction,
    OrganizationHumanActionRequest,
    OrganizationHumanActionRequestStatus,
    OrganizationHumanActionRequestType,
    OrganizationHumanActionType,
    OrganizationWorkPriority,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.organization_command import (
    AuditMutation,
    AuthorityDenied,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_payload_json,
    idempotent_existing,
    require_human,
    require_mutation_role,
    snapshot,
    stage_mutations,
    tenant_record,
)
from app.services.organization_semantic_activity import (
    stage_human_action_appended_activity,
    stage_human_request_assignment_activity,
    stage_human_request_created_activity,
    stage_human_request_status_activity,
)


REQUEST_TRANSITIONS: dict[OrganizationHumanActionRequestStatus, frozenset[OrganizationHumanActionRequestStatus]] = {
    OrganizationHumanActionRequestStatus.required: frozenset(
        {
            OrganizationHumanActionRequestStatus.acknowledged,
            OrganizationHumanActionRequestStatus.completed,
            OrganizationHumanActionRequestStatus.declined,
            OrganizationHumanActionRequestStatus.cancelled,
            OrganizationHumanActionRequestStatus.expired,
        }
    ),
    OrganizationHumanActionRequestStatus.acknowledged: frozenset(
        {
            OrganizationHumanActionRequestStatus.in_progress,
            OrganizationHumanActionRequestStatus.completed,
            OrganizationHumanActionRequestStatus.declined,
            OrganizationHumanActionRequestStatus.cancelled,
            OrganizationHumanActionRequestStatus.expired,
        }
    ),
    OrganizationHumanActionRequestStatus.in_progress: frozenset(
        {
            OrganizationHumanActionRequestStatus.completed,
            OrganizationHumanActionRequestStatus.declined,
            OrganizationHumanActionRequestStatus.cancelled,
            OrganizationHumanActionRequestStatus.expired,
        }
    ),
}


def _validate_targets(
    session: Session,
    context: OrganizationCommandContext,
    *,
    human_action_request_id: UUID | None = None,
    work_item_id: UUID | None = None,
    decision_id: UUID | None = None,
    blocker_id: UUID | None = None,
    contribution_id: UUID | None = None,
    legacy_target_present: bool = False,
) -> None:
    if human_action_request_id:
        tenant_record(session, OrganizationHumanActionRequest, human_action_request_id, context.tenant_key, label="human action request")
    if work_item_id:
        tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    if decision_id:
        tenant_record(session, ExecutiveDecision, decision_id, context.tenant_key, label="decision")
    if blocker_id:
        tenant_record(session, OrganizationBlocker, blocker_id, context.tenant_key, label="blocker")
    if contribution_id:
        tenant_record(session, OrganizationContribution, contribution_id, context.tenant_key, label="contribution")
    if legacy_target_present and context.tenant_key != "default":
        raise InvalidReference("legacy target records are available only in authenticated tenant 'default'")


def create_human_action_request(
    session: Session,
    context: OrganizationCommandContext,
    *,
    request_key: str,
    request_type: OrganizationHumanActionRequestType | str,
    title: str,
    instructions: str,
    required_role: str,
    priority: OrganizationWorkPriority | str = OrganizationWorkPriority.normal,
    assigned_human_id: str | None = None,
    authority_level: str | None = None,
    work_item_id: UUID | None = None,
    decision_id: UUID | None = None,
    blocker_id: UUID | None = None,
    contribution_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    source_object_type: str | None = None,
    source_object_id: str | None = None,
    source_object_version: str | None = None,
    due_at: datetime | None = None,
) -> OrganizationHumanActionRequest:
    require_mutation_role(context)
    request_type = OrganizationHumanActionRequestType(request_type)
    priority = OrganizationWorkPriority(priority)
    targets = [work_item_id, decision_id, blocker_id, contribution_id, lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id]
    if not any(targets):
        raise InvalidReference("human action request requires a target")
    _validate_targets(
        session,
        context,
        work_item_id=work_item_id,
        decision_id=decision_id,
        blocker_id=blocker_id,
        contribution_id=contribution_id,
        legacy_target_present=any((lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id)),
    )
    command = {
        "request_key": request_key,
        "request_type": request_type,
        "title": title,
        "instructions": instructions,
        "required_role": required_role,
        "priority": priority,
        "assigned_human_id": assigned_human_id,
        "authority_level": authority_level,
        "targets": targets,
        "source": [source_object_type, source_object_id, source_object_version],
        "due_at": due_at,
        "tenant_key": context.tenant_key,
        "requested_by_type": context.actor_type,
        "requested_by_id": context.actor_id,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationHumanActionRequest).where(
            OrganizationHumanActionRequest.tenant_key == context.tenant_key,
            OrganizationHumanActionRequest.request_key == request_key,
        )
    ).first()
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="human action request")
    if replay is not None:
        return replay
    row = OrganizationHumanActionRequest(
        request_key=request_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        request_type=request_type,
        title=title,
        instructions=instructions,
        priority=priority,
        required_role=required_role,
        assigned_human_id=assigned_human_id,
        requested_by_type=context.actor_type,
        requested_by_id=context.actor_id,
        authority_level=authority_level,
        work_item_id=work_item_id,
        decision_id=decision_id,
        blocker_id=blocker_id,
        contribution_id=contribution_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
        due_at=due_at,
        created_by=context.actor_id,
        updated_by=context.actor_id,
    )
    session.add(row)
    try:
        stage_mutations(
            session,
            mutations=[
                AuditMutation(
                    "organization.human_request.create",
                    "organization_human_action_request",
                    row.id,
                    after_state=row,
                )
            ],
            context=context,
        )
        stage_human_request_created_activity(session, context, row)
        session.commit()
        session.refresh(row)
    except Exception:
        session.rollback()
        raise
    return row


def assign_human_action_request(
    session: Session,
    context: OrganizationCommandContext,
    *,
    request_id: UUID,
    assigned_human_id: str,
    reason: str,
) -> OrganizationHumanActionRequest:
    require_mutation_role(context)
    row = tenant_record(session, OrganizationHumanActionRequest, request_id, context.tenant_key, label="human action request")
    if row.status not in REQUEST_TRANSITIONS:
        raise InvalidTransition("terminal human action request cannot be assigned")
    if row.assigned_human_id == assigned_human_id:
        return row
    before = snapshot(row)
    previously_assigned = row.assigned_human_id is not None
    row.assigned_human_id = assigned_human_id
    row.updated_by = context.actor_id
    row.updated_at = now_utc()
    session.add(row)
    try:
        stage_mutations(
            session,
            mutations=[
                AuditMutation(
                    "organization.human_request.assign",
                    "organization_human_action_request",
                    row.id,
                    before,
                    row,
                    reason,
                )
            ],
            context=context,
        )
        stage_human_request_assignment_activity(
            session,
            context,
            row,
            previously_assigned=previously_assigned,
        )
        session.commit()
        session.refresh(row)
    except Exception:
        session.rollback()
        raise
    return row


def _require_assigned_human(context: OrganizationCommandContext, row: OrganizationHumanActionRequest) -> None:
    require_human(context)
    if row.assigned_human_id and row.assigned_human_id != context.actor_id and context.role != "admin":
        raise AuthorityDenied("only the assigned human or an admin supervisor may act on this request")
    if row.required_role in ROLES:
        if context.role != row.required_role and context.role != "admin":
            raise AuthorityDenied("human actor does not hold the request's required role")
    elif context.position_key != row.required_role and context.role != "admin":
        raise AuthorityDenied("human actor does not hold the request's required position")


def transition_human_action_request(
    session: Session,
    context: OrganizationCommandContext,
    *,
    request_id: UUID,
    target_status: OrganizationHumanActionRequestStatus | str,
    outcome: str | None = None,
) -> OrganizationHumanActionRequest:
    row = tenant_record(session, OrganizationHumanActionRequest, request_id, context.tenant_key, label="human action request")
    target_status = OrganizationHumanActionRequestStatus(target_status)
    if target_status is OrganizationHumanActionRequestStatus.completed:
        raise InvalidTransition("complete the request through complete_human_action_request so a HumanAction is appended")
    if target_status in {
        OrganizationHumanActionRequestStatus.acknowledged,
        OrganizationHumanActionRequestStatus.in_progress,
        OrganizationHumanActionRequestStatus.declined,
    }:
        _require_assigned_human(context, row)
    else:
        require_mutation_role(context)
    if row.status == target_status:
        return row
    if target_status not in REQUEST_TRANSITIONS.get(row.status, frozenset()):
        raise InvalidTransition(f"human action request cannot transition from {row.status.value} to {target_status.value}")
    if target_status in {OrganizationHumanActionRequestStatus.declined, OrganizationHumanActionRequestStatus.cancelled} and not (outcome or "").strip():
        raise InvalidTransition("decline/cancel outcome is required")
    before = snapshot(row)
    previous_status = row.status.value
    timestamp = now_utc()
    row.status = target_status
    row.updated_at = timestamp
    row.updated_by = context.actor_id
    if target_status is OrganizationHumanActionRequestStatus.acknowledged:
        row.acknowledged_at = timestamp
        row.acknowledged_by_human_id = context.actor_id
    elif target_status is OrganizationHumanActionRequestStatus.in_progress:
        row.started_at = timestamp
        row.started_by_human_id = context.actor_id
    elif target_status is OrganizationHumanActionRequestStatus.declined:
        row.declined_at = timestamp
        row.declined_by_human_id = context.actor_id
        row.outcome = outcome
    elif target_status is OrganizationHumanActionRequestStatus.cancelled:
        row.cancelled_at = timestamp
        row.cancelled_by_actor_id = context.actor_id
        row.outcome = outcome
    elif target_status is OrganizationHumanActionRequestStatus.expired:
        row.expired_at = timestamp
        row.outcome = outcome
    session.add(row)
    try:
        stage_mutations(
            session,
            mutations=[
                AuditMutation(
                    f"organization.human_request.{target_status.value}",
                    "organization_human_action_request",
                    row.id,
                    before,
                    row,
                    outcome,
                )
            ],
            context=context,
        )
        stage_human_request_status_activity(
            session,
            context,
            row,
            previous_status=previous_status,
        )
        session.commit()
        session.refresh(row)
    except Exception:
        session.rollback()
        raise
    return row


def acknowledge_human_action_request(session: Session, context: OrganizationCommandContext, *, request_id: UUID) -> OrganizationHumanActionRequest:
    return transition_human_action_request(session, context, request_id=request_id, target_status=OrganizationHumanActionRequestStatus.acknowledged)


def start_human_action_request(session: Session, context: OrganizationCommandContext, *, request_id: UUID) -> OrganizationHumanActionRequest:
    return transition_human_action_request(session, context, request_id=request_id, target_status=OrganizationHumanActionRequestStatus.in_progress)


def decline_human_action_request(session: Session, context: OrganizationCommandContext, *, request_id: UUID, outcome: str) -> OrganizationHumanActionRequest:
    return transition_human_action_request(session, context, request_id=request_id, target_status=OrganizationHumanActionRequestStatus.declined, outcome=outcome)


def cancel_human_action_request(session: Session, context: OrganizationCommandContext, *, request_id: UUID, outcome: str) -> OrganizationHumanActionRequest:
    return transition_human_action_request(session, context, request_id=request_id, target_status=OrganizationHumanActionRequestStatus.cancelled, outcome=outcome)


def expire_human_action_request(session: Session, context: OrganizationCommandContext, *, request_id: UUID, outcome: str | None = None) -> OrganizationHumanActionRequest:
    return transition_human_action_request(session, context, request_id=request_id, target_status=OrganizationHumanActionRequestStatus.expired, outcome=outcome)


def _build_human_action(
    session: Session,
    context: OrganizationCommandContext,
    *,
    action_key: str,
    action_type: OrganizationHumanActionType | str,
    outcome: str,
    occurred_at: datetime,
    reason: str | None,
    metadata: Mapping[str, Any] | None,
    human_action_request_id: UUID | None,
    work_item_id: UUID | None,
    decision_id: UUID | None,
    blocker_id: UUID | None,
    contribution_id: UUID | None,
    lead_id: UUID | None,
    profile_id: UUID | None,
    application_id: UUID | None,
    corporate_account_id: UUID | None,
    corporate_mobility_case_id: UUID | None,
    source_object_type: str | None,
    source_object_id: str | None,
    source_object_version: str | None,
) -> tuple[OrganizationHumanAction, bool]:
    require_human(context)
    action_type = OrganizationHumanActionType(action_type)
    targets = [human_action_request_id, work_item_id, decision_id, blocker_id, contribution_id, lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id]
    if not any(targets):
        raise InvalidReference("human action requires a target")
    _validate_targets(
        session,
        context,
        human_action_request_id=human_action_request_id,
        work_item_id=work_item_id,
        decision_id=decision_id,
        blocker_id=blocker_id,
        contribution_id=contribution_id,
        legacy_target_present=any((lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id)),
    )
    command = {
        "action_key": action_key,
        "action_type": action_type,
        "outcome": outcome,
        "occurred_at": occurred_at,
        "reason": reason,
        "metadata": metadata or {},
        "targets": targets,
        "source": [source_object_type, source_object_id, source_object_version],
        "tenant_key": context.tenant_key,
        "human_actor_id": context.actor_id,
        "actor_role": context.role,
        "actor_position_key": context.position_key,
        "actor_department": context.department,
        "authority_level": context.authority_level,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationHumanAction).where(
            OrganizationHumanAction.tenant_key == context.tenant_key,
            OrganizationHumanAction.action_key == action_key,
        )
    ).first()
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="human action")
    if replay is not None:
        return replay, True
    row = OrganizationHumanAction(
        action_key=action_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        human_action_request_id=human_action_request_id,
        action_type=action_type,
        human_actor_id=context.actor_id,
        actor_role=context.role,
        actor_position_key=context.position_key,
        actor_department=context.department,
        authority_level=context.authority_level,
        work_item_id=work_item_id,
        decision_id=decision_id,
        blocker_id=blocker_id,
        contribution_id=contribution_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
        outcome=outcome,
        reason=reason,
        metadata_json=canonical_payload_json(metadata),
        occurred_at=occurred_at,
        created_by=context.actor_id,
    )
    return row, False


def append_human_action(
    session: Session,
    context: OrganizationCommandContext,
    *,
    action_key: str,
    action_type: OrganizationHumanActionType | str,
    outcome: str,
    occurred_at: datetime,
    reason: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    human_action_request_id: UUID | None = None,
    work_item_id: UUID | None = None,
    decision_id: UUID | None = None,
    blocker_id: UUID | None = None,
    contribution_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    source_object_type: str | None = None,
    source_object_id: str | None = None,
    source_object_version: str | None = None,
) -> OrganizationHumanAction:
    row, replay = _build_human_action(
        session,
        context,
        action_key=action_key,
        action_type=action_type,
        outcome=outcome,
        occurred_at=occurred_at,
        reason=reason,
        metadata=metadata,
        human_action_request_id=human_action_request_id,
        work_item_id=work_item_id,
        decision_id=decision_id,
        blocker_id=blocker_id,
        contribution_id=contribution_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
    )
    if replay:
        return row
    session.add(row)
    try:
        stage_mutations(
            session,
            mutations=[
                AuditMutation(
                    "organization.human_action.append",
                    "organization_human_action",
                    row.id,
                    after_state=row,
                )
            ],
            context=context,
        )
        stage_human_action_appended_activity(session, context, row)
        session.commit()
        session.refresh(row)
    except Exception:
        session.rollback()
        raise
    return row


def complete_human_action_request(
    session: Session,
    context: OrganizationCommandContext,
    *,
    request_id: UUID,
    action_key: str,
    action_type: OrganizationHumanActionType | str,
    outcome: str,
    occurred_at: datetime,
    reason: str | None = None,
    completion_notes: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> tuple[OrganizationHumanActionRequest, OrganizationHumanAction]:
    request = tenant_record(session, OrganizationHumanActionRequest, request_id, context.tenant_key, label="human action request")
    _require_assigned_human(context, request)
    action, replay = _build_human_action(
        session,
        context,
        action_key=action_key,
        action_type=action_type,
        outcome=outcome,
        occurred_at=occurred_at,
        reason=reason,
        metadata=metadata,
        human_action_request_id=request.id,
        work_item_id=request.work_item_id,
        decision_id=request.decision_id,
        blocker_id=request.blocker_id,
        contribution_id=request.contribution_id,
        lead_id=request.lead_id,
        profile_id=request.profile_id,
        application_id=request.application_id,
        corporate_account_id=request.corporate_account_id,
        corporate_mobility_case_id=request.corporate_mobility_case_id,
        source_object_type=request.source_object_type,
        source_object_id=request.source_object_id,
        source_object_version=request.source_object_version,
    )
    if replay:
        if request.status is not OrganizationHumanActionRequestStatus.completed:
            raise InvalidTransition("human action replay exists but request is not completed")
        return request, action
    if OrganizationHumanActionRequestStatus.completed not in REQUEST_TRANSITIONS.get(request.status, frozenset()):
        raise InvalidTransition("human action request cannot be completed from its current state")
    before = snapshot(request)
    previous_status = request.status.value
    request.status = OrganizationHumanActionRequestStatus.completed
    request.completed_at = now_utc()
    request.completed_by_human_id = context.actor_id
    request.outcome = outcome
    request.completion_notes = completion_notes
    request.updated_by = context.actor_id
    request.updated_at = request.completed_at
    session.add(action)
    session.add(request)
    try:
        stage_mutations(
            session,
            mutations=[
                AuditMutation(
                    "organization.human_action.append",
                    "organization_human_action",
                    action.id,
                    after_state=action,
                ),
                AuditMutation(
                    "organization.human_request.completed",
                    "organization_human_action_request",
                    request.id,
                    before,
                    request,
                    reason,
                ),
            ],
            context=context,
        )
        action_activity = stage_human_action_appended_activity(
            session,
            context,
            action,
        )
        stage_human_request_status_activity(
            session,
            context,
            request,
            previous_status=previous_status,
            causation_activity_id=action_activity.id,
        )
        session.commit()
        session.refresh(request)
        session.refresh(action)
    except Exception:
        session.rollback()
        raise
    return request, action
