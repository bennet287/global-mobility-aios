from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import ApplicationRecord, Lead
from app.routers.application_engine import _application_record_to_dict, _calculate_readiness
from app.services.audit_log import record_audit

router = APIRouter(tags=["application-draft-control"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

ACTIVE_APPLICATION_STATUSES = {
    "draft",
    "approved",
    "submitted",
    "decision_pending",
    "approved_by_authority",
    "rejected_by_authority",
    "withdrawn",
}
DRAFT_STATUSES = {"draft"}
INACTIVE_APPLICATION_STATUSES = {
    "cancelled",
    "canceled",
    "superseded",
    "withdrawn",
    "authority_rejected",
    "rejected_by_authority",
    "authority_approved",
    "approved_by_authority",
}


class ControlledDraftRequest(BaseModel):
    domain: Optional[str] = None
    target_country: Optional[str] = None
    target_institution_or_employer: Optional[str] = None
    note: Optional[str] = None


class CancelDraftRequest(BaseModel):
    reason: Optional[str] = None
    keep_latest_draft_if_no_submitted_application: bool = True


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


def _json_response(payload: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload))


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


def _lead_id(lead: Lead) -> Any:
    return getattr(lead, "id", None)


def _get_lead(session: Session, lead_id: str) -> Lead:
    lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


def _get_application(session: Session, application_id: str) -> ApplicationRecord:
    app = session.get(ApplicationRecord, _uuid_or_404(application_id, "application_id"))
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found")
    return app


def serialize_application(app: ApplicationRecord) -> Dict[str, Any]:
    return _application_record_to_dict(app)


def applications_for_lead(session: Session, lead_id: Any) -> List[ApplicationRecord]:
    target = _normal_id(lead_id)
    apps = session.exec(select(ApplicationRecord)).all()
    return [app for app in apps if _normal_id(getattr(app, "lead_id", None)) == target]


def active_applications_for_lead(session: Session, lead_id: Any) -> List[ApplicationRecord]:
    return [
        app for app in applications_for_lead(session, lead_id)
        if _safe_status(getattr(app, "status", None)) in ACTIVE_APPLICATION_STATUSES
    ]


def draft_applications_for_lead(session: Session, lead_id: Any) -> List[ApplicationRecord]:
    return [
        app for app in applications_for_lead(session, lead_id)
        if _safe_status(getattr(app, "status", None)) in DRAFT_STATUSES
    ]


def _created_at_key(app: ApplicationRecord) -> str:
    return str(getattr(app, "created_at", "") or "")


def _duplicate_groups(session: Session) -> List[Dict[str, Any]]:
    leads = session.exec(select(Lead)).all()
    groups = []
    for lead in leads:
        apps = active_applications_for_lead(session, _lead_id(lead))
        drafts = [app for app in apps if _safe_status(getattr(app, "status", None)) == "draft"]
        submitted_or_approved = [
            app for app in apps
            if _safe_status(getattr(app, "status", None)) in {"approved", "submitted"}
        ]
        has_duplicate_drafts = len(drafts) > 1
        has_draft_with_terminal_active = bool(drafts and submitted_or_approved)
        if has_duplicate_drafts or has_draft_with_terminal_active:
            groups.append({
                "lead": _to_dict(lead),
                "active_application_count": len(apps),
                "draft_count": len(drafts),
                "submitted_or_approved_count": len(submitted_or_approved),
                "issue": (
                    "drafts_exist_after_approved_or_submitted_application"
                    if has_draft_with_terminal_active
                    else "multiple_active_drafts"
                ),
                "applications": [serialize_application(app) for app in sorted(apps, key=_created_at_key)],
            })
    return groups


def _build_application_payload(lead: Lead, request: ControlledDraftRequest) -> Dict[str, Any]:
    fields = _model_fields(ApplicationRecord)
    now = _utcnow()
    domain = request.domain or _safe_status(getattr(lead, "intent", None)) or "general"
    target_country = request.target_country or getattr(lead, "target_country", None)
    payload = {
        "lead_id": _lead_id(lead),
        "domain": domain,
        "target_country": target_country,
        "target_institution_or_employer": request.target_institution_or_employer,
        "status": "draft",
        "risk_score": 0.5,
        "created_at": now,
        "updated_at": now,
    }
    return {key: value for key, value in payload.items() if key in fields and value is not None}


def _draft_control_payload(session: Session, lead: Lead) -> Dict[str, Any]:
    apps = applications_for_lead(session, _lead_id(lead))
    active_apps = [app for app in apps if _safe_status(getattr(app, "status", None)) in ACTIVE_APPLICATION_STATUSES]
    drafts = [app for app in apps if _safe_status(getattr(app, "status", None)) == "draft"]
    submitted = [app for app in apps if _safe_status(getattr(app, "status", None)) == "submitted"]
    readiness = _calculate_readiness(session, lead)

    can_create_draft = len(active_apps) == 0
    blockers = []
    warnings = []

    if active_apps:
        blockers.append("active_application_exists")
    if len(drafts) > 1:
        warnings.append("multiple_active_drafts")
    if drafts and submitted:
        warnings.append("drafts_exist_after_submission")

    return {
        "lead": _to_dict(lead),
        "can_create_draft": can_create_draft,
        "blockers": blockers,
        "warnings": warnings,
        "counts": {
            "applications": len(apps),
            "active_applications": len(active_apps),
            "drafts": len(drafts),
            "submitted": len(submitted),
        },
        "active_applications": [serialize_application(app) for app in sorted(active_apps, key=_created_at_key)],
        "applications": [serialize_application(app) for app in sorted(apps, key=_created_at_key)],
        "readiness": readiness,
        "next_action": (
            "Do not create another draft. Continue with the existing active application or cancel duplicate drafts."
            if active_apps
            else "No active application exists. A controlled draft can be created."
        ),
    }


@router.get("/api/v1/applications/draft-control/duplicates")
def get_duplicate_application_drafts(session: Session = Depends(get_session)):
    groups = _duplicate_groups(session)
    return _json_response({
        "duplicate_group_count": len(groups),
        "groups": groups,
    })


@router.get("/api/v1/applications/leads/{lead_id}/draft-control")
def get_lead_draft_control(lead_id: str, session: Session = Depends(get_session)):
    lead = _get_lead(session, lead_id)
    return _json_response(_draft_control_payload(session, lead))


@router.post("/api/v1/applications/leads/{lead_id}/controlled-draft")
def create_controlled_application_draft(
    lead_id: str,
    request: ControlledDraftRequest = ControlledDraftRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    active_apps = active_applications_for_lead(session, _lead_id(lead))
    if active_apps:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Controlled draft creation blocked because an active application already exists for this lead.",
                "blocker": "active_application_exists",
                "active_applications": [serialize_application(app) for app in active_apps],
                "next_action": "Use the existing application or cancel duplicate drafts first.",
            },
        )

    # Application Draft Control v2.2 readiness guard
    readiness = _calculate_readiness(session, lead)
    readiness_stage = str(readiness.get("stage") or "")
    readiness_blockers = readiness.get("blockers") or []
    readiness_warnings = readiness.get("warnings") or []
    if readiness_stage != "ready_for_human_approval" or readiness_blockers or readiness_warnings:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Controlled draft creation blocked because the lead is not ready for application drafting.",
                "blocker": "readiness_not_clear",
                "readiness_stage": readiness_stage,
                "blockers": readiness_blockers,
                "warnings": readiness_warnings,
                "next_action": readiness.get("next_action", "Complete truth and document prerequisites before creating a draft."),
            },
        )

    payload = _build_application_payload(lead, request)
    app = ApplicationRecord(**payload)
    session.add(app)
    session.commit()
    session.refresh(app)
    record_audit(
        session,
        action="application_drafted",
        entity_type="application",
        entity_id=getattr(app, "id", None),
        before_state=None,
        after_state=serialize_application(app),
        reason=request.note,
        source="application_draft_control",
        commit=True,
    )

    return _json_response({
        "status": "draft_created",
        "application": serialize_application(app),
        "draft_control": _draft_control_payload(session, lead),
    })


