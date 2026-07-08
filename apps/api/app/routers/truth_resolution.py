from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    FollowUp,
    HumanReview,
    Lead,
    SourceReference,
    TruthClaim,
)
from app.services.audit_log import record_audit

router = APIRouter(tags=["truth-resolution"])

REJECTED_TRUTH_STATUSES = {"rejected", "reject", "false", "unsafe", "misleading", "fake"}
PENDING_REVIEW_STATUSES = {"pending", "open", "needs_review", "human_review", "in_review"}

class TruthResolveRequest(BaseModel):
    resolution_note: str = Field(default="Resolved after official-source review.")
    resolution_status: str = Field(default="resolved")
    require_sources: bool = Field(default=True)
    create_follow_up: bool = Field(default=True)

class CorrectedClaimRequest(BaseModel):
    claim: str
    domain: str = "visa"
    country: Optional[str] = None
    verdict: str = "verified"
    confidence: float = 0.9
    explanation: str = "Corrected claim created after official-source review."
    create_follow_up: bool = True

class CloseReviewsRequest(BaseModel):
    status: str = "resolved"
    note: str = "Closed after truth resolution."
    create_follow_up: bool = True

def _value(value: Any) -> Any:
    return getattr(value, "value", value)

def _safe_status(value: Any) -> str:
    return str(_value(value) or "").strip().lower()


def _safe_truth_verdict(value: Any) -> str:
    # Map user-facing/workflow truth words to local VerificationStatus enum names.
    # Persist only: verified, rejected, needs_review.
    status = _safe_status(value)
    if status in {"verified", "verify", "approved", "approve", "accepted", "valid", "true", "resolved", "superseded", "clear"}:
        return "verified"
    if status in {"rejected", "reject", "false", "unsafe", "misleading", "fake", "denied"}:
        return "rejected"
    if status in {"needs_review", "need_review", "review", "human_review", "pending", "in_review"}:
        return "needs_review"
    return status or "needs_review"


def _resolution_note(existing: Any, action: str, note: str) -> str:
    existing_text = str(existing or "").strip()
    marker = f"[truth_resolution:{action}] {note}".strip()
    if marker in existing_text:
        return existing_text
    if existing_text:
        return f"{existing_text}\n\n{marker}"
    return marker

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
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif hasattr(obj, "dict"):
        data = obj.dict()
    else:
        data = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    if not data:
        for field in _model_fields(obj.__class__):
            if hasattr(obj, field):
                data[field] = getattr(obj, field)
    return {k: _json_safe(v) for k, v in data.items()}

def _json_response(payload: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload))

def _uuid_or_404(value: Any, field_name: str = "id") -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc

def _id_hex(value: Any) -> str:
    if isinstance(value, uuid.UUID):
        return value.hex
    try:
        return uuid.UUID(str(value)).hex
    except Exception:
        return str(value).replace("-", "")

def _id_str(value: Any) -> str:
    if isinstance(value, uuid.UUID):
        return str(value)
    try:
        return str(uuid.UUID(str(value)))
    except Exception:
        return str(value)

def _same_id(a: Any, b: Any) -> bool:
    return _id_hex(a) == _id_hex(b)

def _set_if_field(obj: Any, field: str, value: Any) -> bool:
    if field in _model_fields(obj.__class__) or hasattr(obj, field):
        setattr(obj, field, value)
        return True
    return False

def _get_lead(session: Session, lead_id: Any) -> Lead:
    lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

def _get_claim(session: Session, claim_id: Any) -> TruthClaim:
    claim = session.get(TruthClaim, _uuid_or_404(claim_id, "claim_id"))
    if not claim:
        raise HTTPException(status_code=404, detail="Truth claim not found")
    return claim

def _claim_id(claim: TruthClaim) -> Any:
    return getattr(claim, "id", None)

def _lead_id(lead: Lead) -> Any:
    return getattr(lead, "id", None)

def _claim_lead_id(claim: TruthClaim) -> Any:
    return getattr(claim, "lead_id", None)

def _is_rejected_claim(claim: TruthClaim) -> bool:
    verdict = _safe_status(getattr(claim, "verdict", getattr(claim, "status", None)))
    return verdict in REJECTED_TRUTH_STATUSES

def _requires_review(claim: TruthClaim) -> bool:
    return bool(getattr(claim, "requires_human_review", False))

def _is_pending_review(review: HumanReview) -> bool:
    return _safe_status(getattr(review, "status", None)) in PENDING_REVIEW_STATUSES

