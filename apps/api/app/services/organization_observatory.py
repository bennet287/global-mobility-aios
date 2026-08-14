from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
from uuid import UUID

from sqlmodel import Session, func, select

from app.models.domain import (
    AuditLog,
    ExecutiveDecision,
    InitialRuleAssertion,
    JurisdictionSourceCertification,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    OrganizationActivity,
    OrganizationBlocker,
    OrganizationBlockerStatus,
    OrganizationContribution,
    OrganizationContributionRecordKind,
    OrganizationDependencyStatus,
    OrganizationDependencyType,
    OrganizationHumanAction,
    OrganizationHumanActionRequest,
    OrganizationHumanActionRequestStatus,
    OrganizationWorkItemDependency,
    OrganizationalWorkItem,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
)
from app.services.organization_contribution import (
    _initial_rule_publication_version,
    _pathway_publication_version,
    _regulatory_change_publication_version,
    _source_certification_review_version,
)


DEFAULT_TENANT = "default"
ACCEPTED_SOURCE_TYPES = (
    "executive_decision",
    "jurisdiction_source_certification",
    "initial_rule_assertion",
    "regulatory_change",
    "mobility_pathway_version",
)
AUTOMATIC_SOURCE_TYPES = (
    "jurisdiction_source_certification",
    "initial_rule_assertion",
    "regulatory_change",
    "mobility_pathway_version",
)
PENDING_DECISION_STATUSES = {"pending_ceo", "coordinating_ceo", "pending_board"}
PENDING_HUMAN_REQUEST_STATUSES = {
    OrganizationHumanActionRequestStatus.required.value,
    OrganizationHumanActionRequestStatus.acknowledged.value,
    OrganizationHumanActionRequestStatus.in_progress.value,
}
TERMINAL_WORK_STATUSES = {"completed", "cancelled"}
ACTIVE_BLOCKER_STATUSES = {
    OrganizationBlockerStatus.open.value,
    OrganizationBlockerStatus.mitigated.value,
}


@dataclass(frozen=True)
class _SourceState:
    exists: bool
    valid_state: bool
    source_version: str | None
    source_state: str | None
    transition_at: datetime | None
    detail: str


@dataclass(frozen=True)
class _SourceCandidate:
    source_type: str
    source_id: str
    source_state: str
    source_version: str | None
    transition_at: datetime
    detail: str


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _counts(values: Iterable[Any]) -> dict[str, int]:
    counter = Counter(_enum_value(value) for value in values)
    return dict(sorted(counter.items()))


def _count_rows(session: Session, model: type[Any], tenant_key: str | None = None) -> int:
    statement = select(func.count()).select_from(model)
    if tenant_key is not None:
        statement = statement.where(model.tenant_key == tenant_key)
    return int(session.exec(statement).one())


def source_row_counts(session: Session, tenant_key: str) -> dict[str, int]:
    counts = {
        "organization_contributions": _count_rows(session, OrganizationContribution, tenant_key),
        "organizational_work_items": _count_rows(session, OrganizationalWorkItem, tenant_key),
        "organization_blockers": _count_rows(session, OrganizationBlocker, tenant_key),
        "executive_decisions": _count_rows(session, ExecutiveDecision, tenant_key),
        "organization_human_action_requests": _count_rows(
            session, OrganizationHumanActionRequest, tenant_key
        ),
        "organization_human_actions": _count_rows(session, OrganizationHumanAction, tenant_key),
        "organization_work_item_dependencies": _count_rows(
            session, OrganizationWorkItemDependency, tenant_key
        ),
        "organization_activities": _count_rows(session, OrganizationActivity, tenant_key),
    }
    if tenant_key == DEFAULT_TENANT:
        counts.update(
            {
                "jurisdiction_source_certifications": _count_rows(
                    session, JurisdictionSourceCertification
                ),
                "initial_rule_assertions": _count_rows(session, InitialRuleAssertion),
                "regulatory_changes": _count_rows(session, RegulatoryChange),
                "mobility_pathway_versions": _count_rows(session, MobilityPathwayVersion),
            }
        )
    else:
        counts.update(
            {
                "jurisdiction_source_certifications": 0,
                "initial_rule_assertions": 0,
                "regulatory_changes": 0,
                "mobility_pathway_versions": 0,
            }
        )
    return counts


def _tenant_rows(session: Session, model: type[Any], tenant_key: str) -> list[Any]:
    return list(session.exec(select(model).where(model.tenant_key == tenant_key)).all())


def _outcomes_and_corrections(
    session: Session, tenant_key: str
) -> tuple[list[OrganizationContribution], list[OrganizationContribution]]:
    rows = _tenant_rows(session, OrganizationContribution, tenant_key)
    outcomes = [
        row
        for row in rows
        if _enum_value(row.record_kind) == OrganizationContributionRecordKind.outcome.value
    ]
    corrections = [
        row
        for row in rows
        if _enum_value(row.record_kind)
        in {
            OrganizationContributionRecordKind.supersession.value,
            OrganizationContributionRecordKind.retraction.value,
        }
    ]
    return outcomes, corrections


