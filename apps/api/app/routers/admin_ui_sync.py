from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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


router = APIRouter(tags=["admin-ui-sync-v2"])


ACTIVE_APPLICATION_STATUSES = {
    "draft",
    "approved",
    "submitted",
    "decision_pending",
    "approved_by_authority",
    "rejected_by_authority",
    "withdrawn",
}
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
DOCUMENT_PROBLEM_STATUSES = {"missing", "needs_review", "rejected", "expired"}
DOCUMENT_OK_STATUSES = {"received", "verified"}
TRUTH_REJECTED = {"rejected", "REJECTED"}
TRUTH_REVIEW = {"needs_review", "NEEDS_REVIEW"}


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


def _lead_id(lead: Lead) -> Any:
    return getattr(lead, "id", None)


def _same_lead(obj: Any, lead_id: Any) -> bool:
    return _normal_id(getattr(obj, "lead_id", None)) == _normal_id(lead_id)


def _records_for_lead(session: Session, model: Any, lead: Lead) -> List[Any]:
    rows = session.exec(select(model)).all()
    return [row for row in rows if _same_lead(row, _lead_id(lead))]


def _documents_for_lead(session: Session, lead: Lead) -> List[DocumentRecord]:
    return _records_for_lead(session, DocumentRecord, lead)


def _truth_claims_for_lead(session: Session, lead: Lead) -> List[TruthClaim]:
    return _records_for_lead(session, TruthClaim, lead)


def _reviews_for_lead(session: Session, lead: Lead) -> List[HumanReview]:
    return _records_for_lead(session, HumanReview, lead)


def _applications_for_lead(session: Session, lead: Lead) -> List[ApplicationRecord]:
    return _records_for_lead(session, ApplicationRecord, lead)


def _followups_for_lead(session: Session, lead: Lead) -> List[FollowUp]:
    return _records_for_lead(session, FollowUp, lead)


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
        "all_verified": False,
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
    return counts


def _truth_summary(claims: List[TruthClaim], reviews: List[HumanReview]) -> Dict[str, Any]:
    rejected = []
    needs_review = []
    for claim in claims:
        verdict = str(_value(getattr(claim, "verdict", "")) or "")
        status = _safe_status(verdict)
        if verdict in TRUTH_REJECTED or status in TRUTH_REJECTED:
            rejected.append(claim)
        if status in {"needs_review"} or bool(getattr(claim, "requires_human_review", False)):
            needs_review.append(claim)

    pending_reviews = [
        review for review in reviews
        if _safe_status(getattr(review, "status", None)) == "pending"
    ]

    return {
        "truth_claims": len(claims),
        "rejected_truth_claims": len(rejected),
        "truth_claims_needing_review": len(needs_review),
        "pending_reviews": len(pending_reviews),
        "truth_clear": len(rejected) == 0 and len(needs_review) == 0 and len(pending_reviews) == 0,
    }


def _application_summary(apps: List[ApplicationRecord]) -> Dict[str, Any]:
    status_counts: Dict[str, int] = {}
    for app in apps:
        status = _safe_status(getattr(app, "status", None)) or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    active = [
        app for app in apps
        if _safe_status(getattr(app, "status", None)) in ACTIVE_APPLICATION_STATUSES
    ]
    post_submission = [
        app for app in apps
        if _safe_status(getattr(app, "status", None)) in POST_SUBMISSION_STATUSES
    ]
    final = [
        app for app in apps
        if _safe_status(getattr(app, "status", None)) in FINAL_AUTHORITY_STATUSES
    ]
    latest = sorted(apps, key=lambda a: str(getattr(a, "created_at", "") or ""))[-1] if apps else None

    return {
        "applications": len(apps),
        "active_applications": len(active),
        "post_submission_applications": len(post_submission),
        "final_authority_applications": len(final),
        "status_counts": status_counts,
        "latest_application": _to_dict(latest) if latest else None,
        "latest_status": _safe_status(getattr(latest, "status", None)) if latest else "no_application",
        "can_create_draft": len(active) == 0,
    }


