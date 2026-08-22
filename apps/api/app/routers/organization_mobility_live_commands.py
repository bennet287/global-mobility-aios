from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import OrganizationalActionOutput, OrganizationalWorkItem
from app.routers.organization_records import organization_command_context
from app.services.organization_command import OrganizationCommandContext, OrganizationCommandError, require_human
from app.services.organization_mobility_live_organization import (
    austria_owner_synthesis_output_key,
    synthesize_austria_objective_owner,
)


router = APIRouter(
    prefix="/api/v1/organization/live-organization",
    tags=["organization-live-commands-v1"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Board command authority required"},
        404: {"description": "Organization objective not found"},
        409: {"description": "Objective is not ready or persisted state conflicts"},
    },
)


class AustriaOwnerSynthesisCommandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    root_work_item_id: UUID
    action_output_id: UUID
    activity_id: UUID
    disposition: str
    replayed: bool


def _require_board_human(context: OrganizationCommandContext) -> None:
    try:
        require_human(context, admin=True)
    except OrganizationCommandError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board live-organization command access is not permitted.",
        ) from exc
    if context.position_key != "board":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board live-organization command access is not permitted.",
        )


def _root_exists(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> bool:
    return session.exec(
        select(OrganizationalWorkItem.id).where(
            OrganizationalWorkItem.id == root_work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first() is not None


def _replay_after_integrity_conflict(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
):
    """Normalize only a concurrently materialized L.1 output into exact replay.

    The service-level PostgreSQL race proof intentionally demonstrates that the losing
    transaction reaches the database uniqueness boundary. The HTTP/operator boundary is
    friendlier: after rollback, it only retries as replay when the canonical owner output
    now exists. Unrelated integrity errors remain conflicts rather than being disguised as
    successful idempotency.
    """

    session.rollback()
    current = session.exec(
        select(OrganizationalActionOutput.id).where(
            OrganizationalActionOutput.output_key == austria_owner_synthesis_output_key(root_work_item_id)
        )
    ).first()
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Live organization owner synthesis conflicted with persisted state.",
        )
    try:
        return synthesize_austria_objective_owner(
            session,
            tenant_key=tenant_key,
            root_work_item_id=root_work_item_id,
        )
    except OrganizationCommandError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Live organization owner synthesis conflicted with persisted state.",
        ) from exc


@router.post(
    "/austria/{root_work_item_id}/owner-synthesis",
    response_model=AustriaOwnerSynthesisCommandRead,
)
def synthesize_austria_owner_command(
    root_work_item_id: UUID,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> AustriaOwnerSynthesisCommandRead:
    """Materialize or exactly replay one bounded L.1 owner synthesis.

    This is deliberately not a one-click J→K→L autonomous cycle. It exposes the first
    real operator command only after K.1 has already produced current, provenance-valid
    specialist evidence. Existing service gates remain authoritative and no external
    action is authorized by this endpoint.
    """

    _require_board_human(context)
    if not _root_exists(
        session,
        tenant_key=context.tenant_key,
        root_work_item_id=root_work_item_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization live objective not found.",
        )

    try:
        result = synthesize_austria_objective_owner(
            session,
            tenant_key=context.tenant_key,
            root_work_item_id=root_work_item_id,
        )
    except IntegrityError:
        result = _replay_after_integrity_conflict(
            session,
            tenant_key=context.tenant_key,
            root_work_item_id=root_work_item_id,
        )
    except OrganizationCommandError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Austria objective is not ready for bounded owner synthesis.",
        ) from exc

    return AustriaOwnerSynthesisCommandRead.model_validate(result)
