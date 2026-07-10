from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import ApplicationRecord, FollowUp, Lead, LeadStatus
from app.routers.application_engine import _application_record_to_dict, _calculate_readiness
from app.services.audit_log import record_audit


router = APIRouter(tags=["authority-decision-tracking"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

POST_SUBMISSION_STATUSES = {
    "submitted",
    "decision_pending",
    "approved_by_authority",
    "rejected_by_authority",
    "withdrawn",
}
FINAL_AUTHORITY_STATUSES = {
    "approved_by_authority",
    "rejected_by_authority",
    "withdrawn",
}
TRANSITIONS: Dict[str, Set[str]] = {
    "decision_pending": {"submitted"},
    "approved_by_authority": {"submitted", "decision_pending"},
    "rejected_by_authority": {"submitted", "decision_pending"},
    "withdrawn": {"submitted", "decision_pending"},
}


class AuthorityDecisionRequest(BaseModel):
    note: Optional[str] = None
    reference_number: Optional[str] = None
    decision_date: Optional[str] = None
    create_follow_up: bool = True


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


def _applications_for_lead(session: Session, lead: Lead) -> List[ApplicationRecord]:
    target = _normal_id(getattr(lead, "id", None))
    apps = session.exec(select(ApplicationRecord)).all()
    return [app for app in apps if _normal_id(getattr(app, "lead_id", None)) == target]


def _create_follow_up(session: Session, lead: Optional[Lead], message: str) -> Optional[FollowUp]:
    if not lead:
        return None
    fields = _model_fields(FollowUp)
    now = _utcnow()
    payload = {
        "lead_id": getattr(lead, "id", None),
        "channel": "email",
        "message": message,
        "status": "pending",
        "due_at": now,
        "created_at": now,
        "updated_at": now,
    }
    payload = {key: value for key, value in payload.items() if key in fields and value is not None}
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


def _append_lead_note(lead: Optional[Lead], message: str) -> None:
    if not lead:
        return
    existing = str(getattr(lead, "notes", "") or "").strip()
    if message in existing:
        return
    updated = f"{existing}\n\n{message}" if existing else message
    _set_if_field(lead, "notes", updated)
    _set_if_field(lead, "updated_at", _utcnow())


def _update_lead_business_status(lead: Optional[Lead], target_status: str) -> None:
    if not lead:
        return
    if target_status == "approved_by_authority":
        _set_if_field(lead, "status", LeadStatus.converted)
    elif target_status in {"rejected_by_authority", "withdrawn"}:
        _set_if_field(lead, "status", LeadStatus.closed)
    _set_if_field(lead, "updated_at", _utcnow())


def _transition_allowed(current_status: str, target_status: str) -> bool:
    return current_status in TRANSITIONS.get(target_status, set())


def _authority_next_action(stage: str) -> str:
    if stage == "submitted":
        return "Move application to decision_pending or record the authority outcome when received."
    if stage == "decision_pending":
        return "Track the authority decision and record approved_by_authority, rejected_by_authority, or withdrawn."
    if stage == "approved_by_authority":
        return "Authority approved the application. Start post-approval onboarding."
    if stage == "rejected_by_authority":
        return "Authority rejected the application. Record reason and prepare appeal/reapplication workflow if appropriate."
    if stage == "withdrawn":
        return "Application was withdrawn. Stop active submission actions and preserve audit history."
    if stage == "cancelled":
        return "Application was cancelled before authority decision tracking."
    return "Authority tracking is available only after application submission."


def _authority_payload(session: Session, app: ApplicationRecord) -> Dict[str, Any]:
    lead = _lead_for_application(session, app)
    readiness = _calculate_readiness(session, lead) if lead else None
    stage = _safe_status(getattr(app, "status", None))
    return {
        "application": _application_record_to_dict(app),
        "lead": _to_dict(lead) if lead else None,
        "authority_tracking": {
            "stage": stage,
            "is_post_submission": stage in POST_SUBMISSION_STATUSES,
            "is_final": stage in FINAL_AUTHORITY_STATUSES,
            "allowed_next_statuses": [
                target for target, sources in TRANSITIONS.items()
                if stage in sources
            ],
            "next_action": _authority_next_action(stage),
        },
        "readiness": readiness,
    }


def _set_authority_status(
    session: Session,
    app: ApplicationRecord,
    target_status: str,
    request: AuthorityDecisionRequest,
) -> Dict[str, Any]:
    current_status = _safe_status(getattr(app, "status", None))
    if not _transition_allowed(current_status, target_status):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Authority decision transition blocked.",
                "current_status": current_status,
                "requested_status": target_status,
                "allowed_sources": sorted(TRANSITIONS.get(target_status, set())),
                "next_action": _authority_next_action(current_status),
            },
        )

    lead = _lead_for_application(session, app)
    before = _authority_payload(session, app)

    setattr(app, "status", target_status)

    note_parts = [
        "[authority_decision:v1.9]",
        f"application={_json_safe(getattr(app, 'id', None))}",
        f"status={target_status}",
        f"at={_utcnow().isoformat()}",
    ]
    if request.reference_number:
        note_parts.append(f"reference={request.reference_number}")
    if request.decision_date:
        note_parts.append(f"decision_date={request.decision_date}")
    if request.note:
        note_parts.append(f"note={request.note}")
    _append_lead_note(lead, " ".join(note_parts))
    _update_lead_business_status(lead, target_status)

    try:
        session.add(app)
        if lead:
            session.add(lead)
        session.commit()
        session.refresh(app)
        if lead:
            session.refresh(lead)
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Could not update authority decision status.",
                "error": str(exc),
                "target_status": target_status,
            },
        ) from exc

    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(
            session,
            lead,
            f"Authority decision update: application {getattr(app, 'id', None)} is now {target_status}.",
        )

    after = _authority_payload(session, app)
    record_audit(
        session,
        action="authority_decision_recorded",
        entity_type="application",
        entity_id=getattr(app, "id", None),
        before_state=before,
        after_state=after,
        reason=request.note or target_status,
        source="authority_decision",
        commit=True,
    )

    return {
        "status": target_status,
        "before": before,
        "after": after,
        "follow_up": _to_dict(follow_up) if follow_up else None,
    }


