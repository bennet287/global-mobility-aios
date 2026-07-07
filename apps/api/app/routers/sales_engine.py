from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import DocumentRecord, FollowUp, HumanReview, Lead, TruthClaim

try:
    from app.models.domain import LeadStatus
except Exception:  # pragma: no cover - keeps router compatible with older local models
    LeadStatus = None  # type: ignore


router = APIRouter()


class SalesFollowUpCreate(BaseModel):
    channel: str = "email"
    subject: Optional[str] = None
    message: Optional[str] = None
    due_in_days: int = 1
    priority: str = "normal"
    follow_up_type: str = "sales"


class SalesQualificationRequest(BaseModel):
    qualification_status: str = "qualified"
    notes: Optional[str] = None
    create_follow_up: bool = True
    follow_up_due_in_days: int = 1


class ConversionRequest(BaseModel):
    notes: Optional[str] = None
    create_onboarding_follow_up: bool = True
    require_documents_ready: bool = False


class SalesReconcileRequest(BaseModel):
    create_follow_up: bool = False
    only_problem_statuses: bool = True


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _model_fields(model_cls: type) -> set[str]:
    fields = getattr(model_cls, "model_fields", None) or getattr(model_cls, "__fields__", {})
    return set(fields.keys())


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _serialize(obj: Any) -> dict[str, Any]:
    """Serialize SQLModel/Pydantic/SQLAlchemy objects safely.

    SQLModel table objects can sometimes return an empty dict from model_dump()
    after session refresh/expiration. Reading table columns directly keeps API
    responses stable for admin actions.
    """
    if obj is None:
        return {}

    if hasattr(obj, "__table__"):
        data = {column.name: getattr(obj, column.name, None) for column in obj.__table__.columns}
    elif hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif hasattr(obj, "dict"):
        data = obj.dict()
    else:
        data = dict(getattr(obj, "__dict__", {}))

    data.pop("_sa_instance_state", None)
    return {key: _serialize_value(val) for key, val in data.items()}


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(val) for key, val in value.items()}
    return _value(value)


def _set_lead_status(lead: Lead, status: str) -> None:
    if not hasattr(lead, "status"):
        return
    if LeadStatus is not None and hasattr(LeadStatus, status):
        setattr(lead, "status", getattr(LeadStatus, status))
    else:
        setattr(lead, "status", status)
    if hasattr(lead, "updated_at"):
        setattr(lead, "updated_at", _now())


def _truth_status(claim: Any) -> str:
    for name in ("verdict", "status", "verification_status"):
        if hasattr(claim, name):
            return str(_value(getattr(claim, name))).upper()
    return "UNKNOWN"


def _review_status(review: Any) -> str:
    if hasattr(review, "status"):
        return str(_value(getattr(review, "status"))).lower()
    if hasattr(review, "resolved") and getattr(review, "resolved"):
        return "resolved"
    return "pending"


def _followup_status(follow_up: Any) -> str:
    if hasattr(follow_up, "status"):
        return str(_value(getattr(follow_up, "status"))).lower()
    if hasattr(follow_up, "completed_at") and getattr(follow_up, "completed_at"):
        return "completed"
    return "pending"


def _doc_status(document: Any) -> str:
    if hasattr(document, "status"):
        return str(_value(getattr(document, "status"))).lower()
    return "unknown"


def _followup_message_for_lead(lead: Lead, purpose: str = "sales") -> str:
    country = getattr(lead, "target_country", None) or "your target country"
    name = getattr(lead, "full_name", "there")
    if purpose == "qualified":
        return (
            f"Hi {name}, your profile has been qualified for the next stage. "
            f"The next step is to confirm your documents and preferred pathway for {country}."
        )
    if purpose == "converted":
        return (
            f"Hi {name}, welcome onboard. We will now start your structured mobility process, "
            f"including documents, verified guidance, and application tracking for {country}."
        )
    if purpose == "blocked":
        return (
            f"Hi {name}, before we proceed further, our compliance check found that your case "
            f"requires manual review for {country}. We will verify the details and update you with safe next steps."
        )
    return (
        f"Hi {name}, thank you for your interest. We reviewed your profile for {country}. "
        "Please confirm your preferred pathway and share any pending documents so we can proceed."
    )


