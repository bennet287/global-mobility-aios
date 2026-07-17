from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import (
    InitialRuleAssertion,
    Jurisdiction,
    JurisdictionCoverageEvidenceBatch,
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
    SourceMonitor,
    SourceSnapshot,
)
from app.schemas import CoverageTrancheAssistantPrepareRequest
from app.services.coverage_baseline_capture import (
    coverage_batch_baseline_status,
    queue_coverage_batch_baselines,
)
from app.services.jurisdiction_registry import jurisdiction_coverage_receipt


_NAVIGATION_LINES = {
    "about us",
    "accessibility statement",
    "back",
    "close",
    "close search",
    "contact us",
    "content",
    "copyright",
    "data privacy",
    "en",
    "faq",
    "footer",
    "fr",
    "help desk",
    "imprint",
    "main menu",
    "menu",
    "more languages",
    "navigation",
    "news",
    "overview",
    "page navigation",
    "search",
    "share page",
    "start search",
    "straight to:",
    "top of page",
    "welcome",
}
_KEYWORDS = (
    "application",
    "apply",
    "citizenship",
    "family reunification",
    "immigration",
    "job seeker",
    "permit",
    "residence",
    "settlement",
    "study",
    "visa",
    "work",
)


def coverage_tranche_assistant_config() -> dict[str, Any]:
    return {
        "enabled": settings.coverage_tranche_assistant_enabled,
        "max_items": max(1, min(settings.coverage_tranche_assistant_max_items, 25)),
        "defaults": {
            "dry_run": True,
            "queue_eligible_baselines": False,
            "default_batch_size": 1,
        },
        "safety": {
            "creates_review_records": False,
            "approves_evidence": False,
            "creates_assertions": False,
            "publishes_verified_rules": False,
            "creates_coverage_claim": False,
            "mutates_immutable_snapshots": False,
            "message": (
                "The tranche assistant prepares review packets and constrained draft suggestions. "
                "It may queue explicitly selected approved baseline captures only when dry_run=false."
            ),
        },
    }


def _normal_line(value: str) -> str:
    return " ".join(value.strip().split())


def _is_navigation(line: str) -> bool:
    lowered = line.casefold().strip(" :.-")
    if lowered in _NAVIGATION_LINES:
        return True
    return lowered.startswith(("jump to ", "back to ", "find a ", "report an "))


