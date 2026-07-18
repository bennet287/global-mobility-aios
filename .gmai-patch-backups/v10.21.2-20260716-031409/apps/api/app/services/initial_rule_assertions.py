from __future__ import annotations

import hashlib
import json
from typing import Any, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    InitialRuleAssertion,
    Jurisdiction,
    JurisdictionCoverageEvidenceBatch,
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    JurisdictionSourceCertification,
    OfficialSource,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.schemas import (
    InitialRuleAssertionCreateRequest,
    InitialRuleAssertionPublishRequest,
    InitialRuleAssertionReviewRequest,
)
from app.services.audit_log import record_audit
from app.services.jurisdiction_registry import jurisdiction_coverage_receipt
from app.services.official_sources import normalize_country, normalize_domain


_MIN_PUBLISH_CONFIDENCE = 0.90


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _normal(value: str) -> str:
    return " ".join(value.strip().split())


def _batch_item(
    session: Session,
    *,
    batch_id: UUID,
    alpha2_code: str,
) -> tuple[JurisdictionCoverageEvidenceBatch, JurisdictionCoverageEvidenceBatchItem]:
    batch = session.get(JurisdictionCoverageEvidenceBatch, batch_id)
    if batch is None:
        raise ValueError("Coverage evidence batch not found")
    code = alpha2_code.strip().upper()
    item = session.exec(
        select(JurisdictionCoverageEvidenceBatchItem)
        .where(JurisdictionCoverageEvidenceBatchItem.batch_id == batch.id)
        .where(JurisdictionCoverageEvidenceBatchItem.alpha2_code == code)
    ).first()
    if item is None:
        raise ValueError(f"Coverage evidence batch does not contain jurisdiction {code}")
    return batch, item


def _approved_item_context(
    session: Session,
    item: JurisdictionCoverageEvidenceBatchItem,
) -> tuple[Jurisdiction, OfficialSource, SourceSnapshot]:
    if not item.immigration_assessment_id or not item.source_certification_id:
        raise ValueError("Initial rule assertion requires both coverage review records")
    if not item.official_source_id:
        raise ValueError("Initial rule assertion requires an onboarded official source")
    assessment = session.get(JurisdictionImmigrationAssessment, item.immigration_assessment_id)
    certification = session.get(JurisdictionSourceCertification, item.source_certification_id)
    jurisdiction = session.get(Jurisdiction, item.jurisdiction_id)
    source = session.get(OfficialSource, item.official_source_id)
    if not assessment or assessment.status != "approved":
        raise ValueError("Immigration-rule relationship must be independently approved first")
    if not certification or certification.status != "approved":
        raise ValueError("Primary authority/source certification must be independently approved first")
    if not jurisdiction or not source:
        raise ValueError("Coverage item jurisdiction or official source could not be resolved")
    if assessment.jurisdiction_id != jurisdiction.id or certification.jurisdiction_id != jurisdiction.id:
        raise ValueError("Coverage review records do not belong to the selected jurisdiction")
    if assessment.official_source_id not in {None, source.id}:
        raise ValueError("Immigration assessment is linked to a different official source")
    if certification.official_source_id != source.id:
        raise ValueError("Source certification is linked to a different official source")
    if not source.active:
        raise ValueError("Official source is inactive")

    snapshot = session.exec(
        select(SourceSnapshot)
        .where(SourceSnapshot.official_source_id == source.id)
        .where(SourceSnapshot.previous_snapshot_id.is_(None))
        .where(SourceSnapshot.status == "baseline")
        .order_by(SourceSnapshot.captured_at.desc())
    ).first()
    if snapshot is None:
        raise ValueError("An immutable baseline snapshot is required before proposing an initial rule")
    if not snapshot.content_hash or not snapshot.content_text:
        raise ValueError("Baseline snapshot content provenance is incomplete")
    return jurisdiction, source, snapshot


