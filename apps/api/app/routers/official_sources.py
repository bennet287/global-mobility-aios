from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    CountryPolicy,
    Jurisdiction,
    OfficialSource,
    RegulatoryAuthority,
    RegulatoryClassificationProposal,
    RegulatoryChange,
    SourceCheckRun,
    SourceMonitor,
    SourceRetrievalRun,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.schemas import (
    JurisdictionCreate,
    RegulatoryAuthorityCreate,
    RegulatoryClassificationProposalGenerateRequest,
    RegulatoryClassificationProposalReviewRequest,
    RegulatoryChangePublishRequest,
    RegulatoryChangeReviewRequest,
    RegulatoryKnowledgeGraphSyncRequest,
    RegulatorySourceOnboardingRequest,
    SourceMonitorCreate,
    SourceSnapshotCaptureRequest,
    VerifiedRuleRetireRequest,
)
from app.services.official_sources import list_sources, seed_official_sources
from app.services.regulatory_knowledge_graph import knowledge_graph_payload, sync_published_rules
from app.services.regulatory_intelligence import (
    capture_source_snapshot,
    create_or_update_jurisdiction,
    create_or_update_source_monitor,
    create_regulatory_authority,
    generate_classification_proposal,
    onboard_regulatory_source,
    publish_regulatory_change,
    retire_verified_rule,
    review_classification_proposal,
    review_regulatory_change,
)
from app.tasks.source_monitor_tasks import run_source_monitor_task


router = APIRouter(tags=["official-source-truth-v3.4"])


def _json_response(payload: Dict[str, Any], *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(payload), status_code=status_code)


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
        "jurisdiction_id": source.jurisdiction_id,
        "regulatory_authority_id": source.regulatory_authority_id,
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


@router.post("/api/v1/regulatory-intelligence/jurisdictions", status_code=201)
def api_upsert_jurisdiction(payload: JurisdictionCreate, session: Session = Depends(get_session)):
    return _json_response({"jurisdiction": create_or_update_jurisdiction(session, payload)}, status_code=201)


@router.get("/api/v1/regulatory-intelligence/jurisdictions")
def api_list_jurisdictions(active: Optional[bool] = True, session: Session = Depends(get_session)):
    statement = select(Jurisdiction)
    if active is not None:
        statement = statement.where(Jurisdiction.active == active)
    rows = session.exec(statement.order_by(Jurisdiction.name)).all()
    return _json_response({"total": len(rows), "jurisdictions": rows})


@router.post("/api/v1/regulatory-intelligence/authorities", status_code=201)
def api_create_authority(payload: RegulatoryAuthorityCreate, session: Session = Depends(get_session)):
    try:
        authority = create_regulatory_authority(session, payload)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _json_response({"authority": authority}, status_code=201)


@router.get("/api/v1/regulatory-intelligence/authorities")
def api_list_authorities(jurisdiction_id: Optional[UUID] = None, session: Session = Depends(get_session)):
    statement = select(RegulatoryAuthority).where(RegulatoryAuthority.active == True)  # noqa: E712
    if jurisdiction_id:
        statement = statement.where(RegulatoryAuthority.jurisdiction_id == jurisdiction_id)
    rows = session.exec(statement.order_by(RegulatoryAuthority.name)).all()
    return _json_response({"total": len(rows), "authorities": rows})


@router.post("/api/v1/regulatory-intelligence/source-monitors", status_code=201)
def api_create_source_monitor(payload: SourceMonitorCreate, session: Session = Depends(get_session)):
    try:
        monitor = create_or_update_source_monitor(session, payload)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _json_response({"monitor": monitor}, status_code=201)


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _monitor_payload(monitor: SourceMonitor, source: Optional[OfficialSource]) -> Dict[str, Any]:
    checked = _aware(monitor.last_checked_at)
    freshness_limit = timedelta(minutes=max(monitor.schedule_minutes * 2, 1440))
    fresh = checked is not None and now_utc() - checked <= freshness_limit
    return {
        "id": monitor.id,
        "official_source_id": monitor.official_source_id,
        "source_name": source.name if source else None,
        "source_url": source.url if source else None,
        "country": source.country if source else None,
        "domain": source.domain if source else None,
        "schedule_minutes": monitor.schedule_minutes,
        "fetch_method": monitor.fetch_method,
        "allowed_domains": _parse_json(monitor.allowed_domains_json) or [],
        "max_redirects": monitor.max_redirects,
        "parser_profile": monitor.parser_profile,
        "parser_config": _parse_json(monitor.parser_config_json) or {},
        "status": monitor.status,
        "fresh": fresh,
        "last_checked_at": monitor.last_checked_at,
        "next_check_at": monitor.next_check_at,
        "last_http_status": monitor.last_http_status,
        "last_error": monitor.last_error,
        "etag": monitor.etag,
        "last_modified": monitor.last_modified,
    }