def _active_outcomes(
    outcomes: list[OrganizationContribution], corrections: list[OrganizationContribution]
) -> list[OrganizationContribution]:
    corrected_targets = {
        row.supersedes_contribution_id
        for row in corrections
        if row.supersedes_contribution_id is not None
    }
    return [row for row in outcomes if row.id not in corrected_targets]


def _contribution_metrics(
    session: Session, tenant_key: str
) -> tuple[dict[str, Any], list[OrganizationContribution], list[OrganizationContribution]]:
    outcomes, corrections = _outcomes_and_corrections(session, tenant_key)
    active = _active_outcomes(outcomes, corrections)
    supersessions = sum(
        _enum_value(row.record_kind) == OrganizationContributionRecordKind.supersession.value
        for row in corrections
    )
    retractions = sum(
        _enum_value(row.record_kind) == OrganizationContributionRecordKind.retraction.value
        for row in corrections
    )
    return (
        {
            "total_records": len(outcomes) + len(corrections),
            "historical_outcomes": len(outcomes),
            "active_outcomes": len(active),
            "supersessions": supersessions,
            "retractions": retractions,
            "by_department": _counts(row.department for row in active),
            "by_contribution_type": _counts(row.contribution_type for row in active),
        },
        outcomes,
        active,
    )


def _work_metrics(session: Session, tenant_key: str, as_of: datetime) -> dict[str, Any]:
    rows: list[OrganizationalWorkItem] = _tenant_rows(
        session, OrganizationalWorkItem, tenant_key
    )
    active = [row for row in rows if row.status not in TERMINAL_WORK_STATUSES]
    terminal = [row for row in rows if row.status in TERMINAL_WORK_STATUSES]
    overdue = [
        row
        for row in active
        if row.due_at is not None and (_as_utc(row.due_at) or as_of) <= as_of
    ]
    oldest = min((_as_utc(row.created_at) for row in active), default=None)
    return {
        "total": len(rows),
        "active": len(active),
        "terminal": len(terminal),
        "overdue_active": len(overdue),
        "oldest_active_created_at": oldest,
        "by_status": _counts(row.status for row in rows),
        "by_department": _counts(row.department for row in rows),
        "by_priority": _counts(row.priority for row in rows),
    }


def _blocker_metrics(session: Session, tenant_key: str, as_of: datetime) -> dict[str, Any]:
    rows: list[OrganizationBlocker] = _tenant_rows(session, OrganizationBlocker, tenant_key)
    active = [row for row in rows if _enum_value(row.status) in ACTIVE_BLOCKER_STATUSES]
    opened = [row for row in active if _enum_value(row.status) == OrganizationBlockerStatus.open.value]
    mitigated = [
        row
        for row in active
        if _enum_value(row.status) == OrganizationBlockerStatus.mitigated.value
    ]
    due = [
        row
        for row in opened
        if row.due_at is not None and (_as_utc(row.due_at) or as_of) <= as_of
    ]
    return {
        "total": len(rows),
        "open": len(opened),
        "mitigated": len(mitigated),
        "due_or_overdue_open": len(due),
        "by_severity": _counts(row.severity for row in active),
        "by_department": _counts((row.department or "unassigned") for row in active),
    }


def _decision_metrics(session: Session, tenant_key: str) -> dict[str, Any]:
    rows: list[ExecutiveDecision] = _tenant_rows(session, ExecutiveDecision, tenant_key)
    pending = [row for row in rows if row.status in PENDING_DECISION_STATUSES]
    board_attention = [
        row
        for row in pending
        if row.status == "pending_board"
        or row.authority_level == "L4"
        or _enum_value(row.decision_type) == "board_reserved"
    ]
    return {
        "total": len(rows),
        "pending": len(pending),
        "board_attention": len(board_attention),
        "by_status": _counts(row.status for row in rows),
    }


def _human_attention_metrics(session: Session, tenant_key: str, as_of: datetime) -> dict[str, Any]:
    requests: list[OrganizationHumanActionRequest] = _tenant_rows(
        session, OrganizationHumanActionRequest, tenant_key
    )
    actions: list[OrganizationHumanAction] = _tenant_rows(
        session, OrganizationHumanAction, tenant_key
    )
    pending = [
        row for row in requests if _enum_value(row.status) in PENDING_HUMAN_REQUEST_STATUSES
    ]
    overdue = [
        row
        for row in pending
        if row.due_at is not None and (_as_utc(row.due_at) or as_of) <= as_of
    ]
    return {
        "request_total": len(requests),
        "pending_requests": len(pending),
        "overdue_pending_requests": len(overdue),
        "immutable_human_actions": len(actions),
        "by_request_status": _counts(row.status for row in requests),
    }


def _dependency_metrics(session: Session, tenant_key: str) -> dict[str, Any]:
    rows: list[OrganizationWorkItemDependency] = _tenant_rows(
        session, OrganizationWorkItemDependency, tenant_key
    )
    active = [
        row
        for row in rows
        if _enum_value(row.status) == OrganizationDependencyStatus.active.value
    ]
    blocking = {
        row.work_item_id
        for row in active
        if _enum_value(row.dependency_type)
        in {
            OrganizationDependencyType.blocks.value,
            OrganizationDependencyType.requires.value,
        }
    }
    return {
        "total": len(rows),
        "active_edges": len(active),
        "blocked_downstream_work_items": len(blocking),
        "by_status": _counts(row.status for row in rows),
        "by_type": _counts(row.dependency_type for row in active),
    }


