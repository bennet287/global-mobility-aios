from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import get_session
from app.models.domain import DocumentRecord, Lead
from app.services.audit_log import record_audit
from app.services.document_storage import document_storage_client, now_utc, public_document_metadata
from app.services.malware_scan import scan_bytes, should_block_upload


router = APIRouter(tags=["document-upload-v3.5"])


def _json_response(payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload))


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid datetime/date value: {value}") from exc


def _document_payload(doc: DocumentRecord) -> dict[str, Any]:
    return public_document_metadata(doc)


def _lead_or_404(session: Session, lead_id: Optional[UUID]) -> Optional[Lead]:
    if lead_id is None:
        return None
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    lead_id: Optional[UUID] = Form(default=None),
    document_type: str = Form(default="other"),
    status: str = Form(default="received"),
    expiry_date: Optional[str] = Form(default=None),
    verified_by: Optional[str] = Form(default=None),
    session: Session = Depends(get_session),
):
    _lead_or_404(session, lead_id)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    max_bytes = settings.document_upload_max_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds {settings.document_upload_max_mb} MB limit.",
        )

    # Optional ClamAV malware scan (Technology Radar V1.1 Wave 1 pilot).
    # Disabled by default; infected uploads are rejected before storage.
    malware_result = scan_bytes(content)
    if should_block_upload(malware_result):
        if malware_result.status == "infected":
            detail = f"Malware detected: {malware_result.signature}" if malware_result.signature else "Malware detected"
        else:
            detail = f"Malware scan failed: {malware_result.error}"
        raise HTTPException(status_code=400, detail=detail)

    storage = document_storage_client()
    stored = storage.put_document(
        content=content,
        lead_id=lead_id or "unassigned",
        document_type=document_type,
        filename=file.filename or "uploaded-document",
        mime_type=file.content_type,
    )
    now = now_utc()
    verified_at = now if status == "verified" and verified_by else None
    metadata = {
        "upload": {
            "source": "document_upload_v3_5",
            "original_filename": file.filename,
            "storage_provider": stored.storage_provider,
            "uploaded_at": now.isoformat(),
            "malware_scan": malware_result.to_dict(),
        }
    }
    document = DocumentRecord(
        lead_id=lead_id,
        document_type=document_type,
        filename=file.filename or "uploaded-document",
        storage_key=stored.storage_key,
        storage_provider=stored.storage_provider,
        file_hash=stored.file_hash,
        mime_type=stored.mime_type,
        file_size_bytes=stored.file_size_bytes,
        status=status,
        extracted_metadata_json=json.dumps(metadata),
        uploaded_at=now,
        verified_by=verified_by,
        verified_at=verified_at,
        expiry_date=_parse_datetime(expiry_date),
        updated_at=now,
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    record_audit(
        session,
        action="document_uploaded",
        entity_type="document",
        entity_id=document.id,
        after_state=_document_payload(document),
        reason="Document file uploaded and metadata recorded.",
        source="document_upload_v3_5",
        commit=True,
    )

    return _json_response({
        "status": "uploaded",
        "document": _document_payload(document),
    })


@router.get("/api/v1/documents/{document_id}/file")
def get_document_file_metadata(document_id: UUID, session: Session = Depends(get_session)):
    document = session.get(DocumentRecord, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return _json_response({
        "document": _document_payload(document),
        "download_supported": True,
        "signed_access_required": True,
        "grant_endpoint": f"/api/v1/document-access/documents/{document.id}/grants",
        "direct_object_url": None,
        "storage_key_exposed": False,
    })


@router.get("/admin/document-uploads", response_class=HTMLResponse)
def admin_document_uploads(session: Session = Depends(get_session)) -> HTMLResponse:
    leads = session.exec(select(Lead).order_by(Lead.created_at.desc()).limit(100)).all()
    lead_options = "".join(
        f"<option value='{html.escape(str(lead.id))}'>{html.escape(lead.full_name)} - {html.escape(str(lead.target_country or ''))}</option>"
        for lead in leads
    )
    return HTMLResponse(f"""
    <!doctype html>
    <html>
      <head>
        <title>Document Uploads v3.5</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; color: #0f172a; background: #f8fafc; }}
          form {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; max-width: 680px; }}
          label {{ display: block; margin-top: 12px; font-weight: 700; }}
          input, select {{ width: 100%; padding: 8px; margin-top: 4px; }}
          button {{ margin-top: 16px; padding: 8px 12px; }}
          .nav a {{ margin-right: 12px; }}
        </style>
      </head>
      <body>
        <div class="nav">
          <a href="/admin/v2">Admin v2</a>
          <a href="/admin/documents">Documents</a>
          <a href="/debug/document-uploads">Debug</a>
        </div>
        <h1>Document Uploads v3.5</h1>
        <form method="post" action="/admin/document-uploads" enctype="multipart/form-data">
          <label>Lead</label>
          <select name="lead_id">{lead_options}</select>
          <label>Document Type</label>
          <input name="document_type" value="passport" />
          <label>Status</label>
          <select name="status">
            <option value="received">received</option>
            <option value="needs_review">needs_review</option>
            <option value="verified">verified</option>
          </select>
          <label>Expiry Date</label>
          <input name="expiry_date" placeholder="YYYY-MM-DD" />
          <label>File</label>
          <input name="file" type="file" required />
          <button type="submit">Upload Document</button>
        </form>
      </body>
    </html>
    """)


@router.post("/admin/document-uploads", include_in_schema=False)
async def admin_document_upload_redirect(
    file: UploadFile = File(...),
    lead_id: Optional[UUID] = Form(default=None),
    document_type: str = Form(default="other"),
    status: str = Form(default="received"),
    expiry_date: Optional[str] = Form(default=None),
    session: Session = Depends(get_session),
):
    await upload_document(
        file=file,
        lead_id=lead_id,
        document_type=document_type,
        status=status,
        expiry_date=expiry_date,
        verified_by=None,
        session=session,
    )
    return RedirectResponse(url="/admin/document-uploads", status_code=303)


@router.get("/debug/document-uploads")
def debug_document_uploads():
    return {
        "status": "ok",
        "version": "v9.5",
        "storage_backend": settings.document_storage_backend,
        "local_storage_dir": settings.document_local_storage_dir,
        "max_upload_mb": settings.document_upload_max_mb,
        "routes": [
            "POST /api/v1/documents/upload",
            "GET /api/v1/documents/{document_id}/file",
            "POST /api/v1/document-access/documents/{document_id}/grants",
            "POST /api/v1/document-access/content",
            "GET /admin/document-uploads",
        ],
    }