def _content_analysis(snapshot: SourceSnapshot, *, max_candidate_lines: int) -> dict[str, Any]:
    content = snapshot.content_text or ""
    lines: list[str] = []
    seen: set[str] = set()
    for raw in content.splitlines():
        line = _normal_line(raw)
        if not line:
            continue
        key = line.casefold()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)

    navigation_count = sum(1 for line in lines if _is_navigation(line))
    candidates: list[str] = []
    keyword_set: set[str] = set()
    for line in lines:
        lower = line.casefold()
        hits = [keyword for keyword in _KEYWORDS if keyword in lower]
        if hits:
            keyword_set.update(hits)
        if _is_navigation(line) or not hits or not 8 <= len(line) <= 320:
            continue
        candidates.append(line)
        if len(candidates) >= max_candidate_lines:
            break

    line_count = len(lines)
    navigation_ratio = navigation_count / line_count if line_count else 1.0
    score = 0
    score += min(25, len(content) // 80)
    score += min(35, len(candidates) * 7)
    score += min(25, len(keyword_set) * 4)
    score += 10 if snapshot.http_status and 200 <= snapshot.http_status < 300 else 0
    score -= round(navigation_ratio * 30)
    score = max(0, min(100, score))

    if not content.strip():
        classification = "missing_content"
    elif not candidates:
        classification = "insufficient_substantive_text"
    elif score < 45 or navigation_ratio > 0.70:
        classification = "navigation_heavy"
    else:
        classification = "suitable_for_narrow_draft"

    return {
        "snapshot_id": snapshot.id,
        "snapshot_url": snapshot.url,
        "captured_at": snapshot.captured_at,
        "content_hash": snapshot.content_hash,
        "content_characters": len(content),
        "unique_lines": line_count,
        "navigation_lines": navigation_count,
        "navigation_ratio": round(navigation_ratio, 3),
        "keyword_hits": sorted(keyword_set),
        "quality_score": score,
        "classification": classification,
        "candidate_excerpt_lines": candidates,
        "preview": content[:1200],
    }


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _candidate_draft(
    *,
    jurisdiction: Jurisdiction,
    source: OfficialSource,
    analysis: dict[str, Any],
) -> dict[str, Any] | None:
    lines = analysis["candidate_excerpt_lines"]
    if analysis["classification"] != "suitable_for_narrow_draft" or not lines:
        return None
    selected = lines[: min(4, len(lines))]
    quoted = "; ".join(f'"{line}"' for line in selected[:3])
    domain = source.domain or "visa"
    return {
        "alpha2_code": jurisdiction.code.upper(),
        "domain": domain,
        "title": f"{jurisdiction.name} official {domain} information baseline",
        "rule_key": f"{_slug(jurisdiction.code)}_{_slug(domain)}_official_information_baseline",
        "statement": f"The official {source.name} publishes immigration information including {quoted}.",
        "evidence_excerpt": "\n\n".join(selected),
        "rationale": (
            "This constrained draft describes only the exact headings or service statements present in the immutable "
            "baseline snapshot. A human reviewer must confirm scope, remove navigation artefacts, and reject any "
            "wording that implies eligibility, entitlement, approval, timing, or legal effect not stated in the source."
        ),
        "confidence": 0.90,
        "requires_human_edit": True,
        "creates_pending_assertion": False,
    }


def _latest_assertion(
    session: Session,
    item: JurisdictionCoverageEvidenceBatchItem,
) -> InitialRuleAssertion | None:
    rows = session.exec(
        select(InitialRuleAssertion)
        .where(InitialRuleAssertion.coverage_batch_item_id == item.id)
        .order_by(InitialRuleAssertion.created_at.desc())
    ).all()
    priority = {"published": 4, "approved": 3, "pending_review": 2, "rejected": 1}
    return max(rows, key=lambda row: (priority.get(row.status, 0), row.created_at), default=None)


def _stage(
    *,
    baseline_state: str,
    assertion: InitialRuleAssertion | None,
    coverage_ready: bool,
) -> str:
    if coverage_ready:
        return "coverage_ready"
    if assertion is not None:
        if assertion.status == "published":
            return "published_rule_coverage_gap"
        if assertion.status == "approved":
            return "assertion_approved_awaiting_publication"
        if assertion.status == "pending_review":
            return "assertion_pending_independent_review"
        if assertion.status == "rejected":
            return "assertion_rejected_needs_revision"
    if baseline_state == "baseline_ready":
        return "baseline_ready_needs_assertion"
    return baseline_state


def _review_packet(
    *,
    assessment: JurisdictionImmigrationAssessment | None,
    certification: JurisdictionSourceCertification | None,
    authority: RegulatoryAuthority | None,
    source: OfficialSource | None,
    monitor: SourceMonitor | None,
) -> dict[str, Any]:
    return {
        "immigration_assessment": None if assessment is None else {
            "id": assessment.id,
            "status": assessment.status,
            "rule_relationship": assessment.rule_relationship,
            "parent_code": assessment.parent_code,
            "evidence_url": assessment.evidence_url,
            "evidence_title": assessment.evidence_title,
            "rationale": assessment.rationale,
            "proposed_by": assessment.proposed_by,
            "reviewed_by": assessment.reviewed_by,
        },
        "source_certification": None if certification is None else {
            "id": certification.id,
            "status": certification.status,
            "coverage_domains_json": certification.coverage_domains_json,
            "evidence_notes": certification.evidence_notes,
            "proposed_by": certification.proposed_by,
            "reviewed_by": certification.reviewed_by,
        },
        "authority": None if authority is None else {
            "id": authority.id,
            "name": authority.name,
            "authority_type": authority.authority_type,
            "website_url": authority.website_url,
            "active": authority.active,
        },
        "official_source": None if source is None else {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "domain": source.domain,
            "source_type": source.source_type,
            "active": source.active,
        },
        "monitor": None if monitor is None else {
            "id": monitor.id,
            "status": monitor.status,
            "fetch_method": monitor.fetch_method,
            "last_checked_at": monitor.last_checked_at,
            "last_http_status": monitor.last_http_status,
            "last_error": monitor.last_error,
        },
        "review_checks": [
            "Confirm the authority is responsible for the claimed immigration scope.",
            "Confirm the source hostname and page are official and jurisdiction-matched.",
            "Confirm the relationship and certification wording do not exceed the evidence.",
            "Use a reviewer identity different from the proposer.",
        ],
    }


def prepare_coverage_tranche(
    session: Session,
    *,
    batch_id: UUID,
    payload: CoverageTrancheAssistantPrepareRequest,
    actor: str,
) -> dict[str, Any]:
    config = coverage_tranche_assistant_config()
    if not config["enabled"]:
        raise PermissionError(
            "Coverage tranche assistant is disabled. Set COVERAGE_TRANCHE_ASSISTANT_ENABLED=true and rebuild the API."
        )
    if len(payload.alpha2_codes) > config["max_items"]:
        raise ValueError(f"At most {config['max_items']} jurisdictions may be prepared at once")

    batch = session.get(JurisdictionCoverageEvidenceBatch, batch_id)
    if batch is None:
        raise ValueError("Coverage evidence batch not found")
    selected_codes = {code.upper() for code in payload.alpha2_codes}
    items = session.exec(
        select(JurisdictionCoverageEvidenceBatchItem)
        .where(JurisdictionCoverageEvidenceBatchItem.batch_id == batch.id)
        .where(JurisdictionCoverageEvidenceBatchItem.alpha2_code.in_(selected_codes))
        .order_by(JurisdictionCoverageEvidenceBatchItem.row_number)
    ).all()
    found_codes = {item.alpha2_code.upper() for item in items}
    missing_codes = sorted(selected_codes - found_codes)
    if missing_codes:
        raise ValueError(f"Coverage evidence batch does not contain: {', '.join(missing_codes)}")

    baseline = coverage_batch_baseline_status(session, batch.id)
    baseline_by_code = {item["alpha2_code"].upper(): item for item in baseline["items"]}
    result_items: list[dict[str, Any]] = []
    would_queue: list[str] = []

    for item in items:
        code = item.alpha2_code.upper()
        jurisdiction = session.get(Jurisdiction, item.jurisdiction_id)
        assessment = session.get(JurisdictionImmigrationAssessment, item.immigration_assessment_id) if item.immigration_assessment_id else None
        certification = session.get(JurisdictionSourceCertification, item.source_certification_id) if item.source_certification_id else None
        authority = session.get(RegulatoryAuthority, item.regulatory_authority_id) if item.regulatory_authority_id else None
        source = session.get(OfficialSource, item.official_source_id) if item.official_source_id else None
        monitor = session.get(SourceMonitor, item.source_monitor_id) if item.source_monitor_id else None
        baseline_item = baseline_by_code[code]
        snapshot = None
        if baseline_item.get("latest_snapshot") and source is not None:
            snapshot = session.get(SourceSnapshot, baseline_item["latest_snapshot"]["id"])
        assertion = _latest_assertion(session, item)
        receipt = jurisdiction_coverage_receipt(session, item.jurisdiction_id)
        analysis = _content_analysis(snapshot, max_candidate_lines=payload.max_candidate_lines) if snapshot else None
        draft = _candidate_draft(jurisdiction=jurisdiction, source=source, analysis=analysis) if jurisdiction and source and analysis and payload.include_candidate_assertions else None
        if baseline_item["eligible_to_queue"]:
            would_queue.append(code)

        result_items.append({
            "batch_item_id": item.id,
            "alpha2_code": code,
            "jurisdiction_name": jurisdiction.name if jurisdiction else None,
            "stage": _stage(
                baseline_state=baseline_item["state"],
                assertion=assertion,
                coverage_ready=receipt["coverage_ready"],
            ),
            "baseline": baseline_item,
            "review_packet": _review_packet(
                assessment=assessment,
                certification=certification,
                authority=authority,
                source=source,
                monitor=monitor,
            ),
            "snapshot_analysis": analysis,
            "candidate_assertion": draft,
            "existing_assertion": None if assertion is None else {
                "id": assertion.id,
                "status": assertion.status,
                "title": assertion.title,
                "rule_key": assertion.rule_key,
                "proposed_by": assertion.proposed_by,
                "reviewed_by": assertion.reviewed_by,
                "published_by": assertion.published_by,
                "published_rule_id": assertion.published_rule_id,
            },
            "coverage_receipt": receipt,
            "next_action": (
                "Complete independent assessment and certification review."
                if baseline_item["state"] == "pending_independent_review"
                else "Queue the approved source baseline capture."
                if baseline_item["eligible_to_queue"]
                else "Wait for the running source retrieval."
                if baseline_item["state"] == "retrieval_in_progress"
                else "Inspect the retrieval failure before retrying."
                if baseline_item["state"] == "retrieval_failed"
                else "Review and edit the constrained assertion draft; submission remains a separate human action."
                if _stage(baseline_state=baseline_item["state"], assertion=assertion, coverage_ready=receipt["coverage_ready"]) == "baseline_ready_needs_assertion"
                else "Independently review the pending assertion."
                if assertion and assertion.status == "pending_review"
                else "Publish the independently approved assertion using a separate explicit action."
                if assertion and assertion.status == "approved"
                else "No action required; jurisdiction coverage is ready."
                if receipt["coverage_ready"]
                else "Inspect the current evidence gates."
            ),
        })

    queue_result = None
    if payload.queue_eligible_baselines and not payload.dry_run and would_queue:
        queue_result = queue_coverage_batch_baselines(
            session,
            batch_id=batch.id,
            actor=actor,
            alpha2_codes=set(would_queue),
        )

    return {
        "batch_id": batch.id,
        "batch_name": batch.name,
        "actor": actor,
        "dry_run": payload.dry_run,
        "selected_count": len(items),
        "selected_codes": [item.alpha2_code.upper() for item in items],
        "would_queue_baselines": would_queue,
        "queued_baselines": 0 if queue_result is None else queue_result.get("queued", 0),
        "queue_result": queue_result,
        "items": result_items,
        "safety": config["safety"],
    }