@router.get("/api/v1/authority-decision/applications/{application_id}")
def get_authority_decision_detail(application_id: str, session: Session = Depends(get_session)):
    app = _get_application(session, application_id)
    return _json_response(_authority_payload(session, app))


@router.get("/api/v1/authority-decision/queue")
def get_authority_decision_queue(session: Session = Depends(get_session)):
    apps = session.exec(select(ApplicationRecord)).all()
    items = [
        _authority_payload(session, app)
        for app in apps
        if _safe_status(getattr(app, "status", None)) in POST_SUBMISSION_STATUSES
    ]
    stage_counts: Dict[str, int] = {}
    for item in items:
        stage = item["authority_tracking"]["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    return _json_response({
        "total_tracked_applications": len(items),
        "stage_counts": stage_counts,
        "items": items,
    })


@router.get("/api/v1/authority-decision/leads/{lead_id}")
def get_lead_authority_decisions(lead_id: str, session: Session = Depends(get_session)):
    lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    apps = _applications_for_lead(session, lead)
    return _json_response({
        "lead": _to_dict(lead),
        "applications": [_authority_payload(session, app) for app in apps],
    })


@router.post("/api/v1/authority-decision/applications/{application_id}/decision-pending")
def mark_decision_pending(
    application_id: str,
    request: AuthorityDecisionRequest = AuthorityDecisionRequest(
        note="Application is now waiting for authority decision."
    ),
    session: Session = Depends(get_session),
):
    app = _get_application(session, application_id)
    return _json_response(_set_authority_status(session, app, "decision_pending", request))


@router.post("/api/v1/authority-decision/applications/{application_id}/approve")
def mark_approved_by_authority(
    application_id: str,
    request: AuthorityDecisionRequest = AuthorityDecisionRequest(),
    session: Session = Depends(get_session),
):
    app = _get_application(session, application_id)
    return _json_response(_set_authority_status(session, app, "approved_by_authority", request))


@router.post("/api/v1/authority-decision/applications/{application_id}/reject")
def mark_rejected_by_authority(
    application_id: str,
    request: AuthorityDecisionRequest = AuthorityDecisionRequest(),
    session: Session = Depends(get_session),
):
    app = _get_application(session, application_id)
    return _json_response(_set_authority_status(session, app, "rejected_by_authority", request))


@router.post("/api/v1/authority-decision/applications/{application_id}/withdraw")
def mark_withdrawn(
    application_id: str,
    request: AuthorityDecisionRequest = AuthorityDecisionRequest(),
    session: Session = Depends(get_session),
):
    app = _get_application(session, application_id)
    return _json_response(_set_authority_status(session, app, "withdrawn", request))


