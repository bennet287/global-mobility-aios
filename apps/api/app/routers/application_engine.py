from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    ApplicationRecord,
    DocumentRecord,
    FollowUp,
    HumanReview,
    Lead,
    TruthClaim,
)

router = APIRouter(tags=["application-engine"])


class ApplicationDraftRequest(BaseModel):
    application_type: str = Field(default="visa", description="visa, study, job, scholarship, etc.")
    title: Optional[str] = None
    target_country: Optional[str] = None
    notes: Optional[str] = None
    create_follow_up: bool = True


class ApplicationActionRequest(BaseModel):
    note: Optional[str] = None


PROBLEM_DOCUMENT_STATUSES = {"missing", "needs_review", "rejected"}
OK_DOCUMENT_STATUSES = {"verified", "received"}
PENDING_REVIEW_STATUSES = {"pending", "open", "needs_review", "in_review"}
REJECTED_TRUTH_STATUSES = {"rejected", "false", "unsafe"}
APPLICATION_READY_STAGES = {
    "blocked_truth_rejected",
    "human_review_required",
    "documents_incomplete",
    "ready_for_human_approval",
}


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _safe_status(value: Any) -> str:
    return str(_value(value) or "").strip().lower()


def _model_fields(model: Any) -> set[str]:
    return set(getattr(model, "model_fields", getattr(model, "__fields__", {})).keys())


def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif hasattr(obj, "dict"):
        data = obj.dict()
    else:
        data = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return {k: _value(v) for k, v in data.items()}


def _json_response(payload: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload))




def _uuid_or_404(value: Any, field_name: str = "id") -> uuid.UUID:
    """Convert path/string IDs to UUIDs for SQLModel UUID primary keys.

    SQLAlchemy's UUID type expects a uuid.UUID object. Passing a string causes
    errors such as: AttributeError: 'str' object has no attribute 'hex'.
    """
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Invalid {field_name}", field_name: str(value)},
        ) from exc




