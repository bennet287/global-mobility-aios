from __future__ import annotations

import uuid
from datetime import datetime
from html import escape
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import ApplicationRecord, FollowUp, Lead


router = APIRouter(tags=["client-communication-review"])

DRAFT_PREFIX = "[client_communication_draft:v2.6]"
MODULE_VERSION = "v2.7"
APPROVED_AUTHORITY_STATUS = "approved_by_authority"

TEMPLATES: Dict[str, Dict[str, str]] = {
    "approval_confirmation": {
        "subject": "Your application has been approved - next steps",
        "title": "Approval confirmation",
        "body": """Dear {client_name},

Congratulations - your application for {target_country} has been approved by the responsible authority.

Please note that this message is only an agency support update. You should always follow the official approval letter and instructions from the responsible authority.

Next steps:
1. Review the approval letter carefully.
2. Check the validity dates, reference number, and any conditions.
3. Keep copies of your passport, approval letter, insurance, admission/job documents, and financial documents.
4. Share your intended travel date with us so we can support your arrival planning.

Kind regards,
Global Mobility Support Team""",
    },
    "post_approval_next_steps": {
        "subject": "Post-approval next steps checklist",
        "title": "Post-approval next steps",
        "body": """Dear {client_name},

Now that your application for {target_country} has been approved, please use the checklist below to prepare safely.

Post-approval checklist:
1. Confirm travel date and arrival city.
2. Confirm accommodation for your first weeks.
3. Confirm health/travel insurance coverage.
4. Prepare printed and digital copies of all important documents.
5. Review university enrolment, employer onboarding, or appointment requirements.
6. Check local registration or residence follow-up requirements after arrival.

This is a support checklist only and does not replace official authority instructions.

Kind regards,
Global Mobility Support Team""",
    },
    "travel_checklist": {
        "subject": "Travel preparation checklist",
        "title": "Travel checklist",
        "body": """Dear {client_name},

Please share the following travel details once available:

1. Intended travel date.
2. Arrival airport or station.
3. Flight/train booking status.
4. Accommodation address after arrival.
5. Emergency contact details.
6. Any airport pickup or first-week support needs.

Before travelling, please carry your passport, approval/visa document, insurance proof, admission/job documents, accommodation proof, and emergency copies.

Kind regards,
Global Mobility Support Team""",
    },
    "document_checklist": {
        "subject": "Documents to carry after approval",
        "title": "Post-approval document checklist",
        "body": """Dear {client_name},

Please keep the following documents ready before travelling to {target_country}:

1. Passport.
2. Authority approval / visa document.
3. Admission letter or job/employment document, if applicable.
4. Insurance proof.
5. Accommodation proof.
6. Financial proof copies, if applicable.
7. Passport-size photographs.
8. Emergency contact details.
9. Printed and digital copies of all important documents.

Please verify all official document requirements against the responsible authority's instructions.

Kind regards,
Global Mobility Support Team""",
    },
    "local_registration_guidance": {
        "subject": "Arrival and local registration guidance",
        "title": "Local registration guidance",
        "body": """Dear {client_name},

After arriving in {target_country}, you may need to complete local steps such as city registration, residence permit follow-up, university enrolment, employer onboarding, bank account setup, SIM card setup, or insurance activation.

Please check the official instructions from your city, university, employer, and the responsible authority. We can help you organise the next steps, but official requirements must be followed directly.

Kind regards,
Global Mobility Support Team""",
    },
}


class DraftRequest(BaseModel):
    note: Optional[str] = None
    subject_override: Optional[str] = None
    body_override: Optional[str] = None


class GenerateDraftPackRequest(BaseModel):
    note: Optional[str] = None
    template_keys: Optional[List[str]] = None
    skip_existing: bool = True


class UpdateDraftRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    note: Optional[str] = None


class MarkAllReviewedRequest(BaseModel):
    note: Optional[str] = None


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _safe_status(value: Any) -> str:
    return str(_value(value) or "").strip().lower()