def _evidence_entry(contribution: OrganizationContribution) -> Mapping[str, Any] | None:
    payload = _json(contribution.evidence_summary_json, [])
    if not isinstance(payload, list):
        return None
    for item in payload:
        if not isinstance(item, dict):
            continue
        if str(item.get("source_type", "")).strip().lower() == contribution.source_object_type:
            return item
    return None


def _source_certification_review_evidence(
    session: Session,
    certification_id: UUID,
) -> Mapping[str, Any] | None:
    audits = list(
        session.exec(
            select(AuditLog)
            .where(
                AuditLog.action == "jurisdiction_source_certification_reviewed",
                AuditLog.entity_type == "jurisdiction_source_certification",
                AuditLog.entity_id == str(certification_id),
            )
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        ).all()
    )
    for audit in audits:
        payload = _json(audit.after_state_json, {})
        if isinstance(payload, dict) and isinstance(payload.get("review_evidence"), dict):
            return payload["review_evidence"]
    return None


def _uuid(value: str) -> UUID | None:
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _executive_decision_state(
    session: Session,
    tenant_key: str,
    source_id: str,
) -> _SourceState:
    decision_id = _uuid(source_id)
    if decision_id is None:
        return _SourceState(False, False, None, None, None, "decision source ID is not a UUID")
    decision = session.exec(
        select(ExecutiveDecision).where(
            ExecutiveDecision.id == decision_id,
            ExecutiveDecision.tenant_key == tenant_key,
        )
    ).first()
    if decision is None:
        return _SourceState(False, False, None, None, None, "executive decision source is missing")
    version = decision.record_fingerprint or decision.updated_at.isoformat()
    valid = (
        decision.status in {"approved", "rejected"}
        and bool(decision.decided_by)
        and decision.decided_at is not None
    )
    return _SourceState(
        True,
        valid,
        version,
        decision.status,
        _as_utc(decision.decided_at),
        "terminal attributed executive decision" if valid else "decision is no longer a terminal attributed outcome",
    )


def _source_certification_state(
    session: Session,
    tenant_key: str,
    source_id: str,
    *,
    review_evidence: Mapping[str, Any] | None,
) -> _SourceState:
    if tenant_key != DEFAULT_TENANT:
        return _SourceState(False, False, None, None, None, "legacy source certification is default-tenant only")
    certification_id = _uuid(source_id)
    if certification_id is None:
        return _SourceState(False, False, None, None, None, "certification source ID is not a UUID")
    certification = session.get(JurisdictionSourceCertification, certification_id)
    if certification is None:
        return _SourceState(False, False, None, None, None, "source certification is missing")
    valid = (
        certification.status in {"approved", "rejected"}
        and bool(certification.reviewed_by)
        and certification.reviewed_at is not None
        and certification.proposed_by.strip().casefold()
        != str(certification.reviewed_by or "").strip().casefold()
    )
    if not valid:
        return _SourceState(
            True,
            False,
            None,
            certification.status,
            _as_utc(certification.reviewed_at),
            "source certification is no longer a terminal independently reviewed outcome",
        )
    if review_evidence is None:
        review_evidence = _source_certification_review_evidence(session, certification.id)
    if review_evidence is None:
        contribution = session.exec(
            select(OrganizationContribution)
            .where(
                OrganizationContribution.tenant_key == tenant_key,
                OrganizationContribution.record_kind
                == OrganizationContributionRecordKind.outcome,
                OrganizationContribution.source_object_type
                == "jurisdiction_source_certification",
                OrganizationContribution.source_object_id == str(certification.id),
            )
            .order_by(
                OrganizationContribution.created_at.desc(),
                OrganizationContribution.id.desc(),
            )
        ).first()
        if contribution is not None:
            entry = _evidence_entry(contribution)
            candidate_evidence = (
                entry.get("review_evidence") if isinstance(entry, Mapping) else None
            )
            if isinstance(candidate_evidence, Mapping):
                review_evidence = candidate_evidence
    if review_evidence is None:
        return _SourceState(
            True,
            True,
            None,
            certification.status,
            _as_utc(certification.reviewed_at),
            "source certification review evidence is unavailable for exact version reconciliation",
        )
    if str(review_evidence.get("decision", "")).strip().lower() != certification.status:
        return _SourceState(
            True,
            False,
            None,
            certification.status,
            _as_utc(certification.reviewed_at),
            "source certification review evidence no longer matches the terminal state",
        )
    if bool(review_evidence.get("structured_review_pack_required")):
        evidence_hash = str(review_evidence.get("evidence_pack_sha256", "")).strip().lower()
        if (
            review_evidence.get("independent_human_attestation") is not True
            or len(evidence_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in evidence_hash)
            or not str(review_evidence.get("source_snapshot_id", "")).strip()
        ):
            return _SourceState(
                True,
                False,
                None,
                certification.status,
                _as_utc(certification.reviewed_at),
                "structured source-certification review evidence no longer satisfies the accepted D2 gate",
            )
    version = _source_certification_review_version(certification, review_evidence)
    return _SourceState(
        True,
        True,
        version,
        certification.status,
        _as_utc(certification.reviewed_at),
        "terminal independently reviewed source certification",
    )


