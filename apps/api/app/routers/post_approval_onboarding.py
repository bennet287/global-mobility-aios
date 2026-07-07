from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import ApplicationRecord, FollowUp, Lead


router = APIRouter(tags=["post-approval-onboarding"])

APPROVED_AUTHORITY_STATUS = "approved_by_authority"
ONBOARDING_PREFIX = "[post_approval_onboarding:v2.4]"

DEFAULT_ONBOARDING_TASKS = [
    {
        "task_key": "confirm_authority_approval",
        "title": "Confirm authority approval details",
        "message": "Confirm the authority approval reference, decision date, validity, and next official steps with the client.",
        "offset_days": 0,
    },
    {
        "task_key": "send_client_next_steps",
        "title": "Send client post-approval next steps",
        "message": "Send the client a clear post-approval checklist covering travel, accommodation, insurance, enrolment/work start, and local registration.",
        "offset_days": 0,
    },
    {
        "task_key": "collect_travel_plan",
        "title": "Collect travel plan",
        "message": "Collect intended travel date, arrival city, flight booking status, and emergency contact information.",
        "offset_days": 2,
    },
    {
        "task_key": "verify_accommodation_arrival",
        "title": "Verify accommodation and arrival plan",
        "message": "Verify accommodation proof, airport/train arrival plan, and first-week support requirements.",
        "offset_days": 3,
    },
    {
        "task_key": "confirm_insurance_and_documents",
        "title": "Confirm insurance and travel documents",
        "message": "Confirm passport, visa/approval letter, insurance, admission/job documents, financial proof copies, and emergency copies are ready.",
        "offset_days": 4,
    },
    {
        "task_key": "local_registration_guidance",
        "title": "Prepare local registration guidance",
        "message": "Prepare guidance for city registration, residence permit follow-up, university enrolment or employer onboarding, and bank/SIM setup.",
        "offset_days": 7,
    },
]


class GenerateOnboardingRequest(BaseModel):
    note: Optional[str] = None
    create_follow_ups: bool = True
    reset_existing: bool = False


class CompleteOnboardingTaskRequest(BaseModel):
    note: Optional[str] = None


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
    return set(getattr(model, "model_fields", getattr(model, "__fields__", {})).keys())


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


def _approved_applications_for_lead(session: Session, lead: Lead) -> List[ApplicationRecord]:
    return [
        app for app in _applications_for_lead(session, lead)
        if _safe_status(getattr(app, "status", None)) == APPROVED_AUTHORITY_STATUS
    ]


def _followups_for_lead(session: Session, lead: Lead) -> List[FollowUp]:
    target = _normal_id(getattr(lead, "id", None))
    rows = session.exec(select(FollowUp)).all()
    return [row for row in rows if _normal_id(getattr(row, "lead_id", None)) == target]


def _onboarding_followups_for_lead(session: Session, lead: Lead) -> List[FollowUp]:
    return [
        follow_up for follow_up in _followups_for_lead(session, lead)
        if ONBOARDING_PREFIX in str(getattr(follow_up, "message", "") or "")
    ]


def _task_key_in_followup(follow_up: FollowUp, task_key: str) -> bool:
    message = str(getattr(follow_up, "message", "") or "")
    return f"task={task_key}" in message


def _append_lead_note(lead: Lead, message: str) -> None:
    existing = str(getattr(lead, "notes", "") or "").strip()
    if message in existing:
        return
    updated = f"{existing}\n\n{message}" if existing else message
    _set_if_field(lead, "notes", updated)
    _set_if_field(lead, "updated_at", datetime.utcnow())


def _build_followup_payload(lead: Lead, task: Dict[str, Any], request: GenerateOnboardingRequest) -> Dict[str, Any]:
    fields = _model_fields(FollowUp)
    now = datetime.utcnow()
    due_at = now + timedelta(days=int(task.get("offset_days", 0)))
    message = (
        f"{ONBOARDING_PREFIX} task={task['task_key']} title={task['title']} "
        f"message={task['message']}"
    )
    if request.note:
        message = f"{message} note={request.note}"

    payload = {
        "lead_id": getattr(lead, "id", None),
        "channel": "email",
        "status": "pending",
        "due_at": due_at,
        "message": message,
        "created_at": now,
        "updated_at": now,
    }
    return {key: value for key, value in payload.items() if key in fields and value is not None}