def _create_follow_up(
    session: Session,
    lead_id: UUID,
    *,
    channel: str = "email",
    subject: str = "Next steps for your global mobility profile",
    message: str,
    status: str = "pending",
    priority: str = "normal",
    follow_up_type: str = "sales",
    due_in_days: int = 1,
) -> FollowUp:
    fields = _model_fields(FollowUp)
    due_at = _now() + timedelta(days=max(due_in_days, 0))
    candidates: dict[str, Any] = {
        "lead_id": lead_id,
        "channel": channel,
        "subject": subject,
        "message": message,
        "body": message,
        "content": message,
        "follow_up_type": follow_up_type,
        "type": follow_up_type,
        "status": status,
        "priority": priority,
        "due_at": due_at,
        "scheduled_at": due_at,
        "created_at": _now(),
        "updated_at": _now(),
    }
    payload = {key: value for key, value in candidates.items() if key in fields}
    follow_up = FollowUp(**payload)
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up


def _lead_related_records(session: Session, lead_id: UUID) -> dict[str, list[Any]]:
    return {
        "truth_claims": session.exec(select(TruthClaim).where(TruthClaim.lead_id == lead_id)).all(),
        "reviews": session.exec(select(HumanReview).where(HumanReview.lead_id == lead_id)).all(),
        "documents": session.exec(select(DocumentRecord).where(DocumentRecord.lead_id == lead_id)).all(),
        "follow_ups": session.exec(select(FollowUp).where(FollowUp.lead_id == lead_id)).all(),
    }


def _pipeline_item(session: Session, lead: Lead) -> dict[str, Any]:
    lead_id = getattr(lead, "id")
    related = _lead_related_records(session, lead_id)
    truth_claims = related["truth_claims"]
    reviews = related["reviews"]
    documents = related["documents"]
    follow_ups = related["follow_ups"]

    rejected_truth = [claim for claim in truth_claims if _truth_status(claim) == "REJECTED"]
    needs_review_truth = [claim for claim in truth_claims if _truth_status(claim) in {"NEEDS_REVIEW", "REVIEW"}]
    pending_reviews = [review for review in reviews if _review_status(review) in {"pending", "open", "needs_review"}]
    missing_docs = [doc for doc in documents if _doc_status(doc) in {"missing", "needs_review", "rejected"}]
    pending_followups = [fu for fu in follow_ups if _followup_status(fu) in {"pending", "open", "scheduled"}]

    if rejected_truth:
        stage = "blocked_truth_rejected"
    elif pending_reviews or needs_review_truth:
        stage = "human_review"
    elif missing_docs:
        stage = "needs_documents"
    elif pending_followups:
        stage = "follow_up_pending"
    else:
        stage = str(_value(getattr(lead, "status", "new")))

    guardrails = _sales_guardrails(session, lead_id)

    return {
        "lead": _serialize(lead),
        "stage": stage,
        "counts": {
            "truth_claims": len(truth_claims),
            "rejected_truth_claims": len(rejected_truth),
            "pending_reviews": len(pending_reviews),
            "documents": len(documents),
            "missing_or_problem_documents": len(missing_docs),
            "follow_ups": len(follow_ups),
            "pending_follow_ups": len(pending_followups),
        },
        "next_action": _next_action(stage),
        "guardrails": guardrails,
        "status_integrity": _status_integrity(lead, stage, guardrails),
    }


def _next_action(stage: str) -> str:
    return {
        "blocked_truth_rejected": "Resolve or replace the risky claim before sales conversion.",
        "human_review": "Human reviewer must approve, reject, or resolve the case.",
        "needs_documents": "Request missing or rejected documents from the lead.",
        "follow_up_pending": "Complete the pending sales follow-up.",
        "new": "Qualify the lead and create a follow-up.",
        "qualified": "Move lead toward document completion and conversion.",
        "converted": "Start onboarding and application tracking.",
        "closed": "No active action required.",
    }.get(stage, "Review lead and decide next action.")


