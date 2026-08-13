from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationBlocker,
    OrganizationBlockerStatus,
    OrganizationBlockerType,
    OrganizationContribution,
    OrganizationDependencyStatus,
    OrganizationDependencyType,
    OrganizationWorkItemDependency,
    OrganizationWorkPriority,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.organization_command import (
    AuditMutation,
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_payload_json,
    commit_mutations,
    idempotent_existing,
    require_human,
    require_mutation_role,
    snapshot,
    tenant_record,
)


WORK_TRANSITIONS: dict[str, frozenset[str]] = {
    "queued": frozenset({"running", "blocked", "awaiting_human", "cancelled"}),
    "running": frozenset({"blocked", "awaiting_human", "completed", "cancelled"}),
    "blocked": frozenset({"running", "awaiting_human", "cancelled"}),
    "awaiting_human": frozenset({"running", "blocked", "cancelled"}),
    # Legacy execution/governance states are intentionally not reinterpreted here.
    "held": frozenset(),
    "retry_wait": frozenset(),
    "pending_ceo": frozenset(),
    "pending_board": frozenset(),
    "completed": frozenset(),
    "cancelled": frozenset(),
    "failed": frozenset(),
    "rejected": frozenset(),
    "returned": frozenset(),
}


def create_work_item(
    session: Session,
    context: OrganizationCommandContext,
    *,
    idempotency_key: str,
    title: str,
    objective: str,
    department: str,
    authority_level: str,
    assigned_position_key: str,
    work_type: str = "organizational",
    priority: OrganizationWorkPriority | str = OrganizationWorkPriority.normal,
    parent_work_item_id: UUID | None = None,
    objective_key: str | None = None,
    phase_key: str | None = None,
    risk_level: str = "routine",
    is_emergency: bool = False,
    due_at: datetime | None = None,
    source_object_type: str | None = None,
    source_object_id: str | None = None,
    source_object_version: str | None = None,
    context_payload: Mapping[str, Any] | None = None,
) -> OrganizationalWorkItem:
    require_mutation_role(context)
    priority = OrganizationWorkPriority(priority)
    if parent_work_item_id is not None:
        tenant_record(
            session,
            OrganizationalWorkItem,
            parent_work_item_id,
            context.tenant_key,
            label="parent work item",
        )
    command = {
        "idempotency_key": idempotency_key,
        "tenant_key": context.tenant_key,
        "title": title,
        "objective": objective,
        "department": department,
        "authority_level": authority_level,
        "assigned_position_key": assigned_position_key,
        "work_type": work_type,
        "priority": priority,
        "parent_work_item_id": parent_work_item_id,
        "objective_key": objective_key,
        "phase_key": phase_key,
        "risk_level": risk_level,
        "is_emergency": is_emergency,
        "due_at": due_at,
        "source_object_type": source_object_type,
        "source_object_id": source_object_id,
        "source_object_version": source_object_version,
        "context_payload": context_payload or {},
        "requestor_type": context.actor_type,
        "requestor_id": context.actor_id,
    }
    fingerprint = canonical_fingerprint(command)
    # The historic DB uniqueness is global for this key, so check globally and fail
    # closed if another tenant owns it.
    existing = session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.idempotency_key == idempotency_key)
    ).first()
    if existing is not None and existing.tenant_key != context.tenant_key:
        raise DependencyConflict("work item idempotency key is unavailable")
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="idempotency_fingerprint",
        label="work item",
    )
    if replay is not None:
        return replay
    row = OrganizationalWorkItem(
        idempotency_key=idempotency_key,
        idempotency_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        work_type=work_type,
        objective_key=objective_key,
        phase_key=phase_key,
        priority=priority,
        parent_work_item_id=parent_work_item_id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
        requested_by_type=context.actor_type,
        requested_by_id=context.actor_id,
        title=title,
        objective=objective,
        department=department,
        authority_level=authority_level,
        assigned_position_key=assigned_position_key,
        risk_level=risk_level,
        is_emergency=is_emergency,
        due_at=due_at,
        context_json=canonical_payload_json(context_payload),
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation("organization.work.create", "organizational_work_item", row.id, after_state=row)],
        context=context,
        refresh=(row,),
    )
    return row


def transition_work_item(
    session: Session,
    context: OrganizationCommandContext,
    *,
    work_item_id: UUID,
    target_status: str,
    reason: str,
) -> OrganizationalWorkItem:
    require_mutation_role(context)
    row = tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    if row.status == target_status:
        return row
    allowed = WORK_TRANSITIONS.get(row.status, frozenset())
    if target_status not in allowed:
        raise InvalidTransition(f"work item cannot transition from {row.status!r} to {target_status!r}")
    before = snapshot(row)
    row.status = target_status
    row.updated_at = now_utc()
    if target_status == "completed":
        row.completed_at = row.updated_at
    if target_status == "cancelled":
        row.cancel_requested_at = row.updated_at
        row.cancelled_at = row.updated_at
        row.cancelled_by = context.actor_id
        row.cancellation_reason = reason
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                f"organization.work.{target_status}",
                "organizational_work_item",
                row.id,
                before_state=before,
                after_state=row,
                reason=reason,
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def start_work_item(session: Session, context: OrganizationCommandContext, *, work_item_id: UUID, reason: str) -> OrganizationalWorkItem:
    return transition_work_item(session, context, work_item_id=work_item_id, target_status="running", reason=reason)