@router.post("/api/v1/applications/{application_id}/cancel-draft")
def cancel_application_draft(
    application_id: str,
    request: CancelDraftRequest = CancelDraftRequest(),
    session: Session = Depends(get_session),
):
    app = _get_application(session, application_id)
    current_status = _safe_status(getattr(app, "status", None))
    if current_status != "draft":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Only draft applications can be cancelled by this endpoint.",
                "application": serialize_application(app),
            },
        )

    before = serialize_application(app)
    setattr(app, "status", "cancelled")
    session.add(app)
    session.commit()
    session.refresh(app)
    record_audit(
        session,
        action="application_draft_cancelled",
        entity_type="application",
        entity_id=getattr(app, "id", None),
        before_state=before,
        after_state=serialize_application(app),
        reason=request.reason,
        source="application_draft_control",
        commit=True,
    )

    return _json_response({
        "status": "cancelled",
        "application": serialize_application(app),
        "reason": request.reason,
    })


@router.post("/api/v1/applications/leads/{lead_id}/cancel-duplicate-drafts")
def cancel_duplicate_drafts_for_lead(
    lead_id: str,
    request: CancelDraftRequest = CancelDraftRequest(
        reason="Cancelled duplicate draft applications.",
        keep_latest_draft_if_no_submitted_application=True,
    ),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    apps = applications_for_lead(session, _lead_id(lead))
    drafts = sorted(
        [app for app in apps if _safe_status(getattr(app, "status", None)) == "draft"],
        key=_created_at_key,
    )
    submitted_or_approved = [
        app for app in apps
        if _safe_status(getattr(app, "status", None)) in {"approved", "submitted"}
    ]

    if submitted_or_approved:
        drafts_to_cancel = drafts
    elif request.keep_latest_draft_if_no_submitted_application and len(drafts) > 1:
        drafts_to_cancel = drafts[:-1]
    else:
        drafts_to_cancel = drafts

    before = [serialize_application(app) for app in drafts_to_cancel]
    for app in drafts_to_cancel:
        setattr(app, "status", "cancelled")
        session.add(app)

    session.commit()
    for app in drafts_to_cancel:
        session.refresh(app)

    record_audit(
        session,
        action="duplicate_application_drafts_cancelled",
        entity_type="lead",
        entity_id=_lead_id(lead),
        before_state={"applications": before},
        after_state={"applications": [serialize_application(app) for app in drafts_to_cancel]},
        reason=request.reason,
        source="application_draft_control",
        commit=True,
    )

    return _json_response({
        "status": "completed",
        "cancelled_count": len(drafts_to_cancel),
        "cancelled_applications": [serialize_application(app) for app in drafts_to_cancel],
        "draft_control": _draft_control_payload(session, lead),
    })


@router.get("/admin/application-draft-control", response_class=HTMLResponse)
def application_draft_control_admin(session: Session = Depends(get_session)):
    groups = _duplicate_groups(session)
    rows = []
    for group in groups:
        lead = group["lead"]
        lead_id = lead.get("id")
        rows.append(
            f"""
            <tr>
              <td><a href="/admin/leads/{lead_id}">{lead.get('full_name') or lead_id}</a></td>
              <td>{lead.get('target_country') or '-'}</td>
              <td>{group['issue']}</td>
              <td>{group['draft_count']}</td>
              <td>{group['submitted_or_approved_count']}</td>
              <td>{group['active_application_count']}</td>
              <td>
                <form method="post" action="/admin/application-draft-control/leads/{lead_id}/cancel-duplicate-drafts">
                  <button type="submit">Cancel duplicate drafts</button>
                </form>
              </td>
            </tr>
            """
        )

    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>Application Draft Control</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
          th {{ background: #f4f4f4; }}
          button {{ margin: 2px; }}
        </style>
      </head>
      <body>
        <h1>Application Draft Control v1.8</h1>
        <p><a href="/admin">Back to Admin</a> | <a href="/debug/application-draft-control">Debug</a></p>
        <p>Duplicate groups: {len(groups)}</p>
        <table>
          <thead>
            <tr>
              <th>Lead</th><th>Country</th><th>Issue</th><th>Drafts</th><th>Approved/Submitted</th><th>Active Apps</th><th>Action</th>
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </body>
    </html>
    """
    return HTMLResponse(html)


@router.post("/admin/application-draft-control/leads/{lead_id}/cancel-duplicate-drafts")
def admin_cancel_duplicate_drafts_for_lead(lead_id: str, session: Session = Depends(get_session)):
    cancel_duplicate_drafts_for_lead(
        lead_id,
        CancelDraftRequest(
            reason="Admin cancelled duplicate draft applications.",
            keep_latest_draft_if_no_submitted_application=True,
        ),
        session,
    )
    return HTMLResponse(
        f"<html><body><p>Duplicate drafts cancelled for lead {lead_id}.</p>"
        f"<p><a href='/admin/application-draft-control'>Back</a></p></body></html>"
    )


@router.get("/debug/application-draft-control")
def debug_application_draft_control():
    return {
        "status": "ok",
        "version": "v1.8",
        "active_application_statuses": sorted(ACTIVE_APPLICATION_STATUSES),
        "inactive_application_statuses": sorted(INACTIVE_APPLICATION_STATUSES),
        "routes": [
            "GET /api/v1/applications/draft-control/duplicates",
            "GET /api/v1/applications/leads/{lead_id}/draft-control",
            "POST /api/v1/applications/leads/{lead_id}/controlled-draft",
            "POST /api/v1/applications/{application_id}/cancel-draft",
            "POST /api/v1/applications/leads/{lead_id}/cancel-duplicate-drafts",
            "GET /admin/application-draft-control",
        ],
    }
