from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.domain import (
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActivityStream,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.organization_command import (
    AuditMutation,
    DependencyConflict,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_payload_json,
    commit_mutations,
    idempotent_existing,
    require_mutation_role,
    stage_mutations,
    tenant_record,
)


def _write_activity(
    session: Session,
    context: OrganizationCommandContext,
    *,
    _commit: bool,
    activity_key: str,
    stream_key: str,
    activity_class: OrganizationActivityClass | str,
    activity_type: str,
    title: str,
    summary: str,
    source_object_type: str,
    source_object_id: str,
    occurred_at: datetime,
    source_object_version: str | None = None,
    work_item_id: UUID | None = None,
    execution_attempt_id: UUID | None = None,
    agent_run_id: UUID | None = None,
    automation_event_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    causation_activity_id: UUID | None = None,
    supersedes_activity_id: UUID | None = None,
    payload: Mapping[str, Any] | None = None,
    correlation_key: str | None = None,
) -> OrganizationActivity:
    if _commit:
        # The standalone Activity command keeps the authenticated admin/operator
        # contract. Caller-owned staging is an internal integration primitive and
        # inherits authority from the already-validated source transition (for
        # example, an authenticated reviewer publishing governed regulatory data).
        require_mutation_role(context)
    activity_class = OrganizationActivityClass(activity_class)
    command = {
        "activity_key": activity_key,
        "stream_key": stream_key,
        "activity_class": activity_class,
        "activity_type": activity_type,
        "title": title,
        "summary": summary,
        "source_object_type": source_object_type,
        "source_object_id": source_object_id,
        "source_object_version": source_object_version,
        "occurred_at": occurred_at,
        "work_item_id": work_item_id,
        "execution_attempt_id": execution_attempt_id,
        "agent_run_id": agent_run_id,
        "automation_event_id": automation_event_id,
        "lead_id": lead_id,
        "profile_id": profile_id,
        "application_id": application_id,
        "corporate_account_id": corporate_account_id,
        "corporate_mobility_case_id": corporate_mobility_case_id,
        "causation_activity_id": causation_activity_id,
        "supersedes_activity_id": supersedes_activity_id,
        "payload": payload or {},
        "correlation_key": correlation_key or context.correlation_key,
        "actor_type": context.actor_type,
        "actor_id": context.actor_id,
        "department": context.department,
        "position_key": context.position_key,
        "authority_level": context.authority_level,
        "tenant_key": context.tenant_key,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == context.tenant_key,
            OrganizationActivity.activity_key == activity_key,
        )
    ).first()
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="record_fingerprint",
        label="activity",
    )
    if replay is not None:
        return replay

    if work_item_id is not None:
        tenant_record(session, OrganizationalWorkItem, work_item_id, context.tenant_key, label="work item")
    if causation_activity_id is not None:
        tenant_record(session, OrganizationActivity, causation_activity_id, context.tenant_key, label="causation activity")
    if supersedes_activity_id is not None:
        tenant_record(
            session,
            OrganizationActivity,
            supersedes_activity_id,
            context.tenant_key,
            label="superseded activity",
        )

    stream_query = select(OrganizationActivityStream).where(
        OrganizationActivityStream.tenant_key == context.tenant_key,
        OrganizationActivityStream.stream_key == stream_key,
    )
    if session.get_bind().dialect.name == "postgresql":
        stream_query = stream_query.with_for_update()
    stream = session.exec(stream_query).first()
    if stream is None:
        stream = OrganizationActivityStream(tenant_key=context.tenant_key, stream_key=stream_key)
        session.add(stream)
        try:
            session.flush()
        except IntegrityError as exc:
            if not _commit:
                # Caller-owned staging must never roll back a transaction it does not own.
                # The caller receives a retryable conflict and rolls the whole source unit
                # of work back atomically.
                raise DependencyConflict(
                    "activity stream was created concurrently; retry the source transaction"
                ) from exc
            session.rollback()
            concurrent = session.exec(
                select(OrganizationActivity).where(
                    OrganizationActivity.tenant_key == context.tenant_key,
                    OrganizationActivity.activity_key == activity_key,
                )
            ).first()
            replay = idempotent_existing(
                concurrent,
                fingerprint,
                fingerprint_field="record_fingerprint",
                label="activity",
            )
            if replay is not None:
                return replay
            raise DependencyConflict("activity stream was created concurrently; retry the command") from exc

    stream.last_sequence += 1
    stream.updated_at = now_utc()
    activity = OrganizationActivity(
        activity_key=activity_key,
        record_fingerprint=fingerprint,
        tenant_key=context.tenant_key,
        activity_stream_id=stream.id,
        stream_sequence=stream.last_sequence,
        activity_class=activity_class,
        activity_type=activity_type,
        title=title,
        summary=summary,
        department=context.department,
        position_key=context.position_key,
        authority_level=context.authority_level,
        actor_type=context.actor_type,
        actor_id=context.actor_id,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        agent_run_id=agent_run_id,
        automation_event_id=automation_event_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
        correlation_key=correlation_key or context.correlation_key,
        causation_activity_id=causation_activity_id,
        supersedes_activity_id=supersedes_activity_id,
        payload_json=canonical_payload_json(payload),
        occurred_at=occurred_at,
        created_by=context.actor_id,
    )
    session.add(stream)
    session.add(activity)
    mutation = AuditMutation(
        action="organization.activity.append",
        entity_type="organization_activity",
        entity_id=activity.id,
        after_state=activity,
    )
    if not _commit:
        try:
            stage_mutations(session, mutations=[mutation], context=context)
        except IntegrityError as exc:
            # The staging primitive must not query or roll back after a failed flush;
            # the caller owns rollback/retry for the complete source transition.
            raise DependencyConflict(
                "concurrent activity sequence allocation failed; retry the source transaction"
            ) from exc
        return activity

    try:
        commit_mutations(
            session,
            mutations=[mutation],
            context=context,
            refresh=(activity,),
        )
    except IntegrityError as exc:
        concurrent = session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.tenant_key == context.tenant_key,
                OrganizationActivity.activity_key == activity_key,
            )
        ).first()
        replay = idempotent_existing(
            concurrent,
            fingerprint,
            fingerprint_field="record_fingerprint",
            label="activity",
        )
        if replay is not None:
            return replay
        raise DependencyConflict("concurrent activity sequence allocation failed; retry the command") from exc
    return activity