def _coerce_uuid(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


def _json_safe_value(value: Any) -> Any:
    value = _value(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _uuid_match_key(value: Any) -> str:
    """Normalize UUID values for SQLite/SQLModel matching.

    SQLite stores SQLAlchemy UUID values as 32-character hex strings, while
    API paths and JSON responses usually use hyphenated UUID strings. This
    helper makes informational counts robust across both forms.
    """
    value = _value(value)
    if value is None:
        return ""
    if isinstance(value, uuid.UUID):
        return value.hex
    raw = str(value).strip()
    try:
        return uuid.UUID(raw).hex
    except ValueError:
        return raw.replace("-", "").lower()


def _application_record_to_dict(app: Any) -> Dict[str, Any]:
    """Serialize ApplicationRecord reliably.

    Some SQLModel table instances can return an empty model_dump() when the
    table model was declared with fields that are not exposed in the runtime
    serializer. For application workflow responses, read the known persisted
    fields explicitly so PowerShell/API clients can access application.id.
    """
    if app is None:
        return {}

    ordered_fields = [
        "id",
        "lead_id",
        "domain",
        "target_country",
        "target_institution_or_employer",
        "status",
        "risk_score",
        "created_at",
        "updated_at",
        "title",
        "notes",
        "stage",
        "current_stage",
    ]
    data: Dict[str, Any] = {}
    for field in ordered_fields:
        if hasattr(app, field):
            data[field] = _json_safe_value(getattr(app, field))

    if not data:
        try:
            raw = vars(app)
        except TypeError:
            raw = {}
        data = {k: _json_safe_value(v) for k, v in raw.items() if not k.startswith("_")}

    return data

def _set_if_field(obj: Any, field: str, value: Any) -> bool:
    if field in _model_fields(obj.__class__) or hasattr(obj, field):
        setattr(obj, field, value)
        return True
    return False


def _safe_application_workflow_status(readiness_stage: str) -> str:
    """Return a persisted ApplicationRecord status/stage-safe value.

    Readiness stages such as blocked_truth_rejected are computed guardrail states.
    They must not be stored in enum-backed application or lead status columns.
    """
    if readiness_stage == "ready_for_human_approval":
        return "draft"
    return "draft"


def _records_for_lead(session: Session, lead_id: str):
    truth_claims = session.exec(select(TruthClaim).where(TruthClaim.lead_id == lead_id)).all()
    human_reviews = session.exec(select(HumanReview).where(HumanReview.lead_id == lead_id)).all()
    documents = session.exec(select(DocumentRecord).where(DocumentRecord.lead_id == lead_id)).all()

    # ApplicationRecord.lead_id is stored by SQLite as a 32-character UUID hex
    # string, while route/readiness logic may carry uuid.UUID objects or
    # hyphenated UUID strings. Count application records using a normalized key
    # rather than a direct equality comparison.
    lead_key = _uuid_match_key(lead_id)
    application_count = 0
    for app in session.exec(select(ApplicationRecord)).all():
        if _uuid_match_key(getattr(app, "lead_id", None)) == lead_key:
            application_count += 1

    return truth_claims, human_reviews, documents, application_count


def _calculate_readiness(session: Session, lead: Lead) -> Dict[str, Any]:
    lead_id = getattr(lead, "id")
    truth_claims, human_reviews, documents, application_count = _records_for_lead(session, lead_id)

    rejected_truth = [t for t in truth_claims if _safe_status(getattr(t, "verdict", getattr(t, "status", None))) in REJECTED_TRUTH_STATUSES]
    truth_needing_review = [t for t in truth_claims if bool(getattr(t, "requires_human_review", False))]
    pending_reviews = [r for r in human_reviews if _safe_status(getattr(r, "status", None)) in PENDING_REVIEW_STATUSES]
    problem_documents = [d for d in documents if _safe_status(getattr(d, "status", None)) in PROBLEM_DOCUMENT_STATUSES]
    verified_documents = [d for d in documents if _safe_status(getattr(d, "status", None)) in OK_DOCUMENT_STATUSES]

    blockers: List[str] = []
    warnings: List[str] = []
    if rejected_truth:
        blockers.append("truth_claim_rejected")
    if truth_needing_review:
        blockers.append("truth_claim_requires_review")
    if pending_reviews:
        blockers.append("human_review_pending")
    if problem_documents:
        warnings.append("documents_missing_or_problematic")
    if not documents:
        warnings.append("no_document_checklist")

    if rejected_truth:
        stage = "blocked_truth_rejected"
        next_action = "Resolve or replace rejected truth claims before application preparation or submission."
    elif truth_needing_review or pending_reviews:
        stage = "human_review_required"
        next_action = "Complete human review before application preparation or submission."
    elif problem_documents or not documents:
        stage = "documents_incomplete"
        next_action = "Complete and verify required documents before submission."
    else:
        stage = "ready_for_human_approval"
        next_action = "Ready for human approval before submission."

    return {
        "lead": _to_dict(lead),
        "stage": stage,
        "can_create_application": True,
        "can_approve": not blockers and not problem_documents and bool(documents),
        "can_submit": False,
        "blockers": blockers,
        "warnings": warnings,
        "counts": {
            "truth_claims": len(truth_claims),
            "rejected_truth_claims": len(rejected_truth),
            "truth_claims_needing_review": len(truth_needing_review),
            "pending_reviews": len(pending_reviews),
            "documents": len(documents),
            "problem_documents": len(problem_documents),
            "verified_or_received_documents": len(verified_documents),
            "applications": application_count,
        },
        "next_action": next_action,
    }


def _build_application_payload(lead: Lead, request: ApplicationDraftRequest, readiness: Dict[str, Any]) -> Dict[str, Any]:
    fields = _model_fields(ApplicationRecord)
    now = datetime.utcnow()
    target_country = request.target_country or getattr(lead, "target_country", None)
    application_type = request.application_type or getattr(lead, "intent", "visa")
    readiness_stage = readiness["stage"]
    persisted_workflow_stage = _safe_application_workflow_status(readiness_stage)
    title = request.title or f"{application_type.title()} application for {getattr(lead, 'full_name', 'lead')}"
    notes = request.notes or (
        f"Readiness stage: {readiness_stage}. Next action: {readiness['next_action']}"
    )

    candidates: Dict[str, Any] = {
        "lead_id": getattr(lead, "id", None),
        "domain": application_type,
        "application_type": application_type,
        "type": application_type,
        "kind": application_type,
        "target_country": target_country,
        "country": target_country,
        "title": title,
        "name": title,
        "status": "draft",
        "risk_score": 0.5,
        "stage": persisted_workflow_stage,
        "current_stage": persisted_workflow_stage,
        "notes": notes,
        "metadata": readiness,
        "payload": readiness,
        "created_at": now,
        "updated_at": now,
    }

    return {k: v for k, v in candidates.items() if k in fields and v is not None}


def _application_id(app: ApplicationRecord) -> Any:
    return getattr(app, "id", None)


def _get_application(session: Session, application_id: str) -> ApplicationRecord:
    app_pk = _uuid_or_404(application_id, "application_id")
    app = session.get(ApplicationRecord, app_pk)
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found")
    return app


def _create_application_record(session: Session, lead: Lead, request: ApplicationDraftRequest, readiness: Dict[str, Any]) -> ApplicationRecord:
    payload = _build_application_payload(lead, request, readiness)
    try:
        app = ApplicationRecord(**payload)
        session.add(app)
        session.commit()
        session.refresh(app)
        return app
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Could not create ApplicationRecord from available model fields.",
                "error": str(exc),
                "payload_keys": sorted(payload.keys()),
                "model_fields": sorted(_model_fields(ApplicationRecord)),
            },
        ) from exc