def _sales_guardrails(session: Session, lead_id: UUID) -> dict[str, Any]:
    related = _lead_related_records(session, lead_id)
    truth_claims = related["truth_claims"]
    reviews = related["reviews"]
    documents = related["documents"]

    rejected_truth = [claim for claim in truth_claims if _truth_status(claim) == "REJECTED"]
    needs_review_truth = [claim for claim in truth_claims if _truth_status(claim) in {"NEEDS_REVIEW", "REVIEW"}]
    pending_reviews = [review for review in reviews if _review_status(review) in {"pending", "open", "needs_review"}]
    problem_documents = [doc for doc in documents if _doc_status(doc) in {"missing", "needs_review", "rejected"}]

    hard_blockers: list[str] = []
    warnings: list[str] = []

    if rejected_truth:
        hard_blockers.append("truth_claim_rejected")
    if needs_review_truth:
        hard_blockers.append("truth_claim_needs_review")
    if pending_reviews:
        hard_blockers.append("human_review_pending")
    if problem_documents:
        warnings.append("documents_missing_or_problematic")

    return {
        "can_qualify": not hard_blockers,
        "can_convert": not hard_blockers,
        "hard_blockers": hard_blockers,
        "warnings": warnings,
        "counts": {
            "rejected_truth_claims": len(rejected_truth),
            "truth_claims_needing_review": len(needs_review_truth),
            "pending_reviews": len(pending_reviews),
            "problem_documents": len(problem_documents),
        },
    }


def _raise_if_sales_blocked(session: Session, lead_id: UUID, action: str, *, require_documents_ready: bool = False) -> None:
    guardrails = _sales_guardrails(session, lead_id)
    blockers = list(guardrails["hard_blockers"])
    if require_documents_ready and "documents_missing_or_problematic" in guardrails["warnings"]:
        blockers.append("documents_missing_or_problematic")

    if blockers:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Sales action '{action}' is blocked by governance guardrails.",
                "lead_id": str(lead_id),
                "blocked_action": action,
                "blockers": blockers,
                "guardrails": guardrails,
                "next_action": "Resolve rejected truth claims and pending human reviews before qualification or conversion.",
            },
        )




PROBLEM_SALES_STATUSES = {"qualified", "converted"}
INVALID_PERSISTED_SALES_STATUSES = {"blocked_truth_rejected"}


def _lead_status_text(lead: Lead) -> str:
    return str(_value(getattr(lead, "status", "new"))).lower()


def _recommended_status_for_guardrails(guardrails: dict[str, Any]) -> Optional[str]:
    blockers = set(guardrails.get("hard_blockers", []))
    # Persist only operational lead statuses. `blocked_truth_rejected` is a computed
    # pipeline stage, not a safe stored Lead.status value in all DB/model configurations.
    if "truth_claim_rejected" in blockers:
        return "human_review"
    if "truth_claim_needs_review" in blockers or "human_review_pending" in blockers:
        return "human_review"
    return None


def _status_integrity(lead: Lead, stage: str, guardrails: dict[str, Any]) -> dict[str, Any]:
    actual_status = _lead_status_text(lead)
    recommended_status = _recommended_status_for_guardrails(guardrails)
    is_inconsistent = bool(
        (recommended_status and actual_status in PROBLEM_SALES_STATUSES)
        or actual_status in INVALID_PERSISTED_SALES_STATUSES
    )
    return {
        "actual_status": actual_status,
        "effective_stage": stage,
        "recommended_status": recommended_status,
        "is_inconsistent": is_inconsistent,
        "reason": (
            "Lead has a sales-positive status while Truth/Human Review guardrails block sales progression."
            if is_inconsistent else None
        ),
    }


