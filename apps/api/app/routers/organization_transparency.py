from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import OrganizationalWorkItem
from app.routers.organization_records import organization_command_context
from app.schemas_organization_autonomy import CapabilityAutonomyProfileTransparencyRead
from app.schemas_organization_transparency import (
    GovernanceDecisionRead,
    GovernedTransparencyTraceRead,
    TransparencyRecordRead,
    WorkItemTransparencyRead,
)
from app.services.organization_autonomy_profile import (
    AutonomyProfileIntegrityError,
    capability_autonomy_profile_snapshot,
)
from app.services.organization_command import OrganizationCommandContext, OrganizationCommandError
from app.services.organization_transparency import (
    GovernedActionTrace,
    TransparencyActivityRecord,
    TransparencyDataError,
    activities_for_work_item,
    governed_action_trace,
)


router = APIRouter(
    prefix="/api/v1/organization/transparency",
    tags=["organization-transparency-v1.3-c4"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Board transparency access required"},
        404: {"description": "Transparency resource not found"},
        409: {"description": "Durable transparency data is inconsistent"},
    },
)


def _require_board(context: OrganizationCommandContext) -> None:
    # C.4 deliberately exposes the first Cockpit/Board read facade only to the
    # current trusted admin→board role mapping. Broader professional visibility
    # belongs to later sensitivity/retention policy work, not an implicit widening
    # of this first material-transparency API.
    if context.role != "admin" or context.position_key != "board":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board transparency access is not permitted.",
        )


def _record_read(record: TransparencyActivityRecord) -> TransparencyRecordRead:
    return TransparencyRecordRead(
        activity_id=record.activity_id,
        role=record.role.value,
        physical_activity_class=record.physical_activity_class,
        constitutional_activity_class=(
            record.constitutional_activity_class.value
            if record.constitutional_activity_class is not None
            else None
        ),
        board_inspectable=record.board_inspectable,
        requires_durable_record=record.requires_durable_record,
        requires_full_lineage=record.requires_full_lineage,
        may_compact_after_policy_window=record.may_compact_after_policy_window,
        activity_type=record.activity_type,
        title=record.title,
        summary=record.summary,
        actor_type=record.actor_type,
        actor_id=record.actor_id,
        department=record.department,
        position_key=record.position_key,
        authority_level=record.authority_level,
        source_object_type=record.source_object_type,
        source_object_id=record.source_object_id,
        source_object_version=record.source_object_version,
        work_item_id=record.work_item_id,
        trace_id=record.trace_id,
        causation_activity_id=record.causation_activity_id,
        occurred_at=record.occurred_at,
    )


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise TransparencyDataError(f"governance transparency field {key!r} is invalid")
    return value


def _optional_string(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TransparencyDataError(f"governance transparency field {key!r} is invalid")
    return value


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise TransparencyDataError(f"governance transparency field {key!r} is invalid")
    return value


def _governance_read(trace: GovernedActionTrace) -> GovernanceDecisionRead:
    record = trace.governance
    payload = record.payload
    constitutional_class = record.constitutional_activity_class
    if constitutional_class is None:
        raise TransparencyDataError("governance Activity lacks constitutional classification")

    return GovernanceDecisionRead(
        activity_id=record.activity_id,
        trace_id=trace.trace_id,
        action_type=_required_string(payload, "action_type"),
        capability=_required_string(payload, "capability"),
        outcome=_required_string(payload, "outcome"),
        reason=_required_string(payload, "reason"),
        effective_risk_tier=_required_string(payload, "effective_risk_tier"),
        consequence_class=_required_string(payload, "consequence_class"),
        human_review_reason=_optional_string(payload, "human_review_reason"),
        post_review_required=_required_bool(payload, "post_review_required"),
        constitutional_activity_class=constitutional_class.value,
        actor_type=record.actor_type,
        actor_id=record.actor_id,
        department=record.department,
        position_key=record.position_key,
        authority_level=record.authority_level,
        work_item_id=record.work_item_id,
        source_object_type=record.source_object_type,
        source_object_id=record.source_object_id,
        source_object_version=record.source_object_version,
        action_fingerprint=_required_string(payload, "action_fingerprint"),
        idempotency_key=_required_string(payload, "idempotency_key"),
        occurred_at=record.occurred_at,
    )


def _safe_trace(
    session: Session,
    *,
    tenant_key: str,
    trace_id: str,
) -> GovernedTransparencyTraceRead:
    try:
        trace = governed_action_trace(session, tenant_key=tenant_key, trace_id=trace_id)
        if trace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization transparency resource not found.",
            )
        governance = _governance_read(trace)
        return GovernedTransparencyTraceRead(
            trace_id=trace.trace_id,
            board_inspectable=trace.board_inspectable,
            governance=governance,
            records=[_record_read(record) for record in trace.records],
        )
    except HTTPException:
        raise
    except TransparencyDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization transparency data is inconsistent.",
        ) from exc


@router.get("/traces/{trace_id}", response_model=GovernedTransparencyTraceRead)
def read_governed_trace(
    trace_id: str,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> GovernedTransparencyTraceRead:
    """Return one Board-safe governed-action trace without exposing raw payload JSON."""

    _require_board(context)
    return _safe_trace(session, tenant_key=context.tenant_key, trace_id=trace_id)


@router.get(
    "/work-items/{work_item_id}",
    response_model=WorkItemTransparencyRead,
)
def read_work_item_transparency(
    work_item_id: UUID,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> WorkItemTransparencyRead:
    """Return Board-safe durable transparency history for one tenant-owned WorkItem."""

    _require_board(context)
    work_item = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == work_item_id,
            OrganizationalWorkItem.tenant_key == context.tenant_key,
        )
    ).first()
    if work_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization transparency resource not found.",
        )

    try:
        records = activities_for_work_item(
            session,
            tenant_key=context.tenant_key,
            work_item_id=work_item_id,
        )
        return WorkItemTransparencyRead(
            work_item_id=work_item_id,
            records=[_record_read(record) for record in records],
        )
    except TransparencyDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization transparency data is inconsistent.",
        ) from exc


@router.get(
    "/autonomy/profiles/{position_key}/{capability_key}",
    response_model=CapabilityAutonomyProfileTransparencyRead,
)
def read_capability_autonomy_profile(
    position_key: str,
    capability_key: str,
    context_scope: str = Query(..., min_length=1),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> CapabilityAutonomyProfileTransparencyRead:
    """Return the validated append-only Board view of one capability autonomy chain."""

    _require_board(context)
    try:
        snapshot = capability_autonomy_profile_snapshot(
            session,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization transparency resource not found.",
            )
        return CapabilityAutonomyProfileTransparencyRead.model_validate(snapshot)
    except HTTPException:
        raise
    except (AutonomyProfileIntegrityError, OrganizationCommandError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization transparency data is inconsistent.",
        ) from exc