def _create_follow_up(session: Session, lead: Lead, message: str) -> Optional[FollowUp]:
    fields = _model_fields(FollowUp)
    now = datetime.utcnow()
    payload = {
        "lead_id": getattr(lead, "id", None),
        "channel": "email",
        "message": message,
        "status": "pending",
        "due_at": now,
        "created_at": now,
        "updated_at": now,
    }
    payload = {k: v for k, v in payload.items() if k in fields and v is not None}
    try:
        follow_up = FollowUp(**payload)
        session.add(follow_up)
        session.commit()
        session.refresh(follow_up)
        return follow_up
    except Exception:
        session.rollback()
        return None


@router.get("/api/v1/applications/leads/{lead_id}/readiness")
def get_application_readiness(lead_id: str, session: Session = Depends(get_session)):
    lead_pk = _uuid_or_404(lead_id, "lead_id")
    lead = session.get(Lead, lead_pk)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _json_response(_calculate_readiness(session, lead))


@router.get("/api/v1/applications/queue")
def get_application_queue(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    items = []
    stage_counts: Dict[str, int] = {}
    for lead in leads:
        readiness = _calculate_readiness(session, lead)
        stage = readiness["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        items.append(readiness)
    return _json_response({"total_leads": len(leads), "stage_counts": stage_counts, "items": items})


@router.post("/api/v1/applications/leads/{lead_id}/draft")
def create_application_draft(lead_id: str, request: ApplicationDraftRequest, session: Session = Depends(get_session)):

    # Application Draft Control v1.8 duplicate guard
    from fastapi import HTTPException as _V18HTTPException
    from app.routers.application_draft_control import (
        active_applications_for_lead as _v18_active_applications_for_lead,
        serialize_application as _v18_serialize_application,
    )
    _v18_existing_apps = _v18_active_applications_for_lead(session, lead_id)
    if _v18_existing_apps:
        raise _V18HTTPException(
            status_code=409,
            detail={
                "message": "Draft creation blocked because an active application already exists for this lead.",
                "blocker": "active_application_exists",
                "active_applications": [_v18_serialize_application(app) for app in _v18_existing_apps],
                "next_action": "Use the existing application or cancel duplicate drafts first.",
            },
        )

    # Application Draft Guard v2.3 readiness guard
    try:
        _v23_lead = _get_lead(session, lead_id)
    except NameError:
        _v23_lead = session.get(Lead, _coerce_uuid(lead_id))
    if not _v23_lead:
        raise _V18HTTPException(status_code=404, detail="Lead not found")

    _v23_readiness = _calculate_readiness(session, _v23_lead)
    _v23_stage = str(_v23_readiness.get("stage") or "")
    _v23_blockers = _v23_readiness.get("blockers") or []
    _v23_warnings = _v23_readiness.get("warnings") or []
    if _v23_stage != "ready_for_human_approval" or _v23_blockers or _v23_warnings:
        raise _V18HTTPException(
            status_code=409,
            detail={
                "message": "Draft creation blocked because the lead is not ready for application drafting.",
                "blocker": "readiness_not_clear",
                "readiness_stage": _v23_stage,
                "blockers": _v23_blockers,
                "warnings": _v23_warnings,
                "next_action": _v23_readiness.get("next_action", "Complete truth and document prerequisites before creating a draft."),
            },
        )
    lead_pk = _uuid_or_404(lead_id, "lead_id")
    lead = session.get(Lead, lead_pk)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    readiness = _calculate_readiness(session, lead)
    app = _create_application_record(session, lead, request, readiness)

    follow_up = None
    if request.create_follow_up and (readiness["blockers"] or readiness["warnings"]):
        follow_up = _create_follow_up(
            session,
            lead,
            f"Application draft created, but action is needed before submission: {readiness['next_action']}",
        )

    return _json_response({
        "status": "created",
        "application": _application_record_to_dict(app),
        "readiness": readiness,
        "follow_up": _to_dict(follow_up) if follow_up else None,
    })


@router.post("/api/v1/applications/{application_id}/approve")
def approve_application(application_id: str, request: ApplicationActionRequest = ApplicationActionRequest(), session: Session = Depends(get_session)):
    app = _get_application(session, application_id)
    lead_pk = _uuid_or_404(getattr(app, "lead_id", None), "lead_id")
    lead = session.get(Lead, lead_pk)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead for application not found")
    readiness = _calculate_readiness(session, lead)
    if not readiness["can_approve"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Application approval blocked by readiness guardrails.",
                "readiness": jsonable_encoder(readiness),
            },
        )
    _set_if_field(app, "status", "approved")
    _set_if_field(app, "stage", "approved")
    _set_if_field(app, "current_stage", "approved")
    if request.note and hasattr(app, "notes"):
        app.notes = request.note
    _set_if_field(app, "updated_at", datetime.utcnow())
    session.add(app)
    session.commit()
    session.refresh(app)
    return _json_response({"status": "approved", "application": _application_record_to_dict(app), "readiness": readiness})


@router.post("/api/v1/applications/{application_id}/submit")
def submit_application(application_id: str, request: ApplicationActionRequest = ApplicationActionRequest(), session: Session = Depends(get_session)):
    app = _get_application(session, application_id)
    lead_pk = _uuid_or_404(getattr(app, "lead_id", None), "lead_id")
    lead = session.get(Lead, lead_pk)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead for application not found")
    readiness = _calculate_readiness(session, lead)
    app_status = _safe_status(getattr(app, "status", None))
    if app_status != "approved":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Application submission requires explicit human approval first.",
                "application_status": app_status,
                "readiness": jsonable_encoder(readiness),
            },
        )
    if not readiness["can_approve"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Application submission blocked by readiness guardrails.",
                "readiness": jsonable_encoder(readiness),
            },
        )
    _set_if_field(app, "status", "submitted")
    _set_if_field(app, "stage", "submitted")
    _set_if_field(app, "current_stage", "submitted")
    if request.note and hasattr(app, "notes"):
        app.notes = request.note
    _set_if_field(app, "updated_at", datetime.utcnow())
    session.add(app)
    session.commit()
    session.refresh(app)
    return _json_response({"status": "submitted", "application": _application_record_to_dict(app), "readiness": readiness})