def _source_refs_for_claim(session: Session, claim_id: Any) -> List[SourceReference]:
    refs = session.exec(select(SourceReference)).all()
    matches: List[SourceReference] = []
    for ref in refs:
        for field in ("truth_claim_id", "claim_id"):
            if hasattr(ref, field) and _same_id(getattr(ref, field), claim_id):
                matches.append(ref)
                break
    return matches

def _reviews_for_lead(session: Session, lead_id: Any) -> List[HumanReview]:
    reviews = session.exec(select(HumanReview)).all()
    return [r for r in reviews if hasattr(r, "lead_id") and _same_id(getattr(r, "lead_id"), lead_id)]

def _claims_for_lead(session: Session, lead_id: Any) -> List[TruthClaim]:
    claims = session.exec(select(TruthClaim)).all()
    return [c for c in claims if hasattr(c, "lead_id") and _same_id(getattr(c, "lead_id"), lead_id)]

def _create_follow_up(session: Session, lead_id: Any, message: str) -> Optional[FollowUp]:
    fields = _model_fields(FollowUp)
    now = datetime.utcnow()
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

def _truth_resolution_summary(session: Session, lead: Lead) -> Dict[str, Any]:
    lead_id = _lead_id(lead)
    claims = _claims_for_lead(session, lead_id)
    reviews = _reviews_for_lead(session, lead_id)

    rejected_claims = [c for c in claims if _is_rejected_claim(c)]
    claims_needing_review = [c for c in claims if _requires_review(c)]
    pending_reviews = [r for r in reviews if _is_pending_review(r)]

    blockers: List[str] = []
    if rejected_claims:
        blockers.append("truth_claim_rejected")
    if claims_needing_review:
        blockers.append("truth_claim_requires_review")
    if pending_reviews:
        blockers.append("human_review_pending")

    stage = "truth_clear" if not blockers else "truth_resolution_required"
    next_action = (
        "Truth state is clear enough for downstream sales/application guardrails."
        if not blockers
        else "Resolve or supersede rejected claims and close pending human reviews."
    )

    return {
        "lead": _to_dict(lead),
        "stage": stage,
        "can_progress": not blockers,
        "blockers": blockers,
        "counts": {
            "truth_claims": len(claims),
            "rejected_truth_claims": len(rejected_claims),
            "truth_claims_needing_review": len(claims_needing_review),
            "human_reviews": len(reviews),
            "pending_reviews": len(pending_reviews),
        },
        "claims": [_to_dict(c) for c in claims],
        "human_reviews": [_to_dict(r) for r in reviews],
        "next_action": next_action,
    }

def _build_corrected_claim_payload(lead: Lead, request: CorrectedClaimRequest) -> Dict[str, Any]:
    fields = _model_fields(TruthClaim)
    now = datetime.utcnow()
    lead_id = _lead_id(lead)
    country = request.country or getattr(lead, "target_country", None)
    safe_verdict = _safe_truth_verdict(request.verdict)
    candidates = {
        "lead_id": lead_id,
        "claim": request.claim,
        "text": request.claim,
        "statement": request.claim,
        "domain": request.domain,
        "country": country,
        "target_country": country,
        "verdict": safe_verdict,
        "status": safe_verdict,
        "confidence": request.confidence,
        "confidence_score": request.confidence,
        "requires_human_review": safe_verdict != "verified",
        "explanation": request.explanation,
        "reasoning": request.explanation,
        "notes": request.explanation,
        "recommended_next_step": "Use this corrected, source-grounded claim instead of the unsafe original claim.",
        "red_flags_json": "[]",
        "created_at": now,
        "updated_at": now,
    }
    return {k: v for k, v in candidates.items() if k in fields and v is not None}

