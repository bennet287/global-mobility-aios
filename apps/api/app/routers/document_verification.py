from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.pagination import MAX_QUERY_LIMIT
from app.models.domain import DocumentRecord, FollowUp, Lead
from app.services.audit_log import record_audit
from app.services.document_storage import public_document_metadata


router = APIRouter(tags=["document-verification-actions"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

DOCUMENT_OK_STATUSES = {"received", "verified"}
DOCUMENT_PROBLEM_STATUSES = {"missing", "needs_review", "rejected", "expired"}


class DocumentActionRequest(BaseModel):
    note: Optional[str] = None
    filename: Optional[str] = None
    storage_key: Optional[str] = None
    create_follow_up: bool = False


class BulkDocumentActionRequest(BaseModel):
    document_ids: Optional[List[str]] = None
    note: Optional[str] = None
    create_follow_up: bool = False


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _safe_status(value: Any) -> str:
    return str(_value(value) or "").strip().lower()


def _normal_id(value: Any) -> str:
    value = _value(value)
    if value is None:
        return ""
    try:
        return str(uuid.UUID(str(value))).replace("-", "").lower()
    except Exception:
        return str(value).replace("-", "").lower()


def _uuid_or_404(value: Any, field_name: str = "id") -> uuid.UUID:
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Invalid {field_name}") from exc


def _model_fields(model: Any) -> set[str]:
    fields = getattr(model, "model_fields", None)
    if fields is None:
        fields = getattr(model, "__fields__", {})
    return set(fields.keys())


def _json_safe(value: Any) -> Any:
    value = _value(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, DocumentRecord):
        return {key: _json_safe(value) for key, value in public_document_metadata(obj).items()}
    fields = _model_fields(obj.__class__)
    if fields:
        return {name: _json_safe(getattr(obj, name, None)) for name in fields if hasattr(obj, name)}
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif hasattr(obj, "dict"):
        data = obj.dict()
    else:
        data = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return {k: _json_safe(v) for k, v in data.items()}


def _json_response(payload: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload))


def _set_if_field(obj: Any, field: str, value: Any) -> bool:
    if field in _model_fields(obj.__class__) or hasattr(obj, field):
        setattr(obj, field, value)
        return True
    return False


def _lead_id(lead: Lead) -> Any:
    return getattr(lead, "id", None)


def _doc_id(doc: DocumentRecord) -> Any:
    return getattr(doc, "id", None)


def _get_lead(session: Session, lead_id: str) -> Lead:
    lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


def _get_document(session: Session, document_id: str) -> DocumentRecord:
    doc = session.get(DocumentRecord, _uuid_or_404(document_id, "document_id"))
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")
    return doc


def _documents_for_lead(session: Session, lead_id: Any) -> List[DocumentRecord]:
    docs = session.exec(
        select(DocumentRecord)
        .where(DocumentRecord.lead_id == lead_id)
        .limit(MAX_QUERY_LIMIT)
    ).all()
    return list(docs)


def _selected_documents(session: Session, lead: Lead, document_ids: Optional[List[str]]) -> List[DocumentRecord]:
    if not document_ids:
        return _documents_for_lead(session, _lead_id(lead))
    wanted = {_normal_id(doc_id) for doc_id in document_ids}
    docs = _documents_for_lead(session, _lead_id(lead))
    return [doc for doc in docs if _normal_id(_doc_id(doc)) in wanted]


def _load_metadata(doc: DocumentRecord) -> Dict[str, Any]:
    raw = getattr(doc, "extracted_metadata_json", None)
    if not raw:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {"raw_metadata": parsed}
    except Exception:
        return {"raw_metadata": str(raw)}


def _write_metadata(doc: DocumentRecord, action: str, status: str, note: Optional[str]) -> None:
    if "extracted_metadata_json" not in _model_fields(DocumentRecord) and not hasattr(doc, "extracted_metadata_json"):
        return
    meta = _load_metadata(doc)
    history = meta.get("verification_actions", [])
    if not isinstance(history, list):
        history = []
    history.append({
        "action": action,
        "status": status,
        "note": note,
        "timestamp": _utcnow().isoformat(),
        "actor": "document_verification_actions_v1_2",
    })
    meta["verification_actions"] = history
    meta["last_verification_action"] = action
    meta["last_verification_status"] = status
    meta["last_verification_at"] = _utcnow().isoformat()
    setattr(doc, "extracted_metadata_json", json.dumps(meta))


def _default_filename(doc: DocumentRecord, status: str) -> str:
    doc_type = str(getattr(doc, "document_type", "document") or "document")
    suffix = "pdf" if status in {"received", "verified"} else "txt"
    prefix = status.upper()
    return f"{prefix}_{doc_type}.{suffix}"


def _default_storage_key(lead_id: Any, doc: DocumentRecord, status: str) -> str:
    doc_type = str(getattr(doc, "document_type", "document") or "document")
    return f"local://document-verification/{_normal_id(lead_id)}/{doc_type}/{status}"


def _apply_document_status(
    doc: DocumentRecord,
    status: str,
    *,
    lead_id: Any,
    action: str,
    note: Optional[str] = None,
    filename: Optional[str] = None,
    storage_key: Optional[str] = None,
) -> DocumentRecord:
    status = _safe_status(status)
    if status not in {"missing", "received", "needs_review", "verified", "rejected"}:
        raise HTTPException(status_code=400, detail=f"Unsupported document status: {status}")

    _set_if_field(doc, "status", status)

    if filename:
        _set_if_field(doc, "filename", filename)
    elif status in {"received", "verified"}:
        current_filename = str(getattr(doc, "filename", "") or "")
        if current_filename.startswith("PENDING_REQUIRED_") or not current_filename:
            _set_if_field(doc, "filename", _default_filename(doc, status))

    if storage_key:
        _set_if_field(doc, "storage_key", storage_key)
    elif status in {"received", "verified"} and not getattr(doc, "storage_key", None):
        _set_if_field(doc, "storage_key", _default_storage_key(lead_id, doc, status))

    _set_if_field(doc, "updated_at", _utcnow())
    _write_metadata(doc, action, status, note)
    return doc


def _create_follow_up(session: Session, lead_id: Any, message: str) -> Optional[FollowUp]:
    fields = _model_fields(FollowUp)
    now = _utcnow()
    payload = {
        "lead_id": lead_id,
        "channel": "email",
        "message": message,
        "status": "pending",
        "due_at": now,
        "created_at": now,
        "updated_at": now,
    }
    payload = {k: v for k, v in payload.items() if k in fields and v is not None}
    if not payload:
        return None
    try:
        follow_up = FollowUp(**payload)
        session.add(follow_up)
        session.commit()
        session.refresh(follow_up)
        return follow_up
    except Exception:
        session.rollback()
        return None


def _document_summary(docs: List[DocumentRecord]) -> Dict[str, Any]:
    counts: Dict[str, Any] = {
        "total": len(docs),
        "missing": 0,
        "received": 0,
        "needs_review": 0,
        "verified": 0,
        "rejected": 0,
        "problem_documents": 0,
        "verified_or_received_documents": 0,
    }
    for doc in docs:
        status = _safe_status(getattr(doc, "status", None))
        if status in counts:
            counts[status] += 1
        if status in DOCUMENT_PROBLEM_STATUSES:
            counts["problem_documents"] += 1
        if status in DOCUMENT_OK_STATUSES:
            counts["verified_or_received_documents"] += 1

    counts["all_verified"] = counts["total"] > 0 and counts["verified"] == counts["total"]
    counts["all_received_or_verified"] = counts["total"] > 0 and counts["verified_or_received_documents"] == counts["total"]
    return counts


def _lead_document_payload(session: Session, lead: Lead) -> Dict[str, Any]:
    docs = _documents_for_lead(session, _lead_id(lead))
    return {
        "lead": _to_dict(lead),
        "summary": _document_summary(docs),
        "documents": [_to_dict(doc) for doc in docs],
    }


@router.get("/api/v1/document-verification/leads/{lead_id}/summary")
def get_document_verification_summary(lead_id: str, session: Session = Depends(get_session)):
    lead = _get_lead(session, lead_id)
    return _json_response(_lead_document_payload(session, lead))


@router.post("/api/v1/document-verification/documents/{document_id}/receive")
def receive_document(
    document_id: str,
    request: DocumentActionRequest = DocumentActionRequest(),
    session: Session = Depends(get_session),
):
    doc = _get_document(session, document_id)
    lead_id = getattr(doc, "lead_id", None)
    before = _to_dict(doc)
    _apply_document_status(
        doc,
        "received",
        lead_id=lead_id,
        action="receive_document",
        note=request.note,
        filename=request.filename,
        storage_key=request.storage_key,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(session, lead_id, f"Document received: {getattr(doc, 'document_type', 'document')}")
    record_audit(
        session,
        action="document_received",
        entity_type="document",
        entity_id=_doc_id(doc),
        before_state=before,
        after_state=_to_dict(doc),
        reason=request.note,
        source="document_verification",
        commit=True,
    )
    return _json_response({"status": "received", "document": _to_dict(doc), "follow_up": _to_dict(follow_up) if follow_up else None})


@router.post("/api/v1/document-verification/documents/{document_id}/verify")
def verify_document(
    document_id: str,
    request: DocumentActionRequest = DocumentActionRequest(),
    session: Session = Depends(get_session),
):
    doc = _get_document(session, document_id)
    lead_id = getattr(doc, "lead_id", None)
    before = _to_dict(doc)
    _apply_document_status(
        doc,
        "verified",
        lead_id=lead_id,
        action="verify_document",
        note=request.note,
        filename=request.filename,
        storage_key=request.storage_key,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(session, lead_id, f"Document verified: {getattr(doc, 'document_type', 'document')}")
    record_audit(
        session,
        action="document_verified",
        entity_type="document",
        entity_id=_doc_id(doc),
        before_state=before,
        after_state=_to_dict(doc),
        reason=request.note,
        source="document_verification",
        commit=True,
    )
    return _json_response({"status": "verified", "document": _to_dict(doc), "follow_up": _to_dict(follow_up) if follow_up else None})


@router.post("/api/v1/document-verification/documents/{document_id}/reject")
def reject_document(
    document_id: str,
    request: DocumentActionRequest = DocumentActionRequest(),
    session: Session = Depends(get_session),
):
    doc = _get_document(session, document_id)
    lead_id = getattr(doc, "lead_id", None)
    before = _to_dict(doc)
    _apply_document_status(
        doc,
        "rejected",
        lead_id=lead_id,
        action="reject_document",
        note=request.note,
        filename=request.filename,
        storage_key=request.storage_key,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(session, lead_id, f"Document rejected: {getattr(doc, 'document_type', 'document')}. {request.note or ''}".strip())
    record_audit(
        session,
        action="document_rejected",
        entity_type="document",
        entity_id=_doc_id(doc),
        before_state=before,
        after_state=_to_dict(doc),
        reason=request.note,
        source="document_verification",
        commit=True,
    )
    return _json_response({"status": "rejected", "document": _to_dict(doc), "follow_up": _to_dict(follow_up) if follow_up else None})


@router.post("/api/v1/document-verification/leads/{lead_id}/bulk-receive")
def bulk_receive_documents(
    lead_id: str,
    request: BulkDocumentActionRequest = BulkDocumentActionRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    docs = _selected_documents(session, lead, request.document_ids)
    if not docs:
        raise HTTPException(status_code=404, detail="No matching documents found for this lead")

    before = [_to_dict(doc) for doc in docs]
    updated = []
    for doc in docs:
        _apply_document_status(doc, "received", lead_id=_lead_id(lead), action="bulk_receive", note=request.note)
        session.add(doc)
        updated.append(doc)

    session.commit()
    for doc in updated:
        session.refresh(doc)

    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(session, _lead_id(lead), f"Bulk document receive completed for {len(updated)} document(s).")

    record_audit(
        session,
        action="documents_bulk_received",
        entity_type="lead",
        entity_id=_lead_id(lead),
        before_state={"documents": before},
        after_state={"documents": [_to_dict(doc) for doc in updated]},
        reason=request.note,
        source="document_verification",
        commit=True,
    )

    return _json_response({
        "status": "received",
        "updated_count": len(updated),
        "documents": [_to_dict(doc) for doc in updated],
        "follow_up": _to_dict(follow_up) if follow_up else None,
        "summary": _lead_document_payload(session, lead)["summary"],
    })


@router.post("/api/v1/document-verification/leads/{lead_id}/bulk-verify")
def bulk_verify_documents(
    lead_id: str,
    request: BulkDocumentActionRequest = BulkDocumentActionRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    docs = _selected_documents(session, lead, request.document_ids)
    if not docs:
        raise HTTPException(status_code=404, detail="No matching documents found for this lead")

    before = [_to_dict(doc) for doc in docs]
    updated = []
    for doc in docs:
        _apply_document_status(doc, "verified", lead_id=_lead_id(lead), action="bulk_verify", note=request.note)
        session.add(doc)
        updated.append(doc)

    session.commit()
    for doc in updated:
        session.refresh(doc)

    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(session, _lead_id(lead), f"Bulk document verification completed for {len(updated)} document(s).")

    record_audit(
        session,
        action="documents_bulk_verified",
        entity_type="lead",
        entity_id=_lead_id(lead),
        before_state={"documents": before},
        after_state={"documents": [_to_dict(doc) for doc in updated]},
        reason=request.note,
        source="document_verification",
        commit=True,
    )

    return _json_response({
        "status": "verified",
        "updated_count": len(updated),
        "documents": [_to_dict(doc) for doc in updated],
        "follow_up": _to_dict(follow_up) if follow_up else None,
        "summary": _lead_document_payload(session, lead)["summary"],
    })


@router.get("/admin/document-verification", response_class=HTMLResponse)
def document_verification_admin(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead).limit(MAX_QUERY_LIMIT)).all()
    rows = []
    for lead in leads:
        payload = _lead_document_payload(session, lead)
        summary = payload["summary"]
        lead_id = payload["lead"].get("id")
        rows.append(
            f"""
            <tr>
              <td><a href="/admin/leads/{lead_id}">{payload['lead'].get('full_name') or lead_id}</a></td>
              <td>{payload['lead'].get('target_country') or '-'}</td>
              <td>{summary['total']}</td>
              <td>{summary['missing']}</td>
              <td>{summary['received']}</td>
              <td>{summary['verified']}</td>
              <td>{summary['problem_documents']}</td>
              <td>
                <form method="post" action="/admin/document-verification/leads/{lead_id}/bulk-receive" style="display:inline">
                  <button type="submit">Mark All Received</button>
                </form>
                <form method="post" action="/admin/document-verification/leads/{lead_id}/bulk-verify" style="display:inline">
                  <button type="submit">Verify All</button>
                </form>
                <a href="/admin/document-verification/leads/{lead_id}">Open</a>
              </td>
            </tr>
            """
        )

    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>Document Verification Actions</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
          th {{ background: #f4f4f4; }}
          button {{ margin: 2px; }}
        </style>
      </head>
      <body>
        <h1>Document Verification Actions v1.2</h1>
        <p><a href="/admin">Back to Admin</a> | <a href="/debug/document-verification">Debug</a></p>
        <table>
          <thead>
            <tr>
              <th>Lead</th><th>Country</th><th>Total</th><th>Missing</th><th>Received</th><th>Verified</th><th>Problem</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/admin/document-verification/leads/{lead_id}", response_class=HTMLResponse)
def lead_document_verification_admin(lead_id: str, session: Session = Depends(get_session)):
    lead = _get_lead(session, lead_id)
    payload = _lead_document_payload(session, lead)
    rows = []
    for doc in payload["documents"]:
        doc_id = doc.get("id")
        rows.append(
            f"""
            <tr>
              <td>{doc.get('document_type')}</td>
              <td>{doc.get('filename') or '-'}</td>
              <td>{doc.get('status')}</td>
              <td>{doc.get('storage_provider') or '-'} / signed access</td>
              <td>
                <form method="post" action="/admin/document-verification/documents/{doc_id}/receive" style="display:inline">
                  <button type="submit">Received</button>
                </form>
                <form method="post" action="/admin/document-verification/documents/{doc_id}/verify" style="display:inline">
                  <button type="submit">Verify</button>
                </form>
                <form method="post" action="/admin/document-verification/documents/{doc_id}/reject" style="display:inline">
                  <button type="submit">Reject</button>
                </form>
              </td>
            </tr>
            """
        )

    summary = payload["summary"]
    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>Lead Document Verification</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
          th {{ background: #f4f4f4; }}
          button {{ margin: 2px; }}
        </style>
      </head>
      <body>
        <h1>Document Verification: {payload['lead'].get('full_name') or lead_id}</h1>
        <p><a href="/admin/document-verification">Back</a> | <a href="/admin/leads/{lead_id}">Lead Detail</a></p>
        <p>Total: {summary['total']} | Missing: {summary['missing']} | Received: {summary['received']} | Verified: {summary['verified']} | Problems: {summary['problem_documents']}</p>
        <form method="post" action="/admin/document-verification/leads/{lead_id}/bulk-receive" style="display:inline">
          <button type="submit">Mark All Received</button>
        </form>
        <form method="post" action="/admin/document-verification/leads/{lead_id}/bulk-verify" style="display:inline">
          <button type="submit">Verify All</button>
        </form>
        <table>
          <thead>
            <tr><th>Type</th><th>Filename</th><th>Status</th><th>Storage</th><th>Actions</th></tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </body>
    </html>
    """
    return HTMLResponse(html)


@router.post("/admin/document-verification/leads/{lead_id}/bulk-receive")
def admin_bulk_receive_documents(lead_id: str, session: Session = Depends(get_session)):
    bulk_receive_documents(
        lead_id,
        BulkDocumentActionRequest(note="Admin marked all current checklist documents as received."),
        session,
    )
    return RedirectResponse(url=f"/admin/document-verification/leads/{lead_id}", status_code=303)


@router.post("/admin/document-verification/leads/{lead_id}/bulk-verify")
def admin_bulk_verify_documents(lead_id: str, session: Session = Depends(get_session)):
    bulk_verify_documents(
        lead_id,
        BulkDocumentActionRequest(note="Admin verified all current checklist documents."),
        session,
    )
    return RedirectResponse(url=f"/admin/document-verification/leads/{lead_id}", status_code=303)


@router.post("/admin/document-verification/documents/{document_id}/receive")
def admin_receive_document(document_id: str, session: Session = Depends(get_session)):
    doc = _get_document(session, document_id)
    lead_id = str(getattr(doc, "lead_id", ""))
    receive_document(document_id, DocumentActionRequest(note="Admin marked document as received."), session)
    return RedirectResponse(url=f"/admin/document-verification/leads/{lead_id}", status_code=303)


@router.post("/admin/document-verification/documents/{document_id}/verify")
def admin_verify_document(document_id: str, session: Session = Depends(get_session)):
    doc = _get_document(session, document_id)
    lead_id = str(getattr(doc, "lead_id", ""))
    verify_document(document_id, DocumentActionRequest(note="Admin verified document."), session)
    return RedirectResponse(url=f"/admin/document-verification/leads/{lead_id}", status_code=303)


@router.post("/admin/document-verification/documents/{document_id}/reject")
def admin_reject_document(document_id: str, session: Session = Depends(get_session)):
    doc = _get_document(session, document_id)
    lead_id = str(getattr(doc, "lead_id", ""))
    reject_document(document_id, DocumentActionRequest(note="Admin rejected document.", create_follow_up=True), session)
    return RedirectResponse(url=f"/admin/document-verification/leads/{lead_id}", status_code=303)


@router.get("/debug/document-verification")
def debug_document_verification():
    return {
        "status": "ok",
        "version": "v1.2",
        "routes": [
            "GET /api/v1/document-verification/leads/{lead_id}/summary",
            "POST /api/v1/document-verification/leads/{lead_id}/bulk-receive",
            "POST /api/v1/document-verification/leads/{lead_id}/bulk-verify",
            "POST /api/v1/document-verification/documents/{document_id}/receive",
            "POST /api/v1/document-verification/documents/{document_id}/verify",
            "POST /api/v1/document-verification/documents/{document_id}/reject",
            "GET /admin/document-verification",
            "GET /admin/document-verification/leads/{lead_id}",
        ],
    }
