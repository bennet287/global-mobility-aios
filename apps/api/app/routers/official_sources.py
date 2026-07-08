from __future__ import annotations

import html
import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import CountryPolicy, OfficialSource, SourceCheckRun
from app.services.official_sources import list_sources, seed_official_sources


router = APIRouter(tags=["official-source-truth-v3.4"])


def _json_response(payload: Dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload))


def _safe(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _parse_json(value: Any) -> Any:
    if not value:
        return None
    try:
        return json.loads(str(value))
    except Exception:
        return value


def _source_payload(source: OfficialSource) -> Dict[str, Any]:
    return {
        "id": source.id,
        "country": source.country,
        "domain": source.domain,
        "name": source.name,
        "url": source.url,
        "source_type": source.source_type,
        "authority": source.authority,
        "active": source.active,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
    }


def _check_run_payload(run: SourceCheckRun) -> Dict[str, Any]:
    return {
        "id": run.id,
        "truth_claim_id": run.truth_claim_id,
        "country": run.country,
        "domain": run.domain,
        "claim": run.claim,
        "verdict": run.verdict,
        "confidence": run.confidence,
        "evidence_count": run.evidence_count,
        "matched_sources": _parse_json(run.matched_sources_json) or [],
        "corrected_statement": run.corrected_statement,
        "created_at": run.created_at,
    }


@router.post("/api/v1/official-sources/seed")
def seed_sources(session: Session = Depends(get_session)):
    summary = seed_official_sources(session)
    return _json_response(summary)


@router.get("/api/v1/official-sources")
def api_list_sources(
    country: Optional[str] = None,
    domain: Optional[str] = None,
    session: Session = Depends(get_session),
):
    sources = list_sources(session, country=country, domain=domain)
    return _json_response({
        "total": len(sources),
        "sources": [_source_payload(source) for source in sources],
    })


@router.get("/api/v1/official-sources/check-runs")
def api_list_check_runs(limit: int = 50, session: Session = Depends(get_session)):
    runs = session.exec(select(SourceCheckRun).order_by(SourceCheckRun.created_at.desc()).limit(limit)).all()
    return _json_response({
        "total_returned": len(runs),
        "check_runs": [_check_run_payload(run) for run in runs],
    })


@router.get("/api/v1/official-sources/policies")
def api_list_policies(session: Session = Depends(get_session)):
    policies = session.exec(select(CountryPolicy).order_by(CountryPolicy.country, CountryPolicy.domain)).all()
    return _json_response({
        "total": len(policies),
        "policies": [
            {
                "id": policy.id,
                "country": policy.country,
                "domain": policy.domain,
                "policy": _parse_json(policy.policy_json) or {},
                "status": policy.status,
                "last_reviewed_at": policy.last_reviewed_at,
            }
            for policy in policies
        ],
    })


@router.get("/admin/official-sources", response_class=HTMLResponse)
def admin_official_sources(session: Session = Depends(get_session)) -> HTMLResponse:
    sources = session.exec(select(OfficialSource).order_by(OfficialSource.country, OfficialSource.domain, OfficialSource.name)).all()
    runs = session.exec(select(SourceCheckRun).order_by(SourceCheckRun.created_at.desc()).limit(10)).all()
    rows = "".join(
        f"""
        <tr>
          <td>{_safe(source.country)}</td>
          <td>{_safe(source.domain)}</td>
          <td>{_safe(source.name)}</td>
          <td><a href="{_safe(source.url)}">{_safe(source.url)}</a></td>
          <td>{_safe(source.source_type)}</td>
        </tr>
        """
        for source in sources
    )
    run_rows = "".join(
        f"""
        <tr>
          <td>{_safe(run.created_at)}</td>
          <td>{_safe(run.country)}</td>
          <td>{_safe(run.domain)}</td>
          <td>{_safe(run.verdict)}</td>
          <td>{_safe(run.evidence_count)}</td>
        </tr>
        """
        for run in runs
    )
    return HTMLResponse(f"""
    <!doctype html>
    <html>
      <head>
        <title>Official Sources v3.4</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
          table {{ border-collapse: collapse; width: 100%; background: white; margin: 16px 0; }}
          th, td {{ border: 1px solid #e2e8f0; padding: 8px; vertical-align: top; font-size: 14px; }}
          th {{ background: #eef2f7; }}
          button {{ padding: 6px 10px; }}
          .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0; }}
          .nav a {{ margin-right: 12px; }}
        </style>
      </head>
      <body>
        <div class="nav">
          <a href="/admin/v2">Admin v2</a>
          <a href="/admin/truth-resolution">Truth Resolution</a>
          <a href="/admin/audit-logs">Audit Logs</a>
          <a href="/debug/official-sources">Debug</a>
        </div>
        <h1>Official Sources v3.4</h1>
        <div class="card">
          <form method="post" action="/api/v1/official-sources/seed">
            <button type="submit">Seed Official Sources</button>
          </form>
          <p>Sources: {len(sources)} | Recent source checks: {len(runs)}</p>
        </div>
        <h2>Sources</h2>
        <table><thead><tr><th>Country</th><th>Domain</th><th>Name</th><th>URL</th><th>Type</th></tr></thead><tbody>{rows}</tbody></table>
        <h2>Recent Source Checks</h2>
        <table><thead><tr><th>Created</th><th>Country</th><th>Domain</th><th>Verdict</th><th>Evidence</th></tr></thead><tbody>{run_rows}</tbody></table>
      </body>
    </html>
    """)


@router.get("/debug/official-sources")
def debug_official_sources():
    return {
        "status": "ok",
        "version": "v3.4",
        "models": ["OfficialSource", "SourceSnapshot", "SourceCheckRun", "VerifiedRule", "CountryPolicy"],
        "routes": [
            "POST /api/v1/official-sources/seed",
            "GET /api/v1/official-sources",
            "GET /api/v1/official-sources/check-runs",
            "GET /api/v1/official-sources/policies",
            "GET /admin/official-sources",
        ],
    }
