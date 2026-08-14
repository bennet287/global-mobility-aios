from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import ExecutiveDecision, OrganizationDecisionType, OrganizationalWorkItem, now_utc
from app.services.organization_command import (
    AuditMutation,
    AuthorityDenied,
    IdempotencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_json,
    idempotent_existing,
    require_human,
    require_mutation_role,
    snapshot,
    stage_mutations,
    tenant_record,
)
from app.services.organization_semantic_activity import (
    stage_decision_created_activity,
    stage_decision_outcome_activity,
)


def create_executive_decision(
    session: Session,
    context: OrganizationCommandContext,
    *,
    decision_key: str,
    decision_type: OrganizationDecisionType | str,
    authority_level: str,
    requested_by_position: str,
    decision_owner_position: str,
    title: str,
    question: str,
    recommendation: str,
    alternatives: Sequence[Any] = (),
    evidence: Sequence[Any] = (),
    impact: Mapping[str, Any] | None = None,
    conditions: Sequence[Any] = (),
    work_item_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    source_object_type: str | None = None,
    source_object_id: str | None = None,
    source_object_version: str | None = None,
    supersedes_decision_id: UUID | None = None,
    due_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> ExecutiveDecision:
    require_mutation_role(context)
    decision_type = OrganizationDecisionType(decision_type)
    if decision_type is OrganizationDecisionType.board_reserved:
        if context.role != "admin" or context.position_key not in {"board", "owner"}:
            raise AuthorityDenied("only Board/owner authority may propose a Board-reserved decision")
    if work_item_id:
        tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    if supersedes_decision_id:
        predecessor = tenant_record(
            session,
            ExecutiveDecision,
            supersedes_decision_id,
            context.tenant_key,
            label="superseded decision",
        )
        if predecessor.status not in {"approved", "rejected", "returned", "expired", "superseded"}:
            raise InvalidTransition("only a settled decision may be superseded by a new version")
    if any((lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id)) and context.tenant_key != "default":
        raise AuthorityDenied("legacy decision targets are available only in authenticated tenant 'default'")
    status = "pending_board" if decision_type is OrganizationDecisionType.board_reserved or authority_level == "L4" else "pending_ceo"
    command = {
        "decision_key": decision_key,
        "tenant_key": context.tenant_key,
        "decision_type": decision_type,
        "authority_level": authority_level,
        "requested_by_position": requested_by_position,
        "decision_owner_position": decision_owner_position,
        "title": title,
        "question": question,
        "recommendation": recommendation,
        "alternatives": list(alternatives),
        "evidence": list(evidence),
        "impact": impact or {},
        "conditions": list(conditions),
        "work_item_id": work_item_id,
        "targets": [lead_id, profile_id, application_id, corporate_account_id, corporate_mobility_case_id],
        "source": [source_object_type, source_object_id, source_object_version],
        "supersedes_decision_id": supersedes_decision_id,
        "due_at": due_at,
        "expires_at": expires_at,
        "initial_status": status,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.decision_key == decision_key)).first()
    if existing is not None and existing.tenant_key != context.tenant_key:
        raise IdempotencyConflict("decision key is unavailable")
    replay = idempotent_existing(existing, fingerprint, fingerprint_field="record_fingerprint", label="decision")
    if replay is not None:
        return replay
    row = ExecutiveDecision(
        decision_key=decision_key,
        tenant_key=context.tenant_key,
        decision_type=decision_type,
        record_fingerprint=fingerprint,
        work_item_id=work_item_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
        supersedes_decision_id=supersedes_decision_id,
        authority_level=authority_level,
        requested_by_position=requested_by_position,
        decision_owner_position=decision_owner_position,
        title=title,
        question=question,
        recommendation=recommendation,
        alternatives_json=canonical_json(list(alternatives)),
        evidence_json=canonical_json(list(evidence)),
        impact_json=canonical_json(impact or {}),
        conditions_json=canonical_json(list(conditions)),
        status=status,
        due_at=due_at,
        expires_at=expires_at,
    )
    session.add(row)
    try:
        stage_mutations(
            session,
            mutations=[
                AuditMutation(
                    "organization.decision.create",
                    "executive_decision",
                    row.id,
                    after_state=row,
                )
            ],
            context=context,
        )
        stage_decision_created_activity(session, context, row)
        session.commit()
        session.refresh(row)
    except Exception:
        session.rollback()
        raise
    return row