def block_work_item(session: Session, context: OrganizationCommandContext, *, work_item_id: UUID, reason: str) -> OrganizationalWorkItem:
    return transition_work_item(session, context, work_item_id=work_item_id, target_status="blocked", reason=reason)


def await_human_for_work_item(session: Session, context: OrganizationCommandContext, *, work_item_id: UUID, reason: str) -> OrganizationalWorkItem:
    return transition_work_item(session, context, work_item_id=work_item_id, target_status="awaiting_human", reason=reason)


def complete_work_item(session: Session, context: OrganizationCommandContext, *, work_item_id: UUID, reason: str) -> OrganizationalWorkItem:
    return transition_work_item(session, context, work_item_id=work_item_id, target_status="completed", reason=reason)


def cancel_work_item(session: Session, context: OrganizationCommandContext, *, work_item_id: UUID, reason: str) -> OrganizationalWorkItem:
    return transition_work_item(session, context, work_item_id=work_item_id, target_status="cancelled", reason=reason)


def assign_work_item(
    session: Session,
    context: OrganizationCommandContext,
    *,
    work_item_id: UUID,
    assigned_position_key: str,
    reason: str,
) -> OrganizationalWorkItem:
    require_mutation_role(context)
    row = tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    if row.status in {"completed", "cancelled", "failed", "rejected", "returned"}:
        raise InvalidTransition("terminal work cannot be reassigned")
    if row.assigned_position_key == assigned_position_key:
        return row
    before = snapshot(row)
    row.assigned_position_key = assigned_position_key
    row.updated_at = now_utc()
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation("organization.work.assign", "organizational_work_item", row.id, before, row, reason)],
        context=context,
        refresh=(row,),
    )
    return row


def _cycle_exists(session: Session, tenant_key: str, work_item_id: UUID, depends_on_id: UUID) -> bool:
    # Adding work -> depends_on is a cycle when depends_on can already reach work.
    frontier = [depends_on_id]
    visited: set[UUID] = set()
    while frontier:
        current = frontier.pop()
        if current == work_item_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        edges = session.exec(
            select(OrganizationWorkItemDependency).where(
                OrganizationWorkItemDependency.tenant_key == tenant_key,
                OrganizationWorkItemDependency.work_item_id == current,
                OrganizationWorkItemDependency.status == OrganizationDependencyStatus.active,
            )
        ).all()
        frontier.extend(edge.depends_on_work_item_id for edge in edges)
    return False


def create_dependency(
    session: Session,
    context: OrganizationCommandContext,
    *,
    dependency_key: str,
    work_item_id: UUID,
    depends_on_work_item_id: UUID,
    dependency_type: OrganizationDependencyType | str,
) -> OrganizationWorkItemDependency:
    require_mutation_role(context)
    dependency_type = OrganizationDependencyType(dependency_type)
    if work_item_id == depends_on_work_item_id:
        raise DependencyConflict("work item cannot depend on itself")
    tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    tenant_record(session, OrganizationalWorkItem, depends_on_work_item_id, context.tenant_key, label="dependency work item")
    command = {
        "dependency_key": dependency_key,
        "tenant_key": context.tenant_key,
        "work_item_id": work_item_id,
        "depends_on_work_item_id": depends_on_work_item_id,
        "dependency_type": dependency_type,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationWorkItemDependency).where(
            OrganizationWorkItemDependency.tenant_key == context.tenant_key,
            OrganizationWorkItemDependency.dependency_key == dependency_key,
        )
    ).first()
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="dependency")
    if replay is not None:
        return replay
    duplicate = session.exec(
        select(OrganizationWorkItemDependency).where(
            OrganizationWorkItemDependency.tenant_key == context.tenant_key,
            OrganizationWorkItemDependency.work_item_id == work_item_id,
            OrganizationWorkItemDependency.depends_on_work_item_id == depends_on_work_item_id,
            OrganizationWorkItemDependency.dependency_type == dependency_type,
        )
    ).first()
    if duplicate is not None:
        raise DependencyConflict("dependency edge already exists under another key")
    if _cycle_exists(session, context.tenant_key, work_item_id, depends_on_work_item_id):
        raise DependencyConflict("dependency would create a cycle")
    row = OrganizationWorkItemDependency(
        dependency_key=dependency_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        work_item_id=work_item_id,
        depends_on_work_item_id=depends_on_work_item_id,
        dependency_type=dependency_type,
        created_by=context.actor_id,
        updated_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation("organization.dependency.create", "organization_work_item_dependency", row.id, after_state=row)],
        context=context,
        refresh=(row,),
    )
    return row