def _clean_text(value: Any) -> str:
    text = str(_value(value) or "")
    replacements = {
        "\u00e2\u20ac\u201d": "-",
        "\u00e2\u20ac\u201c": "-",
        "\u2014": "-",
        "\u2013": "-",
        "\u00e2\u20ac\u02dc": "'",
        "\u00e2\u20ac\u2122": "'",
        "\u00e2\u20ac\u0153": '"',
        "\u00e2\u20ac\ufffd": '"',
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _html(value: Any) -> str:
    return escape(str(_value(value) or ""), quote=True)


def _review_note(note: Optional[str] = None) -> str:
    if note:
        return _clean_text(note)
    return f"Reviewed by human operator at {datetime.utcnow().isoformat()}Z."


def _communication_status(value: Any) -> str:
    status = _safe_status(value)
    if status == "pending":
        return "draft"
    if status == "completed":
        return "reviewed"
    return status


def _storage_status_for_communication_filter(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    status = _safe_status(value)
    if status == "draft":
        return "pending"
    if status == "reviewed":
        return "completed"
    return status


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


def _get_follow_up(session: Session, follow_up_id: str) -> FollowUp:
    follow_up = session.get(FollowUp, _uuid_or_404(follow_up_id, "follow_up_id"))
    if not follow_up:
        raise HTTPException(status_code=404, detail="Communication draft not found")
    return follow_up


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


def _draft_followups_for_lead(session: Session, lead: Lead) -> List[FollowUp]:
    return [
        follow_up for follow_up in _followups_for_lead(session, lead)
        if DRAFT_PREFIX in str(getattr(follow_up, "message", "") or "")
    ]


def _all_draft_followups(session: Session) -> List[FollowUp]:
    return [
        follow_up for follow_up in session.exec(select(FollowUp)).all()
        if DRAFT_PREFIX in str(getattr(follow_up, "message", "") or "")
    ]


def _extract_between(message: str, start: str, end: Optional[str] = None) -> Optional[str]:
    try:
        start_index = message.index(start) + len(start)
        if end and end in message[start_index:]:
            end_index = message.index(end, start_index)
            return message[start_index:end_index].strip()
        return message[start_index:].strip()
    except ValueError:
        return None


def _template_key_in_draft(follow_up: FollowUp, template_key: str) -> bool:
    message = str(getattr(follow_up, "message", "") or "")
    return f"template={template_key}" in message


def _lead_for_draft(session: Session, draft: FollowUp) -> Optional[Lead]:
    lead_id = getattr(draft, "lead_id", None)
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


def _render_template(lead: Lead, template_key: str, request: Optional[DraftRequest] = None) -> Dict[str, str]:
    if template_key not in TEMPLATES:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Unknown communication template.",
                "template_key": template_key,
                "available_templates": sorted(TEMPLATES.keys()),
            },
        )

    template = TEMPLATES[template_key]
    context = {
        "client_name": getattr(lead, "full_name", None) or "Client",
        "target_country": getattr(lead, "target_country", None) or "your destination country",
    }
    subject = _clean_text(template["subject"].format(**context))
    body = _clean_text(template["body"].format(**context))

    if request:
        subject = _clean_text(request.subject_override) if request.subject_override else subject
        body = _clean_text(request.body_override) if request.body_override else body

    return {
        "template_key": template_key,
        "title": template["title"],
        "subject": subject,
        "body": body,
    }


def _draft_message(template_data: Dict[str, str], note: Optional[str] = None) -> str:
    template_key = _clean_text(template_data["template_key"])
    title = _clean_text(template_data["title"])
    subject = _clean_text(template_data["subject"])
    body = _clean_text(template_data["body"])
    message = (
        f"{DRAFT_PREFIX} template={template_key} "
        f"title={title} subject={subject} "
        f"body={body}"
    )
    if note:
        message = f"{message} note={_clean_text(note)}"
    return message


def _parse_draft(follow_up: FollowUp) -> Dict[str, Any]:
    message = str(getattr(follow_up, "message", "") or "")
    template_key = _extract_between(message, "template=", " title=") or "unknown_template"
    title = _extract_between(message, "title=", " subject=") or TEMPLATES.get(template_key, {}).get("title", "Client communication")
    subject = _extract_between(message, "subject=", " body=") or TEMPLATES.get(template_key, {}).get("subject", "Client update")
    body = _extract_between(message, "body=", " note=")
    if body is None:
        body = _extract_between(message, "body=") or ""
    note = _extract_between(message, " note=")
    return {
        "template_key": _clean_text(template_key),
        "title": _clean_text(title),
        "subject": _clean_text(subject),
        "body": _clean_text(body),
        "note": _clean_text(note) if note else None,
        "status": _communication_status(getattr(follow_up, "status", None)),
        "channel": getattr(follow_up, "channel", None),
        "created_at": _json_safe(getattr(follow_up, "created_at", None)),
        "updated_at": _json_safe(getattr(follow_up, "updated_at", None)),
    }


