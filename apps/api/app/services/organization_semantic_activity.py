from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from sqlmodel import Session

from app.models.domain import (
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationBlocker,
    OrganizationContribution,
    OrganizationHumanAction,
    OrganizationHumanActionRequest,
    OrganizationWorkItemDependency,
    OrganizationalWorkItem,
)
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    OrganizationCommandContext,
    canonical_fingerprint,
    tenant_record,
)


SEMANTIC_ACTIVITY_CONTRACT_VERSION = "v1"


def _event_version(
    *,
    source_type: str,
    source_id: UUID | str,
    activity_type: str,
    occurred_at: datetime,
    payload: Mapping[str, Any],
) -> str:
    return canonical_fingerprint(
        {
            "contract": SEMANTIC_ACTIVITY_CONTRACT_VERSION,
            "source_type": source_type,
            "source_id": str(source_id),
            "activity_type": activity_type,
            "occurred_at": occurred_at,
            "payload": dict(payload),
        }
    )


def _stage_semantic_activity(
    session: Session,
    context: OrganizationCommandContext,
    *,
    source_type: str,
    source_id: UUID | str,
    stream_key: str,
    activity_class: OrganizationActivityClass | str,
    activity_type: str,
    title: str,
    summary: str,
    occurred_at: datetime,
    payload: Mapping[str, Any],
    department: str | None = None,
    work_item_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    causation_activity_id: UUID | None = None,
) -> OrganizationActivity:
    source_version = _event_version(
        source_type=source_type,
        source_id=source_id,
        activity_type=activity_type,
        occurred_at=occurred_at,
        payload=payload,
    )
    activity_context = context if department is None else replace(context, department=department)
    return stage_activity(
        session,
        activity_context,
        activity_key=(
            f"semantic:{source_type}:{source_id}:{activity_type}:{source_version}"
        ),
        stream_key=stream_key,
        activity_class=activity_class,
        activity_type=activity_type,
        title=title,
        summary=summary,
        source_object_type=source_type,
        source_object_id=str(source_id),
        source_object_version=source_version,
        occurred_at=occurred_at,
        work_item_id=work_item_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        causation_activity_id=causation_activity_id,
        payload=payload,
    )


def _linked_work_department(
    session: Session,
    context: OrganizationCommandContext,
    work_item_id: UUID | None,
) -> str | None:
    if work_item_id is None:
        return None
    work = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        context.tenant_key,
        label="activity-linked work item",
    )
    return work.department


def _blocker_department(
    session: Session,
    context: OrganizationCommandContext,
    blocker: OrganizationBlocker,
) -> str | None:
    # Keep E1's accepted ownership rule: when a blocker is linked to work, the work
    # department is authoritative for organization reporting. The blocker field is a
    # fallback for blockers that do not target a WorkItem.
    return (
        _linked_work_department(session, context, blocker.work_item_id)
        or blocker.department
        or context.department
    )


def _request_department(
    session: Session,
    context: OrganizationCommandContext,
    request: OrganizationHumanActionRequest,
) -> str | None:
    work_department = _linked_work_department(session, context, request.work_item_id)
    if work_department is not None:
        return work_department
    if request.blocker_id is not None:
        blocker = tenant_record(
            session,
            OrganizationBlocker,
            request.blocker_id,
            context.tenant_key,
            label="activity-linked blocker",
        )
        return _blocker_department(session, context, blocker)
    if request.decision_id is not None:
        decision = tenant_record(
            session,
            ExecutiveDecision,
            request.decision_id,
            context.tenant_key,
            label="activity-linked decision",
        )
        return _linked_work_department(session, context, decision.work_item_id) or context.department
    return context.department