def _transition_dependency(
    session: Session,
    context: OrganizationCommandContext,
    *,
    dependency_id: UUID,
    target_status: OrganizationDependencyStatus,
    reason: str,
    contribution_id: UUID | None = None,
) -> OrganizationWorkItemDependency:
    if target_status is OrganizationDependencyStatus.waived:
        require_human(context, admin=True)
        if not reason.strip():
            raise DependencyConflict("waiver reason is required")
    elif target_status in {
        OrganizationDependencyStatus.satisfied,
        OrganizationDependencyStatus.superseded,
    }:
        require_mutation_role(context)
    contribution = None
    if target_status is OrganizationDependencyStatus.satisfied:
        if contribution_id is None:
            raise DependencyConflict("satisfaction requires an authoritative contribution")
        contribution = tenant_record(
            session,
            OrganizationContribution,
            contribution_id,
            context.tenant_key,
            label="contribution",
        )
    row = tenant_record(
        session,
        OrganizationWorkItemDependency,
        dependency_id,
        context.tenant_key,
        label="dependency",
    )
    if row.status == target_status:
        return row
    if row.status is not OrganizationDependencyStatus.active:
        raise InvalidTransition("only an active dependency can transition")
    before = snapshot(row)
    row.status = target_status
    row.updated_by = context.actor_id
    row.updated_at = now_utc()
    if target_status is OrganizationDependencyStatus.satisfied:
        assert contribution is not None
        row.satisfied_by_contribution_id = contribution_id
    if target_status is OrganizationDependencyStatus.waived:
        row.waived_by_human_id = context.actor_id
        row.waiver_reason = reason
        row.waived_at = row.updated_at
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation(f"organization.dependency.{target_status.value}", "organization_work_item_dependency", row.id, before, row, reason)],
        context=context,
        refresh=(row,),
    )
    return row


def satisfy_dependency(session: Session, context: OrganizationCommandContext, *, dependency_id: UUID, contribution_id: UUID, reason: str) -> OrganizationWorkItemDependency:
    require_mutation_role(context)
    return _transition_dependency(session, context, dependency_id=dependency_id, target_status=OrganizationDependencyStatus.satisfied, reason=reason, contribution_id=contribution_id)


def waive_dependency(session: Session, context: OrganizationCommandContext, *, dependency_id: UUID, reason: str) -> OrganizationWorkItemDependency:
    return _transition_dependency(session, context, dependency_id=dependency_id, target_status=OrganizationDependencyStatus.waived, reason=reason)


def supersede_dependency(session: Session, context: OrganizationCommandContext, *, dependency_id: UUID, reason: str) -> OrganizationWorkItemDependency:
    require_mutation_role(context)
    return _transition_dependency(session, context, dependency_id=dependency_id, target_status=OrganizationDependencyStatus.superseded, reason=reason)