def _onboarding_summary(session: Session, lead: Lead) -> Dict[str, Any]:
    apps = _approved_applications_for_lead(session, lead)
    tasks = _onboarding_followups_for_lead(session, lead)
    pending = [task for task in tasks if _safe_status(getattr(task, "status", None)) == "pending"]
    completed = [task for task in tasks if _safe_status(getattr(task, "status", None)) == "completed"]

    generated_keys = []
    for task in DEFAULT_ONBOARDING_TASKS:
        if any(_task_key_in_followup(fu, task["task_key"]) for fu in tasks):
            generated_keys.append(task["task_key"])

    missing_keys = [
        task["task_key"]
        for task in DEFAULT_ONBOARDING_TASKS
        if task["task_key"] not in generated_keys
    ]

    if not apps:
        stage = "not_authority_approved"
        next_action = "Authority approval is required before post-approval onboarding."
    elif missing_keys:
        stage = "onboarding_not_generated"
        next_action = "Generate post-approval onboarding tasks."
    elif pending:
        stage = "onboarding_in_progress"
        next_action = "Complete pending onboarding tasks."
    else:
        stage = "onboarding_complete"
        next_action = "All onboarding tasks are complete."

    return {
        "stage": stage,
        "approved_applications": len(apps),
        "task_count": len(tasks),
        "pending_tasks": len(pending),
        "completed_tasks": len(completed),
        "generated_task_keys": generated_keys,
        "missing_task_keys": missing_keys,
        "next_action": next_action,
    }


def _lead_payload(session: Session, lead: Lead) -> Dict[str, Any]:
    return {
        "lead": _to_dict(lead),
        "approved_applications": [_to_dict(app) for app in _approved_applications_for_lead(session, lead)],
        "summary": _onboarding_summary(session, lead),
        "onboarding_tasks": [_to_dict(task) for task in _onboarding_followups_for_lead(session, lead)],
    }


@router.get("/api/v1/post-approval-onboarding/queue")
def get_post_approval_onboarding_queue(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    items = []
    for lead in leads:
        payload = _lead_payload(session, lead)
        if payload["summary"]["approved_applications"] > 0 or payload["summary"]["task_count"] > 0:
            items.append(payload)

    stage_counts: Dict[str, int] = {}
    for item in items:
        stage = item["summary"]["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    return _json_response({
        "total_items": len(items),
        "stage_counts": stage_counts,
        "items": items,
    })


@router.get("/api/v1/post-approval-onboarding/leads/{lead_id}")
def get_lead_post_approval_onboarding(lead_id: str, session: Session = Depends(get_session)):
    lead = _get_lead(session, lead_id)
    return _json_response(_lead_payload(session, lead))


@router.post("/api/v1/post-approval-onboarding/leads/{lead_id}/generate")
def generate_post_approval_onboarding(
    lead_id: str,
    request: GenerateOnboardingRequest = GenerateOnboardingRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    approved_apps = _approved_applications_for_lead(session, lead)
    if not approved_apps:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Post-approval onboarding requires an approved-by-authority application.",
                "blocker": "not_authority_approved",
                "next_action": "Complete authority decision tracking before onboarding.",
            },
        )

    existing = _onboarding_followups_for_lead(session, lead)

    if request.reset_existing:
        for follow_up in existing:
            _set_if_field(follow_up, "status", "cancelled")
            _set_if_field(follow_up, "updated_at", datetime.utcnow())
            session.add(follow_up)
        session.commit()
        existing = []

    created = []
    skipped = []
    if request.create_follow_ups:
        for task in DEFAULT_ONBOARDING_TASKS:
            if any(_task_key_in_followup(fu, task["task_key"]) for fu in existing):
                skipped.append(task["task_key"])
                continue
            follow_up = FollowUp(**_build_followup_payload(lead, task, request))
            session.add(follow_up)
            created.append(follow_up)

        session.commit()
        for follow_up in created:
            session.refresh(follow_up)

    note = (
        f"{ONBOARDING_PREFIX} generated={len(created)} skipped={len(skipped)} "
        f"at={datetime.utcnow().isoformat()}"
    )
    if request.note:
        note = f"{note} note={request.note}"
    _append_lead_note(lead, note)
    session.add(lead)
    session.commit()
    session.refresh(lead)

    return _json_response({
        "status": "generated",
        "created_count": len(created),
        "skipped_existing_count": len(skipped),
        "created_tasks": [_to_dict(task) for task in created],
        "skipped_task_keys": skipped,
        "onboarding": _lead_payload(session, lead),
    })


