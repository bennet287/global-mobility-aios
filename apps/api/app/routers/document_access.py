from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import DocumentAccessGrant
from app.schemas import (
    DocumentAccessExpiryResult,
    DocumentAccessGrantCreateRequest,
    DocumentAccessGrantIssued,
    DocumentAccessGrantRead,
    DocumentAccessGrantRevokeRequest,
    DocumentAccessTokenRequest,
    DocumentStoragePostureRead,
)
from app.services.document_access import (
    access_document_with_token,
    expire_document_access_grants,
    grant_read,
    issue_document_access_grant,
    revoke_document_access_grant,
    storage_posture_read,
)


router = APIRouter(prefix="/api/v1/document-access", tags=["document-access-v9.5"])


def _auth(request: Request) -> tuple[str, str]:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator"), getattr(context, "role", "read_only")


def _error(exc: (ValueError | RuntimeError)) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if "not found" in lowered:
        status = 404
    elif "denied" in lowered or "only" in lowered or "scope" in lowered:
        status = 403
    elif "configuration failed" in lowered:
        status = 503
    else:
        status = 400
    return HTTPException(status_code=status, detail=message)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[\r\n\"\\/]+", "_", filename).strip(" .")
    return cleaned[:180] or "document.bin"


@router.get("/storage-posture", response_model=DocumentStoragePostureRead)
def api_document_storage_posture() -> DocumentStoragePostureRead:
    return DocumentStoragePostureRead(**storage_posture_read())


@router.post("/documents/{document_id}/grants", response_model=DocumentAccessGrantIssued, status_code=201)
def api_issue_document_access_grant(
    document_id: UUID,
    payload: DocumentAccessGrantCreateRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentAccessGrantIssued:
    actor, role = _auth(request)
    try:
        grant, token = issue_document_access_grant(
            session,
            document_id,
            actor=actor,
            actor_role=role,
            lead_id=payload.lead_id,
            purpose=payload.purpose,
            ttl_seconds=payload.ttl_seconds,
            max_uses=payload.max_uses,
            recipient_username=payload.recipient_username,
            recipient_role=payload.recipient_role,
        )
        return DocumentAccessGrantIssued(
            grant=DocumentAccessGrantRead(**grant_read(grant)),
            token=token,
        )
    except (ValueError, RuntimeError) as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/grants", response_model=list[DocumentAccessGrantRead])
def api_list_document_access_grants(
    lead_id: UUID | None = None,
    document_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[DocumentAccessGrantRead]:
    expire_document_access_grants(session)
    statement = select(DocumentAccessGrant).order_by(DocumentAccessGrant.created_at.desc())
    if lead_id:
        statement = statement.where(DocumentAccessGrant.lead_id == lead_id)
    if document_id:
        statement = statement.where(DocumentAccessGrant.document_id == document_id)
    if status:
        statement = statement.where(DocumentAccessGrant.status == status)
    rows = session.exec(statement.limit(max(1, min(limit, 500)))).all()
    return [DocumentAccessGrantRead(**grant_read(row)) for row in rows]


@router.get("/grants/{grant_id}", response_model=DocumentAccessGrantRead)
def api_get_document_access_grant(
    grant_id: UUID,
    session: Session = Depends(get_session),
) -> DocumentAccessGrantRead:
    expire_document_access_grants(session)
    grant = session.get(DocumentAccessGrant, grant_id)
    if grant is None:
        raise HTTPException(status_code=404, detail="Document access grant not found")
    return DocumentAccessGrantRead(**grant_read(grant))


@router.post("/grants/{grant_id}/revoke", response_model=DocumentAccessGrantRead)
def api_revoke_document_access_grant(
    grant_id: UUID,
    payload: DocumentAccessGrantRevokeRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentAccessGrantRead:
    actor, role = _auth(request)
    try:
        grant = revoke_document_access_grant(
            session,
            grant_id,
            actor=actor,
            actor_role=role,
            reason=payload.reason,
        )
        return DocumentAccessGrantRead(**grant_read(grant))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/grants/expire", response_model=DocumentAccessExpiryResult)
def api_expire_document_access_grants(
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentAccessExpiryResult:
    actor, _ = _auth(request)
    return DocumentAccessExpiryResult(**expire_document_access_grants(session, actor=actor))


@router.post("/content")
def api_access_document_content(
    payload: DocumentAccessTokenRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    actor, role = _auth(request)
    try:
        accessed = access_document_with_token(
            session,
            payload.token,
            actor=actor,
            actor_role=role,
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    filename = _safe_filename(accessed.filename)
    return StreamingResponse(
        iter([accessed.content]),
        media_type=accessed.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store, private, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
            "X-GMAI-Document-Grant": str(accessed.grant.id),
        },
    )