@router.get("/api/v1/truth/resolution-queue")
def get_truth_resolution_queue(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    items = [_truth_resolution_summary(session, lead) for lead in leads]
    stage_counts: Dict[str, int] = {}
    for item in items:
        stage = item["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    return _json_response({"total_leads": len(leads), "stage_counts": stage_counts, "items": items})

@router.get("/api/v1/leads/{lead_id}/truth-resolution")
def get_lead_truth_resolution(lead_id: str, session: Session = Depends(get_session)):
    lead = _get_lead(session, lead_id)
    return _json_response(_truth_resolution_summary(session, lead))

@router.post("/api/v1/truth/claims/{claim_id}/resolve")
def resolve_truth_claim(
    claim_id: str,
    request: TruthResolveRequest = TruthResolveRequest(),
    session: Session = Depends(get_session),
):
    claim = _get_claim(session, claim_id)
    lead_id = _claim_lead_id(claim)
    if request.require_sources:
        refs = _source_refs_for_claim(session, _claim_id(claim))
        if not refs:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Attach official source evidence before resolving this truth claim.",
                    "claim_id": _id_str(_claim_id(claim)),
                    "next_action": "Use the existing Attach Official Sources action or attach evidence manually.",
                },
            )

    before = _to_dict(claim)
    action = _safe_status(request.resolution_status) or "resolved"

    safe_verdict = _safe_truth_verdict(request.resolution_status)
    if safe_verdict not in {"verified", "rejected", "needs_review"}:
        safe_verdict = "verified"

    old_explanation = getattr(claim, "explanation", None)
    old_next_step = getattr(claim, "recommended_next_step", None)
    note = request.resolution_note

    _set_if_field(claim, "verdict", safe_verdict)
    _set_if_field(claim, "status", safe_verdict)
    _set_if_field(claim, "requires_human_review", False)
    _set_if_field(claim, "red_flags_json", "[]")
    _set_if_field(claim, "resolved_at", datetime.utcnow())
    _set_if_field(claim, "updated_at", datetime.utcnow())
    _set_if_field(claim, "resolution_status", action)
    _set_if_field(claim, "resolution_note", note)
    _set_if_field(claim, "notes", _resolution_note(getattr(claim, "notes", ""), action, note))
    _set_if_field(claim, "explanation", _resolution_note(old_explanation, action, note))
    _set_if_field(claim, "recommended_next_step", _resolution_note(old_next_step, action, note))

    try:
        session.add(claim)
        session.commit()
        session.refresh(claim)
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Could not resolve truth claim safely.",
                "error": str(exc),
                "safe_verdict": safe_verdict,
                "requested_resolution_status": request.resolution_status,
            },
        ) from exc

    follow_up = None
    if request.create_follow_up and lead_id is not None:
        follow_up = _create_follow_up(session, lead_id, f"Truth claim {action}: {request.resolution_note}")

    lead = _get_lead(session, lead_id)
    record_audit(
        session,
        action="truth_claim_rejected" if safe_verdict == "rejected" else "truth_claim_resolved",
        entity_type="truth_claim",
        entity_id=_claim_id(claim),
        before_state=before,
        after_state=_to_dict(claim),
        reason=request.resolution_note,
        source="truth_resolution",
        commit=True,
    )
    return _json_response({
        "status": action,
        "before": before,
        "claim": _to_dict(claim),
        "follow_up": _to_dict(follow_up) if follow_up else None,
        "truth_resolution": _truth_resolution_summary(session, lead),
    })

@router.post("/api/v1/truth/claims/{claim_id}/supersede")
def supersede_truth_claim(
    claim_id: str,
    request: TruthResolveRequest = TruthResolveRequest(
        resolution_status="superseded",
        resolution_note="Superseded by corrected official-source-backed claim.",
    ),
    session: Session = Depends(get_session),
):
    request.resolution_status = "superseded"
    return resolve_truth_claim(claim_id, request, session)

@router.post("/api/v1/truth/leads/{lead_id}/corrected-claim")
def create_corrected_claim(
    lead_id: str,
    request: CorrectedClaimRequest,
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    payload = _build_corrected_claim_payload(lead, request)
    try:
        claim = TruthClaim(**payload)
        session.add(claim)
        session.commit()
        session.refresh(claim)
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Could not create corrected truth claim from available model fields.",
                "error": str(exc),
                "payload_keys": sorted(payload.keys()),
                "model_fields": sorted(_model_fields(TruthClaim)),
            },
        ) from exc

    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(session, _lead_id(lead), f"Corrected truth claim created for {getattr(lead, 'target_country', 'target country')}.")

    record_audit(
        session,
        action="truth_claim_corrected",
        entity_type="truth_claim",
        entity_id=_claim_id(claim),
        before_state=None,
        after_state=_to_dict(claim),
        reason=request.explanation,
        source="truth_resolution",
        commit=True,
    )

    return _json_response({
        "status": "created",
        "claim": _to_dict(claim),
        "follow_up": _to_dict(follow_up) if follow_up else None,
        "truth_resolution": _truth_resolution_summary(session, lead),
    })

