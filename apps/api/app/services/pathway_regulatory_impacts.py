from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityTimeline,
    PathwayComparisonAssessment,
    PathwayRegulatoryImpact,
    RegulatoryChange,
    RegulatoryKnowledgeNode,
    VerifiedRule,
    now_utc,
)
from app.schemas import PathwayRegulatoryImpactRead, PathwayRegulatoryImpactReviewRequest
from app.services.audit_log import record_audit


GRAPH_PROJECTION_VERSION = "regulatory-graph-v1"
TERMINAL_STATUSES = {"no_change_required", "resolved"}


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _normal(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _relevant_rule_domains(pathway_domain: str) -> set[str]:
    return {
        "study": {"study", "visa"},
        "work": {"work", "visa"},
        "visa": {"visa"},
        "scholarship": {"scholarship", "study"},
        "settlement": {"settlement", "visa"},
        "family": {"family", "visa"},
        "digital_nomad": {"digital_nomad", "work", "visa"},
    }.get(_normal(pathway_domain), {_normal(pathway_domain)})


def _event_type(rule: VerifiedRule) -> str:
    if rule.active:
        return "rule_supersession" if rule.supersedes_rule_id else "rule_published"
    return "rule_retired"


def _event_at(rule: VerifiedRule) -> datetime:
    if rule.active:
        return rule.published_at or rule.created_at
    return rule.retired_at or rule.effective_to or rule.updated_at


def _version_rule_ids(version: MobilityPathwayVersion) -> set[UUID]:
    values = _load(version.verified_rule_ids_json, [])
    result: set[UUID] = set()
    for value in values if isinstance(values, list) else []:
        try:
            result.add(UUID(str(value)))
        except (TypeError, ValueError):
            continue
    return result


def _candidate_versions(
    session: Session,
    rule: VerifiedRule,
    *,
    event_at: datetime,
) -> list[tuple[MobilityPathwayVersion, MobilityPathway, list[str]]]:
    rows = session.exec(
        select(MobilityPathwayVersion, MobilityPathway)
        .join(MobilityPathway, MobilityPathway.id == MobilityPathwayVersion.pathway_id)
        .where(MobilityPathwayVersion.lifecycle_status == "published")
    ).all()
    candidates: list[tuple[MobilityPathwayVersion, MobilityPathway, list[str]]] = []
    for version, pathway in rows:
        if version.published_at and _as_utc(version.published_at) > _as_utc(event_at):
            # The reviewed regulatory event predates this exact pathway version.
            # The publication gate should already have considered it.
            continue
        jurisdiction_match = bool(
            pathway.jurisdiction_id
            and rule.jurisdiction_id
            and pathway.jurisdiction_id == rule.jurisdiction_id
        )
        country_match = _normal(pathway.country) == _normal(rule.country)
        if not jurisdiction_match and not country_match:
            continue
        if _normal(rule.domain) not in _relevant_rule_domains(pathway.domain):
            continue

        version_rule_ids = _version_rule_ids(version)
        match_basis = [
            "jurisdiction_match" if jurisdiction_match else "country_match",
            "regulatory_domain_match",
        ]
        if rule.id in version_rule_ids:
            match_basis.append("direct_rule_reference")
        if rule.supersedes_rule_id and rule.supersedes_rule_id in version_rule_ids:
            match_basis.append("superseded_rule_reference")
        if version.official_source_id and version.official_source_id == rule.official_source_id:
            match_basis.append("official_source_match")
        candidates.append((version, pathway, match_basis))
    return candidates


def _historical_usage_counts(session: Session, pathway_version_id: UUID) -> tuple[int, int]:
    assessments = session.exec(
        select(PathwayComparisonAssessment.id).where(
            PathwayComparisonAssessment.primary_pathway_version_id == pathway_version_id
        )
    ).all()
    timelines = session.exec(
        select(MobilityTimeline.id).where(
            MobilityTimeline.primary_pathway_version_id == pathway_version_id
        )
    ).all()
    return len(assessments), len(timelines)


def link_rule_to_affected_pathways(
    session: Session,
    rule: VerifiedRule,
    *,
    actor: str,
    audit: bool = True,
) -> dict[str, int]:
    if not rule.approved_by or not rule.published_at:
        return {"created": 0, "existing": 0}
    if not rule.regulatory_change_id or not rule.source_snapshot_id:
        return {"created": 0, "existing": 0}
    change = session.get(RegulatoryChange, rule.regulatory_change_id)
    if change is None or change.status != "published" or not change.reviewed_by:
        return {"created": 0, "existing": 0}

    impact_type = _event_type(rule)
    event_at = _event_at(rule)
    graph_node = session.exec(
        select(RegulatoryKnowledgeNode).where(
            RegulatoryKnowledgeNode.node_key == f"verified_rule:{rule.id}"
        )
    ).first()
    created = 0
    existing = 0
    for version, pathway, match_basis in _candidate_versions(session, rule, event_at=event_at):
        impact_key = f"{version.id}:{rule.id}:{impact_type}"
        impact = session.exec(
            select(PathwayRegulatoryImpact).where(
                PathwayRegulatoryImpact.impact_key == impact_key
            )
        ).first()
        if impact is not None:
            if graph_node and impact.graph_rule_node_id != graph_node.id:
                impact.graph_rule_node_id = graph_node.id
                impact.updated_at = now_utc()
                session.add(impact)
            existing += 1
            continue

        assessment_count, timeline_count = _historical_usage_counts(session, version.id)
        impact = PathwayRegulatoryImpact(
            impact_key=impact_key,
            pathway_id=pathway.id,
            pathway_version_id=version.id,
            verified_rule_id=rule.id,
            superseded_rule_id=rule.supersedes_rule_id,
            regulatory_change_id=change.id,
            source_snapshot_id=rule.source_snapshot_id,
            graph_rule_node_id=graph_node.id if graph_node else None,
            graph_projection_version=GRAPH_PROJECTION_VERSION,
            impact_type=impact_type,
            status="pending_review",
            materiality=change.materiality,
            match_basis_json=_dump(match_basis),
            impact_context_json=_dump({
                "pathway_version_number": version.version_number,
                "pathway_version_lifecycle_status": version.lifecycle_status,
                "pathway_rule_ids": [str(value) for value in sorted(_version_rule_ids(version), key=str)],
                "pathway_official_source_id": version.official_source_id,
                "pathway_source_snapshot_id": version.source_snapshot_id,
                "rule_key": rule.rule_key,
                "rule_statement": rule.statement,
                "rule_active_at_detection": rule.active,
                "change_type": change.change_type,
                "change_title": change.title,
                "change_summary": change.summary,
            }),
            client_assessment_count_at_detection=assessment_count,
            timeline_count_at_detection=timeline_count,
            human_review_required=True,
            event_at=event_at,
        )
        session.add(impact)
        session.flush()
        created += 1

    if audit and (created or existing):
        record_audit(
            session,
            action="pathway_regulatory_impacts_linked",
            entity_type="verified_rule",
            entity_id=rule.id,
            after_state={
                "impact_type": impact_type,
                "created": created,
                "existing": existing,
                "graph_projection_version": GRAPH_PROJECTION_VERSION,
            },
            reason="Linked a human-published regulatory graph update to exact published pathway versions",
            actor=actor,
            source="pathway_regulatory_impacts_v10_6",
        )
    return {"created": created, "existing": existing}


def pathway_regulatory_impact_read(
    session: Session,
    impact: PathwayRegulatoryImpact,
) -> PathwayRegulatoryImpactRead:
    pathway = session.get(MobilityPathway, impact.pathway_id)
    version = session.get(MobilityPathwayVersion, impact.pathway_version_id)
    rule = session.get(VerifiedRule, impact.verified_rule_id)
    change = session.get(RegulatoryChange, impact.regulatory_change_id)
    if not pathway or not version or not rule or not change:
        raise ValueError("Pathway regulatory impact provenance is incomplete")
    return PathwayRegulatoryImpactRead(
        id=impact.id,
        impact_type=impact.impact_type,
        status=impact.status,
        materiality=impact.materiality,
        event_at=impact.event_at,
        pathway_id=pathway.id,
        pathway_key=pathway.pathway_key,
        pathway_name=pathway.name,
        pathway_country=pathway.country,
        pathway_domain=pathway.domain,
        pathway_version_id=version.id,
        pathway_version_number=version.version_number,
        pathway_version_lifecycle_status=version.lifecycle_status,
        verified_rule_id=rule.id,
        rule_key=rule.rule_key,
        rule_active=rule.active,
        superseded_rule_id=impact.superseded_rule_id,
        regulatory_change_id=change.id,
        change_type=change.change_type,
        source_snapshot_id=impact.source_snapshot_id,
        graph_rule_node_id=impact.graph_rule_node_id,
        graph_projection_version=impact.graph_projection_version,
        match_basis=_load(impact.match_basis_json, []),
        impact_context=_load(impact.impact_context_json, {}),
        client_assessment_count_at_detection=impact.client_assessment_count_at_detection,
        timeline_count_at_detection=impact.timeline_count_at_detection,
        client_assessments_unchanged=True,
        human_review_required=impact.human_review_required,
        reviewed_by=impact.reviewed_by,
        reviewed_at=impact.reviewed_at,
        review_notes=impact.review_notes,
        replacement_pathway_version_id=impact.replacement_pathway_version_id,
        created_at=impact.created_at,
        updated_at=impact.updated_at,
    )


def list_pathway_regulatory_impacts(
    session: Session,
    *,
    status: Optional[str] = None,
    pathway_id: Optional[UUID] = None,
    pathway_version_id: Optional[UUID] = None,
    verified_rule_id: Optional[UUID] = None,
    impact_type: Optional[str] = None,
    limit: int = 200,
) -> dict[str, Any]:
    statement = select(PathwayRegulatoryImpact)
    if status:
        statement = statement.where(PathwayRegulatoryImpact.status == status)
    if pathway_id:
        statement = statement.where(PathwayRegulatoryImpact.pathway_id == pathway_id)
    if pathway_version_id:
        statement = statement.where(PathwayRegulatoryImpact.pathway_version_id == pathway_version_id)
    if verified_rule_id:
        statement = statement.where(PathwayRegulatoryImpact.verified_rule_id == verified_rule_id)
    if impact_type:
        statement = statement.where(PathwayRegulatoryImpact.impact_type == impact_type)
    rows = session.exec(
        statement.order_by(PathwayRegulatoryImpact.event_at.desc()).limit(min(max(limit, 1), 500))
    ).all()
    counts = Counter(row.status for row in session.exec(select(PathwayRegulatoryImpact)).all())
    return {
        "total_returned": len(rows),
        "counts_by_status": dict(sorted(counts.items())),
        "pending_review": counts.get("pending_review", 0),
        "client_assessments_unchanged": True,
        "impacts": [pathway_regulatory_impact_read(session, row) for row in rows],
    }


def review_pathway_regulatory_impact(
    session: Session,
    impact_id: UUID,
    payload: PathwayRegulatoryImpactReviewRequest,
    *,
    actor: str,
) -> PathwayRegulatoryImpact:
    impact = session.get(PathwayRegulatoryImpact, impact_id)
    if impact is None:
        raise ValueError("Pathway regulatory impact not found")
    if impact.status in TERMINAL_STATUSES:
        raise ValueError("This pathway regulatory impact is already resolved")

    replacement: Optional[MobilityPathwayVersion] = None
    if payload.decision == "resolved":
        if payload.replacement_pathway_version_id is None:
            raise ValueError("A reviewed replacement pathway version is required to resolve this impact")
        replacement = session.get(MobilityPathwayVersion, payload.replacement_pathway_version_id)
        impacted_version = session.get(MobilityPathwayVersion, impact.pathway_version_id)
        if replacement is None or impacted_version is None:
            raise ValueError("Replacement pathway version not found")
        if replacement.pathway_id != impact.pathway_id:
            raise ValueError("Replacement pathway version must belong to the affected pathway")
        if replacement.version_number <= impacted_version.version_number:
            raise ValueError("Replacement pathway version must be newer than the affected version")
        if replacement.lifecycle_status not in {"published", "superseded"}:
            raise ValueError("Replacement pathway version must have completed human-reviewed publication")
    elif payload.replacement_pathway_version_id is not None:
        raise ValueError("Replacement pathway version is only accepted when resolving an impact")

    before = {
        "status": impact.status,
        "reviewed_by": impact.reviewed_by,
        "replacement_pathway_version_id": impact.replacement_pathway_version_id,
    }
    now = now_utc()
    impact.status = payload.decision
    impact.reviewed_by = actor
    impact.reviewed_at = now
    impact.review_notes = payload.notes
    impact.replacement_pathway_version_id = replacement.id if replacement else None
    impact.updated_at = now
    session.add(impact)
    record_audit(
        session,
        action="pathway_regulatory_impact_reviewed",
        entity_type="pathway_regulatory_impact",
        entity_id=impact.id,
        before_state=before,
        after_state={
            "status": impact.status,
            "reviewed_by": impact.reviewed_by,
            "replacement_pathway_version_id": impact.replacement_pathway_version_id,
            "client_assessments_unchanged": True,
        },
        reason=payload.notes,
        actor=actor,
        source="pathway_regulatory_impacts_v10_6",
    )
    session.commit()
    session.refresh(impact)
    return impact