def _initial_rule_state(
    session: Session,
    tenant_key: str,
    source_id: str,
) -> _SourceState:
    if tenant_key != DEFAULT_TENANT:
        return _SourceState(False, False, None, None, None, "legacy initial-rule source is default-tenant only")
    assertion_id = _uuid(source_id)
    if assertion_id is None:
        return _SourceState(False, False, None, None, None, "initial-rule source ID is not a UUID")
    assertion = session.get(InitialRuleAssertion, assertion_id)
    if assertion is None:
        return _SourceState(False, False, None, None, None, "initial rule assertion is missing")
    if assertion.status != "published" or assertion.published_rule_id is None or assertion.published_at is None:
        return _SourceState(
            True,
            False,
            None,
            assertion.status,
            _as_utc(assertion.published_at),
            "initial rule assertion is no longer in its published authoritative state",
        )
    rule = session.get(VerifiedRule, assertion.published_rule_id)
    if rule is None:
        return _SourceState(True, False, None, assertion.status, _as_utc(assertion.published_at), "published VerifiedRule is missing")
    source = session.get(OfficialSource, assertion.official_source_id)
    snapshot = session.get(SourceSnapshot, assertion.source_snapshot_id)
    if source is None or snapshot is None or snapshot.official_source_id != assertion.official_source_id:
        return _SourceState(
            True,
            False,
            None,
            assertion.status,
            _as_utc(assertion.published_at),
            "initial-rule official-source or immutable snapshot provenance is missing",
        )
    valid = (
        rule.initial_rule_assertion_id == assertion.id
        and rule.regulatory_change_id is None
        and rule.jurisdiction_id == assertion.jurisdiction_id
        and rule.official_source_id == assertion.official_source_id
        and rule.source_snapshot_id == assertion.source_snapshot_id
        and rule.rule_key == assertion.rule_key
        and rule.domain == assertion.domain
        and rule.statement == assertion.statement
        and rule.confidence == assertion.confidence
        and rule.effective_from == assertion.effective_from
        and rule.effective_to == assertion.effective_to
        and rule.active
        and bool(rule.approved_by)
        and rule.published_at is not None
        and bool(assertion.reviewed_by)
        and assertion.reviewed_at is not None
        and bool(assertion.published_by)
        and assertion.proposed_by.strip().casefold()
        != str(assertion.reviewed_by or "").strip().casefold()
        and assertion.proposed_by.strip().casefold()
        != str(assertion.published_by or "").strip().casefold()
        and str(rule.approved_by or "").strip().casefold()
        == str(assertion.published_by or "").strip().casefold()
        and _as_utc(rule.published_at) == _as_utc(assertion.published_at)
    )
    if not valid:
        return _SourceState(
            True,
            False,
            None,
            assertion.status,
            _as_utc(assertion.published_at),
            "initial-rule / VerifiedRule provenance or active publication state has drifted",
        )
    version = _initial_rule_publication_version(assertion, rule)
    return _SourceState(
        True,
        True,
        version,
        "published",
        _as_utc(assertion.published_at),
        "published initial-rule assertion reconciles to its active VerifiedRule",
    )


def _regulatory_rule_for_change(
    session: Session,
    change: RegulatoryChange,
    contribution: OrganizationContribution | None,
) -> VerifiedRule | None:
    if contribution is not None:
        entry = _evidence_entry(contribution)
        if entry is not None:
            rule_id = _uuid(str(entry.get("verified_rule_id", "")))
            if rule_id is not None:
                return session.get(VerifiedRule, rule_id)
    return session.exec(
        select(VerifiedRule)
        .where(VerifiedRule.regulatory_change_id == change.id)
        .order_by(VerifiedRule.published_at.desc(), VerifiedRule.created_at.desc(), VerifiedRule.id.desc())
    ).first()


