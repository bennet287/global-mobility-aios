from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import ApplicationRecord, Lead
from app.routers.application_engine import _application_record_to_dict, _calculate_readiness

router = APIRouter(tags=["application-lifecycle"])


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _safe_status(value: Any) -> str:
    return str(_value(value) or "").strip().lower()


def _uuid_or_404(value: Any, field_name: str = "id") -> uuid.UUID:
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Invalid {field_name}") from exc


def _normal_id(value: Any) -> str:
    value = _value(value)
    if value is None:
        return ""
    try:
        return str(uuid.UUID(str(value))).replace("-", "").lower()
    except Exception:
        return str(value).replace("-", "").lower()


def _json_safe(value: Any) -> Any:
    value = _value(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _model_fields(model: Any) -> set[str]:
    fields = getattr(model, "model_fields", None)
    if fields is None:
        fields = getattr(model, "__fields__", {})
    return set(fields.keys())


def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
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


def _get_application(session: Session, application_id: str) -> ApplicationRecord:
    app = session.get(ApplicationRecord, _uuid_or_404(application_id, "application_id"))
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found")
    return app


def _lead_for_application(session: Session, app: ApplicationRecord) -> Optional[Lead]:
    lead_id = getattr(app, "lead_id", None)
    if not lead_id:
        return None
    try:
        return session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    except HTTPException:
        target = _normal_id(lead_id)
        for lead in session.exec(select(Lead)).all():
            if _normal_id(getattr(lead, "id", None)) == target:
                return lead
    return None


def _lifecycle_stage(app: ApplicationRecord) -> str:
    return _safe_status(getattr(app, "status", None)) or "unknown"


def _next_action(stage: str, readiness: Optional[Dict[str, Any]]) -> str:
    # Authority Decision Tracking v1.9.1 lifecycle patch
    if stage == "draft":
        if readiness and readiness.get("can_approve"):
            return "Human reviewer can approve this application."
        return readiness.get("next_action", "Complete prerequisites before approval.") if readiness else "Complete prerequisites before approval."
    if stage == "approved":
        return "Application has human approval and can be submitted."
    if stage == "submitted":
        return "Application has been submitted. Track authority decision outside readiness checks."
    if stage == "decision_pending":
        return "Waiting for authority decision. Record final outcome when received."
    if stage == "approved_by_authority":
        return "Authority approved the application. Start post-approval onboarding."
    if stage == "rejected_by_authority":
        return "Authority rejected the application. Record reason and prepare appeal/reapplication workflow if appropriate."
    if stage == "withdrawn":
        return "Application was withdrawn. Stop active submission actions and preserve audit history."
    if stage == "cancelled":
        return "Application was cancelled before authority decision tracking."
    return readiness.get("next_action", "Review lifecycle state.") if readiness else "Review lifecycle state."

def _payload(session: Session, app: ApplicationRecord) -> Dict[str, Any]:
    lead = _lead_for_application(session, app)
    readiness = _calculate_readiness(session, lead) if lead else None
    stage = _lifecycle_stage(app)
    return {
        "application": _application_record_to_dict(app),
        "lead": _to_dict(lead) if lead else None,
        "lifecycle": {
            "stage": stage,
            "application_status": stage,
            "readiness_stage": readiness.get("stage") if readiness else None,
            "is_submitted": stage == "submitted",
            "next_action": _next_action(stage, readiness),
        },
        "readiness": readiness,
    }


@router.get("/api/v1/applications/{application_id}/detail")
def get_application_detail(application_id: str, session: Session = Depends(get_session)):
    app = _get_application(session, application_id)
    return _json_response(_payload(session, app))


@router.get("/api/v1/applications/lifecycle-queue")
def get_application_lifecycle_queue(session: Session = Depends(get_session)):
    apps = session.exec(select(ApplicationRecord)).all()
    items = [_payload(session, app) for app in apps]
    stage_counts: Dict[str, int] = {}
    for item in items:
        stage = item["lifecycle"]["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    return _json_response({"total_applications": len(apps), "stage_counts": stage_counts, "items": items})


@router.get("/api/v1/applications/leads/{lead_id}/lifecycle")
def get_lead_lifecycle(lead_id: str, session: Session = Depends(get_session)):
    lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    target = _normal_id(getattr(lead, "id", None))
    apps = [
        app for app in session.exec(select(ApplicationRecord)).all()
        if _normal_id(getattr(app, "lead_id", None)) == target
    ]
    app_items = [_payload(session, app) for app in apps]
    latest = app_items[-1] if app_items else None
    return _json_response({
        "lead": _to_dict(lead),
        "readiness": _calculate_readiness(session, lead),
        "application_count": len(apps),
        "latest_lifecycle_stage": latest["lifecycle"]["stage"] if latest else "no_application",
        "applications": app_items,
    })


@router.get("/admin/application-lifecycle", response_class=HTMLResponse)
def application_lifecycle_admin(session: Session = Depends(get_session)):
    apps = session.exec(select(ApplicationRecord)).all()
    items = [_payload(session, app) for app in apps]
    rows = []
    counts: Dict[str, int] = {}
    for item in items:
        app = item["application"]
        lead = item["lead"] or {}
        lifecycle = item["lifecycle"]
        readiness = item["readiness"] or {}
        stage = lifecycle["stage"]
        counts[stage] = counts.get(stage, 0) + 1
        app_id = app.get("id")
        lead_id = lead.get("id")
        lead_link = f'<a href="/admin/leads/{lead_id}">Lead</a>' if lead_id else "-"
        rows.append(
            f"<tr><td><a href='/api/v1/applications/{app_id}/detail'>{app_id}</a></td>"
            f"<td>{lead.get('full_name') or '-'}</td><td>{app.get('domain') or '-'}</td>"
            f"<td>{stage}</td><td>{readiness.get('stage') or '-'}</td>"
            f"<td>{lifecycle.get('next_action')}</td><td>{lead_link}</td></tr>"
        )
    count_text = " | ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "No applications"
    return HTMLResponse(f"""
    <!doctype html><html><head><title>Application Lifecycle</title>
    <style>body{{font-family:Arial;margin:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px}}th{{background:#f4f4f4}}</style>
    </head><body><h1>Application Lifecycle Engine v1.7</h1>
    <p><a href="/admin">Back to Admin</a> | <a href="/debug/application-lifecycle">Debug</a></p>
    <p><b>Counts:</b> {count_text}</p>
    <table><thead><tr><th>Application</th><th>Lead</th><th>Domain</th><th>Lifecycle</th><th>Readiness</th><th>Next action</th><th>Links</th></tr></thead>
    <tbody>{''.join(rows)}</tbody></table></body></html>
    """)


@router.get("/debug/application-lifecycle")
def debug_application_lifecycle():
    return {
        "status": "ok",
        "version": "v1.7",
        "routes": [
            "GET /api/v1/applications/{application_id}/detail",
            "GET /api/v1/applications/lifecycle-queue",
            "GET /api/v1/applications/leads/{lead_id}/lifecycle",
            "GET /admin/application-lifecycle",
        ],
        "design_note": "Lifecycle stage is derived from ApplicationRecord.status and shown separately from readiness stage.",
    }
