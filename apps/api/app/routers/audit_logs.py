from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import AuditLog


router = APIRouter(tags=["audit-log"])


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _safe_text(value: Any) -> str:
    if value is None:
        return "-"
    return str(_value(value))


def _json_safe(value: Any) -> Any:
    value = _value(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _json_load(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def _to_dict(log: AuditLog, include_states: bool = True) -> Dict[str, Any]:
    payload = {
        "id": _json_safe(getattr(log, "id", None)),
        "actor": getattr(log, "actor", None),
        "action": getattr(log, "action", None),
        "entity_type": getattr(log, "entity_type", None),
        "entity_id": getattr(log, "entity_id", None),
        "reason": getattr(log, "reason", None),
        "source": getattr(log, "source", None),
        "created_at": _json_safe(getattr(log, "created_at", None)),
    }
    if include_states:
        payload["before_state"] = _json_load(getattr(log, "before_state_json", None))
        payload["after_state"] = _json_load(getattr(log, "after_state_json", None))
    return payload


def _json_response(payload: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload))


def _filtered_logs(
    session: Session,
    *,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
) -> list[AuditLog]:
    logs = session.exec(select(AuditLog)).all()
    if action:
        logs = [log for log in logs if str(getattr(log, "action", "") or "") == action]
    if entity_type:
        logs = [log for log in logs if str(getattr(log, "entity_type", "") or "") == entity_type]
    if entity_id:
        logs = [log for log in logs if str(getattr(log, "entity_id", "") or "") == entity_id]
    logs = sorted(logs, key=lambda log: str(getattr(log, "created_at", "") or ""), reverse=True)
    return logs[: max(1, min(limit, 500))]


@router.get("/api/v1/audit-logs")
def get_audit_logs(
    action: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100),
    include_states: bool = Query(default=False),
    session: Session = Depends(get_session),
):
    logs = _filtered_logs(
        session,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
    action_counts: Dict[str, int] = {}
    for log in session.exec(select(AuditLog)).all():
        key = str(getattr(log, "action", "") or "unknown")
        action_counts[key] = action_counts.get(key, 0) + 1
    return _json_response({
        "total_returned": len(logs),
        "action_counts": action_counts,
        "logs": [_to_dict(log, include_states=include_states) for log in logs],
    })


@router.get("/api/v1/audit-logs/{audit_log_id}")
def get_audit_log_detail(audit_log_id: str, session: Session = Depends(get_session)):
    try:
        log_id = uuid.UUID(str(audit_log_id))
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Invalid audit_log_id") from exc
    log = session.get(AuditLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return _json_response(_to_dict(log, include_states=True))


@router.get("/admin/audit-logs", response_class=HTMLResponse)
def audit_logs_admin(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    session: Session = Depends(get_session),
):
    logs = _filtered_logs(session, action=action, entity_type=entity_type, entity_id=entity_id, limit=200)
    rows = []
    for log in logs:
        log_id = _safe_text(getattr(log, "id", None))
        rows.append(
            f"""
            <tr>
              <td>{_safe_text(getattr(log, 'created_at', None))}</td>
              <td>{_safe_text(getattr(log, 'action', None))}</td>
              <td>{_safe_text(getattr(log, 'entity_type', None))}</td>
              <td>{_safe_text(getattr(log, 'entity_id', None))}</td>
              <td>{_safe_text(getattr(log, 'actor', None))}</td>
              <td>{_safe_text(getattr(log, 'source', None))}</td>
              <td>{_safe_text(getattr(log, 'reason', None))}</td>
              <td><a href="/api/v1/audit-logs/{log_id}">JSON</a></td>
            </tr>
            """
        )
    html = f"""
    <!doctype html>
    <html>
      <head>
        <title>Audit Logs</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
          table {{ border-collapse: collapse; width: 100%; background: white; }}
          th, td {{ border: 1px solid #e2e8f0; padding: 8px; vertical-align: top; font-size: 14px; }}
          th {{ background: #eef2f7; }}
          .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 16px 0; }}
        </style>
      </head>
      <body>
        <h1>Audit Log v2.8</h1>
        <p><a href="/admin/v2">Admin v2</a> | <a href="/debug/audit-logs">Debug</a> | <a href="/api/v1/audit-logs">JSON</a></p>
        <div class="card">
          <strong>Total shown:</strong> {len(logs)}
          <br><strong>Filters:</strong> action={_safe_text(action)}, entity_type={_safe_text(entity_type)}, entity_id={_safe_text(entity_id)}
        </div>
        <table>
          <thead><tr><th>Created</th><th>Action</th><th>Entity</th><th>Entity ID</th><th>Actor</th><th>Source</th><th>Reason</th><th>Detail</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/debug/audit-logs")
def debug_audit_logs():
    return {
        "status": "ok",
        "version": "v2.8",
        "routes": [
            "GET /api/v1/audit-logs",
            "GET /api/v1/audit-logs/{audit_log_id}",
            "GET /admin/audit-logs",
            "GET /debug/audit-logs",
        ],
        "captured_actions": [
            "truth_claim_resolved",
            "truth_claim_rejected",
            "truth_claim_corrected",
            "human_reviews_closed",
            "document_received",
            "document_verified",
            "document_rejected",
            "documents_bulk_received",
            "documents_bulk_verified",
            "application_drafted",
            "application_approved",
            "application_submitted",
            "application_draft_cancelled",
            "duplicate_application_drafts_cancelled",
            "authority_decision_recorded",
            "onboarding_generated",
            "onboarding_task_completed",
            "client_draft_generated",
            "client_draft_reviewed",
            "client_drafts_reviewed",
        ],
    }