def _readiness_stage(truth: Dict[str, Any], docs: Dict[str, Any]) -> str:
    if truth["rejected_truth_claims"] > 0 or truth["truth_claims_needing_review"] > 0 or truth["pending_reviews"] > 0:
        return "blocked_truth_rejected"
    if docs["total"] == 0:
        return "no_document_checklist"
    if docs["problem_documents"] > 0:
        return "documents_incomplete"
    return "ready_for_human_approval"


def _lead_sync_payload(session: Session, lead: Lead) -> Dict[str, Any]:
    docs = _documents_for_lead(session, lead)
    claims = _truth_claims_for_lead(session, lead)
    reviews = _reviews_for_lead(session, lead)
    apps = _applications_for_lead(session, lead)
    followups = _followups_for_lead(session, lead)

    doc_summary = _document_summary(docs)
    truth = _truth_summary(claims, reviews)
    app_summary = _application_summary(apps)
    readiness = _readiness_stage(truth, doc_summary)
    pending_followups = [
        fu for fu in followups
        if _safe_status(getattr(fu, "status", None)) == "pending"
    ]

    lifecycle_stage = app_summary["latest_status"]
    authority_stage = lifecycle_stage if lifecycle_stage in POST_SUBMISSION_STATUSES else "-"

    return {
        "lead": _to_dict(lead),
        "readiness_stage": readiness,
        "lifecycle_stage": lifecycle_stage,
        "authority_stage": authority_stage,
        "documents": doc_summary,
        "truth": truth,
        "applications": app_summary,
        "followups": {
            "total": len(followups),
            "pending": len(pending_followups),
        },
        "can_create_draft": app_summary["can_create_draft"],
        "next_action": _next_action(readiness, lifecycle_stage, authority_stage, doc_summary, truth, app_summary),
    }


def _next_action(
    readiness: str,
    lifecycle_stage: str,
    authority_stage: str,
    docs: Dict[str, Any],
    truth: Dict[str, Any],
    apps: Dict[str, Any],
) -> str:
    if truth["rejected_truth_claims"] > 0 or truth["truth_claims_needing_review"] > 0:
        return "Resolve or replace risky truth claims."
    if truth["pending_reviews"] > 0:
        return "Close pending human reviews."
    if docs["total"] == 0:
        return "Generate the document checklist."
    if docs["problem_documents"] > 0:
        return "Receive and verify missing/problematic documents."
    if lifecycle_stage == "no_application":
        return "Create a controlled application draft."
    if lifecycle_stage == "draft":
        return "Human reviewer can approve the draft."
    if lifecycle_stage == "approved":
        return "Submit the approved application."
    if lifecycle_stage == "submitted":
        return "Move to decision pending or record final authority decision."
    if lifecycle_stage == "decision_pending":
        return "Record final authority decision."
    if lifecycle_stage == "approved_by_authority":
        return "Start post-approval onboarding."
    if lifecycle_stage == "rejected_by_authority":
        return "Record rejection reason and prepare reapplication/appeal workflow."
    if lifecycle_stage == "withdrawn":
        return "Stop active processing and preserve audit history."
    if lifecycle_stage == "cancelled":
        return "No active application exists. Create a new controlled draft if needed."
    return "Review lead state."


def _badge(text: Any, kind: str = "neutral") -> str:
    value = str(text)
    return f'<span class="badge {kind}">{value}</span>'


def _stage_kind(stage: str) -> str:
    if stage in {"ready_for_human_approval", "approved_by_authority", "converted"}:
        return "good"
    if stage in {"documents_incomplete", "decision_pending", "submitted", "draft", "approved"}:
        return "warn"
    if stage in {"blocked_truth_rejected", "rejected_by_authority", "withdrawn"}:
        return "bad"
    return "neutral"