def _regulatory_change_state(
    session: Session,
    tenant_key: str,
    source_id: str,
    *,
    contribution: OrganizationContribution | None = None,
) -> _SourceState:
    if tenant_key != DEFAULT_TENANT:
        return _SourceState(False, False, None, None, None, "legacy regulatory-change source is default-tenant only")
    change_id = _uuid(source_id)
    if change_id is None:
        return _SourceState(False, False, None, None, None, "regulatory-change source ID is not a UUID")
    change = session.get(RegulatoryChange, change_id)
    if change is None:
        return _SourceState(False, False, None, None, None, "regulatory change is missing")
    if change.status != "published" or change.published_at is None or not change.reviewed_by or change.reviewed_at is None:
        return _SourceState(
            True,
            False,
            None,
            change.status,
            _as_utc(change.published_at),
            "regulatory change is no longer a reviewed published outcome",
        )
    snapshot = session.get(SourceSnapshot, change.current_snapshot_id)
    if snapshot is None:
        return _SourceState(True, False, None, change.status, _as_utc(change.published_at), "current source snapshot is missing")
    snapshot_hash = str(snapshot.content_hash or "").strip().lower()
    if (
        snapshot.official_source_id != change.official_source_id
        or len(snapshot_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in snapshot_hash)
    ):
        return _SourceState(True, False, None, change.status, _as_utc(change.published_at), "regulatory-change immutable snapshot provenance has drifted")
    rule = _regulatory_rule_for_change(session, change, contribution)
    if rule is None:
        return _SourceState(True, False, None, change.status, _as_utc(change.published_at), "published regulatory-change VerifiedRule is missing")
    valid = (
        rule.regulatory_change_id == change.id
        and rule.initial_rule_assertion_id is None
        and rule.jurisdiction_id == change.jurisdiction_id
        and rule.official_source_id == change.official_source_id
        and rule.source_snapshot_id == change.current_snapshot_id
        and rule.domain == change.domain
        and rule.active
        and bool(rule.approved_by)
        and rule.published_at is not None
        and _as_utc(rule.published_at) == _as_utc(change.published_at)
    )
    if rule.supersedes_rule_id is not None:
        previous = session.get(VerifiedRule, rule.supersedes_rule_id)
        valid = valid and previous is not None and not bool(previous.active)
    if not valid:
        return _SourceState(True, False, None, change.status, _as_utc(change.published_at), "regulatory-change / VerifiedRule publication state or provenance has drifted")
    version = _regulatory_change_publication_version(change, rule)
    return _SourceState(
        True,
        True,
        version,
        "published",
        _as_utc(change.published_at),
        "published regulatory change reconciles to its active VerifiedRule",
    )


def _pathway_version_state(
    session: Session,
    tenant_key: str,
    source_id: str,
) -> _SourceState:
    if tenant_key != DEFAULT_TENANT:
        return _SourceState(False, False, None, None, None, "legacy pathway-version source is default-tenant only")
    version_id = _uuid(source_id)
    if version_id is None:
        return _SourceState(False, False, None, None, None, "pathway-version source ID is not a UUID")
    version = session.get(MobilityPathwayVersion, version_id)
    if version is None:
        return _SourceState(False, False, None, None, None, "mobility pathway version is missing")
    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None:
        return _SourceState(True, False, None, version.lifecycle_status, _as_utc(version.published_at), "mobility pathway is missing")
    if (
        version.lifecycle_status != "published"
        or pathway.catalogue_status != "active"
        or not version.approved_by
        or version.published_at is None
    ):
        return _SourceState(
            True,
            False,
            None,
            version.lifecycle_status,
            _as_utc(version.published_at),
            "pathway version is no longer the active published catalogue version",
        )
    from app.services.pathway_catalogue import _publication_evidence_blockers

    blockers = _publication_evidence_blockers(session, pathway, version)
    if blockers:
        return _SourceState(
            True,
            False,
            None,
            version.lifecycle_status,
            _as_utc(version.published_at),
            "pathway publication evidence gate has drifted: " + blockers[0],
        )
    try:
        version_hash = _pathway_publication_version(session, pathway, version)
    except Exception as exc:  # read-only reconciliation reports malformed provenance; it never repairs it
        return _SourceState(
            True,
            False,
            None,
            version.lifecycle_status,
            _as_utc(version.published_at),
            f"pathway publication provenance cannot be reconstructed: {exc}",
        )
    return _SourceState(
        True,
        True,
        version_hash,
        "published",
        _as_utc(version.published_at),
        "published pathway version satisfies the current catalogue evidence gate",
    )


def _current_source_state(
    session: Session,
    tenant_key: str,
    contribution: OrganizationContribution,
) -> _SourceState:
    source_type = contribution.source_object_type
    if source_type == "executive_decision":
        return _executive_decision_state(session, tenant_key, contribution.source_object_id)
    if source_type == "jurisdiction_source_certification":
        entry = _evidence_entry(contribution)
        review_evidence = entry.get("review_evidence") if isinstance(entry, Mapping) else None
        return _source_certification_state(
            session,
            tenant_key,
            contribution.source_object_id,
            review_evidence=review_evidence if isinstance(review_evidence, Mapping) else None,
        )
    if source_type == "initial_rule_assertion":
        return _initial_rule_state(session, tenant_key, contribution.source_object_id)
    if source_type == "regulatory_change":
        return _regulatory_change_state(
            session,
            tenant_key,
            contribution.source_object_id,
            contribution=contribution,
        )
    if source_type == "mobility_pathway_version":
        return _pathway_version_state(session, tenant_key, contribution.source_object_id)
    return _SourceState(
        False,
        False,
        None,
        None,
        None,
        f"source type {source_type!r} is outside the accepted Observatory reconciliation contract",
    )