def _classification_proposal_payload(proposal: RegulatoryClassificationProposal) -> Dict[str, Any]:
    return {
        **proposal.model_dump(exclude={"evidence_json", "model_metadata_json"}),
        "evidence": _parse_json(proposal.evidence_json) or [],
        "model_metadata": _parse_json(proposal.model_metadata_json) or {},
    }


def _percentage(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 1) if denominator else 0.0


def _coverage_payload(
    jurisdictions: list[Jurisdiction],
    authorities: list[RegulatoryAuthority],
    sources: list[OfficialSource],
    monitors: list[SourceMonitor],
    monitor_rows: list[Dict[str, Any]],
    changes: list[RegulatoryChange],
    rules: list[VerifiedRule],
) -> Dict[str, Any]:
    monitor_by_source = {
        monitor.official_source_id: row
        for monitor, row in zip(monitors, monitor_rows)
    }

    jurisdiction_rows = []
    for jurisdiction in jurisdictions:
        jurisdiction_sources = [source for source in sources if source.jurisdiction_id == jurisdiction.id]
        jurisdiction_authorities = [
            authority for authority in authorities if authority.jurisdiction_id == jurisdiction.id
        ]
        monitored = [source for source in jurisdiction_sources if source.id in monitor_by_source]
        fresh = [source for source in monitored if monitor_by_source[source.id]["fresh"]]
        stale = [source for source in monitored if not monitor_by_source[source.id]["fresh"]]
        jurisdiction_rows.append({
            "id": jurisdiction.id,
            "code": jurisdiction.code,
            "name": jurisdiction.name,
            "region": jurisdiction.region,
            "authorities": len(jurisdiction_authorities),
            "official_sources": len(jurisdiction_sources),
            "monitored_sources": len(monitored),
            "fresh_monitors": len(fresh),
            "stale_monitors": len(stale),
            "pending_changes": sum(
                1 for change in changes
                if change.jurisdiction_id == jurisdiction.id and change.status == "pending_review"
            ),
            "active_rules": sum(
                1 for rule in rules
                if rule.jurisdiction_id == jurisdiction.id and rule.active
            ),
            "domains": sorted({source.domain for source in jurisdiction_sources}),
            "monitoring_coverage_percent": _percentage(len(monitored), len(jurisdiction_sources)),
            "freshness_percent": _percentage(len(fresh), len(monitored)),
        })

    authority_rows = []
    jurisdiction_by_id = {jurisdiction.id: jurisdiction for jurisdiction in jurisdictions}
    for authority in authorities:
        authority_sources = [source for source in sources if source.regulatory_authority_id == authority.id]
        monitored = [source for source in authority_sources if source.id in monitor_by_source]
        fresh = [source for source in monitored if monitor_by_source[source.id]["fresh"]]
        errors = [
            source for source in monitored
            if monitor_by_source[source.id]["status"] == "error"
        ]
        jurisdiction = jurisdiction_by_id.get(authority.jurisdiction_id)
        authority_rows.append({
            "id": authority.id,
            "name": authority.name,
            "authority_type": authority.authority_type,
            "jurisdiction_id": authority.jurisdiction_id,
            "jurisdiction_code": jurisdiction.code if jurisdiction else None,
            "declared_domains": _parse_json(authority.domains_json) or [],
            "official_sources": len(authority_sources),
            "monitored_sources": len(monitored),
            "fresh_monitors": len(fresh),
            "monitor_errors": len(errors),
            "monitoring_coverage_percent": _percentage(len(monitored), len(authority_sources)),
            "freshness_percent": _percentage(len(fresh), len(monitored)),
        })

    declared_domains = {
        str(domain)
        for authority in authorities
        for domain in (_parse_json(authority.domains_json) or [])
    }
    domain_rows = []
    for domain in sorted({source.domain for source in sources} | declared_domains):
        domain_sources = [source for source in sources if source.domain == domain]
        domain_authorities = {
            authority.id for authority in authorities
            if domain in (_parse_json(authority.domains_json) or [])
        } | {
            source.regulatory_authority_id for source in domain_sources
            if source.regulatory_authority_id is not None
        }
        monitored = [source for source in domain_sources if source.id in monitor_by_source]
        fresh = [source for source in monitored if monitor_by_source[source.id]["fresh"]]
        domain_rows.append({
            "domain": domain,
            "jurisdictions": len({source.jurisdiction_id for source in domain_sources if source.jurisdiction_id}),
            "authorities": len(domain_authorities),
            "official_sources": len(domain_sources),
            "monitored_sources": len(monitored),
            "fresh_monitors": len(fresh),
            "pending_changes": sum(
                1 for change in changes if change.domain == domain and change.status == "pending_review"
            ),
            "active_rules": sum(1 for rule in rules if rule.domain == domain and rule.active),
            "monitoring_coverage_percent": _percentage(len(monitored), len(domain_sources)),
            "freshness_percent": _percentage(len(fresh), len(monitored)),
        })

    return {
        "jurisdictions": sorted(jurisdiction_rows, key=lambda row: row["name"]),
        "authorities": sorted(authority_rows, key=lambda row: (row["jurisdiction_code"] or "", row["name"])),
        "domains": domain_rows,
    }


