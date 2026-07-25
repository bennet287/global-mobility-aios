from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import EcosystemPortalAccessGrant
from app.schemas_ecosystem_portal import (
    EcosystemPortalDashboard,
    EcosystemPortalGrantCreate,
    EcosystemPortalGrantIssued,
    EcosystemPortalGrantRead,
    EcosystemPortalGrantRevoke,
)
from app.services.ecosystem_portal import (
    ecosystem_grant_read,
    ecosystem_portal_dashboard,
    expire_ecosystem_portal_grants,
    issue_ecosystem_portal_grant,
    revoke_ecosystem_portal_grant,
)


router = APIRouter(tags=["ecosystem-portal-v12.1"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    status = 404 if "not found" in message.lower() else 400
    return HTTPException(status_code=status, detail=message)


@router.post(
    "/api/v1/ecosystem-portal/grants",
    response_model=EcosystemPortalGrantIssued,
    status_code=201,
)
def create_ecosystem_portal_grant(
    payload: EcosystemPortalGrantCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> EcosystemPortalGrantIssued:
    try:
        grant, token = issue_ecosystem_portal_grant(
            session,
            payload.corporate_account_id,
            actor=_actor(request),
            audience_type=payload.audience_type,
            label=payload.label,
            expires_in_days=payload.expires_in_days,
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return EcosystemPortalGrantIssued(
        grant=EcosystemPortalGrantRead(**ecosystem_grant_read(grant)),
        token=token,
        portal_path=f"/partner-portal?token={token}",
    )


@router.get(
    "/api/v1/ecosystem-portal/grants",
    response_model=list[EcosystemPortalGrantRead],
)
def list_ecosystem_portal_grants(
    corporate_account_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[EcosystemPortalGrantRead]:
    expire_ecosystem_portal_grants(session)
    statement = select(EcosystemPortalAccessGrant).order_by(
        EcosystemPortalAccessGrant.created_at.desc()
    )
    if corporate_account_id:
        statement = statement.where(
            EcosystemPortalAccessGrant.corporate_account_id == corporate_account_id
        )
    grants = session.exec(statement.limit(limit)).all()
    return [EcosystemPortalGrantRead(**ecosystem_grant_read(grant)) for grant in grants]


@router.post(
    "/api/v1/ecosystem-portal/grants/{grant_id}/revoke",
    response_model=EcosystemPortalGrantRead,
)
def revoke_ecosystem_portal_access(
    grant_id: UUID,
    payload: EcosystemPortalGrantRevoke,
    request: Request,
    session: Session = Depends(get_session),
) -> EcosystemPortalGrantRead:
    try:
        grant = revoke_ecosystem_portal_grant(
            session,
            grant_id,
            actor=_actor(request),
            reason=payload.reason,
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return EcosystemPortalGrantRead(**ecosystem_grant_read(grant))


@router.get(
    "/api/v1/public/ecosystem-portal/dashboard",
    response_model=EcosystemPortalDashboard,
)
def get_ecosystem_portal_dashboard(
    x_gmai_ecosystem_token: str = Header(alias="X-GMAI-Ecosystem-Token"),
    session: Session = Depends(get_session),
) -> EcosystemPortalDashboard:
    try:
        return EcosystemPortalDashboard(
            **ecosystem_portal_dashboard(session, x_gmai_ecosystem_token)
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(
            status_code=404,
            detail="Ecosystem portal access is invalid or unavailable",
        ) from exc