def stage_work_item_created_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
) -> OrganizationActivity:
    payload = {
        "status": work.status,
        "priority": work.priority,
        "department": work.department,
        "assigned_position_key": work.assigned_position_key,
        "parent_work_item_id": work.parent_work_item_id,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.work.created.v1",
        title="Work item created",
        summary=f"Governed organizational work was created in {work.status} state.",
        occurred_at=work.created_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_deadline_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    previous_due_at: datetime | None,
) -> OrganizationActivity:
    payload = {
        "previous_due_at": previous_due_at,
        "due_at": work.due_at,
        "status": work.status,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.work.deadline.set.v1",
        title="Work item deadline set",
        summary="The governed deadline for organizational work changed.",
        occurred_at=work.updated_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_escalation_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    previous_position_key: str,
    reason: str,
    emergency: bool,
) -> OrganizationActivity:
    payload = {
        "previous_position_key": previous_position_key,
        "assigned_position_key": work.assigned_position_key,
        "status": work.status,
        "is_emergency": work.is_emergency,
        "reason": reason,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type=(
            "organization.work.emergency_escalated.v1"
            if emergency
            else "organization.work.escalated.v1"
        ),
        title="Work item emergency escalation" if emergency else "Work item escalated",
        summary=(
            "Emergency work accountability moved to a higher governed position."
            if emergency
            else "Work accountability moved to a higher governed position."
        ),
        occurred_at=work.updated_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_emergency_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    previous_status: str,
    reason: str,
) -> OrganizationActivity:
    payload = {
        "previous_status": previous_status,
        "status": work.status,
        "authority_level": work.authority_level,
        "risk_level": work.risk_level,
        "is_emergency": work.is_emergency,
        "reason": reason,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.work.emergency_marked.v1",
        title="Work item marked emergency",
        summary="Governed work was explicitly marked as an emergency and held for escalation.",
        occurred_at=work.updated_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_cancellation_requested_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    previous_status: str,
) -> OrganizationActivity:
    payload = {
        "previous_status": previous_status,
        "status": work.status,
        "cancel_requested_at": work.cancel_requested_at,
        "cancelled_by": work.cancelled_by,
        "cancellation_reason": work.cancellation_reason,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.work.cancellation_requested.v1",
        title="Work item cancellation requested",
        summary="Cancellation of governed work was explicitly requested.",
        occurred_at=work.updated_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_retry_requested_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    previous_status: str,
    reason: str,
) -> OrganizationActivity:
    payload = {
        "previous_status": previous_status,
        "status": work.status,
        "next_attempt": work.execution_attempts + 1,
        "max_attempts": work.max_execution_attempts,
        "reason": reason,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.work.retry_requested.v1",
        title="Work item retry authorized",
        summary="A governed retry was explicitly authorized without implying execution success.",
        occurred_at=work.updated_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_evidence_amended_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    revision: int,
    evidence_keys_added: list[str],
    fact_keys_added: list[str],
    before_gaps: list[str],
    after_gaps: list[str],
) -> OrganizationActivity:
    payload = {
        "evidence_revision": revision,
        "evidence_keys_added": evidence_keys_added,
        "fact_keys_added": fact_keys_added,
        "previous_missing_evidence_fields": before_gaps,
        "missing_evidence_fields": after_gaps,
        "status": work.status,
        "external_action_authorized": False,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.work.evidence.amended.v1",
        title="Work item evidence amended",
        summary="Governed evidence context was amended without authorizing external action.",
        occurred_at=work.updated_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_status_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    previous_status: str,
) -> OrganizationActivity:
    occurred_at = work.updated_at
    payload = {
        "previous_status": previous_status,
        "status": work.status,
    }
    if work.status == "completed":
        payload["completed_at"] = work.completed_at
    if work.status == "cancelled":
        payload["cancelled_at"] = work.cancelled_at
    if work.status == "held" and work.last_error:
        payload["hold_reason"] = work.last_error
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type=f"organization.work.status.{work.status}.v1",
        title=f"Work item {work.status.replace('_', ' ')}",
        summary=f"Work item moved from {previous_status} to {work.status}.",
        occurred_at=occurred_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_work_item_assignment_activity(
    session: Session,
    context: OrganizationCommandContext,
    work: OrganizationalWorkItem,
    *,
    previous_position_key: str,
) -> OrganizationActivity:
    payload = {
        "previous_position_key": previous_position_key,
        "assigned_position_key": work.assigned_position_key,
        "status": work.status,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organizational_work_item",
        source_id=work.id,
        stream_key=f"work:{work.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.work.assigned.v1",
        title="Work item assignment changed",
        summary="Governed work assignment changed without implying completion or impact.",
        occurred_at=work.updated_at,
        payload=payload,
        department=work.department,
        work_item_id=work.id,
    )