def _automatic_candidates(session: Session, tenant_key: str, source_type: str) -> list[_SourceCandidate]:
    if tenant_key != DEFAULT_TENANT:
        return []
    candidates: list[_SourceCandidate] = []
    if source_type == "jurisdiction_source_certification":
        rows = list(session.exec(select(JurisdictionSourceCertification)).all())
        for row in rows:
            if row.status not in {"approved", "rejected"} or row.reviewed_at is None:
                continue
            state = _source_certification_state(
                session,
                tenant_key,
                str(row.id),
                review_evidence=None,
            )
            candidates.append(
                _SourceCandidate(
                    source_type,
                    str(row.id),
                    row.status,
                    state.source_version,
                    _as_utc(row.reviewed_at) or _now_utc(),
                    state.detail,
                )
            )
    elif source_type == "initial_rule_assertion":
        rows = list(
            session.exec(
                select(InitialRuleAssertion).where(InitialRuleAssertion.status == "published")
            ).all()
        )
        for row in rows:
            if row.published_at is None:
                continue
            state = _initial_rule_state(session, tenant_key, str(row.id))
            candidates.append(
                _SourceCandidate(
                    source_type,
                    str(row.id),
                    row.status,
                    state.source_version,
                    _as_utc(row.published_at) or _now_utc(),
                    state.detail,
                )
            )
    elif source_type == "regulatory_change":
        rows = list(
            session.exec(select(RegulatoryChange).where(RegulatoryChange.status == "published")).all()
        )
        for row in rows:
            if row.published_at is None:
                continue
            state = _regulatory_change_state(session, tenant_key, str(row.id))
            candidates.append(
                _SourceCandidate(
                    source_type,
                    str(row.id),
                    row.status,
                    state.source_version,
                    _as_utc(row.published_at) or _now_utc(),
                    state.detail,
                )
            )
    elif source_type == "mobility_pathway_version":
        rows = list(
            session.exec(
                select(MobilityPathwayVersion).where(
                    MobilityPathwayVersion.lifecycle_status == "published"
                )
            ).all()
        )
        for row in rows:
            if row.published_at is None:
                continue
            pathway = session.get(MobilityPathway, row.pathway_id)
            if pathway is None or pathway.catalogue_status != "active":
                continue
            state = _pathway_version_state(session, tenant_key, str(row.id))
            candidates.append(
                _SourceCandidate(
                    source_type,
                    str(row.id),
                    row.lifecycle_status,
                    state.source_version,
                    _as_utc(row.published_at) or _now_utc(),
                    state.detail,
                )
            )
    return candidates