def open_blocker(
    session: Session,
    context: OrganizationCommandContext,
    *,
    blocker_key: str,
    blocker_type: OrganizationBlockerType | str,
    severity: str,
    title: str,
    description: str,
    work_item_id: UUID | None = None,
    decision_id: UUID | None = None,
    contribution_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    department: str | None = None,
    accountable_position_key: str | None = None,
    authority_level: str | None = None,
    requires_human_action: bool = False,
    due_at: datetime | None = None,
    source_object_type: str | None = None,
    source_object_id: str | None = None,
    source_object_version: str | None = None,
    supersedes_blocker_id: UUID | None = None,
) -> OrganizationBlocker:
    require_mutation_role(context)
    blocker_type = OrganizationBlockerType(blocker_type)
    targets = [work_item_id, decision_id, contribution_id, lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id]
    if not any(targets):
        raise DependencyConflict("blocker requires a target")
    if work_item_id:
        tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    if decision_id:
        tenant_record(session, ExecutiveDecision, decision_id, context.tenant_key, label="decision")
    if contribution_id:
        tenant_record(session, OrganizationContribution, contribution_id, context.tenant_key, label="contribution")
    if any((lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id)) and context.tenant_key != "default":
        raise DependencyConflict("legacy target records are available only in authenticated tenant 'default'")
    predecessor = None
    if supersedes_blocker_id:
        predecessor = tenant_record(session, OrganizationBlocker, supersedes_blocker_id, context.tenant_key, label="superseded blocker")
    command = {
        "blocker_key": blocker_key,
        "blocker_type": blocker_type,
        "severity": severity,
        "title": title,
        "description": description,
        "targets": targets,
        "department": department,
        "accountable_position_key": accountable_position_key,
        "authority_level": authority_level,
        "requires_human_action": requires_human_action,
        "due_at": due_at,
        "source": [source_object_type, source_object_id, source_object_version],
        "supersedes_blocker_id": supersedes_blocker_id,
        "tenant_key": context.tenant_key,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(select(OrganizationBlocker).where(OrganizationBlocker.tenant_key == context.tenant_key, OrganizationBlocker.blocker_key == blocker_key)).first()
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="blocker")
    if replay is not None:
        return replay
    if predecessor is not None and predecessor.status not in {
        OrganizationBlockerStatus.open,
        OrganizationBlockerStatus.mitigated,
    }:
        raise InvalidTransition("only an active blocker can be superseded")
    row = OrganizationBlocker(
        blocker_key=blocker_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        blocker_type=blocker_type,
        severity=severity,
        title=title,
        description=description,
        department=department,
        accountable_position_key=accountable_position_key,
        authority_level=authority_level,
        work_item_id=work_item_id,
        decision_id=decision_id,
        contribution_id=contribution_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
        requires_human_action=requires_human_action,
        due_at=due_at,
        supersedes_blocker_id=supersedes_blocker_id,
        created_by=context.actor_id,
        updated_by=context.actor_id,
    )
    session.add(row)
    mutations = [AuditMutation("organization.blocker.open", "organization_blocker", row.id, after_state=row)]
    if predecessor is not None:
        before = snapshot(predecessor)
        predecessor.status = OrganizationBlockerStatus.superseded
        predecessor.updated_at = now_utc()
        predecessor.updated_by = context.actor_id
        session.add(predecessor)
        mutations.append(AuditMutation("organization.blocker.superseded", "organization_blocker", predecessor.id, before, predecessor, f"superseded by {blocker_key}"))
    commit_mutations(session, mutations=mutations, context=context, refresh=(row,))
    return row


def transition_blocker(
    session: Session,
    context: OrganizationCommandContext,
    *,
    blocker_id: UUID,
    target_status: OrganizationBlockerStatus | str,
    reason: str,
) -> OrganizationBlocker:
    require_mutation_role(context)
    target_status = OrganizationBlockerStatus(target_status)
    if target_status is OrganizationBlockerStatus.waived:
        require_human(context, admin=True)
        if not reason.strip():
            raise DependencyConflict("waiver reason is required")
    row = tenant_record(session, OrganizationBlocker, blocker_id, context.tenant_key, label="blocker")
    if row.status == target_status:
        return row
    allowed = {
        OrganizationBlockerStatus.open: {OrganizationBlockerStatus.mitigated, OrganizationBlockerStatus.resolved, OrganizationBlockerStatus.waived},
        OrganizationBlockerStatus.mitigated: {OrganizationBlockerStatus.resolved, OrganizationBlockerStatus.waived},
    }.get(row.status, set())
    if target_status not in allowed:
        raise InvalidTransition(f"blocker cannot transition from {row.status.value} to {target_status.value}")
    before = snapshot(row)
    timestamp = now_utc()
    row.status = target_status
    row.updated_at = timestamp
    row.updated_by = context.actor_id
    if target_status is OrganizationBlockerStatus.mitigated:
        row.mitigated_at = timestamp
        row.resolution_summary = reason
    elif target_status is OrganizationBlockerStatus.resolved:
        row.resolved_at = timestamp
        row.resolution_summary = reason
        row.resolving_actor_type = context.actor_type
        row.resolving_actor_id = context.actor_id
    elif target_status is OrganizationBlockerStatus.waived:
        row.waived_by_human_id = context.actor_id
        row.waiver_reason = reason
        row.waived_at = timestamp
    session.add(row)
    commit_mutations(
        session,
        mutations=[AuditMutation(f"organization.blocker.{target_status.value}", "organization_blocker", row.id, before, row, reason)],
        context=context,
        refresh=(row,),
    )
    return row


def mitigate_blocker(session: Session, context: OrganizationCommandContext, *, blocker_id: UUID, reason: str) -> OrganizationBlocker:
    return transition_blocker(session, context, blocker_id=blocker_id, target_status=OrganizationBlockerStatus.mitigated, reason=reason)


def resolve_blocker(session: Session, context: OrganizationCommandContext, *, blocker_id: UUID, reason: str) -> OrganizationBlocker:
    return transition_blocker(session, context, blocker_id=blocker_id, target_status=OrganizationBlockerStatus.resolved, reason=reason)


def waive_blocker(session: Session, context: OrganizationCommandContext, *, blocker_id: UUID, reason: str) -> OrganizationBlocker:
    return transition_blocker(session, context, blocker_id=blocker_id, target_status=OrganizationBlockerStatus.waived, reason=reason)