def stage_dependency_created_activity(
    session: Session,
    context: OrganizationCommandContext,
    dependency: OrganizationWorkItemDependency,
) -> OrganizationActivity:
    work_department = _linked_work_department(session, context, dependency.work_item_id)
    payload = {
        "status": dependency.status,
        "dependency_type": dependency.dependency_type,
        "work_item_id": dependency.work_item_id,
        "depends_on_work_item_id": dependency.depends_on_work_item_id,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_work_item_dependency",
        source_id=dependency.id,
        stream_key=f"dependency:{dependency.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type="organization.dependency.created.v1",
        title="Work dependency created",
        summary="A governed dependency edge was added between WorkItems.",
        occurred_at=dependency.created_at,
        payload=payload,
        department=work_department,
        work_item_id=dependency.work_item_id,
    )


def stage_dependency_status_activity(
    session: Session,
    context: OrganizationCommandContext,
    dependency: OrganizationWorkItemDependency,
    *,
    previous_status: str,
) -> OrganizationActivity:
    work_department = _linked_work_department(session, context, dependency.work_item_id)
    payload = {
        "previous_status": previous_status,
        "status": dependency.status,
        "dependency_type": dependency.dependency_type,
        "satisfied_by_contribution_id": dependency.satisfied_by_contribution_id,
        "waived_at": dependency.waived_at,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_work_item_dependency",
        source_id=dependency.id,
        stream_key=f"dependency:{dependency.id}",
        activity_class=OrganizationActivityClass.work,
        activity_type=f"organization.dependency.status.{dependency.status.value}.v1",
        title=f"Work dependency {dependency.status.value}",
        summary=f"Dependency moved from {previous_status} to {dependency.status.value}.",
        occurred_at=dependency.updated_at,
        payload=payload,
        department=work_department,
        work_item_id=dependency.work_item_id,
    )


def stage_blocker_opened_activity(
    session: Session,
    context: OrganizationCommandContext,
    blocker: OrganizationBlocker,
) -> OrganizationActivity:
    payload = {
        "status": blocker.status,
        "blocker_type": blocker.blocker_type,
        "severity": blocker.severity,
        "requires_human_action": blocker.requires_human_action,
        "supersedes_blocker_id": blocker.supersedes_blocker_id,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_blocker",
        source_id=blocker.id,
        stream_key=f"blocker:{blocker.id}",
        activity_class=OrganizationActivityClass.blocker,
        activity_type="organization.blocker.opened.v1",
        title="Blocker opened",
        summary="A current organizational blocker was opened.",
        occurred_at=blocker.opened_at,
        payload=payload,
        department=_blocker_department(session, context, blocker),
        work_item_id=blocker.work_item_id,
        lead_id=blocker.lead_id,
        profile_id=blocker.profile_id,
        application_id=blocker.application_id,
        corporate_account_id=blocker.corporate_account_id,
        corporate_mobility_case_id=blocker.corporate_mobility_case_id,
    )


def stage_blocker_status_activity(
    session: Session,
    context: OrganizationCommandContext,
    blocker: OrganizationBlocker,
    *,
    previous_status: str,
) -> OrganizationActivity:
    payload = {
        "previous_status": previous_status,
        "status": blocker.status,
        "severity": blocker.severity,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_blocker",
        source_id=blocker.id,
        stream_key=f"blocker:{blocker.id}",
        activity_class=OrganizationActivityClass.blocker,
        activity_type=f"organization.blocker.status.{blocker.status.value}.v1",
        title=f"Blocker {blocker.status.value}",
        summary=f"Blocker moved from {previous_status} to {blocker.status.value}.",
        occurred_at=blocker.updated_at,
        payload=payload,
        department=_blocker_department(session, context, blocker),
        work_item_id=blocker.work_item_id,
        lead_id=blocker.lead_id,
        profile_id=blocker.profile_id,
        application_id=blocker.application_id,
        corporate_account_id=blocker.corporate_account_id,
        corporate_mobility_case_id=blocker.corporate_mobility_case_id,
    )