def _draft_payload(session: Session, draft: FollowUp) -> Dict[str, Any]:
    lead = _lead_for_draft(session, draft)
    return {
        "draft": _to_dict(draft),
        "communication": _parse_draft(draft),
        "lead": _to_dict(lead) if lead else None,
    }


def _lead_payload(session: Session, lead: Lead) -> Dict[str, Any]:
    approved_apps = _approved_applications_for_lead(session, lead)
    drafts = _draft_followups_for_lead(session, lead)
    status_counts: Dict[str, int] = {}
    for draft in drafts:
        status = _communication_status(getattr(draft, "status", None))
        status_counts[status] = status_counts.get(status, 0) + 1

    existing_templates = []
    for key in TEMPLATES:
        if any(_template_key_in_draft(draft, key) for draft in drafts):
            existing_templates.append(key)

    missing_templates = [key for key in TEMPLATES if key not in existing_templates]

    if not approved_apps:
        stage = "not_authority_approved"
        next_action = "Authority approval is required before client communication drafts."
    elif missing_templates:
        stage = "drafts_missing"
        next_action = "Generate missing client communication drafts."
    elif status_counts.get("draft", 0) > 0:
        stage = "drafts_ready_for_review"
        next_action = "Review client communication drafts before sending manually."
    else:
        stage = "drafts_reviewed"
        next_action = "Drafts have been reviewed. Send manually outside the system if appropriate."

    return {
        "lead": _to_dict(lead),
        "approved_applications": [_to_dict(app) for app in approved_apps],
        "summary": {
            "stage": stage,
            "draft_count": len(drafts),
            "status_counts": status_counts,
            "existing_templates": existing_templates,
            "missing_templates": missing_templates,
            "next_action": next_action,
        },
        "drafts": [_draft_payload(session, draft) for draft in drafts],
    }


def _create_draft(
    session: Session,
    lead: Lead,
    template_key: str,
    request: DraftRequest,
) -> FollowUp:
    approved_apps = _approved_applications_for_lead(session, lead)
    if not approved_apps:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Client communication drafting requires an approved-by-authority application.",
                "blocker": "not_authority_approved",
                "next_action": "Complete authority decision tracking before drafting client communication.",
            },
        )

    template_data = _render_template(lead, template_key, request)
    now = datetime.utcnow()
    fields = _model_fields(FollowUp)
    payload = {
        "lead_id": getattr(lead, "id", None),
        "channel": "email_draft",
        "message": _draft_message(template_data, request.note),
        "status": "pending",
        "due_at": now,
        "created_at": now,
        "updated_at": now,
    }
    payload = {key: value for key, value in payload.items() if key in fields and value is not None}

    draft = FollowUp(**payload)
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft


def _ensure_client_communication_draft(draft: FollowUp) -> None:
    if DRAFT_PREFIX not in str(getattr(draft, "message", "") or ""):
        raise HTTPException(status_code=404, detail="Client communication draft not found")


def _update_draft_content(draft: FollowUp, request: UpdateDraftRequest) -> FollowUp:
    _ensure_client_communication_draft(draft)
    if _communication_status(getattr(draft, "status", None)) != "draft":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Reviewed drafts cannot be edited without a future reopen workflow.",
                "blocker": "draft_already_reviewed",
                "next_action": "Create a replacement draft if the reviewed message must change.",
            },
        )

    parsed = _parse_draft(draft)
    template_data = {
        "template_key": parsed["template_key"],
        "title": parsed["title"],
        "subject": request.subject if request.subject is not None else parsed["subject"],
        "body": request.body if request.body is not None else parsed["body"],
    }
    note = request.note if request.note is not None else parsed.get("note")
    _set_if_field(draft, "message", _draft_message(template_data, note))
    _set_if_field(draft, "updated_at", datetime.utcnow())
    return draft


def _mark_draft_reviewed(draft: FollowUp, request: Optional[UpdateDraftRequest] = None) -> FollowUp:
    _ensure_client_communication_draft(draft)
    parsed = _parse_draft(draft)
    if _communication_status(getattr(draft, "status", None)) == "draft" and request and (request.subject or request.body):
        draft = _update_draft_content(draft, request)
        parsed = _parse_draft(draft)

    template_data = {
        "template_key": parsed["template_key"],
        "title": parsed["title"],
        "subject": parsed["subject"],
        "body": parsed["body"],
    }
    note = _review_note(request.note if request else None)
    _set_if_field(draft, "message", _draft_message(template_data, note))
    _set_if_field(draft, "status", "completed")
    _set_if_field(draft, "updated_at", datetime.utcnow())
    return draft