@router.post("/api/v1/truth/leads/{lead_id}/close-reviews")
def close_truth_reviews(
    lead_id: str,
    request: CloseReviewsRequest = CloseReviewsRequest(),
    session: Session = Depends(get_session),
):
    lead = _get_lead(session, lead_id)
    reviews = _reviews_for_lead(session, _lead_id(lead))
    pending_reviews = [r for r in reviews if _is_pending_review(r)]

    updated = []
    for review in pending_reviews:
        _set_if_field(review, "status", request.status)
        _set_if_field(review, "resolution_note", request.note)
        _set_if_field(review, "notes", request.note)
        _set_if_field(review, "reviewer_notes", request.note)
        _set_if_field(review, "updated_at", datetime.utcnow())
        _set_if_field(review, "resolved_at", datetime.utcnow())
        session.add(review)
        updated.append(review)

    try:
        session.commit()
        for review in updated:
            session.refresh(review)
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Could not close truth human reviews safely.",
                "error": str(exc),
                "requested_status": request.status,
                "updated_count": len(updated),
            },
        ) from exc

    follow_up = None
    if request.create_follow_up:
        follow_up = _create_follow_up(session, _lead_id(lead), f"Human reviews closed for truth resolution: {request.note}")

    record_audit(
        session,
        action="human_reviews_closed",
        entity_type="lead",
        entity_id=_lead_id(lead),
        before_state={"pending_review_count": len(pending_reviews)},
        after_state={"closed_review_count": len(updated), "reviews": [_to_dict(r) for r in updated]},
        reason=request.note,
        source="truth_resolution",
        commit=True,
    )

    return _json_response({
        "status": "closed",
        "closed_count": len(updated),
        "reviews": [_to_dict(r) for r in updated],
        "follow_up": _to_dict(follow_up) if follow_up else None,
        "truth_resolution": _truth_resolution_summary(session, lead),
    })

@router.get("/admin/truth-resolution", response_class=HTMLResponse)
def truth_resolution_admin(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    items = [_truth_resolution_summary(session, lead) for lead in leads]
    stage_counts: Dict[str, int] = {}
    for item in items:
        stage = item["stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    rows = []
    for item in items:
        lead = item["lead"]
        blockers = ", ".join(item["blockers"]) or "-"
        rows.append(
            f"""
            <tr>
              <td><a href="/admin/leads/{lead.get('id')}">{lead.get('full_name')}</a></td>
              <td>{lead.get('intent') or '-'}</td>
              <td>{lead.get('target_country') or '-'}</td>
              <td>{item['stage']}</td>
              <td>{item['counts']['rejected_truth_claims']}</td>
              <td>{item['counts']['pending_reviews']}</td>
              <td>{blockers}</td>
              <td>{item['next_action']}</td>
              <td>
                <form method="post" action="/admin/truth-resolution/leads/{lead.get('id')}/close-reviews">
                  <button type="submit">Close Reviews</button>
                </form>
              </td>
            </tr>
            """
        )

    html = f"""
    <!doctype html>
    <html>
    <head>
      <title>Truth Resolution</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
        th {{ background: #f3f4f6; }}
        .cards {{ display: flex; gap: 12px; margin: 12px 0 24px; }}
        .card {{ border: 1px solid #ddd; padding: 12px; border-radius: 8px; }}
        button {{ padding: 6px 10px; cursor: pointer; }}
      </style>
    </head>
    <body>
      <h1>Truth Resolution Engine</h1>
      <p><a href="/admin">← Admin Dashboard</a></p>
      <div class="cards">
        <div class="card"><b>Total leads</b><br>{len(leads)}</div>
        <div class="card"><b>Clear</b><br>{stage_counts.get('truth_clear', 0)}</div>
        <div class="card"><b>Resolution required</b><br>{stage_counts.get('truth_resolution_required', 0)}</div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Lead</th>
            <th>Intent</th>
            <th>Country</th>
            <th>Stage</th>
            <th>Rejected Claims</th>
            <th>Pending Reviews</th>
            <th>Blockers</th>
            <th>Next Action</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </body>
    </html>
    """
    return HTMLResponse(html)

@router.post("/admin/truth-resolution/leads/{lead_id}/close-reviews")
def admin_close_reviews(lead_id: str, session: Session = Depends(get_session)):
    close_truth_reviews(lead_id, CloseReviewsRequest(create_follow_up=False), session)
    return RedirectResponse(url="/admin/truth-resolution", status_code=303)

@router.get("/debug/truth-resolution")
def debug_truth_resolution():
    return {
        "status": "ok",
        "version": "v1.2",
        "routes": [
            "GET /api/v1/truth/resolution-queue",
            "GET /api/v1/leads/{lead_id}/truth-resolution",
            "POST /api/v1/truth/claims/{claim_id}/resolve",
            "POST /api/v1/truth/claims/{claim_id}/supersede",
            "POST /api/v1/truth/leads/{lead_id}/corrected-claim",
            "POST /api/v1/truth/leads/{lead_id}/close-reviews",
            "GET /admin/truth-resolution",
        ],
    }