def _reconcile_lead_status(
    session: Session,
    lead: Lead,
    *,
    create_follow_up: bool = False,
    only_problem_statuses: bool = True,
) -> dict[str, Any]:
    lead_id = getattr(lead, "id")
    before_status = _lead_status_text(lead)
    guardrails = _sales_guardrails(session, lead_id)
    recommended_status = _recommended_status_for_guardrails(guardrails)

    if not recommended_status:
        return {
            "lead_id": str(lead_id),
            "action": "noop",
            "before_status": before_status,
            "after_status": before_status,
            "reason": "No hard sales guardrails found.",
            "guardrails": guardrails,
            "follow_up": None,
        }

    if only_problem_statuses and before_status not in PROBLEM_SALES_STATUSES:
        return {
            "lead_id": str(lead_id),
            "action": "noop",
            "before_status": before_status,
            "after_status": before_status,
            "reason": "Status is already not sales-positive; no reconciliation required.",
            "guardrails": guardrails,
            "follow_up": None,
        }

    _set_lead_status(lead, recommended_status)
    if hasattr(lead, "notes"):
        existing = getattr(lead, "notes", None) or ""
        note = (
            f"Sales status reconciled from '{before_status}' to '{recommended_status}' "
            "because governance guardrails are active."
        )
        setattr(lead, "notes", (existing + "\n" if existing else "") + note)
    session.add(lead)
    session.commit()
    session.refresh(lead)

    follow_up = None
    if create_follow_up:
        follow_up = _create_follow_up(
            session,
            lead_id,
            subject="Compliance review required before next sales step",
            message=_followup_message_for_lead(lead, purpose="blocked"),
            follow_up_type="sales_guardrail_reconciliation",
            due_in_days=0,
        )

    return {
        "lead_id": str(lead_id),
        "action": "reconciled",
        "before_status": before_status,
        "after_status": _lead_status_text(lead),
        "recommended_status": recommended_status,
        "guardrails": guardrails,
        "follow_up": _serialize(follow_up) if follow_up else None,
    }

def _get_lead_or_404(session: Session, lead_id: UUID) -> Lead:
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/api/v1/sales/pipeline")
def get_sales_pipeline(session: Session = Depends(get_session)) -> dict[str, Any]:
    leads = session.exec(select(Lead)).all()
    items = [_pipeline_item(session, lead) for lead in leads]
    stage_counts: dict[str, int] = {}
    for item in items:
        stage_counts[item["stage"]] = stage_counts.get(item["stage"], 0) + 1
    return {
        "total_leads": len(items),
        "stage_counts": stage_counts,
        "items": items,
    }




@router.get("/api/v1/sales/inconsistencies")
def list_sales_status_inconsistencies(session: Session = Depends(get_session)) -> dict[str, Any]:
    leads = session.exec(select(Lead)).all()
    items = [_pipeline_item(session, lead) for lead in leads]
    inconsistent = [item for item in items if item.get("status_integrity", {}).get("is_inconsistent")]
    return {
        "count": len(inconsistent),
        "items": inconsistent,
    }