def _send_blocker_payload(session: Session, draft: FollowUp) -> Dict[str, Any]:
    _ensure_client_communication_draft(draft)
    payload = _draft_payload(session, draft)
    status = payload["communication"]["status"]
    if status != "reviewed":
        return {
            "status": "blocked",
            "blocker": "human_review_required",
            "message": "Sending/export is blocked until a human reviews this draft.",
            "draft": payload,
        }
    return {
        "status": "blocked",
        "blocker": "automatic_sending_disabled",
        "message": "This MVP does not send email or WhatsApp messages automatically. Reviewed drafts must be sent manually outside the system.",
        "manual_send_allowed": True,
        "draft": payload,
    }


@router.get("/api/v1/client-communications/templates")
def get_client_communication_templates():
    return {
        "templates": [
            {
                "template_key": key,
                "title": value["title"],
                "subject": value["subject"],
            }
            for key, value in TEMPLATES.items()
        ],
        "safety_rule": "Drafts are generated for human review only. The system does not send messages automatically.",
    }


@router.get("/api/v1/client-communications/drafts")
def get_client_communication_drafts(
    status: Optional[str] = Query(default=None),
    lead_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    drafts = _all_draft_followups(session)
    if status:
        wanted = _storage_status_for_communication_filter(status)
        drafts = [draft for draft in drafts if _safe_status(getattr(draft, "status", None)) == wanted]
    if lead_id:
        wanted_lead = _normal_id(lead_id)
        drafts = [draft for draft in drafts if _normal_id(getattr(draft, "lead_id", None)) == wanted_lead]
    return _json_response({
        "total_drafts": len(drafts),
        "drafts": [_draft_payload(session, draft) for draft in drafts],
    })


@router.get("/api/v1/client-communications/reviewed")
def get_reviewed_client_communication_drafts(session: Session = Depends(get_session)):
    drafts = [
        draft for draft in _all_draft_followups(session)
        if _communication_status(getattr(draft, "status", None)) == "reviewed"
    ]
    return _json_response({
        "total_reviewed": len(drafts),
        "drafts": [_draft_payload(session, draft) for draft in drafts],
    })


@router.get("/api/v1/client-communications/drafts/{draft_id}")
def get_client_communication_draft(draft_id: str, session: Session = Depends(get_session)):
    draft = _get_follow_up(session, draft_id)
    _ensure_client_communication_draft(draft)
    return _json_response(_draft_payload(session, draft))


@router.get("/api/v1/client-communications/drafts/{draft_id}/preview")
def preview_client_communication_draft(draft_id: str, session: Session = Depends(get_session)):
    draft = _get_follow_up(session, draft_id)
    _ensure_client_communication_draft(draft)
    payload = _draft_payload(session, draft)
    payload["send_blocker"] = _send_blocker_payload(session, draft)
    return _json_response(payload)


@router.patch("/api/v1/client-communications/drafts/{draft_id}")
def update_client_communication_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    session: Session = Depends(get_session),
):
    draft = _get_follow_up(session, draft_id)
    _update_draft_content(draft, request)
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return _json_response({
        "status": "draft_updated",
        "draft": _draft_payload(session, draft),
    })


@router.get("/api/v1/client-communications/leads/{lead_id}")
def get_lead_client_communications(lead_id: str, session: Session = Depends(get_session)):
    lead = _get_lead(session, lead_id)
    return _json_response(_lead_payload(session, lead))


@router.post("/api/v1/client-communications/leads/{lead_id}/drafts/{template_key}")
def create_client_communication_draft(
    lead_id: str,
    template_key: str,
    request: DraftRequest = DraftRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    draft = _create_draft(session, lead, template_key, request)
    return _json_response({
        "status": "draft_created",
        "draft": _draft_payload(session, draft),
        "lead_communications": _lead_payload(session, lead),
    })


@router.post("/api/v1/client-communications/leads/{lead_id}/draft-pack")
def generate_client_communication_draft_pack(
    lead_id: str,
    request: GenerateDraftPackRequest = GenerateDraftPackRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    approved_apps = _approved_applications_for_lead(session, lead)
    if not approved_apps:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Client communication drafting requires an approved-by-authority application.",
                "blocker": "not_authority_approved",
                "next_action": "Complete authority decision tracking before drafting client communication.",
            },
        )

    wanted_templates = request.template_keys or list(TEMPLATES.keys())
    unknown = [key for key in wanted_templates if key not in TEMPLATES]
    if unknown:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Unknown communication templates.",
                "unknown_templates": unknown,
                "available_templates": sorted(TEMPLATES.keys()),
            },
        )

    existing = _draft_followups_for_lead(session, lead)
    created = []
    skipped = []
    for template_key in wanted_templates:
        if request.skip_existing and any(_template_key_in_draft(draft, template_key) for draft in existing):
            skipped.append(template_key)
            continue
        draft = _create_draft(session, lead, template_key, DraftRequest(note=request.note))
        created.append(draft)
        existing.append(draft)

    return _json_response({
        "status": "draft_pack_generated",
        "created_count": len(created),
        "skipped_existing_count": len(skipped),
        "created_drafts": [_draft_payload(session, draft) for draft in created],
        "skipped_templates": skipped,
        "lead_communications": _lead_payload(session, lead),
    })