def stage_decision_created_activity(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
) -> OrganizationActivity:
    payload = {
        "status": decision.status,
        "decision_type": decision.decision_type,
        "authority_level": decision.authority_level,
        "supersedes_decision_id": decision.supersedes_decision_id,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        stream_key=f"decision:{decision.id}",
        activity_class=OrganizationActivityClass.decision,
        activity_type="organization.decision.created.v1",
        title="Executive decision created",
        summary="A governed executive decision entered its pending authority state.",
        occurred_at=decision.created_at,
        payload=payload,
        department=(
            _linked_work_department(session, context, decision.work_item_id)
            or context.department
        ),
        work_item_id=decision.work_item_id,
        lead_id=decision.lead_id,
        profile_id=decision.profile_id,
        application_id=decision.application_id,
        corporate_account_id=decision.corporate_account_id,
        corporate_mobility_case_id=decision.corporate_mobility_case_id,
    )


def stage_decision_outcome_activity(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
    *,
    previous_status: str,
) -> OrganizationActivity:
    if decision.decided_at is None:
        raise ValueError("decision outcome activity requires decided_at")
    payload = {
        "previous_status": previous_status,
        "status": decision.status,
        "decision_type": decision.decision_type,
        "authority_level": decision.authority_level,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        stream_key=f"decision:{decision.id}",
        activity_class=OrganizationActivityClass.decision,
        activity_type=f"organization.decision.status.{decision.status}.v1",
        title=f"Executive decision {decision.status}",
        summary=f"Decision moved from {previous_status} to {decision.status} by authenticated authority.",
        occurred_at=decision.decided_at,
        payload=payload,
        department=(
            _linked_work_department(session, context, decision.work_item_id)
            or context.department
        ),
        work_item_id=decision.work_item_id,
        lead_id=decision.lead_id,
        profile_id=decision.profile_id,
        application_id=decision.application_id,
        corporate_account_id=decision.corporate_account_id,
        corporate_mobility_case_id=decision.corporate_mobility_case_id,
    )



def stage_decision_deadline_activity(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
    *,
    previous_due_at: datetime | None,
) -> OrganizationActivity:
    payload = {
        "previous_due_at": previous_due_at,
        "due_at": decision.due_at,
        "status": decision.status,
        "decision_owner_position": decision.decision_owner_position,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        stream_key=f"decision:{decision.id}",
        activity_class=OrganizationActivityClass.decision,
        activity_type="organization.decision.deadline.set.v1",
        title="Executive decision deadline set",
        summary="The governed deadline for an executive decision changed.",
        occurred_at=decision.updated_at,
        payload=payload,
        department=(
            _linked_work_department(session, context, decision.work_item_id)
            or context.department
        ),
        work_item_id=decision.work_item_id,
        lead_id=decision.lead_id,
        profile_id=decision.profile_id,
        application_id=decision.application_id,
        corporate_account_id=decision.corporate_account_id,
        corporate_mobility_case_id=decision.corporate_mobility_case_id,
    )


def stage_decision_escalation_activity(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
    *,
    previous_status: str,
    previous_owner_position: str,
    previous_authority_level: str,
    reason: str,
    emergency: bool = False,
) -> OrganizationActivity:
    payload = {
        "previous_status": previous_status,
        "status": decision.status,
        "previous_owner_position": previous_owner_position,
        "decision_owner_position": decision.decision_owner_position,
        "previous_authority_level": previous_authority_level,
        "authority_level": decision.authority_level,
        "reason": reason,
        "emergency": emergency,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        stream_key=f"decision:{decision.id}",
        activity_class=OrganizationActivityClass.decision,
        activity_type=(
            "organization.decision.emergency_escalated.v1"
            if emergency
            else "organization.decision.escalated.v1"
        ),
        title=(
            "Executive decision emergency escalation"
            if emergency
            else "Executive decision escalated"
        ),
        summary=(
            "Emergency decision authority or ownership moved to a higher governed boundary."
            if emergency
            else "Decision authority or ownership moved to a higher governed boundary."
        ),
        occurred_at=decision.updated_at,
        payload=payload,
        department=(
            _linked_work_department(session, context, decision.work_item_id)
            or context.department
        ),
        work_item_id=decision.work_item_id,
        lead_id=decision.lead_id,
        profile_id=decision.profile_id,
        application_id=decision.application_id,
        corporate_account_id=decision.corporate_account_id,
        corporate_mobility_case_id=decision.corporate_mobility_case_id,
    )