@router.post("/api/v1/sales/leads/{lead_id}/reconcile")
def reconcile_one_sales_lead(
    lead_id: UUID,
    payload: SalesReconcileRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    payload = payload or SalesReconcileRequest()
    lead = _get_lead_or_404(session, lead_id)
    result = _reconcile_lead_status(
        session,
        lead,
        create_follow_up=payload.create_follow_up,
        only_problem_statuses=payload.only_problem_statuses,
    )
    return {
        "status": result["action"],
        "result": result,
        "pipeline_item": _pipeline_item(session, lead),
    }


@router.post("/api/v1/sales/reconcile")
def reconcile_sales_pipeline_statuses(
    payload: SalesReconcileRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    payload = payload or SalesReconcileRequest()
    leads = session.exec(select(Lead)).all()
    results = [
        _reconcile_lead_status(
            session,
            lead,
            create_follow_up=payload.create_follow_up,
            only_problem_statuses=payload.only_problem_statuses,
        )
        for lead in leads
    ]
    changed = [result for result in results if result.get("action") == "reconciled"]
    return {
        "status": "completed",
        "checked": len(results),
        "reconciled": len(changed),
        "results": results,
    }


@router.post("/admin/sales/reconcile", include_in_schema=False)
def admin_reconcile_sales_statuses(session: Session = Depends(get_session)) -> RedirectResponse:
    reconcile_sales_pipeline_statuses(SalesReconcileRequest(), session)
    return RedirectResponse(url="/admin/sales", status_code=303)

@router.get("/api/v1/sales/follow-ups")
def list_sales_follow_ups(
    status: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    follow_ups = session.exec(select(FollowUp)).all()
    if status:
        follow_ups = [fu for fu in follow_ups if _followup_status(fu) == status.lower()]
    return {
        "count": len(follow_ups),
        "items": [_serialize(fu) for fu in follow_ups],
    }


@router.post("/api/v1/sales/leads/{lead_id}/follow-ups")
def create_sales_follow_up(
    lead_id: UUID,
    payload: SalesFollowUpCreate | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    payload = payload or SalesFollowUpCreate()
    lead = _get_lead_or_404(session, lead_id)
    guardrails = _sales_guardrails(session, lead_id)
    message = payload.message or _followup_message_for_lead(
        lead,
        purpose="blocked" if guardrails["hard_blockers"] else "sales",
    )
    follow_up = _create_follow_up(
        session,
        lead_id,
        channel=payload.channel,
        subject=payload.subject or "Next steps for your global mobility profile",
        message=message,
        priority=payload.priority,
        follow_up_type=payload.follow_up_type,
        due_in_days=payload.due_in_days,
    )
    return {
        "status": "created",
        "lead_id": str(lead_id),
        "guardrails": guardrails,
        "follow_up": _serialize(follow_up),
    }


@router.post("/api/v1/sales/leads/{lead_id}/qualify")
def qualify_lead(
    lead_id: UUID,
    payload: SalesQualificationRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    payload = payload or SalesQualificationRequest()
    lead = _get_lead_or_404(session, lead_id)
    _raise_if_sales_blocked(session, lead_id, "qualify")

    _set_lead_status(lead, payload.qualification_status)
    if payload.notes and hasattr(lead, "notes"):
        existing = getattr(lead, "notes", None) or ""
        setattr(lead, "notes", (existing + "\n" if existing else "") + payload.notes)
    session.add(lead)
    session.commit()
    session.refresh(lead)

    follow_up = None
    if payload.create_follow_up:
        follow_up = _create_follow_up(
            session,
            lead_id,
            subject="Profile qualified - next steps",
            message=_followup_message_for_lead(lead, purpose="qualified"),
            follow_up_type="sales_qualification",
            due_in_days=payload.follow_up_due_in_days,
        )

    return {
        "status": "qualified",
        "lead": _serialize(lead),
        "guardrails": _sales_guardrails(session, lead_id),
        "follow_up": _serialize(follow_up) if follow_up else None,
    }


@router.post("/api/v1/sales/leads/{lead_id}/convert")
def convert_lead(
    lead_id: UUID,
    payload: ConversionRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    payload = payload or ConversionRequest()
    lead = _get_lead_or_404(session, lead_id)
    _raise_if_sales_blocked(
        session,
        lead_id,
        "convert",
        require_documents_ready=payload.require_documents_ready,
    )

    _set_lead_status(lead, "converted")
    if payload.notes and hasattr(lead, "notes"):
        existing = getattr(lead, "notes", None) or ""
        setattr(lead, "notes", (existing + "\n" if existing else "") + payload.notes)
    session.add(lead)
    session.commit()
    session.refresh(lead)

    follow_up = None
    if payload.create_onboarding_follow_up:
        follow_up = _create_follow_up(
            session,
            lead_id,
            subject="Client onboarding started",
            message=_followup_message_for_lead(lead, purpose="converted"),
            follow_up_type="onboarding",
            due_in_days=0,
        )

    return {
        "status": "converted",
        "lead": _serialize(lead),
        "guardrails": _sales_guardrails(session, lead_id),
        "follow_up": _serialize(follow_up) if follow_up else None,
    }


@router.post("/api/v1/sales/follow-ups/{follow_up_id}/complete")
def complete_sales_follow_up(
    follow_up_id: UUID,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    follow_up = session.get(FollowUp, follow_up_id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    fields = _model_fields(FollowUp)
    if "status" in fields:
        setattr(follow_up, "status", "completed")
    if "completed_at" in fields:
        setattr(follow_up, "completed_at", _now())
    if "updated_at" in fields:
        setattr(follow_up, "updated_at", _now())
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return {
        "status": "completed",
        "follow_up": _serialize(follow_up),
    }


@router.get("/admin/sales", include_in_schema=False)
def admin_sales_page(session: Session = Depends(get_session)) -> str:
    pipeline = get_sales_pipeline(session)
    rows = []
    for item in pipeline["items"]:
        lead = item["lead"]
        lead_id = lead.get("id")
        guardrails = item.get("guardrails", {})
        blocked = bool(guardrails.get("hard_blockers"))
        integrity = item.get("status_integrity", {})
        blocker_text = ", ".join(guardrails.get("hard_blockers", [])) or "None"
        status_integrity_text = "MISMATCH" if integrity.get("is_inconsistent") else "OK"
        recommended_text = integrity.get("recommended_status") or "-"
        disabled = "disabled title='Blocked by Truth Engine/Human Review guardrails'" if blocked else ""
        rows.append(
            "<tr>"
            f"<td><a href='/admin/leads/{lead_id}'>{lead.get('full_name', 'Unknown')}</a></td>"
            f"<td>{lead.get('email') or ''}</td>"
            f"<td>{lead.get('intent') or ''}</td>"
            f"<td>{lead.get('target_country') or ''}</td>"
            f"<td><strong>{item['stage']}</strong></td>"
            f"<td>{status_integrity_text}<br><small>Recommended: {recommended_text}</small></td>"
            f"<td>{item['next_action']}<br><small>Blockers: {blocker_text}</small></td>"
            f"<td>"
            f"<form method='post' action='/api/v1/sales/leads/{lead_id}/qualify' style='display:inline'><button {disabled}>Qualify</button></form> "
            f"<form method='post' action='/api/v1/sales/leads/{lead_id}/convert' style='display:inline'><button {disabled}>Convert</button></form> "
            f"<form method='post' action='/api/v1/sales/leads/{lead_id}/follow-ups' style='display:inline'><button>Create Follow-up</button></form>"
            f"</td>"
            "</tr>"
        )

    stage_cards = "".join(
        f"<div class='card'><h3>{stage}</h3><p>{count}</p></div>"
        for stage, count in sorted(pipeline["stage_counts"].items())
    )

    return f"""
    <!doctype html>
    <html>
    <head>
      <title>Sales Pipeline - Global Mobility AIOS</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f7f8; }}
        a {{ color: #164ea6; text-decoration: none; }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
        th {{ background: #111827; color: white; }}
        button {{ padding: 6px 10px; margin: 2px; cursor: pointer; }}
        button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }}
        .card {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 12px 16px; min-width: 180px; }}
        .card h3 {{ margin: 0 0 8px 0; font-size: 14px; }}
        .card p {{ margin: 0; font-size: 24px; font-weight: bold; }}
        .warning {{ background: #fff7ed; border: 1px solid #fed7aa; padding: 12px; border-radius: 8px; }}
      </style>
    </head>
    <body>
      <h1>Sales Pipeline</h1>
      <p><a href='/admin'>← Back to Admin Dashboard</a> | <a href='/api/v1/sales/pipeline'>Raw Pipeline JSON</a></p>
      <div class='warning'><strong>Governance:</strong> Qualification and conversion are blocked when a lead has rejected truth claims or unresolved human-review items.</div>
      <form method='post' action='/admin/sales/reconcile' style='margin: 12px 0'>
        <button>Reconcile blocked sales statuses</button>
        <small>Use after guardrail changes or imported legacy data.</small>
      </form>
      <div class='cards'>{stage_cards}</div>
      <table>
        <thead>
          <tr>
            <th>Lead</th><th>Email</th><th>Intent</th><th>Country</th><th>Stage</th><th>Status Integrity</th><th>Next Action</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </body>
    </html>
    """


@router.get("/debug/sales-engine", include_in_schema=False)
def debug_sales_engine() -> dict[str, Any]:
    return {
        "module": "sales_engine",
        "version": "1.2",
        "guardrails": [
            "qualification blocked by rejected truth claim",
            "qualification blocked by pending human review",
            "conversion blocked by rejected truth claim",
            "conversion blocked by pending human review",
            "optional conversion block for missing/problem documents",
        ],
        "routes": [
            "GET /api/v1/sales/pipeline",
            "GET /api/v1/sales/follow-ups",
            "GET /api/v1/sales/inconsistencies",
            "POST /api/v1/sales/leads/{lead_id}/reconcile",
            "POST /api/v1/sales/reconcile",
            "POST /admin/sales/reconcile",
            "POST /api/v1/sales/leads/{lead_id}/follow-ups",
            "POST /api/v1/sales/leads/{lead_id}/qualify",
            "POST /api/v1/sales/leads/{lead_id}/convert",
            "POST /api/v1/sales/follow-ups/{follow_up_id}/complete",
            "GET /admin/sales",
        ],
    }
