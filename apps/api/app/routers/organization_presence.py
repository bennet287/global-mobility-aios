from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import now_utc
from app.routers.organization_records import organization_command_context
from app.schemas_organization_presence import (
    AustriaOrganizationPresenceLatestRead,
    AustriaOrganizationPresenceSnapshotRead,
    OrganizationPositionPresenceRead,
)
from app.services.organization_command import OrganizationCommandContext, OrganizationCommandError
from app.services.organization_mobility_live_organization import (
    latest_austria_live_organization_snapshot,
)
from app.services.organization_position_presence import (
    HEARTBEAT_NOT_ESTABLISHED,
    organization_position_presence_snapshot,
)


router = APIRouter(
    prefix="/api/v1/organization/transparency/presence",
    tags=["organization-presence-track-b"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Board transparency access required"},
        409: {"description": "Durable presence data is inconsistent"},
    },
)


def _require_board(context: OrganizationCommandContext) -> None:
    if context.role != "admin" or context.position_key != "board":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board transparency access is not permitted.",
        )


@router.get("/austria/latest", response_model=AustriaOrganizationPresenceLatestRead)
def read_latest_austria_organization_presence(
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> AustriaOrganizationPresenceLatestRead:
    """Return bounded execution-derived position presence for the latest Austria cycle.

    Presence is derived only from durable OrganizationExecutionAttempt records. The
    endpoint deliberately reports heartbeat capability as not established; it never
    converts projection time, UI refresh time, provider identity, or model activity into
    an employee heartbeat or organizational authority signal.
    """

    _require_board(context)
    try:
        live_snapshot = latest_austria_live_organization_snapshot(
            session,
            tenant_key=context.tenant_key,
        )
        if live_snapshot is None:
            return AustriaOrganizationPresenceLatestRead(established=False, snapshot=None)

        positions = [
            OrganizationPositionPresenceRead.model_validate(
                organization_position_presence_snapshot(
                    session,
                    tenant_key=context.tenant_key,
                    work_item_id=specialist.work_item_id,
                )
            )
            for specialist in live_snapshot.specialist_outputs
        ]
        return AustriaOrganizationPresenceLatestRead(
            established=True,
            snapshot=AustriaOrganizationPresenceSnapshotRead(
                generated_at=now_utc(),
                root_work_item_id=live_snapshot.root_work_item_id,
                positions=positions,
                heartbeat_capability_state=HEARTBEAT_NOT_ESTABLISHED,
            ),
        )
    except OrganizationCommandError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization presence transparency data is inconsistent.",
        ) from exc