def stage_decision_held_activity(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
    *,
    previous_status: str,
    reason: str,
) -> OrganizationActivity:
    payload = {
        "previous_status": previous_status,
        "status": decision.status,
        "decision_owner_position": decision.decision_owner_position,
        "authority_level": decision.authority_level,
        "reason": reason,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        stream_key=f"decision:{decision.id}",
        activity_class=OrganizationActivityClass.decision,
        activity_type="organization.decision.held.v1",
        title="Executive decision held",
        summary="CEO coordination returned a governed decision to pending review without recording an outcome.",
        occurred_at=decision.updated_at,
        payload=payload,
        department=(
            _linked_work_department(session, context, decision.work_item_id)
            or context.department
        ),
        work_item_id=decision.work_item_id,
        lead_id=decision.lead_id,
        profile_id=decision.profile_id,
        application_id=decision.application_id,
        corporate_account_id=decision.corporate_account_id,
        corporate_mobility_case_id=decision.corporate_mobility_case_id,
    )

def _contribution_stream_root(
    session: Session,
    context: OrganizationCommandContext,
    contribution: OrganizationContribution,
) -> UUID:
    """Return the immutable root outcome for a Contribution correction lineage."""

    current = contribution
    visited: set[UUID] = set()
    while current.supersedes_contribution_id is not None:
        if current.id in visited:
            raise ValueError("Contribution correction lineage contains a cycle")
        visited.add(current.id)
        current = tenant_record(
            session,
            OrganizationContribution,
            current.supersedes_contribution_id,
            context.tenant_key,
            label="superseded contribution",
        )
    return current.id


def stage_contribution_record_activity(
    session: Session,
    context: OrganizationCommandContext,
    contribution: OrganizationContribution,
) -> OrganizationActivity:
    record_kind = contribution.record_kind.value
    payload = {
        "record_kind": contribution.record_kind,
        "contribution_type": contribution.contribution_type,
        "impact_kind": contribution.impact_kind,
        "source_object_type": contribution.source_object_type,
        "source_object_id": contribution.source_object_id,
        "source_object_version": contribution.source_object_version,
        "source_state": contribution.source_state,
        "supersedes_contribution_id": contribution.supersedes_contribution_id,
    }
    stream_root = _contribution_stream_root(session, context, contribution)
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_contribution",
        source_id=contribution.id,
        stream_key=f"contribution:{stream_root}",
        activity_class=OrganizationActivityClass.contribution,
        activity_type=f"organization.contribution.{record_kind}.v1",
        title=f"Contribution {record_kind} recorded",
        summary=(
            "An immutable governed Contribution record was appended; Activity volume "
            "does not alter its verified-outcome semantics."
        ),
        occurred_at=contribution.effective_at,
        payload=payload,
        department=contribution.department,
        work_item_id=contribution.work_item_id,
        lead_id=contribution.lead_id,
        profile_id=contribution.profile_id,
        application_id=contribution.application_id,
        corporate_account_id=contribution.corporate_account_id,
        corporate_mobility_case_id=contribution.corporate_mobility_case_id,
    )


def stage_human_request_created_activity(
    session: Session,
    context: OrganizationCommandContext,
    request: OrganizationHumanActionRequest,
) -> OrganizationActivity:
    payload = {
        "status": request.status,
        "request_type": request.request_type,
        "required_role": request.required_role,
        "assigned": request.assigned_human_id is not None,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_human_action_request",
        source_id=request.id,
        stream_key=f"human-request:{request.id}",
        activity_class=OrganizationActivityClass.human_action,
        activity_type="organization.human_request.created.v1",
        title="Human action requested",
        summary="A governed human intervention request was created.",
        occurred_at=request.requested_at,
        payload=payload,
        department=_request_department(session, context, request),
        work_item_id=request.work_item_id,
        lead_id=request.lead_id,
        profile_id=request.profile_id,
        application_id=request.application_id,
        corporate_account_id=request.corporate_account_id,
        corporate_mobility_case_id=request.corporate_mobility_case_id,
    )