def _reconciliation_state(
    session: Session,
    tenant_key: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    outcomes, _corrections = _outcomes_and_corrections(session, tenant_key)
    accepted = [row for row in outcomes if row.source_object_type in ACCEPTED_SOURCE_TYPES]
    unsupported = [row for row in outcomes if row.source_object_type not in ACCEPTED_SOURCE_TYPES]

    by_identity: dict[tuple[str, str, str], list[OrganizationContribution]] = defaultdict(list)
    for row in accepted:
        by_identity[(row.source_object_type, row.source_object_id, row.source_object_version)].append(row)

    coverage: list[dict[str, Any]] = []
    gap_items: list[dict[str, Any]] = []
    warnings: list[str] = []

    exec_outcomes = [row for row in accepted if row.source_object_type == "executive_decision"]
    terminal_decisions = list(
        session.exec(
            select(ExecutiveDecision).where(
                ExecutiveDecision.tenant_key == tenant_key,
                ExecutiveDecision.status.in_(["approved", "rejected"]),
            )
        ).all()
    )
    matched_exec = 0
    for row in exec_outcomes:
        state = _current_source_state(session, tenant_key, row)
        if (
            state.exists
            and state.valid_state
            and state.source_state == row.source_state
            and state.source_version == row.source_object_version
        ):
            matched_exec += 1
    coverage.append(
        {
            "source_type": "executive_decision",
            "automatic_emitter": False,
            "coverage_basis": "explicit_command_only",
            "coverage_start": None,
            "coverage_established": True,
            "contribution_outcome_count": len(exec_outcomes),
            "eligible_source_rows": len(terminal_decisions),
            "matched_source_rows": matched_exec,
            "precoverage_source_rows": 0,
            "missing_contribution_in_coverage": 0,
            "warnings": [
                "ExecutiveDecision remains explicit-command-only; terminal decisions without Contributions are not completeness gaps."
            ],
        }
    )

    for source_type in AUTOMATIC_SOURCE_TYPES:
        type_outcomes = [row for row in accepted if row.source_object_type == source_type]
        coverage_start = min(
            (_as_utc(row.created_at) for row in type_outcomes if row.created_at is not None),
            default=None,
        )
        candidates = _automatic_candidates(session, tenant_key, source_type)
        precoverage = 0
        matched = 0
        missing = 0
        local_warnings: list[str] = []
        if coverage_start is None:
            basis = "not_established"
            established = False
            if candidates:
                local_warnings.append(
                    "Automatic-emitter coverage is not established because no observed Contribution exists; source completeness is not assessed."
                )
        else:
            basis = "first_observed_contribution"
            established = True
            for candidate in candidates:
                exact = (
                    candidate.source_version is not None
                    and (
                        source_type,
                        candidate.source_id,
                        candidate.source_version,
                    )
                    in by_identity
                )
                if exact:
                    matched += 1
                    continue
                if candidate.transition_at < coverage_start:
                    precoverage += 1
                    continue
                prior_for_source = any(
                    row.source_object_type == source_type
                    and row.source_object_id == candidate.source_id
                    for row in type_outcomes
                )
                if prior_for_source:
                    # The Contribution-side row will surface state/version drift. Do not
                    # also call the same authoritative transition "missing" merely
                    # because its current source version has changed after publication.
                    continue
                missing += 1
                gap_items.append(
                    {
                        "status": "missing_contribution_in_coverage",
                        "source_type": source_type,
                        "source_id": candidate.source_id,
                        "contribution_id": None,
                        "contribution_key": None,
                        "contribution_source_version": None,
                        "current_source_version": candidate.source_version,
                        "source_state": None,
                        "current_source_state": candidate.source_state,
                        "source_transition_at": candidate.transition_at,
                        "contribution_created_at": None,
                        "coverage_basis": basis,
                        "duplicate_contribution_ids": [],
                        "detail": (
                            "Eligible authoritative source transition is inside established automatic-emitter coverage but has no exact Contribution. "
                            + candidate.detail
                        ),
                    }
                )
        coverage.append(
            {
                "source_type": source_type,
                "automatic_emitter": True,
                "coverage_basis": basis,
                "coverage_start": coverage_start,
                "coverage_established": established,
                "contribution_outcome_count": len(type_outcomes),
                "eligible_source_rows": len(candidates),
                "matched_source_rows": matched,
                "precoverage_source_rows": precoverage,
                "missing_contribution_in_coverage": missing,
                "warnings": local_warnings,
            }
        )

    contribution_items: list[dict[str, Any]] = []
    for row in accepted:
        identity = (row.source_object_type, row.source_object_id, row.source_object_version)
        duplicates = by_identity[identity]
        source = _current_source_state(session, tenant_key, row)
        basis = (
            "explicit_command_only"
            if row.source_object_type == "executive_decision"
            else "first_observed_contribution"
        )
        if len(duplicates) > 1:
            status = "duplicate_outcome"
            detail = "More than one outcome Contribution exists for the same source identity and version."
        elif not source.exists:
            status = "missing_source"
            detail = source.detail
        elif not source.valid_state or source.source_state != row.source_state:
            status = "source_state_drift"
            detail = source.detail
        elif source.source_version is None or source.source_version != row.source_object_version:
            status = "source_version_drift"
            detail = source.detail
        else:
            status = "matched"
            detail = source.detail
        contribution_items.append(
            {
                "status": status,
                "source_type": row.source_object_type,
                "source_id": row.source_object_id,
                "contribution_id": row.id,
                "contribution_key": row.contribution_key,
                "contribution_source_version": row.source_object_version,
                "current_source_version": source.source_version,
                "source_state": row.source_state,
                "current_source_state": source.source_state,
                "source_transition_at": source.transition_at,
                "contribution_created_at": _as_utc(row.created_at),
                "coverage_basis": basis,
                "duplicate_contribution_ids": sorted(
                    [duplicate.id for duplicate in duplicates if duplicate.id != row.id],
                    key=str,
                ),
                "detail": detail,
            }
        )

    for row in unsupported:
        contribution_items.append(
            {
                "status": "unsupported_source",
                "source_type": row.source_object_type,
                "source_id": row.source_object_id,
                "contribution_id": row.id,
                "contribution_key": row.contribution_key,
                "contribution_source_version": row.source_object_version,
                "current_source_version": None,
                "source_state": row.source_state,
                "current_source_state": None,
                "source_transition_at": None,
                "contribution_created_at": _as_utc(row.created_at),
                "coverage_basis": "not_established",
                "duplicate_contribution_ids": [],
                "detail": "Contribution source type is outside the accepted Observatory reconciliation contract.",
            }
        )
    if unsupported:
        warnings.append(
            "One or more outcome Contributions use source types outside the accepted E1 reconciliation contract."
        )
    if any(item["status"] != "matched" for item in contribution_items) or gap_items:
        warnings.append(
            "Contribution reconciliation contains visible gaps or drift; GET responses never repair or re-emit records."
        )
    if tenant_key == DEFAULT_TENANT:
        warnings.append(
            "Legacy certification/rule/regulatory/pathway source tables are reconciled explicitly to the default tenant only."
        )
    return coverage, contribution_items + gap_items, warnings


def observatory_summary(
    session: Session,
    tenant_key: str,
    *,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    instant = _as_utc(as_of) or _now_utc()
    contribution_metrics, _outcomes, _active = _contribution_metrics(session, tenant_key)
    coverage, _items, reconciliation_warnings = _reconciliation_state(session, tenant_key)
    warnings = [
        "Historical throughput, cycle-time, resolved-blocker period metrics, and last-material-transition ageing are unavailable until curated Activity transition coverage is complete."
    ]
    warnings.extend(reconciliation_warnings)
    return {
        "as_of": instant,
        "timezone": "UTC",
        "tenant_scope": tenant_key,
        "source_row_counts": source_row_counts(session, tenant_key),
        "metrics": {
            "work": _work_metrics(session, tenant_key, instant),
            "blockers": _blocker_metrics(session, tenant_key, instant),
            "decisions": _decision_metrics(session, tenant_key),
            "human_attention": _human_attention_metrics(session, tenant_key, instant),
            "dependencies": _dependency_metrics(session, tenant_key),
            "contributions": contribution_metrics,
        },
        "coverage": {
            "snapshot_basis": "authoritative_current_rows",
            "activity_history_basis": "partial_activity_coverage",
            "activity_history_established": False,
            "contribution_sources": coverage,
        },
        "warnings": warnings,
    }


def observatory_departments(
    session: Session,
    tenant_key: str,
    *,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    instant = _as_utc(as_of) or _now_utc()
    work: list[OrganizationalWorkItem] = _tenant_rows(session, OrganizationalWorkItem, tenant_key)
    blockers: list[OrganizationBlocker] = _tenant_rows(session, OrganizationBlocker, tenant_key)
    requests: list[OrganizationHumanActionRequest] = _tenant_rows(
        session, OrganizationHumanActionRequest, tenant_key
    )
    outcomes, corrections = _outcomes_and_corrections(session, tenant_key)
    active_outcomes = _active_outcomes(outcomes, corrections)
    work_by_id = {row.id: row for row in work}

    def blocker_department(row: OrganizationBlocker) -> str | None:
        if row.work_item_id is not None:
            work_item = work_by_id.get(row.work_item_id)
            if work_item is not None:
                return work_item.department
        return row.department

    departments = {
        row.department for row in work if row.department
    } | {
        department
        for row in blockers
        if (department := blocker_department(row)) is not None
    } | {
        row.department for row in outcomes if row.department
    }
    rows: list[dict[str, Any]] = []
    for department in sorted(departments):
        department_work = [row for row in work if row.department == department]
        department_blockers = [
            row for row in blockers if blocker_department(row) == department
        ]
        department_outcomes = [row for row in outcomes if row.department == department]
        department_active_outcomes = [
            row for row in active_outcomes if row.department == department
        ]
        linked_pending_requests = [
            row
            for row in requests
            if _enum_value(row.status) in PENDING_HUMAN_REQUEST_STATUSES
            and row.work_item_id is not None
            and row.work_item_id in work_by_id
            and work_by_id[row.work_item_id].department == department
        ]
        rows.append(
            {
                "department": department,
                "work_items_total": len(department_work),
                "work_items_active": sum(
                    row.status not in TERMINAL_WORK_STATUSES for row in department_work
                ),
                "work_items_terminal": sum(
                    row.status in TERMINAL_WORK_STATUSES for row in department_work
                ),
                "blockers_open": sum(
                    _enum_value(row.status) == OrganizationBlockerStatus.open.value
                    for row in department_blockers
                ),
                "blockers_mitigated": sum(
                    _enum_value(row.status) == OrganizationBlockerStatus.mitigated.value
                    for row in department_blockers
                ),
                "historical_contribution_outcomes": len(department_outcomes),
                "active_contributions": len(department_active_outcomes),
                "pending_human_action_requests_linked_to_work": len(linked_pending_requests),
            }
        )

    coverage, _items, reconciliation_warnings = _reconciliation_state(session, tenant_key)
    warnings = [
        "Department metrics are point-in-time snapshots; transition throughput and cycle-time remain unavailable until curated Activity coverage is complete.",
        "Human-action requests without a WorkItem department are intentionally not attributed to a department.",
    ]
    warnings.extend(reconciliation_warnings)
    return {
        "as_of": instant,
        "timezone": "UTC",
        "tenant_scope": tenant_key,
        "source_row_counts": source_row_counts(session, tenant_key),
        "coverage": {
            "snapshot_basis": "authoritative_current_rows",
            "activity_history_basis": "partial_activity_coverage",
            "activity_history_established": False,
            "contribution_sources": coverage,
        },
        "departments": rows,
        "warnings": warnings,
    }


def observatory_contribution_reconciliation(
    session: Session,
    tenant_key: str,
    *,
    page: int,
    page_size: int,
    source_type: str | None = None,
    reconciliation_status: str | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    instant = _as_utc(as_of) or _now_utc()
    coverage, items, warnings = _reconciliation_state(session, tenant_key)
    if source_type is not None:
        normalized = source_type.strip().lower()
        items = [item for item in items if item["source_type"] == normalized]
        coverage = [item for item in coverage if item["source_type"] == normalized]
    if reconciliation_status is not None:
        items = [item for item in items if item["status"] == reconciliation_status]

    def sort_key(item: dict[str, Any]) -> tuple[datetime, str, str, str]:
        event_at = item.get("contribution_created_at") or item.get("source_transition_at")
        event = _as_utc(event_at) or datetime.min.replace(tzinfo=timezone.utc)
        return (event, item["source_type"], item["source_id"], str(item.get("contribution_id") or ""))

    items.sort(key=sort_key, reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    data = items[start : start + page_size]
    return {
        "as_of": instant,
        "timezone": "UTC",
        "tenant_scope": tenant_key,
        "source_row_counts": source_row_counts(session, tenant_key),
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size) if total else 0,
        "coverage": coverage,
        "data": data,
        "warnings": warnings,
    }