@router.post("/api/v1/client-communications/drafts/{draft_id}/mark-reviewed")
def mark_client_communication_draft_reviewed(
    draft_id: str,
    request: UpdateDraftRequest = UpdateDraftRequest(),
    session: Session = Depends(get_session),
):
    draft = _get_follow_up(session, draft_id)
    _mark_draft_reviewed(draft, request)
    session.add(draft)
    session.commit()
    session.refresh(draft)

    return _json_response({
        "status": "reviewed",
        "draft": _draft_payload(session, draft),
    })


@router.post("/api/v1/client-communications/leads/{lead_id}/mark-all-reviewed")
def mark_all_client_communication_drafts_reviewed(
    lead_id: str,
    request: MarkAllReviewedRequest = MarkAllReviewedRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    drafts = _draft_followups_for_lead(session, lead)
    changed = []
    skipped = []
    for draft in drafts:
        if _communication_status(getattr(draft, "status", None)) == "draft":
            _mark_draft_reviewed(draft, UpdateDraftRequest(note=request.note))
            session.add(draft)
            changed.append(draft)
        else:
            skipped.append(draft)

    session.commit()
    for draft in changed:
        session.refresh(draft)

    return _json_response({
        "status": "reviewed",
        "reviewed_count": len(changed),
        "skipped_count": len(skipped),
        "reviewed_drafts": [_draft_payload(session, draft) for draft in changed],
        "lead_communications": _lead_payload(session, lead),
    })


@router.post("/api/v1/client-communications/drafts/{draft_id}/send-blocked")
def client_communication_send_blocker(draft_id: str, session: Session = Depends(get_session)):
    draft = _get_follow_up(session, draft_id)
    payload = _send_blocker_payload(session, draft)
    status_code = 409 if payload["blocker"] == "human_review_required" else 501
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def _badge(status: str) -> str:
    status = _safe_status(status)
    if status in {"reviewed", "completed"}:
        return '<span class="badge good">reviewed</span>'
    if status in {"draft", "pending"}:
        return '<span class="badge warn">draft</span>'
    return f'<span class="badge neutral">{status or "-"}</span>'


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"""
    <!doctype html>
    <html>
      <head>
        <title>{title}</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
          table {{ border-collapse: collapse; width: 100%; background: white; }}
          th, td {{ border: 1px solid #e2e8f0; padding: 8px; vertical-align: top; }}
          th {{ background: #eef2f7; }}
          .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 16px 0; }}
          .badge {{ display: inline-block; padding: 2px 7px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
          .good {{ background: #dcfce7; color: #166534; }}
          .warn {{ background: #fef9c3; color: #854d0e; }}
          .neutral {{ background: #e2e8f0; color: #334155; }}
          button {{ padding: 5px 9px; border-radius: 6px; border: 1px solid #94a3b8; }}
          pre {{ white-space: pre-wrap; background: #f8fafc; padding: 8px; border: 1px solid #e2e8f0; }}
          input[type=text], textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; font-family: Arial, sans-serif; }}
          textarea {{ min-height: 220px; }}
          .actions form, .actions a {{ margin-right: 8px; }}
          small {{ color: #64748b; }}
        </style>
      </head>
      <body>{body}</body>
    </html>
    """)