@router.post("/api/v1/post-approval-onboarding/follow-ups/{follow_up_id}/complete")
def complete_onboarding_follow_up(
    follow_up_id: str,
    request: CompleteOnboardingTaskRequest = CompleteOnboardingTaskRequest(),
    session: Session = Depends(get_session),
):
    follow_up = session.get(FollowUp, _uuid_or_404(follow_up_id, "follow_up_id"))
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    if ONBOARDING_PREFIX not in str(getattr(follow_up, "message", "") or ""):
        raise HTTPException(
            status_code=409,
            detail="This follow-up is not a post-approval onboarding task.",
        )

    _set_if_field(follow_up, "status", "completed")
    _set_if_field(follow_up, "updated_at", datetime.utcnow())

    lead = None
    lead_id = getattr(follow_up, "lead_id", None)
    if lead_id:
        try:
            lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
        except HTTPException:
            lead = None
    if lead and request.note:
        _append_lead_note(lead, f"{ONBOARDING_PREFIX} completed_follow_up={follow_up_id} note={request.note}")
        session.add(lead)

    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    if lead:
        session.refresh(lead)

    return _json_response({
        "status": "completed",
        "follow_up": _to_dict(follow_up),
        "onboarding": _lead_payload(session, lead) if lead else None,
    })


@router.get("/admin/post-approval-onboarding", response_class=HTMLResponse)
def post_approval_onboarding_admin(session: Session = Depends(get_session)):
    queue = get_post_approval_onboarding_queue(session).body
    # Avoid importing json just for this; rebuild directly for HTML.
    leads = session.exec(select(Lead)).all()
    rows = []
    for lead in leads:
        payload = _lead_payload(session, lead)
        summary = payload["summary"]
        if summary["approved_applications"] == 0 and summary["task_count"] == 0:
            continue
        lead_data = payload["lead"]
        lead_id = lead_data.get("id")
        rows.append(
            f"""
            <tr>
              <td><a href="/admin/v2/leads/{lead_id}">{lead_data.get('full_name') or lead_id}</a></td>
              <td>{lead_data.get('target_country') or '-'}</td>
              <td>{summary['stage']}</td>
              <td>{summary['pending_tasks']}</td>
              <td>{summary['completed_tasks']}</td>
              <td>{summary['next_action']}</td>
              <td>
                <form method="post" action="/admin/post-approval-onboarding/leads/{lead_id}/generate" style="display:inline">
                  <button type="submit">Generate Tasks</button>
                </form>
                <a href="/api/v1/post-approval-onboarding/leads/{lead_id}">JSON</a>
              </td>
            </tr>
            """
        )

    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>Post-Approval Onboarding</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
          th {{ background: #f4f4f4; }}
          button {{ margin: 2px; }}
        </style>
      </head>
      <body>
        <h1>Post-Approval Onboarding v2.4</h1>
        <p><a href="/admin/v2">Admin v2</a> | <a href="/debug/post-approval-onboarding">Debug</a></p>
        <table>
          <thead>
            <tr><th>Lead</th><th>Country</th><th>Stage</th><th>Pending</th><th>Completed</th><th>Next Action</th><th>Actions</th></tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </body>
    </html>
    """
    return HTMLResponse(html)


@router.post("/admin/post-approval-onboarding/leads/{lead_id}/generate")
def admin_generate_post_approval_onboarding(lead_id: str, session: Session = Depends(get_session)):
    generate_post_approval_onboarding(
        lead_id,
        GenerateOnboardingRequest(note="Generated from admin post-approval onboarding page."),
        session,
    )
    return RedirectResponse(url="/admin/post-approval-onboarding", status_code=303)


@router.get("/debug/post-approval-onboarding")
def debug_post_approval_onboarding():
    return {
        "status": "ok",
        "version": "v2.4",
        "onboarding_prefix": ONBOARDING_PREFIX,
        "task_keys": [task["task_key"] for task in DEFAULT_ONBOARDING_TASKS],
        "routes": [
            "GET /api/v1/post-approval-onboarding/queue",
            "GET /api/v1/post-approval-onboarding/leads/{lead_id}",
            "POST /api/v1/post-approval-onboarding/leads/{lead_id}/generate",
            "POST /api/v1/post-approval-onboarding/follow-ups/{follow_up_id}/complete",
            "GET /admin/post-approval-onboarding",
        ],
    }