def _assertion_hash(
    *,
    item: JurisdictionCoverageEvidenceBatchItem,
    snapshot: SourceSnapshot,
    payload: InitialRuleAssertionCreateRequest,
) -> str:
    canonical = {
        "coverage_batch_item_id": str(item.id),
        "jurisdiction_id": str(item.jurisdiction_id),
        "official_source_id": str(item.official_source_id),
        "source_snapshot_id": str(snapshot.id),
        "source_snapshot_hash": snapshot.content_hash,
        "domain": normalize_domain(payload.domain),
        "title": _normal(payload.title),
        "rule_key": _normal(payload.rule_key).lower().replace(" ", "_"),
        "statement": _normal(payload.statement),
        "rationale": _normal(payload.rationale),
        "evidence_excerpt": _normal(payload.evidence_excerpt),
        "confidence": round(payload.confidence, 6),
        "effective_from": payload.effective_from,
        "effective_to": payload.effective_to,
    }
    return hashlib.sha256(_dump(canonical).encode("utf-8")).hexdigest()


def initial_rule_assertion_payload(
    session: Session,
    assertion: InitialRuleAssertion,
) -> dict[str, Any]:
    jurisdiction = session.get(Jurisdiction, assertion.jurisdiction_id)
    source = session.get(OfficialSource, assertion.official_source_id)
    snapshot = session.get(SourceSnapshot, assertion.source_snapshot_id)
    rule = session.get(VerifiedRule, assertion.published_rule_id) if assertion.published_rule_id else None
    return {
        **assertion.model_dump(),
        "alpha2_code": jurisdiction.code if jurisdiction else None,
        "jurisdiction_name": jurisdiction.name if jurisdiction else None,
        "source_name": source.name if source else None,
        "source_url": source.url if source else None,
        "snapshot": None if snapshot is None else {
            "id": snapshot.id,
            "status": snapshot.status,
            "content_hash": snapshot.content_hash,
            "captured_at": snapshot.captured_at,
            "url": snapshot.url,
        },
        "verified_rule": None if rule is None else {
            "id": rule.id,
            "rule_key": rule.rule_key,
            "active": rule.active,
            "published_at": rule.published_at,
        },
        "safety": {
            "source_change_claimed": False,
            "human_review_required": True,
            "publishes_automatically": False,
            "message": "This is a baseline rule assertion, not a detected source change. Publication requires independent review and a separate explicit action.",
        },
    }


def list_initial_rule_assertions(
    session: Session,
    *,
    batch_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 200,
) -> list[InitialRuleAssertion]:
    statement = select(InitialRuleAssertion)
    if batch_id is not None:
        item_ids = list(session.exec(
            select(JurisdictionCoverageEvidenceBatchItem.id).where(
                JurisdictionCoverageEvidenceBatchItem.batch_id == batch_id
            )
        ).all())
        if not item_ids:
            return []
        statement = statement.where(InitialRuleAssertion.coverage_batch_item_id.in_(item_ids))
    if status:
        statement = statement.where(InitialRuleAssertion.status == status)
    return list(session.exec(
        statement.order_by(InitialRuleAssertion.created_at.desc()).limit(min(max(limit, 1), 500))
    ).all())