@router.get("/admin/authority-decision", response_class=HTMLResponse)
def authority_decision_admin(session: Session = Depends(get_session)):
    apps = session.exec(select(ApplicationRecord)).all()
    items = [
        _authority_payload(session, app)
        for app in apps
        if _safe_status(getattr(app, "status", None)) in POST_SUBMISSION_STATUSES
    ]

    rows = []
    for item in items:
        app = item["application"]
        lead = item["lead"] or {}
        tracking = item["authority_tracking"]
        app_id = app.get("id")
        lead_id = lead.get("id")
        rows.append(
            f"""
            <tr>
              <td>{app_id}</td>
              <td>{lead.get('full_name') or '-'}</td>
              <td>{app.get('target_country') or lead.get('target_country') or '-'}</td>
              <td>{tracking.get('stage')}</td>
              <td>{tracking.get('next_action')}</td>
              <td>
                <form method="post" action="/admin/authority-decision/applications/{app_id}/decision-pending" style="display:inline">
                  <button type="submit">Decision Pending</button>
                </form>
                <form method="post" action="/admin/authority-decision/applications/{app_id}/approve" style="display:inline">
                  <button type="submit">Approve</button>
                </form>
                <form method="post" action="/admin/authority-decision/applications/{app_id}/reject" style="display:inline">
                  <button type="submit">Reject</button>
                </form>
                <form method="post" action="/admin/authority-decision/applications/{app_id}/withdraw" style="display:inline">
                  <button type="submit">Withdraw</button>
                </form>
                {'<a href="/admin/leads/' + lead_id + '">Lead</a>' if lead_id else ''}
              </td>
            </tr>
            """
        )

    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>Authority Decision Tracking</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
          th {{ background: #f4f4f4; }}
          button {{ margin: 2px; }}
        </style>
      </head>
      <body>
        <h1>Authority Decision Tracking v1.9</h1>
        <p><a href="/admin">Back to Admin</a> | <a href="/debug/authority-decision">Debug</a></p>
        <table>
          <thead>
            <tr>
              <th>Application</th><th>Lead</th><th>Country</th><th>Authority Stage</th><th>Next Action</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </body>
    </html>
    """
    return HTMLResponse(html)


def _admin_transition(application_id: str, target_status: str, session: Session):
    app = _get_application(session, application_id)
    request = AuthorityDecisionRequest(
        note=f"Admin marked authority decision stage as {target_status}.",
        create_follow_up=True,
    )
    try:
        _set_authority_status(session, app, target_status, request)
        return HTMLResponse(
            f"<html><body><p>Application {application_id} moved to {target_status}.</p>"
            f"<p><a href='/admin/authority-decision'>Back</a></p></body></html>"
        )
    except HTTPException as exc:
        return HTMLResponse(
            f"<html><body><p>Transition blocked: {exc.detail}</p>"
            f"<p><a href='/admin/authority-decision'>Back</a></p></body></html>",
            status_code=exc.status_code,
        )


@router.post("/admin/authority-decision/applications/{application_id}/decision-pending")
def admin_decision_pending(application_id: str, session: Session = Depends(get_session)):
    return _admin_transition(application_id, "decision_pending", session)


@router.post("/admin/authority-decision/applications/{application_id}/approve")
def admin_approve(application_id: str, session: Session = Depends(get_session)):
    return _admin_transition(application_id, "approved_by_authority", session)


@router.post("/admin/authority-decision/applications/{application_id}/reject")
def admin_reject(application_id: str, session: Session = Depends(get_session)):
    return _admin_transition(application_id, "rejected_by_authority", session)


@router.post("/admin/authority-decision/applications/{application_id}/withdraw")
def admin_withdraw(application_id: str, session: Session = Depends(get_session)):
    return _admin_transition(application_id, "withdrawn", session)


@router.get("/debug/authority-decision")
def debug_authority_decision():
    return {
        "status": "ok",
        "version": "v1.9",
        "post_submission_statuses": sorted(POST_SUBMISSION_STATUSES),
        "final_authority_statuses": sorted(FINAL_AUTHORITY_STATUSES),
        "transitions": {target: sorted(sources) for target, sources in TRANSITIONS.items()},
        "routes": [
            "GET /api/v1/authority-decision/applications/{application_id}",
            "GET /api/v1/authority-decision/queue",
            "GET /api/v1/authority-decision/leads/{lead_id}",
            "POST /api/v1/authority-decision/applications/{application_id}/decision-pending",
            "POST /api/v1/authority-decision/applications/{application_id}/approve",
            "POST /api/v1/authority-decision/applications/{application_id}/reject",
            "POST /api/v1/authority-decision/applications/{application_id}/withdraw",
            "GET /admin/authority-decision",
        ],
    }
