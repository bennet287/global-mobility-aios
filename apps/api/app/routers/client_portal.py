from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import ClientPortalAccessGrant
from app.schemas_client_portal import (
    ClientPortalDashboard,
    ClientPortalGrantCreate,
    ClientPortalGrantIssued,
    ClientPortalGrantRead,
    ClientPortalGrantRevoke,
)
from app.services.client_portal import (
    client_portal_dashboard,
    expire_client_portal_grants,
    grant_read,
    issue_client_portal_grant,
    revoke_client_portal_grant,
)


router = APIRouter(tags=["client-portal-v12.0"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    if "not found" in message.lower():
        return HTTPException(status_code=404, detail=message)
    return HTTPException(status_code=400, detail=message)


@router.post(
    "/api/v1/client-portal/grants",
    response_model=ClientPortalGrantIssued,
    status_code=201,
)
def create_client_portal_grant(
    payload: ClientPortalGrantCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ClientPortalGrantIssued:
    try:
        grant, token = issue_client_portal_grant(
            session,
            payload.lead_id,
            actor=_actor(request),
            label=payload.label,
            expires_in_days=payload.expires_in_days,
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return ClientPortalGrantIssued(
        grant=ClientPortalGrantRead(**grant_read(grant)),
        token=token,
        portal_path=f"/portal?token={token}",
    )


@router.get(
    "/api/v1/client-portal/grants",
    response_model=list[ClientPortalGrantRead],
)
def list_client_portal_grants(
    lead_id: UUID | None = None,
    session: Session = Depends(get_session),
) -> list[ClientPortalGrantRead]:
    expire_client_portal_grants(session)
    statement = select(ClientPortalAccessGrant).order_by(ClientPortalAccessGrant.created_at.desc())
    if lead_id:
        statement = statement.where(ClientPortalAccessGrant.lead_id == lead_id)
    grants = session.exec(statement.limit(200)).all()
    return [ClientPortalGrantRead(**grant_read(grant)) for grant in grants]


@router.post(
    "/api/v1/client-portal/grants/{grant_id}/revoke",
    response_model=ClientPortalGrantRead,
)
def revoke_client_portal_access(
    grant_id: UUID,
    payload: ClientPortalGrantRevoke,
    request: Request,
    session: Session = Depends(get_session),
) -> ClientPortalGrantRead:
    try:
        grant = revoke_client_portal_grant(
            session,
            grant_id,
            actor=_actor(request),
            reason=payload.reason,
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return ClientPortalGrantRead(**grant_read(grant))


@router.get(
    "/api/v1/public/client-portal/dashboard",
    response_model=ClientPortalDashboard,
)
def get_client_portal_dashboard(
    x_gmai_portal_token: str = Header(alias="X-GMAI-Portal-Token"),
    x_gmai_portal_device: str | None = Header(default=None, alias="X-GMAI-Portal-Device"),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
    session: Session = Depends(get_session),
) -> ClientPortalDashboard | JSONResponse:
    try:
        return ClientPortalDashboard(**client_portal_dashboard(
            session,
            x_gmai_portal_token,
            device_fingerprint=x_gmai_portal_device,
            device_label=None,
            user_agent=user_agent,
        ))
    except ValueError as exc:
        session.rollback()
        message = str(exc)
        if message.startswith("device_mismatch"):
            return JSONResponse(
                status_code=403,
                content={
                    "action": "request_new_grant",
                    "message": "This secure link is already bound to a different device. Please contact your consultant for a new access link.",
                },
            )
        raise HTTPException(
            status_code=404,
            detail="Client portal access is invalid or unavailable",
        ) from exc