def _safe_text(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def _render_create_draft_action(item: Dict[str, Any]) -> str:
    lead = item["lead"]
    lead_id = lead.get("id")
    if item["can_create_draft"] and item["readiness_stage"] == "ready_for_human_approval":
        return f"""
        <form method="post" action="/api/v1/applications/leads/{lead_id}/controlled-draft" style="display:inline">
          <button type="submit">Create Controlled Draft</button>
        </form>
        """
    if item["readiness_stage"] != "ready_for_human_approval":
        return '<button disabled title="Draft blocked until truth and document readiness are clear">Draft Blocked: Not Ready</button>'
    return '<button disabled title="Draft blocked because active/final application already exists">Draft Blocked</button>'


def _render_row(item: Dict[str, Any]) -> str:
    lead = item["lead"]
    lead_id = lead.get("id")
    docs = item["documents"]
    truth = item["truth"]
    apps = item["applications"]
    doc_label = f"{docs['verified']}/{docs['total']} verified"
    truth_label = "clear" if truth["truth_clear"] else f"{truth['rejected_truth_claims']} rejected / {truth['pending_reviews']} pending"
    app_label = f"{apps['latest_status']} ({apps['applications']} total)"

    return f"""
    <tr>
      <td><a href="/admin/v2/leads/{lead_id}">{_safe_text(lead.get('full_name'))}</a><br><small>{lead_id}</small></td>
      <td>{_badge(lead.get('status'), _stage_kind(_safe_status(lead.get('status'))))}</td>
      <td>{_safe_text(lead.get('intent'))}<br>{_safe_text(lead.get('target_country'))}</td>
      <td>{_badge(item['readiness_stage'], _stage_kind(item['readiness_stage']))}</td>
      <td>{_badge(item['lifecycle_stage'], _stage_kind(item['lifecycle_stage']))}</td>
      <td>{_badge(item['authority_stage'], _stage_kind(item['authority_stage']))}</td>
      <td>{_badge(doc_label, "good" if docs['problem_documents'] == 0 and docs['total'] > 0 else "warn")}</td>
      <td>{_badge(truth_label, "good" if truth["truth_clear"] else "bad")}</td>
      <td>{_badge(app_label, _stage_kind(apps['latest_status']))}</td>
      <td>{_safe_text(item['next_action'])}</td>
      <td>
        {_render_create_draft_action(item)}
        <br>
        <a href="/admin/leads/{lead_id}">Old Detail</a> |
        <a href="/admin/document-verification/leads/{lead_id}">Docs</a> |
        <a href="/api/v1/applications/leads/{lead_id}/lifecycle">Lifecycle JSON</a>
      </td>
    </tr>
    """


def _page_shell(title: str, body: str) -> HTMLResponse:
    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>{title}</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
          h1, h2 {{ margin-top: 0; }}
          .nav a {{ margin-right: 12px; }}
          .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 16px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
          table {{ border-collapse: collapse; width: 100%; background: white; }}
          th, td {{ border: 1px solid #e2e8f0; padding: 8px; vertical-align: top; font-size: 14px; }}
          th {{ background: #eef2f7; }}
          small {{ color: #64748b; }}
          button {{ padding: 6px 10px; border: 1px solid #94a3b8; border-radius: 6px; background: #f8fafc; cursor: pointer; }}
          button:disabled {{ color: #94a3b8; cursor: not-allowed; background: #e2e8f0; }}
          .badge {{ display: inline-block; padding: 2px 7px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
          .good {{ background: #dcfce7; color: #166534; }}
          .warn {{ background: #fef9c3; color: #854d0e; }}
          .bad {{ background: #fee2e2; color: #991b1b; }}
          .neutral {{ background: #e2e8f0; color: #334155; }}
          pre {{ background: #020617; color: #e2e8f0; padding: 12px; overflow-x: auto; border-radius: 8px; }}
        </style>
      </head>
      <body>
        <div class="nav">
          <a href="/admin">Old Admin</a>
          <a href="/admin/v2">Admin v2</a>
          <a href="/admin/applications">Applications</a>
          <a href="/admin/application-lifecycle">Lifecycle</a>
          <a href="/admin/authority-decision">Authority</a>
          <a href="/admin/application-draft-control">Draft Control</a>
          <a href="/admin/document-verification">Document Verification</a>
          <a href="/admin/document-uploads">Document Uploads</a>
          <a href="/admin/truth-resolution">Truth Resolution</a>
          <a href="/admin/official-sources">Official Sources</a>
          <a href="/admin/sales">Sales</a>
          <a href="/admin/post-approval-onboarding">Onboarding</a>
          <a href="/admin/client-communications">Client Comms</a>
          <a href="/admin/controlled-agents">Agent Console</a>
          <a href="/admin/agent-output-reviews">Agent Review Queue</a>
          <a href="/admin/audit-logs">Audit Logs</a>
          <a href="/admin/auth">Auth</a>
          <a href="/debug/admin-ui-sync">Debug</a>
        </div>
        {body}
      </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/api/v1/admin-ui-sync/summary")
def admin_ui_sync_summary(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    items = [_lead_sync_payload(session, lead) for lead in leads]

    readiness_counts: Dict[str, int] = {}
    lifecycle_counts: Dict[str, int] = {}
    authority_counts: Dict[str, int] = {}

    for item in items:
        readiness_counts[item["readiness_stage"]] = readiness_counts.get(item["readiness_stage"], 0) + 1
        lifecycle_counts[item["lifecycle_stage"]] = lifecycle_counts.get(item["lifecycle_stage"], 0) + 1
        authority_counts[item["authority_stage"]] = authority_counts.get(item["authority_stage"], 0) + 1

    return _json_response({
        "total_leads": len(items),
        "readiness_counts": readiness_counts,
        "lifecycle_counts": lifecycle_counts,
        "authority_counts": authority_counts,
        "items": items,
    })


@router.get("/api/v1/admin-ui-sync/leads/{lead_id}")
def admin_ui_sync_lead_detail(lead_id: str, session: Session = Depends(get_session)):
    lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _json_response(_lead_sync_payload(session, lead))


@router.get("/admin/v2", response_class=HTMLResponse)
def admin_v2(session: Session = Depends(get_session)):
    leads = session.exec(select(Lead)).all()
    items = [_lead_sync_payload(session, lead) for lead in leads]

    readiness_counts: Dict[str, int] = {}
    lifecycle_counts: Dict[str, int] = {}
    authority_counts: Dict[str, int] = {}
    for item in items:
        readiness_counts[item["readiness_stage"]] = readiness_counts.get(item["readiness_stage"], 0) + 1
        lifecycle_counts[item["lifecycle_stage"]] = lifecycle_counts.get(item["lifecycle_stage"], 0) + 1
        authority_counts[item["authority_stage"]] = authority_counts.get(item["authority_stage"], 0) + 1

    rows = "".join(_render_row(item) for item in items)
    body = f"""
      <h1>Global Mobility AIOS Admin v2.0</h1>
      <div class="card">
        <h2>Synced Operations Snapshot</h2>
        <p><strong>Total leads:</strong> {len(items)}</p>
        <p><strong>Readiness:</strong> {readiness_counts}</p>
        <p><strong>Lifecycle:</strong> {lifecycle_counts}</p>
        <p><strong>Authority:</strong> {authority_counts}</p>
      </div>
      <div class="card">
        <h2>Demo Quick Links v4.4</h2>
        <p>
          <a href="/admin/controlled-agents">Agent Console</a> |
          <a href="/admin/agent-output-reviews">Agent Review Dashboard</a> |
          <a href="/admin/client-communications">Client Communications</a> |
          <a href="/admin/document-uploads">Document Uploads</a> |
          <a href="/admin/audit-logs">Audit Trail</a>
        </p>
        <p><small>Seed demo data with <code>python scripts/seed_demo_data.py --reset-all --yes</code>, then run <code>python scripts/check_demo_readiness.py</code>.</small></p>
      </div>
      <div class="card">
        <h2>Lead Operations</h2>
        <table>
          <thead>
            <tr>
              <th>Lead</th>
              <th>Lead Status</th>
              <th>Intent / Country</th>
              <th>Readiness</th>
              <th>Lifecycle</th>
              <th>Authority</th>
              <th>Documents</th>
              <th>Truth</th>
              <th>Applications</th>
              <th>Next Action</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    """
    return _page_shell("Global Mobility AIOS Admin v2.0", body)


@router.get("/admin/v2/leads/{lead_id}", response_class=HTMLResponse)
def admin_v2_lead_detail(lead_id: str, session: Session = Depends(get_session)):
    lead = session.get(Lead, _uuid_or_404(lead_id, "lead_id"))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    item = _lead_sync_payload(session, lead)
    lead_data = item["lead"]
    docs = _documents_for_lead(session, lead)
    claims = _truth_claims_for_lead(session, lead)
    apps = _applications_for_lead(session, lead)
    followups = _followups_for_lead(session, lead)

    body = f"""
      <h1>Lead Operations Detail v2.0</h1>
      <div class="card">
        <h2>{_safe_text(lead_data.get('full_name'))}</h2>
        <p><strong>Email:</strong> {_safe_text(lead_data.get('email'))}</p>
        <p><strong>Status:</strong> {_badge(lead_data.get('status'), _stage_kind(_safe_status(lead_data.get('status'))))}</p>
        <p><strong>Readiness:</strong> {_badge(item['readiness_stage'], _stage_kind(item['readiness_stage']))}</p>
        <p><strong>Lifecycle:</strong> {_badge(item['lifecycle_stage'], _stage_kind(item['lifecycle_stage']))}</p>
        <p><strong>Authority:</strong> {_badge(item['authority_stage'], _stage_kind(item['authority_stage']))}</p>
        <p><strong>Next action:</strong> {item['next_action']}</p>
      </div>
      <div class="card">
        <h2>Documents</h2>
        <p>{item['documents']}</p>
        <p><a href="/admin/document-verification/leads/{lead_id}">Open Document Verification</a></p>
      </div>
      <div class="card">
        <h2>Truth</h2>
        <p>{item['truth']}</p>
        <p><a href="/api/v1/leads/{lead_id}/truth-resolution">Open Truth Resolution JSON</a></p>
      </div>
      <div class="card">
        <h2>Applications</h2>
        <p>{item['applications']}</p>
        <p>
          <a href="/api/v1/applications/leads/{lead_id}/lifecycle">Lifecycle JSON</a> |
          <a href="/api/v1/applications/leads/{lead_id}/draft-control">Draft Control JSON</a> |
          <a href="/api/v1/authority-decision/leads/{lead_id}">Authority JSON</a>
        </p>
      </div>
      <div class="card">
        <h2>Raw Synced Payload</h2>
        <pre>{jsonable_encoder(item)}</pre>
      </div>
    """
    return _page_shell("Lead Operations Detail v2.0", body)


@router.get("/admin/sync", response_class=HTMLResponse)
def admin_sync_redirect():
    return RedirectResponse(url="/admin/v2", status_code=303)


@router.get("/debug/admin-ui-sync")
def debug_admin_ui_sync():
    return {
        "status": "ok",
        "version": "v2.0",
        "routes": [
            "GET /admin/v2",
            "GET /admin/v2/leads/{lead_id}",
            "GET /admin/sync",
            "GET /api/v1/admin-ui-sync/summary",
            "GET /api/v1/admin-ui-sync/leads/{lead_id}",
            "GET /debug/admin-ui-sync",
        ],
        "design_note": "Admin UI v2.0 shows readiness, lifecycle, authority, document, truth, and draft-control states in one synced operations dashboard.",
    }