def append_activity(
    session: Session,
    context: OrganizationCommandContext,
    *,
    activity_key: str,
    stream_key: str,
    activity_class: OrganizationActivityClass | str,
    activity_type: str,
    title: str,
    summary: str,
    source_object_type: str,
    source_object_id: str,
    occurred_at: datetime,
    source_object_version: str | None = None,
    work_item_id: UUID | None = None,
    execution_attempt_id: UUID | None = None,
    agent_run_id: UUID | None = None,
    automation_event_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    causation_activity_id: UUID | None = None,
    supersedes_activity_id: UUID | None = None,
    payload: Mapping[str, Any] | None = None,
    correlation_key: str | None = None,
) -> OrganizationActivity:
    """Append and commit one standalone governed Activity command."""

    return _write_activity(
        session,
        context,
        _commit=True,
        activity_key=activity_key,
        stream_key=stream_key,
        activity_class=activity_class,
        activity_type=activity_type,
        title=title,
        summary=summary,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        occurred_at=occurred_at,
        source_object_version=source_object_version,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        agent_run_id=agent_run_id,
        automation_event_id=automation_event_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        causation_activity_id=causation_activity_id,
        supersedes_activity_id=supersedes_activity_id,
        payload=payload,
        correlation_key=correlation_key,
    )


def stage_activity(
    session: Session,
    context: OrganizationCommandContext,
    *,
    activity_key: str,
    stream_key: str,
    activity_class: OrganizationActivityClass | str,
    activity_type: str,
    title: str,
    summary: str,
    source_object_type: str,
    source_object_id: str,
    occurred_at: datetime,
    source_object_version: str | None = None,
    work_item_id: UUID | None = None,
    execution_attempt_id: UUID | None = None,
    agent_run_id: UUID | None = None,
    automation_event_id: UUID | None = None,
    lead_id: UUID | None = None,
    profile_id: UUID | None = None,
    application_id: UUID | None = None,
    corporate_account_id: UUID | None = None,
    corporate_mobility_case_id: UUID | None = None,
    causation_activity_id: UUID | None = None,
    supersedes_activity_id: UUID | None = None,
    payload: Mapping[str, Any] | None = None,
    correlation_key: str | None = None,
) -> OrganizationActivity:
    """Stage Activity + Activity audit inside a caller-owned source transaction.

    This internal composition primitive never commits or rolls back. Source-owned
    semantic adapters must call it before their transaction owner commits the domain
    transition. Any failure propagates so the caller can roll back source state,
    source audit, Activity, and Activity audit together.
    """

    return _write_activity(
        session,
        context,
        _commit=False,
        activity_key=activity_key,
        stream_key=stream_key,
        activity_class=activity_class,
        activity_type=activity_type,
        title=title,
        summary=summary,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        occurred_at=occurred_at,
        source_object_version=source_object_version,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        agent_run_id=agent_run_id,
        automation_event_id=automation_event_id,
        lead_id=lead_id,
        profile_id=profile_id,
        application_id=application_id,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=corporate_mobility_case_id,
        causation_activity_id=causation_activity_id,
        supersedes_activity_id=supersedes_activity_id,
        payload=payload,
        correlation_key=correlation_key,
    )
