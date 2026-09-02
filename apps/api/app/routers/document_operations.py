from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.pagination import DEFAULT_QUERY_LIMIT, MAX_QUERY_LIMIT, clamp_query_limit
from app.models.domain import DocumentRecord, FollowUp, Lead
from app.services.document_storage import public_document_metadata

router = APIRouter()

MISSING_STATUSES = {"missing", "needs_review", "rejected"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fields(model_cls: type[Any]) -> set[str]:
    raw = getattr(model_cls, "model_fields", None) or getattr(model_cls, "__fields__", {})
    return set(raw.keys())


def _field_defs(model_cls: type[Any]) -> dict[str, Any]:
    return getattr(model_cls, "model_fields", None) or getattr(model_cls, "__fields__", {})


def _has(model_cls: type[Any], name: str) -> bool:
    return name in _fields(model_cls)


def _safe_value(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)


def _status(doc: DocumentRecord) -> str:
    return str(_safe_value(doc, "status", "missing") or "missing").lower()


def _doc_label(document_type: str) -> str:
    return document_type.replace("_", " ").strip().title()


def _document_to_dict(doc: DocumentRecord) -> dict[str, Any]:
    payload = public_document_metadata(doc)
    payload.update({
        "id": str(_safe_value(doc, "id")),
        "lead_id": str(_safe_value(doc, "lead_id")) if _safe_value(doc, "lead_id") else None,
        "label": _doc_label(str(_safe_value(doc, "document_type", ""))),
        "created_at": str(_safe_value(doc, "created_at")) if _safe_value(doc, "created_at") else None,
    })
    return payload


def _lead_or_404(session: Session, lead_id: UUID) -> Lead:
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


def _lead_documents(session: Session, lead_id: UUID) -> list[DocumentRecord]:
    return list(
        session.exec(
            select(DocumentRecord)
            .where(DocumentRecord.lead_id == lead_id)
            .limit(MAX_QUERY_LIMIT)
        ).all()
    )


def _build_summary(lead: Lead, documents: list[DocumentRecord]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for doc in documents:
        status = _status(doc)
        counts[status] = counts.get(status, 0) + 1

    missing_docs = [doc for doc in documents if _status(doc) in MISSING_STATUSES]
    verified_docs = [doc for doc in documents if _status(doc) == "verified"]
    received_docs = [doc for doc in documents if _status(doc) == "received"]

    total = len(documents)
    completed = len(verified_docs)
    completion_rate = round(completed / total, 3) if total else 0.0

    return {
        "lead": {
            "id": str(_safe_value(lead, "id")),
            "full_name": _safe_value(lead, "full_name"),
            "email": _safe_value(lead, "email"),
            "intent": str(_safe_value(lead, "intent", "")),
            "target_country": _safe_value(lead, "target_country"),
            "status": str(_safe_value(lead, "status", "")),
        },
        "total_documents": total,
        "verified_count": len(verified_docs),
        "received_count": len(received_docs),
        "missing_count": len(missing_docs),
        "completion_rate": completion_rate,
        "counts_by_status": counts,
        "missing_documents": [_document_to_dict(doc) for doc in missing_docs],
        "documents": [_document_to_dict(doc) for doc in documents],
    }


def _missing_request_message(lead: Lead, missing_docs: list[dict[str, Any]]) -> str:
    name = _safe_value(lead, "full_name", "there") or "there"
    intent = str(_safe_value(lead, "intent", "your application")).replace("LeadIntent.", "").replace("_", " ")
    country = _safe_value(lead, "target_country", "your target country") or "your target country"
    items = "\n".join(f"{idx}. {doc['label']}" for idx, doc in enumerate(missing_docs, start=1))
    return (
        f"Dear {name},\n\n"
        f"Thank you for sharing your profile. To continue your {intent} process for {country}, "
        f"please send the following pending documents:\n\n"
        f"{items}\n\n"
        "Once we receive them, our document team will verify the files and update your application checklist.\n\n"
        "Kind regards,\n"
        "Global Mobility AIOS"
    )


def _make_follow_up(lead: Lead, message: str) -> FollowUp:
    fields = _fields(FollowUp)
    kwargs: dict[str, Any] = {}

    common_values: dict[str, Any] = {
        "lead_id": _safe_value(lead, "id"),
        "channel": "email",
        "purpose": "request_missing_documents",
        "category": "document_request",
        "type": "document_request",
        "template_key": "missing_documents_v1",
        "subject": "Pending documents required for your application",
        "title": "Request missing documents",
        "message": message,
        "body": message,
        "content": message,
        "notes": message,
        "status": "pending",
        "created_at": _now(),
        "updated_at": _now(),
        "due_at": _now() + timedelta(days=2),
        "scheduled_at": _now() + timedelta(days=1),
    }

    for key, value in common_values.items():
        if key in fields:
            kwargs[key] = value

    # Best-effort support for SQLModel/Pydantic required fields with unexpected names.
    for name, field in _field_defs(FollowUp).items():
        if name in kwargs or name == "id":
            continue
        required = False
        try:
            required = field.is_required()  # Pydantic v2
        except Exception:
            required = bool(getattr(field, "required", False))  # Pydantic v1
        if not required:
            continue
        annotation = getattr(field, "annotation", None) or getattr(field, "type_", None)
        lname = name.lower()
        if lname.endswith("lead_id"):
            kwargs[name] = _safe_value(lead, "id")
        elif "message" in lname or "body" in lname or "content" in lname or "note" in lname:
            kwargs[name] = message
        elif "subject" in lname or "title" in lname:
            kwargs[name] = "Pending documents required for your application"
        elif "status" in lname:
            kwargs[name] = "pending"
        elif annotation in (int,):
            kwargs[name] = 0
        elif annotation in (float,):
            kwargs[name] = 0.0
        elif annotation in (bool,):
            kwargs[name] = False
        else:
            kwargs[name] = ""

    return FollowUp(**kwargs)


@router.get("/api/v1/leads/{lead_id}/documents/summary")
def get_lead_document_summary(lead_id: UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    lead = _lead_or_404(session, lead_id)
    return _build_summary(lead, _lead_documents(session, lead_id))


@router.get("/api/v1/documents/missing")
def get_missing_documents(
    limit: int = DEFAULT_QUERY_LIMIT,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    query_limit = clamp_query_limit(limit)
    missing = list(
        session.exec(
            select(DocumentRecord)
            .where(DocumentRecord.status.in_(MISSING_STATUSES))
            .limit(query_limit)
        ).all()
    )
    lead_cache: dict[str, Lead | None] = {}
    rows: list[dict[str, Any]] = []

    for doc in missing:
        lead_id = _safe_value(doc, "lead_id")
        lead_key = str(lead_id) if lead_id else ""
        if lead_key not in lead_cache:
            lead_cache[lead_key] = session.get(Lead, lead_id) if lead_id else None
        lead = lead_cache[lead_key]
        row = _document_to_dict(doc)
        row["lead_name"] = _safe_value(lead, "full_name") if lead else None
        row["target_country"] = _safe_value(lead, "target_country") if lead else None
        row["intent"] = str(_safe_value(lead, "intent", "")) if lead else None
        rows.append(row)

    return {"missing_count": len(rows), "items": rows}


@router.get("/api/v1/documents/summary")
def get_global_document_summary(
    limit: int = DEFAULT_QUERY_LIMIT,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    query_limit = clamp_query_limit(limit)
    leads = list(session.exec(select(Lead).limit(query_limit)).all())
    summaries = []
    total_missing = 0
    total_documents = 0

    for lead in leads:
        summary = _build_summary(lead, _lead_documents(session, _safe_value(lead, "id")))
        total_missing += summary["missing_count"]
        total_documents += summary["total_documents"]
        summaries.append(summary)

    return {
        "lead_count": len(leads),
        "total_documents": total_documents,
        "total_missing_documents": total_missing,
        "leads": summaries,
    }


@router.post("/api/v1/operations/leads/{lead_id}/request-missing-documents")
def request_missing_documents(lead_id: UUID, session: Session = Depends(get_session)) -> dict[str, Any]:
    lead = _lead_or_404(session, lead_id)
    summary = _build_summary(lead, _lead_documents(session, lead_id))
    missing_docs = summary["missing_documents"]

    if not missing_docs:
        return {
            "created": False,
            "reason": "No missing, rejected, or needs_review documents found for this lead.",
            "lead_id": str(lead_id),
            "missing_count": 0,
        }

    message = _missing_request_message(lead, missing_docs)
    follow_up = _make_follow_up(lead, message)
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)

    return {
        "created": True,
        "follow_up_id": str(_safe_value(follow_up, "id")),
        "lead_id": str(lead_id),
        "missing_count": len(missing_docs),
        "message": message,
    }


def _html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f7fb; color: #151515; }}
    a {{ color: #174ea6; text-decoration: none; }}
    .card {{ background: white; border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
    .muted {{ color: #666; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border-bottom: 1px solid #eee; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #fafafa; }}
    button {{ padding: 8px 12px; border: 0; border-radius: 8px; background: #174ea6; color: white; cursor: pointer; }}
    button:hover {{ opacity: .92; }}
    .pill {{ display: inline-block; padding: 3px 8px; border-radius: 999px; background: #eee; font-size: 12px; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""


@router.get("/admin/documents", response_class=HTMLResponse)
def admin_documents(session: Session = Depends(get_session)) -> HTMLResponse:
    summary = get_global_document_summary(session)
    rows = []
    for item in summary["leads"]:
        lead = item["lead"]
        rows.append(
            "<tr>"
            f"<td><a href='/admin/leads/{lead['id']}'>{lead.get('full_name') or lead['id']}</a></td>"
            f"<td>{lead.get('intent') or ''}</td>"
            f"<td>{lead.get('target_country') or ''}</td>"
            f"<td>{item['total_documents']}</td>"
            f"<td><strong>{item['missing_count']}</strong></td>"
            f"<td>{item['completion_rate']}</td>"
            f"<td><a href='/admin/leads/{lead['id']}/documents'>Document workspace</a></td>"
            f"<td><form method='post' action='/api/v1/operations/leads/{lead['id']}/request-missing-documents'><button>Request missing docs</button></form></td>"
            "</tr>"
        )
    table = "".join(rows) or "<tr><td colspan='8'>No leads found.</td></tr>"
    body = f"""
<h1>Document Operations</h1>
<p><a href='/admin'>← Back to Admin Dashboard</a></p>
<div class='card'>
  <strong>Total leads:</strong> {summary['lead_count']} &nbsp; | &nbsp;
  <strong>Total documents:</strong> {summary['total_documents']} &nbsp; | &nbsp;
  <strong>Total missing documents:</strong> {summary['total_missing_documents']}
</div>
<div class='card'>
<table>
<thead><tr><th>Lead</th><th>Intent</th><th>Country</th><th>Total</th><th>Missing</th><th>Completion</th><th>Documents</th><th>Action</th></tr></thead>
<tbody>{table}</tbody>
</table>
</div>
"""
    return HTMLResponse(_html_page("Document Operations", body))


@router.get("/admin/documents/missing-card", response_class=HTMLResponse)
def admin_missing_documents_card(session: Session = Depends(get_session)) -> HTMLResponse:
    data = get_missing_documents(session)
    rows = []
    for item in data["items"][:25]:
        lead_link = f"<a href='/admin/leads/{item['lead_id']}'>{item.get('lead_name') or item['lead_id']}</a>" if item.get("lead_id") else "-"
        rows.append(
            "<tr>"
            f"<td>{lead_link}</td>"
            f"<td>{item['label']}</td>"
            f"<td><span class='pill'>{item['status']}</span></td>"
            f"<td>{item.get('target_country') or ''}</td>"
            "</tr>"
        )
    table = "".join(rows) or "<tr><td colspan='4'>No missing documents.</td></tr>"
    body = f"""
<div class='card'>
  <h2>Missing Documents</h2>
  <p class='muted'>Showing up to 25 missing, rejected, or needs-review documents.</p>
  <p><strong>Total pending:</strong> {data['missing_count']} &nbsp; | &nbsp; <a href='/admin/documents' target='_top'>Open Document Operations</a></p>
  <table>
    <thead><tr><th>Lead</th><th>Document</th><th>Status</th><th>Country</th></tr></thead>
    <tbody>{table}</tbody>
  </table>
</div>
"""
    return HTMLResponse(_html_page("Missing Documents", body))


@router.get("/admin/leads/{lead_id}/documents/summary-card", response_class=HTMLResponse)
def admin_lead_document_summary_card(lead_id: UUID, session: Session = Depends(get_session)) -> HTMLResponse:
    lead = _lead_or_404(session, lead_id)
    summary = _build_summary(lead, _lead_documents(session, lead_id))
    rows = []
    for doc in summary["missing_documents"]:
        rows.append(
            "<tr>"
            f"<td>{doc['label']}</td>"
            f"<td><span class='pill'>{doc['status']}</span></td>"
            f"<td>{doc.get('filename') or ''}</td>"
            "</tr>"
        )
    table = "".join(rows) or "<tr><td colspan='3'>No missing documents.</td></tr>"
    body = f"""
<div class='card'>
  <h2>Document Summary</h2>
  <p>
    <strong>Total:</strong> {summary['total_documents']} &nbsp; | &nbsp;
    <strong>Verified:</strong> {summary['verified_count']} &nbsp; | &nbsp;
    <strong>Received:</strong> {summary['received_count']} &nbsp; | &nbsp;
    <strong>Missing / review:</strong> {summary['missing_count']} &nbsp; | &nbsp;
    <strong>Completion:</strong> {summary['completion_rate']}
  </p>
  <p>
    <a href='/admin/leads/{lead_id}/documents' target='_top'>Open Document Workspace</a>
  </p>
  <form method='post' action='/api/v1/operations/leads/{lead_id}/request-missing-documents'>
    <button>Request Missing Documents</button>
  </form>
  <h3>Pending Documents</h3>
  <table>
    <thead><tr><th>Document</th><th>Status</th><th>Filename</th></tr></thead>
    <tbody>{table}</tbody>
  </table>
</div>
"""
    return HTMLResponse(_html_page("Lead Document Summary", body))
