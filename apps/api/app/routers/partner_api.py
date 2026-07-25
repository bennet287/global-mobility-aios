from __future__ import annotations

import math
from typing import Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlmodel import Session, func, select

from app.core.db import get_session
from app.models.domain import (
    CorporateAccount,
    CorporateComplianceEvent,
    CorporateMobilityCase,
    Lead,
    PartnerApiCredential,
)
from app.schemas_partner_api import (
    ApiPageMeta,
    PartnerAccountProjection,
    PartnerApiCredentialCreate,
    PartnerApiCredentialIssued,
    PartnerApiCredentialRead,
    PartnerApiCredentialRevoke,
    PartnerCasePage,
    PartnerCaseProjection,
    PartnerCompliancePage,
    PartnerComplianceProjection,
)
from app.services.partner_api import (
    expire_partner_api_credentials,
    issue_partner_api_credential,
    partner_credential_read,
    resolve_partner_api_credential,
    revoke_partner_api_credential,
)


router = APIRouter(tags=["public-partner-api-v1"])
API_VERSION = "1.0"


def _version(response: Response) -> None:
    response.headers["X-GMAI-API-Version"] = API_VERSION
    response.headers["Deprecation"] = "false"


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _management_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    return HTTPException(
        status_code=404 if "not found" in message.lower() else 400,
        detail=message,
    )


def _partner_auth(scope: str) -> Callable:
    def dependency(
        request: Request,
        x_gmai_partner_key: str = Header(alias="X-GMAI-Partner-Key"),
        session: Session = Depends(get_session),
    ) -> PartnerApiCredential:
        try:
            return resolve_partner_api_credential(
                session,
                x_gmai_partner_key,
                required_scope=scope,
                request=request,
            )
        except LookupError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(
                status_code=401,
                detail="Partner API credential is invalid or unavailable",
            ) from exc
    return dependency


def _page_meta(page: int, page_size: int, total: int) -> ApiPageMeta:
    return ApiPageMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/api/public/v1")
def public_api_root(response: Response) -> dict[str, object]:
    _version(response)
    response.headers["Cache-Control"] = "public, max-age=300"
    return {
        "name": "Global Mobility AIOS Public API",
        "version": API_VERSION,
        "status": "available",
        "partner_api": "/api/partner/v1",
        "documentation": "/docs",
        "data_policy": "No tenant or client data is exposed by the unauthenticated public API.",
    }


@router.get("/api/public/v1/capabilities")
def public_api_capabilities(response: Response) -> dict[str, object]:
    _version(response)
    response.headers["Cache-Control"] = "public, max-age=300"
    return {
        "version": API_VERSION,
        "resources": ["partner_account", "partner_cases", "partner_compliance"],
        "authentication": {
            "partner": "X-GMAI-Partner-Key",
            "tenant_scope": "derived_from_credential",
        },
        "pagination": {
            "style": "page",
            "default_page_size": 25,
            "maximum_page_size": 100,
        },
    }