def propose_initial_rule_assertion(
    session: Session,
    *,
    batch_id: UUID,
    payload: InitialRuleAssertionCreateRequest,
    actor: str,
) -> tuple[InitialRuleAssertion, bool]:
    _, item = _batch_item(session, batch_id=batch_id, alpha2_code=payload.alpha2_code)
    jurisdiction, source, snapshot = _approved_item_context(session, item)
    domain = normalize_domain(payload.domain)
    rule_key = _normal(payload.rule_key).lower().replace(" ", "_")
    if payload.effective_from and payload.effective_to and payload.effective_to <= payload.effective_from:
        raise ValueError("Initial rule effective_to must be later than effective_from")
    active_duplicate = session.exec(
        select(VerifiedRule)
        .where(VerifiedRule.jurisdiction_id == jurisdiction.id)
        .where(VerifiedRule.domain == domain)
        .where(VerifiedRule.rule_key == rule_key)
        .where(VerifiedRule.active == True)  # noqa: E712
    ).first()
    if active_duplicate is not None:
        raise ValueError("An active verified rule already exists for this jurisdiction, domain, and rule key")

    assertion_sha256 = _assertion_hash(item=item, snapshot=snapshot, payload=payload)
    existing = session.exec(
        select(InitialRuleAssertion).where(
            InitialRuleAssertion.assertion_sha256 == assertion_sha256
        )
    ).first()
    if existing is not None:
        return existing, False

    assertion = InitialRuleAssertion(
        assertion_sha256=assertion_sha256,
        coverage_batch_item_id=item.id,
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        domain=domain,
        title=_normal(payload.title),
        rule_key=rule_key,
        statement=_normal(payload.statement),
        rationale=_normal(payload.rationale),
        evidence_excerpt=_normal(payload.evidence_excerpt),
        confidence=payload.confidence,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status="pending_review",
        proposed_by=actor,
    )
    session.add(assertion)
    session.flush()
    record_audit(
        session,
        action="initial_rule_assertion_proposed",
        entity_type="initial_rule_assertion",
        entity_id=assertion.id,
        after_state={
            "assertion_sha256": assertion.assertion_sha256,
            "coverage_batch_item_id": item.id,
            "jurisdiction_id": jurisdiction.id,
            "official_source_id": source.id,
            "source_snapshot_id": snapshot.id,
            "domain": domain,
            "rule_key": rule_key,
            "status": assertion.status,
        },
        reason=assertion.rationale,
        actor=actor,
        source="initial_rule_assertions_v10_19",
    )
    session.commit()
    session.refresh(assertion)
    return assertion, True


def review_initial_rule_assertion(
    session: Session,
    assertion_id: UUID,
    payload: InitialRuleAssertionReviewRequest,
    *,
    actor: str,
) -> InitialRuleAssertion:
    assertion = session.get(InitialRuleAssertion, assertion_id)
    if assertion is None:
        raise ValueError("Initial rule assertion not found")
    if assertion.status != "pending_review":
        raise ValueError(f"Initial rule assertion cannot be reviewed from status '{assertion.status}'")
    if actor.strip().lower() == assertion.proposed_by.strip().lower():
        raise ValueError("A different authenticated reviewer must decide the initial rule assertion")
    before = {"status": assertion.status, "reviewed_by": assertion.reviewed_by}
    assertion.status = payload.decision
    assertion.reviewed_by = actor
    assertion.reviewed_at = now_utc()
    assertion.review_notes = _normal(payload.notes)
    assertion.updated_at = now_utc()
    session.add(assertion)
    record_audit(
        session,
        action="initial_rule_assertion_reviewed",
        entity_type="initial_rule_assertion",
        entity_id=assertion.id,
        before_state=before,
        after_state={
            "status": assertion.status,
            "reviewed_by": assertion.reviewed_by,
            "reviewed_at": assertion.reviewed_at,
        },
        reason=assertion.review_notes,
        actor=actor,
        source="initial_rule_assertions_v10_19",
    )
    session.commit()
    session.refresh(assertion)
    return assertion