@router.get("/admin/applications", response_class=HTMLResponse)
def applications_admin(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    items = [_calculate_readiness(session, lead) for lead in leads]
    stage_counts: Dict[str, int] = {}
    for item in items:
        stage_counts[item["stage"]] = stage_counts.get(item["stage"], 0) + 1
    rows = []
    for item in items:
        lead = item["lead"]
        blockers = ", ".join(item["blockers"]) or "-"
        warnings = ", ".join(item["warnings"]) or "-"
        rows.append(
            f"""
            <tr>
              <td><a href='/admin/leads/{lead.get('id')}'>{lead.get('full_name')}</a></td>
              <td>{lead.get('intent') or '-'}</td>
              <td>{lead.get('target_country') or '-'}</td>
              <td>{lead.get('status') or '-'}</td>
              <td><strong>{item['stage']}</strong></td>
              <td>{blockers}</td>
              <td>{warnings}</td>
              <td>{item['next_action']}</td>
              <td>
                <form method='post' action='/admin/applications/leads/{lead.get('id')}/draft'>
                  <button type='submit'>Create Draft</button>
                </form>
              </td>
            </tr>
            """
        )
    html = f"""
    <!doctype html>
    <html>
    <head>
      <title>Application Engine</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
        a {{ color: #2563eb; }}
        .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
        table {{ border-collapse: collapse; width: 100%; background: white; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px; text-align: left; vertical-align: top; }}
        th {{ background: #e2e8f0; }}
        button {{ padding: 8px 10px; border: 1px solid #94a3b8; border-radius: 8px; background: #f1f5f9; cursor: pointer; }}
      </style>
    </head>
    <body>
      <h1>Application Engine</h1>
      <div class='card'>
        <p><a href='/admin'>Back to Dashboard</a> | <a href='/admin/sales'>Sales</a> | <a href='/admin/documents'>Documents</a></p>
        <p><strong>Total leads:</strong> {len(items)}</p>
        <p><strong>Stage counts:</strong> {stage_counts}</p>
      </div>
      <table>
        <thead>
          <tr><th>Lead</th><th>Intent</th><th>Country</th><th>Lead Status</th><th>Application Stage</th><th>Blockers</th><th>Warnings</th><th>Next Action</th><th>Action</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.post("/admin/applications/leads/{lead_id}/draft")
def admin_create_application_draft(lead_id: str, session: Session = Depends(get_session)):
    lead_pk = _uuid_or_404(lead_id, "lead_id")
    lead = session.get(Lead, lead_pk)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    request = ApplicationDraftRequest(application_type=str(_value(getattr(lead, "intent", "visa")) or "visa"))
    create_application_draft(lead_id, request, session)
    return RedirectResponse(url="/admin/applications", status_code=303)


@router.get("/debug/application-engine")
def debug_application_engine():
    return {
        "status": "ok",
        "version": "v1.6",
        "routes": [
            "GET /api/v1/applications/queue",
            "GET /api/v1/applications/leads/{lead_id}/readiness",
            "POST /api/v1/applications/leads/{lead_id}/draft",
            "POST /api/v1/applications/{application_id}/approve",
            "POST /api/v1/applications/{application_id}/submit",
            "GET /admin/applications",
        ],
    }