def stage_human_request_assignment_activity(
    session: Session,
    context: OrganizationCommandContext,
    request: OrganizationHumanActionRequest,
    *,
    previously_assigned: bool,
) -> OrganizationActivity:
    payload = {
        "status": request.status,
        "previously_assigned": previously_assigned,
        "assigned": request.assigned_human_id is not None,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_human_action_request",
        source_id=request.id,
        stream_key=f"human-request:{request.id}",
        activity_class=OrganizationActivityClass.human_action,
        activity_type="organization.human_request.assigned.v1",
        title="Human action request assignment changed",
        summary="Responsibility for a governed human-action request changed.",
        occurred_at=request.updated_at,
        payload=payload,
        department=_request_department(session, context, request),
        work_item_id=request.work_item_id,
        lead_id=request.lead_id,
        profile_id=request.profile_id,
        application_id=request.application_id,
        corporate_account_id=request.corporate_account_id,
        corporate_mobility_case_id=request.corporate_mobility_case_id,
    )


def stage_human_request_status_activity(
    session: Session,
    context: OrganizationCommandContext,
    request: OrganizationHumanActionRequest,
    *,
    previous_status: str,
    causation_activity_id: UUID | None = None,
) -> OrganizationActivity:
    payload = {
        "previous_status": previous_status,
        "status": request.status,
        "request_type": request.request_type,
    }
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_human_action_request",
        source_id=request.id,
        stream_key=f"human-request:{request.id}",
        activity_class=OrganizationActivityClass.human_action,
        activity_type=f"organization.human_request.status.{request.status.value}.v1",
        title=f"Human action request {request.status.value.replace('_', ' ')}",
        summary=f"Human-action request moved from {previous_status} to {request.status.value}.",
        occurred_at=request.updated_at,
        payload=payload,
        department=_request_department(session, context, request),
        work_item_id=request.work_item_id,
        lead_id=request.lead_id,
        profile_id=request.profile_id,
        application_id=request.application_id,
        corporate_account_id=request.corporate_account_id,
        corporate_mobility_case_id=request.corporate_mobility_case_id,
        causation_activity_id=causation_activity_id,
    )


def _human_action_department(
    session: Session,
    context: OrganizationCommandContext,
    action: OrganizationHumanAction,
) -> str | None:
    work_department = _linked_work_department(session, context, action.work_item_id)
    if work_department is not None:
        return work_department
    if action.human_action_request_id is not None:
        request = tenant_record(
            session,
            OrganizationHumanActionRequest,
            action.human_action_request_id,
            context.tenant_key,
            label="activity-linked human action request",
        )
        return _request_department(session, context, request)
    if action.blocker_id is not None:
        blocker = tenant_record(
            session,
            OrganizationBlocker,
            action.blocker_id,
            context.tenant_key,
            label="activity-linked blocker",
        )
        return _blocker_department(session, context, blocker)
    if action.decision_id is not None:
        decision = tenant_record(
            session,
            ExecutiveDecision,
            action.decision_id,
            context.tenant_key,
            label="activity-linked decision",
        )
        return _linked_work_department(session, context, decision.work_item_id) or context.department
    return action.actor_department or context.department


def _human_action_stream_key(action: OrganizationHumanAction) -> str:
    if action.human_action_request_id is not None:
        return f"human-request:{action.human_action_request_id}"
    if action.work_item_id is not None:
        return f"work:{action.work_item_id}"
    if action.decision_id is not None:
        return f"decision:{action.decision_id}"
    if action.blocker_id is not None:
        return f"blocker:{action.blocker_id}"
    return f"human-action:{action.id}"


def stage_human_action_appended_activity(
    session: Session,
    context: OrganizationCommandContext,
    action: OrganizationHumanAction,
) -> OrganizationActivity:
    payload = {
        "action_type": action.action_type,
        "human_action_request_id": action.human_action_request_id,
        "has_reason": bool((action.reason or "").strip()),
    }
    department = _human_action_department(session, context, action)
    return _stage_semantic_activity(
        session,
        context,
        source_type="organization_human_action",
        source_id=action.id,
        stream_key=_human_action_stream_key(action),
        activity_class=OrganizationActivityClass.human_action,
        activity_type=f"organization.human_action.{action.action_type.value}.v1",
        title="Authenticated human action recorded",
        summary=f"An immutable {action.action_type.value.replace('_', ' ')} human intervention was recorded.",
        occurred_at=action.occurred_at,
        payload=payload,
        department=department,
        work_item_id=action.work_item_id,
        lead_id=action.lead_id,
        profile_id=action.profile_id,
        application_id=action.application_id,
        corporate_account_id=action.corporate_account_id,
        corporate_mobility_case_id=action.corporate_mobility_case_id,
    )