@router.get("/admin/client-communications", response_class=HTMLResponse)
def client_communications_admin(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    rows = []
    for lead in leads:
        payload = _lead_payload(session, lead)
        summary = payload["summary"]
        if summary["draft_count"] == 0 and not payload["approved_applications"]:
            continue
        lead_data = payload["lead"]
        lead_id = lead_data.get("id")
        rows.append(
            f"""
            <tr>
              <td><a href="/admin/client-communications/leads/{lead_id}">{lead_data.get('full_name') or lead_id}</a></td>
              <td>{lead_data.get('target_country') or '-'}</td>
              <td>{summary['stage']}</td>
              <td>{summary['draft_count']}</td>
              <td>{summary['status_counts']}</td>
              <td>{summary['next_action']}</td>
              <td>
                <form method="post" action="/admin/client-communications/leads/{lead_id}/draft-pack" style="display:inline">
                  <button type="submit">Generate Draft Pack</button>
                </form>
                <a href="/api/v1/client-communications/leads/{lead_id}">JSON</a>
              </td>
            </tr>
            """
        )
    body = f"""
      <h1>Client Communication Review {MODULE_VERSION}</h1>
      <p><a href="/admin/v2">Admin v2</a> | <a href="/debug/client-communications">Debug</a></p>
      <div class="card">
        <p><strong>Safety rule:</strong> Drafts are reviewable only. This module does not send emails automatically.</p>
        <p><a href="/admin/client-communications/drafts?status=draft">Drafts</a> |
        <a href="/admin/client-communications/reviewed">Reviewed</a> |
        <a href="/api/v1/client-communications/templates">Templates JSON</a></p>
      </div>
      <table>
        <thead><tr><th>Lead</th><th>Country</th><th>Stage</th><th>Drafts</th><th>Status Counts</th><th>Next Action</th><th>Actions</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    """
    return _page("Client Communication Review", body)


@router.get("/admin/client-communications/drafts", response_class=HTMLResponse)
def client_communications_drafts_admin(
    status: Optional[str] = None,
    session: Session = Depends(get_session),
):
    drafts = _all_draft_followups(session)
    if status:
        wanted = _storage_status_for_communication_filter(status)
        drafts = [draft for draft in drafts if _safe_status(getattr(draft, "status", None)) == wanted]

    rows = []
    for draft in drafts:
        lead = _lead_for_draft(session, draft)
        parsed = _parse_draft(draft)
        draft_id = str(getattr(draft, "id", ""))
        lead_name = _html(getattr(lead, "full_name", "-") if lead else "-")
        action = (
            f"""
            <form method="post" action="/admin/client-communications/drafts/{draft_id}/mark-reviewed" style="display:inline">
              <button type="submit">Mark Reviewed</button>
            </form>
            """
            if parsed["status"] == "draft"
            else "<button disabled>Reviewed</button>"
        )
        rows.append(
            f"""
            <tr>
              <td>{lead_name}</td>
              <td>{_html(parsed['title'])}<br><small>{_html(parsed['template_key'])}</small></td>
              <td>{_html(parsed['subject'])}</td>
              <td><pre>{_html(parsed['body'])}</pre></td>
              <td>{_badge(parsed['status'])}</td>
              <td class="actions">
                <a href="/admin/client-communications/drafts/{draft_id}">Preview/Edit</a>
                {action}
                <a href="/api/v1/client-communications/drafts/{draft_id}">JSON</a>
              </td>
            </tr>
            """
        )
    label = f"Filtered: {status}" if status else "All communication drafts"
    body = f"""
      <h1>Client Communication Drafts {MODULE_VERSION}</h1>
      <p><a href="/admin/client-communications">Back</a> |
      <a href="/admin/client-communications/drafts?status=draft">Draft</a> |
      <a href="/admin/client-communications/reviewed">Reviewed</a></p>
      <div class="card"><strong>{label}</strong> | Total: {len(drafts)}</div>
      <table>
        <thead><tr><th>Lead</th><th>Template</th><th>Subject</th><th>Body</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    """
    return _page("Client Communication Drafts", body)


@router.get("/admin/client-communications/reviewed", response_class=HTMLResponse)
def client_communications_reviewed_admin(session: Session = Depends(get_session)):
    return client_communications_drafts_admin(status="reviewed", session=session)


@router.get("/admin/client-communications/drafts/{draft_id}", response_class=HTMLResponse)
def client_communication_draft_preview_admin(draft_id: str, session: Session = Depends(get_session)):
    draft = _get_follow_up(session, draft_id)
    _ensure_client_communication_draft(draft)
    parsed = _parse_draft(draft)
    lead = _lead_for_draft(session, draft)
    lead_id = str(getattr(lead, "id", "")) if lead else ""
    lead_name = getattr(lead, "full_name", None) or lead_id or "-"
    is_draft = parsed["status"] == "draft"
    send_blocker = _send_blocker_payload(session, draft)

    edit_form = (
        f"""
        <form method="post" action="/admin/client-communications/drafts/{draft_id}/edit">
          <p><label>Subject<br><input type="text" name="subject" value="{_html(parsed['subject'])}"></label></p>
          <p><label>Body<br><textarea name="body">{_html(parsed['body'])}</textarea></label></p>
          <p><label>Operator note<br><input type="text" name="note" value="{_html(parsed.get('note') or '')}"></label></p>
          <button type="submit">Save Draft Edits</button>
        </form>
        """
        if is_draft
        else "<p><button disabled>Reviewed drafts are locked</button></p>"
    )
    review_form = (
        f"""
        <form method="post" action="/admin/client-communications/drafts/{draft_id}/mark-reviewed" style="display:inline">
          <button type="submit">Mark Reviewed</button>
        </form>
        """
        if is_draft
        else "<button disabled>Reviewed</button>"
    )

    body = f"""
      <h1>Draft Preview {MODULE_VERSION}</h1>
      <p><a href="/admin/client-communications/drafts">Draft queue</a> |
      <a href="/admin/client-communications/reviewed">Reviewed queue</a> |
      <a href="/api/v1/client-communications/drafts/{draft_id}/preview">Preview JSON</a></p>
      <div class="card">
        <p><strong>Lead:</strong> {_html(lead_name)}</p>
        <p><strong>Template:</strong> {_html(parsed['title'])} <small>{_html(parsed['template_key'])}</small></p>
        <p><strong>Status:</strong> {_badge(parsed['status'])}</p>
        <p><strong>Send blocker:</strong> {_html(send_blocker['blocker'])} - {_html(send_blocker['message'])}</p>
      </div>
      <div class="card">
        <h2>Preview</h2>
        <p><strong>Subject:</strong> {_html(parsed['subject'])}</p>
        <pre>{_html(parsed['body'])}</pre>
      </div>
      <div class="card">
        <h2>Edit Before Review</h2>
        {edit_form}
      </div>
      <div class="card actions">
        {review_form}
        <form method="post" action="/api/v1/client-communications/drafts/{draft_id}/send-blocked" style="display:inline">
          <button type="submit">Send Placeholder</button>
        </form>
      </div>
    """
    return _page("Client Communication Draft Preview", body)


@router.get("/admin/client-communications/leads/{lead_id}", response_class=HTMLResponse)
def client_communications_lead_admin(lead_id: str, session: Session = Depends(get_session)):
    lead = _get_lead(session, lead_id)
    payload = _lead_payload(session, lead)
    summary = payload["summary"]

    rows = []
    for item in payload["drafts"]:
        draft = item["draft"]
        parsed = item["communication"]
        draft_id = draft.get("id")
        action = (
            f"""
            <form method="post" action="/admin/client-communications/drafts/{draft_id}/mark-reviewed" style="display:inline">
              <button type="submit">Mark Reviewed</button>
            </form>
            """
            if parsed["status"] == "draft"
            else "<button disabled>Reviewed</button>"
        )
        rows.append(
            f"""
            <tr>
              <td>{_html(parsed['title'])}<br><small>{_html(parsed['template_key'])}</small></td>
              <td>{_html(parsed['subject'])}</td>
              <td><pre>{_html(parsed['body'])}</pre></td>
              <td>{_badge(parsed['status'])}</td>
              <td class="actions">
                <a href="/admin/client-communications/drafts/{draft_id}">Preview/Edit</a>
                {action}
                <a href="/api/v1/client-communications/drafts/{draft_id}">JSON</a>
              </td>
            </tr>
            """
        )

    generate_buttons = "".join(
        f"""
        <form method="post" action="/admin/client-communications/leads/{lead_id}/drafts/{template_key}" style="display:inline">
          <button type="submit">{data['title']}</button>
        </form>
        """
        for template_key, data in TEMPLATES.items()
    )

    body = f"""
      <h1>Client Communication: {payload['lead'].get('full_name') or lead_id}</h1>
      <p><a href="/admin/client-communications">Back</a> | <a href="/admin/v2/leads/{lead_id}">Lead v2</a></p>
      <div class="card">
        <p><strong>Stage:</strong> {_html(summary['stage'])}</p>
        <p><strong>Drafts:</strong> {summary['draft_count']} | <strong>Status:</strong> {summary['status_counts']}</p>
        <p><strong>Next action:</strong> {_html(summary['next_action'])}</p>
        <form method="post" action="/admin/client-communications/leads/{lead_id}/draft-pack" style="display:inline">
          <button type="submit">Generate Full Draft Pack</button>
        </form>
        <form method="post" action="/admin/client-communications/leads/{lead_id}/mark-all-reviewed" style="display:inline">
          <button type="submit">Mark All Reviewed</button>
        </form>
        <div>{generate_buttons}</div>
      </div>
      <table>
        <thead><tr><th>Template</th><th>Subject</th><th>Body</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    """
    return _page("Lead Client Communication", body)


@router.post("/admin/client-communications/leads/{lead_id}/draft-pack")
def admin_generate_client_communication_draft_pack(lead_id: str, session: Session = Depends(get_session)):
    generate_client_communication_draft_pack(
        lead_id,
        GenerateDraftPackRequest(note="Generated from admin client communication page.", skip_existing=True),
        session,
    )
    return RedirectResponse(url=f"/admin/client-communications/leads/{lead_id}", status_code=303)


@router.post("/admin/client-communications/leads/{lead_id}/drafts/{template_key}")
def admin_create_client_communication_draft(
    lead_id: str,
    template_key: str,
    session: Session = Depends(get_session),
):
    create_client_communication_draft(
        lead_id,
        template_key,
        DraftRequest(note="Generated from admin client communication lead page."),
        session,
    )
    return RedirectResponse(url=f"/admin/client-communications/leads/{lead_id}", status_code=303)


@router.post("/admin/client-communications/leads/{lead_id}/mark-all-reviewed")
def admin_mark_all_client_communication_drafts_reviewed(lead_id: str, session: Session = Depends(get_session)):
    mark_all_client_communication_drafts_reviewed(
        lead_id,
        MarkAllReviewedRequest(note="Marked all reviewed from admin client communication lead page."),
        session,
    )
    return RedirectResponse(url=f"/admin/client-communications/leads/{lead_id}", status_code=303)


@router.post("/admin/client-communications/drafts/{draft_id}/edit")
async def admin_update_client_communication_draft(
    draft_id: str,
    request: Request,
    session: Session = Depends(get_session),
):
    form = parse_qs((await request.body()).decode("utf-8"))
    update_client_communication_draft(
        draft_id,
        UpdateDraftRequest(
            subject=(form.get("subject") or [""])[0],
            body=(form.get("body") or [""])[0],
            note=(form.get("note") or [""])[0] or None,
        ),
        session,
    )
    return RedirectResponse(url=f"/admin/client-communications/drafts/{draft_id}", status_code=303)


@router.post("/admin/client-communications/drafts/{draft_id}/mark-reviewed")
def admin_mark_client_communication_draft_reviewed(draft_id: str, session: Session = Depends(get_session)):
    mark_client_communication_draft_reviewed(
        draft_id,
        UpdateDraftRequest(note="Marked reviewed from admin client communication page."),
        session,
    )
    return RedirectResponse(url=f"/admin/client-communications/drafts/{draft_id}", status_code=303)


@router.get("/debug/client-communications")
def debug_client_communications():
    return {
        "status": "ok",
        "version": MODULE_VERSION,
        "draft_prefix": DRAFT_PREFIX,
        "templates": sorted(TEMPLATES.keys()),
        "safety_rule": "Drafts only; no automatic sending. FollowUp.status uses enum-safe pending/completed storage.",
        "routes": [
            "GET /api/v1/client-communications/templates",
            "GET /api/v1/client-communications/drafts",
            "GET /api/v1/client-communications/reviewed",
            "GET /api/v1/client-communications/drafts/{draft_id}",
            "GET /api/v1/client-communications/drafts/{draft_id}/preview",
            "PATCH /api/v1/client-communications/drafts/{draft_id}",
            "GET /api/v1/client-communications/leads/{lead_id}",
            "POST /api/v1/client-communications/leads/{lead_id}/drafts/{template_key}",
            "POST /api/v1/client-communications/leads/{lead_id}/draft-pack",
            "POST /api/v1/client-communications/drafts/{draft_id}/mark-reviewed",
            "POST /api/v1/client-communications/leads/{lead_id}/mark-all-reviewed",
            "POST /api/v1/client-communications/drafts/{draft_id}/send-blocked",
            "GET /admin/client-communications",
            "GET /admin/client-communications/drafts",
            "GET /admin/client-communications/reviewed",
            "GET /admin/client-communications/drafts/{draft_id}",
            "GET /admin/client-communications/leads/{lead_id}",
            "POST /admin/client-communications/drafts/{draft_id}/edit",
            "POST /admin/client-communications/drafts/{draft_id}/mark-reviewed",
            "POST /admin/client-communications/leads/{lead_id}/mark-all-reviewed",
        ],
    }