@router.post("/api/v1/regulatory-intelligence/source-onboarding", status_code=201)
def api_onboard_regulatory_source(
    payload: RegulatorySourceOnboardingRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    from fastapi import HTTPException

    context = getattr(request.state, "auth", None)
    actor = getattr(context, "username", "api-operator")
    try:
        jurisdiction, authority, source, monitor = onboard_regulatory_source(
            session,
            payload,
            actor=actor,
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _json_response({
        "jurisdiction": jurisdiction,
        "authority": authority,
        "official_source": _source_payload(source),
        "monitor": _monitor_payload(monitor, source),
    }, status_code=201)


@router.get("/api/v1/regulatory-intelligence/source-monitors")
def api_list_source_monitors(status: Optional[str] = None, session: Session = Depends(get_session)):
    statement = select(SourceMonitor)
    if status:
        statement = statement.where(SourceMonitor.status == status)
    monitors = session.exec(statement.order_by(SourceMonitor.next_check_at)).all()
    source_ids = {monitor.official_source_id for monitor in monitors}
    sources = {
        source.id: source
        for source in session.exec(select(OfficialSource).where(OfficialSource.id.in_(source_ids))).all()
    } if source_ids else {}
    return _json_response({
        "total": len(monitors),
        "monitors": [_monitor_payload(monitor, sources.get(monitor.official_source_id)) for monitor in monitors],
    })


@router.get("/api/v1/regulatory-intelligence/dashboard")
def api_regulatory_dashboard(session: Session = Depends(get_session)):
    jurisdictions = session.exec(select(Jurisdiction).where(Jurisdiction.active == True)).all()  # noqa: E712
    authorities = session.exec(select(RegulatoryAuthority).where(RegulatoryAuthority.active == True)).all()  # noqa: E712
    sources = session.exec(select(OfficialSource).where(OfficialSource.active == True)).all()  # noqa: E712
    monitors = session.exec(select(SourceMonitor)).all()
    changes = session.exec(select(RegulatoryChange)).all()
    rules = session.exec(select(VerifiedRule)).all()
    runs = session.exec(
        select(SourceRetrievalRun).order_by(SourceRetrievalRun.started_at.desc()).limit(100)
    ).all()
    source_map = {source.id: source for source in sources}
    monitor_rows = [_monitor_payload(monitor, source_map.get(monitor.official_source_id)) for monitor in monitors]
    now = now_utc()
    due = sum(
        1 for monitor in monitors
        if monitor.next_check_at is None or (_aware(monitor.next_check_at) or now) <= now
    )
    return _json_response({
        "generated_at": now,
        "counts": {
            "jurisdictions": len(jurisdictions),
            "authorities": len(authorities),
            "official_sources": len(sources),
            "monitors": len(monitors),
            "monitors_active": sum(1 for monitor in monitors if monitor.status == "active"),
            "monitors_error": sum(1 for monitor in monitors if monitor.status == "error"),
            "monitors_due": due,
            "monitors_stale": sum(1 for row in monitor_rows if not row["fresh"]),
            "changes_pending_review": sum(1 for change in changes if change.status == "pending_review"),
            "changes_critical_pending": sum(
                1 for change in changes
                if change.status == "pending_review" and change.materiality == "critical"
            ),
            "changes_published": sum(1 for change in changes if change.status == "published"),
            "recent_failed_retrievals": sum(1 for run in runs if run.status == "failed"),
        },
        "monitors": monitor_rows,
        "recent_failures": [run for run in runs if run.status == "failed"][:20],
        "coverage": _coverage_payload(
            jurisdictions,
            authorities,
            sources,
            monitors,
            monitor_rows,
            changes,
            rules,
        ),
    })


@router.post("/api/v1/regulatory-intelligence/source-monitors/{monitor_id}/run", status_code=202)
def api_run_source_monitor(monitor_id: UUID, session: Session = Depends(get_session)):
    from fastapi import HTTPException
    from app.models.domain import SourceMonitor

    if session.get(SourceMonitor, monitor_id) is None:
        raise HTTPException(status_code=404, detail="Source monitor not found")
    task = run_source_monitor_task.delay(str(monitor_id))
    return _json_response(
        {"status": "queued", "monitor_id": monitor_id, "task_id": getattr(task, "id", None)},
        status_code=202,
    )


@router.get("/api/v1/regulatory-intelligence/retrieval-runs")
def api_list_source_retrieval_runs(
    monitor_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    statement = select(SourceRetrievalRun)
    if monitor_id:
        statement = statement.where(SourceRetrievalRun.monitor_id == monitor_id)
    if status:
        statement = statement.where(SourceRetrievalRun.status == status)
    rows = session.exec(
        statement.order_by(SourceRetrievalRun.started_at.desc()).limit(min(max(limit, 1), 500))
    ).all()
    return _json_response({"total_returned": len(rows), "retrieval_runs": rows})


@router.get("/api/v1/regulatory-intelligence/snapshots")
def api_list_source_snapshots(
    source_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    statement = select(SourceSnapshot)
    if source_id:
        statement = statement.where(SourceSnapshot.official_source_id == source_id)
    if status:
        statement = statement.where(SourceSnapshot.status == status)
    rows = session.exec(
        statement.order_by(SourceSnapshot.captured_at.desc()).limit(min(max(limit, 1), 500))
    ).all()
    snapshots = [{
        "id": row.id,
        "official_source_id": row.official_source_id,
        "previous_snapshot_id": row.previous_snapshot_id,
        "url": row.url,
        "content_hash": row.content_hash,
        "content_preview": (row.content_text or "")[:600],
        "http_status": row.http_status,
        "retrieval_method": row.retrieval_method,
        "parser_version": row.parser_version,
        "status": row.status,
        "metadata": _parse_json(row.metadata_json) or {},
        "captured_at": row.captured_at,
    } for row in rows]
    return _json_response({"total_returned": len(snapshots), "snapshots": snapshots})


@router.post("/api/v1/regulatory-intelligence/sources/{source_id}/snapshots", status_code=201)
def api_capture_source_snapshot(
    source_id: UUID,
    payload: SourceSnapshotCaptureRequest,
    session: Session = Depends(get_session),
):
    from fastapi import HTTPException
    try:
        snapshot, change, unchanged = capture_source_snapshot(session, source_id, payload)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    classification_proposal = None
    if change is not None:
        classification_proposal = session.exec(
            select(RegulatoryClassificationProposal)
            .where(RegulatoryClassificationProposal.regulatory_change_id == change.id)
            .order_by(RegulatoryClassificationProposal.created_at.desc())
        ).first()
    return _json_response(
        {
            "snapshot": snapshot,
            "change": change,
            "classification_proposal": (
                _classification_proposal_payload(classification_proposal)
                if classification_proposal else None
            ),
            "unchanged": unchanged,
        },
        status_code=201,
    )


@router.get("/api/v1/regulatory-intelligence/changes")
def api_list_regulatory_changes(
    status: Optional[str] = None,
    jurisdiction_id: Optional[UUID] = None,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    statement = select(RegulatoryChange)
    if status:
        statement = statement.where(RegulatoryChange.status == status)
    if jurisdiction_id:
        statement = statement.where(RegulatoryChange.jurisdiction_id == jurisdiction_id)
    rows = session.exec(statement.order_by(RegulatoryChange.detected_at.desc()).limit(min(limit, 500))).all()
    return _json_response({"total_returned": len(rows), "changes": rows})


@router.get("/api/v1/regulatory-intelligence/classification-proposals")
def api_list_classification_proposals(
    change_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 200,
    session: Session = Depends(get_session),
):
    statement = select(RegulatoryClassificationProposal)
    if change_id:
        statement = statement.where(RegulatoryClassificationProposal.regulatory_change_id == change_id)
    if status:
        statement = statement.where(RegulatoryClassificationProposal.status == status)
    rows = session.exec(
        statement.order_by(RegulatoryClassificationProposal.created_at.desc()).limit(min(max(limit, 1), 500))
    ).all()
    return _json_response({
        "total_returned": len(rows),
        "classification_proposals": [_classification_proposal_payload(row) for row in rows],
    })


@router.post("/api/v1/regulatory-intelligence/changes/{change_id}/classification-proposals", status_code=201)
def api_generate_classification_proposal(
    change_id: UUID,
    payload: RegulatoryClassificationProposalGenerateRequest,
    session: Session = Depends(get_session),
):
    from fastapi import HTTPException
    try:
        proposal = generate_classification_proposal(session, change_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _json_response(
        {"classification_proposal": _classification_proposal_payload(proposal)},
        status_code=201,
    )


@router.post("/api/v1/regulatory-intelligence/classification-proposals/{proposal_id}/review")
def api_review_classification_proposal(
    proposal_id: UUID,
    payload: RegulatoryClassificationProposalReviewRequest,
    session: Session = Depends(get_session),
):
    from fastapi import HTTPException
    try:
        proposal = review_classification_proposal(session, proposal_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _json_response({"classification_proposal": _classification_proposal_payload(proposal)})


@router.post("/api/v1/regulatory-intelligence/changes/{change_id}/review")
def api_review_regulatory_change(
    change_id: UUID,
    payload: RegulatoryChangeReviewRequest,
    session: Session = Depends(get_session),
):
    from fastapi import HTTPException
    try:
        change = review_regulatory_change(session, change_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _json_response({"change": change})


@router.post("/api/v1/regulatory-intelligence/changes/{change_id}/publish")
def api_publish_regulatory_change(
    change_id: UUID,
    payload: RegulatoryChangePublishRequest,
    session: Session = Depends(get_session),
):
    from fastapi import HTTPException
    try:
        rule = publish_regulatory_change(session, change_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _json_response({"verified_rule": rule})


@router.get("/api/v1/regulatory-intelligence/verified-rules")
def api_list_verified_rules(
    active: Optional[bool] = None,
    jurisdiction_id: Optional[UUID] = None,
    domain: Optional[str] = None,
    limit: int = 200,
    session: Session = Depends(get_session),
):
    statement = select(VerifiedRule)
    if active is not None:
        statement = statement.where(VerifiedRule.active == active)
    if jurisdiction_id:
        statement = statement.where(VerifiedRule.jurisdiction_id == jurisdiction_id)
    if domain:
        statement = statement.where(VerifiedRule.domain == domain)
    rows = session.exec(
        statement.order_by(VerifiedRule.updated_at.desc()).limit(min(max(limit, 1), 500))
    ).all()
    return _json_response({"total_returned": len(rows), "verified_rules": rows})


@router.get("/api/v1/regulatory-intelligence/knowledge-graph")
def api_regulatory_knowledge_graph(
    jurisdiction_id: Optional[UUID] = None,
    verified_rule_id: Optional[UUID] = None,
    active: Optional[bool] = True,
    limit: int = 500,
    session: Session = Depends(get_session),
):
    return _json_response(knowledge_graph_payload(
        session,
        jurisdiction_id=jurisdiction_id,
        verified_rule_id=verified_rule_id,
        active=active,
        limit=limit,
    ))


@router.post("/api/v1/regulatory-intelligence/knowledge-graph/sync")
def api_sync_regulatory_knowledge_graph(
    payload: RegulatoryKnowledgeGraphSyncRequest,
    session: Session = Depends(get_session),
):
    return _json_response({"sync": sync_published_rules(session, actor=payload.actor)})


@router.post("/api/v1/regulatory-intelligence/verified-rules/{rule_id}/retire")
def api_retire_verified_rule(
    rule_id: UUID,
    payload: VerifiedRuleRetireRequest,
    session: Session = Depends(get_session),
):
    from fastapi import HTTPException
    try:
        rule = retire_verified_rule(session, rule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _json_response({"verified_rule": rule})


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
        "version": "v7.0",
        "models": [
            "Jurisdiction",
            "RegulatoryAuthority",
            "OfficialSource",
            "SourceMonitor",
            "SourceSnapshot",
            "RegulatoryChange",
            "SourceCheckRun",
            "VerifiedRule",
            "CountryPolicy",
        ],
        "routes": [
            "POST /api/v1/official-sources/seed",
            "GET /api/v1/official-sources",
            "GET /api/v1/official-sources/check-runs",
            "GET /api/v1/official-sources/policies",
            "GET /admin/official-sources",
        ],
    }