@router.post(
    "/api/v1/partner-api/credentials",
    response_model=PartnerApiCredentialIssued,
    status_code=201,
)
def create_partner_api_credential(
    payload: PartnerApiCredentialCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> PartnerApiCredentialIssued:
    try:
        credential, api_key = issue_partner_api_credential(
            session,
            payload.corporate_account_id,
            actor=_actor(request),
            label=payload.label,
            scopes=list(payload.scopes),
            expires_in_days=payload.expires_in_days,
        )
    except ValueError as exc:
        session.rollback()
        raise _management_error(exc) from exc
    return PartnerApiCredentialIssued(
        credential=PartnerApiCredentialRead(**partner_credential_read(credential)),
        api_key=api_key,
    )


@router.get(
    "/api/v1/partner-api/credentials",
    response_model=list[PartnerApiCredentialRead],
)
def list_partner_api_credentials(
    corporate_account_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[PartnerApiCredentialRead]:
    expire_partner_api_credentials(session)
    statement = select(PartnerApiCredential).order_by(
        PartnerApiCredential.created_at.desc()
    )
    if corporate_account_id:
        statement = statement.where(
            PartnerApiCredential.corporate_account_id == corporate_account_id
        )
    return [
        PartnerApiCredentialRead(**partner_credential_read(credential))
        for credential in session.exec(statement.limit(limit)).all()
    ]


@router.post(
    "/api/v1/partner-api/credentials/{credential_id}/revoke",
    response_model=PartnerApiCredentialRead,
)
def revoke_partner_api_access(
    credential_id: UUID,
    payload: PartnerApiCredentialRevoke,
    request: Request,
    session: Session = Depends(get_session),
) -> PartnerApiCredentialRead:
    try:
        credential = revoke_partner_api_credential(
            session,
            credential_id,
            actor=_actor(request),
            reason=payload.reason,
        )
    except ValueError as exc:
        session.rollback()
        raise _management_error(exc) from exc
    return PartnerApiCredentialRead(**partner_credential_read(credential))


@router.get("/api/partner/v1/account", response_model=PartnerAccountProjection)
def partner_account(
    response: Response,
    credential: PartnerApiCredential = Depends(_partner_auth("account:read")),
    session: Session = Depends(get_session),
) -> PartnerAccountProjection:
    _version(response)
    response.headers["Cache-Control"] = "private, no-store"
    account = session.get(CorporateAccount, credential.corporate_account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Partner account unavailable")
    return PartnerAccountProjection(
        account_reference=account.id,
        name=account.display_name or account.legal_name,
        primary_country=account.primary_country,
        status=account.account_status,
        updated_at=account.updated_at,
    )


@router.get("/api/partner/v1/cases", response_model=PartnerCasePage)
def partner_cases(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    credential: PartnerApiCredential = Depends(_partner_auth("cases:read")),
    session: Session = Depends(get_session),
) -> PartnerCasePage:
    _version(response)
    response.headers["Cache-Control"] = "private, no-store"
    base = select(CorporateMobilityCase).where(
        CorporateMobilityCase.corporate_account_id == credential.corporate_account_id
    )
    count_statement = select(func.count()).select_from(CorporateMobilityCase).where(
        CorporateMobilityCase.corporate_account_id == credential.corporate_account_id
    )
    if status:
        clean_status = status.strip().lower()
        base = base.where(CorporateMobilityCase.status == clean_status)
        count_statement = count_statement.where(CorporateMobilityCase.status == clean_status)
    total = int(session.exec(count_statement).one() or 0)
    cases = session.exec(
        base.order_by(CorporateMobilityCase.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    lead_ids = {case.employee_lead_id for case in cases if case.employee_lead_id}
    leads = {
        lead.id: lead
        for lead in session.exec(select(Lead).where(Lead.id.in_(lead_ids))).all()
    } if lead_ids else {}
    return PartnerCasePage(
        data=[
            PartnerCaseProjection(
                case_reference=case.case_reference,
                case_type=case.case_type,
                status=case.status,
                employee_name=leads.get(case.employee_lead_id).full_name
                if leads.get(case.employee_lead_id) else None,
                origin_country=case.origin_country,
                destination_country=case.destination_country,
                target_start_date=case.target_start_date,
                compliance_due_date=case.compliance_due_date,
                updated_at=case.updated_at,
            )
            for case in cases
        ],
        meta=_page_meta(page, page_size, total),
    )


@router.get("/api/partner/v1/compliance", response_model=PartnerCompliancePage)
def partner_compliance(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    credential: PartnerApiCredential = Depends(_partner_auth("compliance:read")),
    session: Session = Depends(get_session),
) -> PartnerCompliancePage:
    _version(response)
    response.headers["Cache-Control"] = "private, no-store"
    case_rows = session.exec(
        select(CorporateMobilityCase.id, CorporateMobilityCase.case_reference).where(
            CorporateMobilityCase.corporate_account_id == credential.corporate_account_id
        )
    ).all()
    case_references = {row[0]: row[1] for row in case_rows}
    case_ids = set(case_references)
    if not case_ids:
        return PartnerCompliancePage(data=[], meta=_page_meta(page, page_size, 0))
    base = select(CorporateComplianceEvent).where(
        CorporateComplianceEvent.corporate_mobility_case_id.in_(case_ids)
    )
    count_statement = select(func.count()).select_from(CorporateComplianceEvent).where(
        CorporateComplianceEvent.corporate_mobility_case_id.in_(case_ids)
    )
    if status:
        clean_status = status.strip().lower()
        base = base.where(CorporateComplianceEvent.status == clean_status)
        count_statement = count_statement.where(CorporateComplianceEvent.status == clean_status)
    total = int(session.exec(count_statement).one() or 0)
    events = session.exec(
        base.order_by(CorporateComplianceEvent.due_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return PartnerCompliancePage(
        data=[
            PartnerComplianceProjection(
                case_reference=case_references[event.corporate_mobility_case_id],
                event_type=event.event_type,
                title=event.title,
                due_at=event.due_at,
                status=event.status,
                evidence_required=event.evidence_required,
            )
            for event in events
        ],
        meta=_page_meta(page, page_size, total),
    )