def publish_initial_rule_assertion(
    session: Session,
    assertion_id: UUID,
    payload: InitialRuleAssertionPublishRequest,
    *,
    actor: str,
) -> tuple[VerifiedRule, dict[str, Any]]:
    assertion = session.get(InitialRuleAssertion, assertion_id)
    if assertion is None:
        raise ValueError("Initial rule assertion not found")
    if assertion.published_rule_id:
        existing = session.get(VerifiedRule, assertion.published_rule_id)
        if existing is None:
            raise ValueError("Published assertion rule provenance is broken")
        current = jurisdiction_coverage_receipt(session, assertion.jurisdiction_id)
        return existing, {
            "idempotent": True,
            "became_ready": False,
            "before": current,
            "after": current,
            "verified_rule_id": existing.id,
            "message": "The assertion was already published; current coverage posture was reconciled without mutation.",
        }
    if assertion.status != "approved" or not assertion.reviewed_by or not assertion.reviewed_at:
        raise ValueError("Only an independently approved initial rule assertion can be published")
    if actor.strip().lower() == assertion.proposed_by.strip().lower():
        raise ValueError("The proposer cannot publish the initial rule assertion")
    if not payload.attestation:
        raise ValueError("Publication attestation is required")
    if assertion.confidence < _MIN_PUBLISH_CONFIDENCE:
        raise ValueError(f"Initial rule confidence must be at least {_MIN_PUBLISH_CONFIDENCE:.2f} before publication")

    item = session.get(JurisdictionCoverageEvidenceBatchItem, assertion.coverage_batch_item_id) if assertion.coverage_batch_item_id else None
    if item is None:
        raise ValueError("Initial rule assertion is not linked to its coverage batch item")
    jurisdiction, source, snapshot = _approved_item_context(session, item)
    if (
        assertion.jurisdiction_id != jurisdiction.id
        or assertion.official_source_id != source.id
        or assertion.source_snapshot_id != snapshot.id
    ):
        raise ValueError("Initial rule assertion provenance no longer matches the approved coverage evidence")

    coverage_before = jurisdiction_coverage_receipt(session, assertion.jurisdiction_id)

    duplicate = session.exec(
        select(VerifiedRule)
        .where(VerifiedRule.jurisdiction_id == assertion.jurisdiction_id)
        .where(VerifiedRule.domain == assertion.domain)
        .where(VerifiedRule.rule_key == assertion.rule_key)
        .where(VerifiedRule.active == True)  # noqa: E712
    ).first()
    if duplicate is not None:
        raise ValueError("An active verified rule already exists for this initial assertion key")

    published_at = now_utc()
    rule = VerifiedRule(
        country=normalize_country(jurisdiction.name),
        domain=assertion.domain,
        rule_key=assertion.rule_key,
        statement=assertion.statement,
        official_source_id=assertion.official_source_id,
        jurisdiction_id=assertion.jurisdiction_id,
        regulatory_change_id=None,
        initial_rule_assertion_id=assertion.id,
        source_snapshot_id=assertion.source_snapshot_id,
        confidence=assertion.confidence,
        active=True,
        effective_from=assertion.effective_from,
        effective_to=assertion.effective_to,
        approved_by=actor,
        published_at=published_at,
    )
    session.add(rule)
    session.flush()
    assertion.status = "published"
    assertion.published_rule_id = rule.id
    assertion.published_by = actor
    assertion.published_at = published_at
    assertion.updated_at = published_at
    session.add(assertion)

    from app.services.regulatory_knowledge_graph import project_verified_rule

    project_verified_rule(session, rule, actor=actor)
    record_audit(
        session,
        action="initial_rule_assertion_published",
        entity_type="initial_rule_assertion",
        entity_id=assertion.id,
        after_state={
            "verified_rule_id": rule.id,
            "jurisdiction_id": rule.jurisdiction_id,
            "source_snapshot_id": rule.source_snapshot_id,
            "rule_key": rule.rule_key,
            "published_at": published_at,
        },
        reason=_normal(payload.publication_notes),
        actor=actor,
        source="initial_rule_assertions_v10_20",
    )
    record_audit(
        session,
        action="verified_rule_published",
        entity_type="verified_rule",
        entity_id=rule.id,
        after_state=rule,
        reason=f"Initial baseline assertion {assertion.id}: {_normal(payload.publication_notes)}",
        actor=actor,
        source="initial_rule_assertions_v10_20",
    )
    session.flush()
    coverage_after = jurisdiction_coverage_receipt(session, assertion.jurisdiction_id)
    coverage_receipt = {
        "idempotent": False,
        "became_ready": (
            not bool(coverage_before.get("coverage_ready"))
            and bool(coverage_after.get("coverage_ready"))
        ),
        "before": coverage_before,
        "after": coverage_after,
        "verified_rule_id": rule.id,
        "message": (
            "Verified-rule publication completed the jurisdiction coverage gates."
            if coverage_after.get("coverage_ready")
            else "Verified-rule publication succeeded; remaining evidence gates are listed in the receipt."
        ),
    }
    record_audit(
        session,
        action="jurisdiction_coverage_readiness_reconciled",
        entity_type="jurisdiction",
        entity_id=assertion.jurisdiction_id,
        before_state=coverage_before,
        after_state=coverage_after,
        reason=coverage_receipt["message"],
        actor=actor,
        source="initial_rule_assertions_v10_20",
    )
    session.commit()
    session.refresh(rule)
    return rule, coverage_receipt