def record_executive_decision_outcome(
    session: Session,
    context: OrganizationCommandContext,
    *,
    decision_id: UUID,
    outcome: str,
    reason: str,
    effect_summary: str | None = None,
) -> ExecutiveDecision:
    require_human(context, admin=True)
    if outcome not in {"approved", "rejected"}:
        raise InvalidTransition("decision outcome must be approved or rejected")
    row = tenant_record(session, ExecutiveDecision, decision_id, context.tenant_key, label="executive decision")
    if row.status == "pending_board" or row.authority_level == "L4" or row.decision_type is OrganizationDecisionType.board_reserved:
        if context.position_key not in {"board", "owner"}:
            raise AuthorityDenied("Board/owner position is required for this decision outcome")
    elif context.position_key not in {"board", "owner", "ceo"}:
        raise AuthorityDenied("CEO or Board/owner position is required for this decision outcome")
    if row.status == outcome and row.decided_by == context.actor_id and row.decision_reason == reason:
        return row
    if row.status not in {"pending_ceo", "coordinating_ceo", "pending_board"}:
        raise InvalidTransition(f"decision cannot be recorded from status {row.status!r}")
    before = snapshot(row)
    previous_status = row.status
    row.status = outcome
    row.decided_by = context.actor_id
    row.decision_reason = reason
    row.effect_summary = effect_summary
    row.decided_at = now_utc()
    row.updated_at = row.decided_at
    session.add(row)
    try:
        stage_mutations(
            session,
            mutations=[
                AuditMutation(
                    f"organization.decision.{outcome}",
                    "executive_decision",
                    row.id,
                    before,
                    row,
                    reason,
                )
            ],
            context=context,
        )
        stage_decision_outcome_activity(
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


def supersede_executive_decision(
    session: Session,
    context: OrganizationCommandContext,
    *,
    original_decision_id: UUID,
    new_decision_key: str,
    title: str,
    question: str,
    recommendation: str,
    reason: str,
) -> ExecutiveDecision:
    original = tenant_record(session, ExecutiveDecision, original_decision_id, context.tenant_key, label="executive decision")
    replacement = create_executive_decision(
        session,
        context,
        decision_key=new_decision_key,
        decision_type=original.decision_type,
        authority_level=original.authority_level,
        requested_by_position=context.position_key or original.requested_by_position,
        decision_owner_position=original.decision_owner_position,
        title=title,
        question=question,
        recommendation=recommendation,
        evidence=[{"supersession_reason": reason, "original_decision_id": str(original.id)}],
        work_item_id=original.work_item_id,
        lead_id=original.lead_id,
        profile_id=original.profile_id,
        application_id=original.application_id,
        corporate_account_id=original.corporate_account_id,
        corporate_mobility_case_id=original.corporate_mobility_case_id,
        source_object_type=original.source_object_type,
        source_object_id=original.source_object_id,
        source_object_version=original.source_object_version,
        supersedes_decision_id=original.id,
    )
    # The historical row remains untouched; the new row carries the version edge.
    return replacement


def attach_executive_decision_reference(
    session: Session,
    context: OrganizationCommandContext,
    *,
    decision_id: UUID,
    reference_key: str,
    reference_role: str,
    target_type: str,
    target_id: UUID | str,
    target_version: str | None = None,
    target_state: str | None = None,
    label: str | None = None,
    source_url: str | None = None,
) -> Any:
    """Attach validated evidence/provenance without expanding the decision row."""

    tenant_record(session, ExecutiveDecision, decision_id, context.tenant_key, label="executive decision")
    # Local import keeps the decision and heterogeneous-reference boundaries separate.
    from app.services.organization_reference import create_record_reference

    return create_record_reference(
        session,
        context,
        reference_key=reference_key,
        reference_role=reference_role,
        target_type=target_type,
        target_id=target_id,
        decision_id=decision_id,
        target_version=target_version,
        target_state=target_state,
        label=label,
        source_url=source_url,
    )
