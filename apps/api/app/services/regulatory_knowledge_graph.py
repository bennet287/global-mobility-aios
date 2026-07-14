from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    OfficialSource,
    RegulatoryAuthority,
    RegulatoryChange,
    RegulatoryKnowledgeEdge,
    RegulatoryKnowledgeNode,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.audit_log import record_audit


PROJECTION_VERSION = "regulatory-graph-v1"


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: Optional[str]) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _published_context(session: Session, rule: VerifiedRule) -> dict[str, Any]:
    if not rule.approved_by or not rule.published_at:
        raise ValueError("Only a human-published verified rule can update the regulatory graph")
    if not rule.jurisdiction_id or not rule.official_source_id or not rule.source_snapshot_id:
        raise ValueError("Published rule provenance is incomplete")
    if not rule.regulatory_change_id:
        raise ValueError("Published rule is not linked to a reviewed regulatory change")
    jurisdiction = session.get(Jurisdiction, rule.jurisdiction_id)
    source = session.get(OfficialSource, rule.official_source_id)
    snapshot = session.get(SourceSnapshot, rule.source_snapshot_id)
    change = session.get(RegulatoryChange, rule.regulatory_change_id)
    if not jurisdiction or not source or not snapshot or not change:
        raise ValueError("Published rule provenance records could not be resolved")
    if change.status != "published" or not change.reviewed_by or not change.reviewed_at:
        raise ValueError("Regulatory change has not completed human review and publication")
    if snapshot.official_source_id != source.id or change.current_snapshot_id != snapshot.id:
        raise ValueError("Published rule snapshot provenance does not match its source change")
    if change.official_source_id != source.id or change.jurisdiction_id != jurisdiction.id:
        raise ValueError("Published rule source or jurisdiction provenance is inconsistent")
    authority = (
        session.get(RegulatoryAuthority, source.regulatory_authority_id)
        if source.regulatory_authority_id else None
    )
    return {
        "jurisdiction": jurisdiction,
        "source": source,
        "snapshot": snapshot,
        "change": change,
        "authority": authority,
    }


def _upsert_node(
    session: Session,
    *,
    node_key: str,
    node_type: str,
    label: str,
    properties: dict[str, Any],
    rule: VerifiedRule,
) -> RegulatoryKnowledgeNode:
    node = session.exec(
        select(RegulatoryKnowledgeNode).where(RegulatoryKnowledgeNode.node_key == node_key)
    ).first()
    if node is None:
        node = RegulatoryKnowledgeNode(
            node_key=node_key,
            node_type=node_type,
            label=label,
            properties_json=_dump(properties),
            active=True,
            created_from_verified_rule_id=rule.id,
            last_verified_rule_id=rule.id,
        )
    else:
        node.node_type = node_type
        node.label = label
        node.properties_json = _dump(properties)
        node.active = True
        node.last_verified_rule_id = rule.id
        node.updated_at = now_utc()
    session.add(node)
    session.flush()
    return node


def _upsert_edge(
    session: Session,
    *,
    source: RegulatoryKnowledgeNode,
    target: RegulatoryKnowledgeNode,
    relation_type: str,
    rule: VerifiedRule,
) -> RegulatoryKnowledgeEdge:
    edge_key = f"{rule.id}:{relation_type}:{source.node_key}:{target.node_key}"
    edge = session.exec(
        select(RegulatoryKnowledgeEdge).where(RegulatoryKnowledgeEdge.edge_key == edge_key)
    ).first()
    if edge is None:
        edge = RegulatoryKnowledgeEdge(
            edge_key=edge_key,
            source_node_id=source.id,
            target_node_id=target.id,
            relation_type=relation_type,
            verified_rule_id=rule.id,
            source_snapshot_id=rule.source_snapshot_id,
            regulatory_change_id=rule.regulatory_change_id,
            projection_version=PROJECTION_VERSION,
            active=rule.active,
            effective_from=rule.effective_from,
            effective_to=rule.effective_to,
            retired_at=rule.retired_at,
        )
    else:
        edge.active = rule.active
        edge.effective_from = rule.effective_from
        edge.effective_to = rule.effective_to
        edge.retired_at = rule.retired_at
        edge.updated_at = now_utc()
    session.add(edge)
    session.flush()
    return edge


def _refresh_node_activity(session: Session, node_ids: set[UUID]) -> None:
    for node_id in node_ids:
        node = session.get(RegulatoryKnowledgeNode, node_id)
        if node is None:
            continue
        active_edge = session.exec(
            select(RegulatoryKnowledgeEdge.id)
            .where(RegulatoryKnowledgeEdge.active == True)  # noqa: E712
            .where(or_(
                RegulatoryKnowledgeEdge.source_node_id == node_id,
                RegulatoryKnowledgeEdge.target_node_id == node_id,
            ))
            .limit(1)
        ).first()
        node.active = active_edge is not None
        node.updated_at = now_utc()
        session.add(node)


def deactivate_rule_projection(
    session: Session,
    rule: VerifiedRule,
    *,
    actor: str,
    audit: bool = True,
) -> int:
    edges = session.exec(
        select(RegulatoryKnowledgeEdge).where(RegulatoryKnowledgeEdge.verified_rule_id == rule.id)
    ).all()
    touched_nodes: set[UUID] = set()
    retired_at = rule.retired_at or now_utc()
    for edge in edges:
        touched_nodes.update({edge.source_node_id, edge.target_node_id})
        edge.active = False
        edge.effective_to = rule.effective_to or retired_at
        edge.retired_at = retired_at
        edge.updated_at = now_utc()
        session.add(edge)
    session.flush()
    _refresh_node_activity(session, touched_nodes)
    if audit and edges:
        record_audit(
            session,
            action="regulatory_knowledge_graph_deactivated",
            entity_type="verified_rule",
            entity_id=rule.id,
            after_state={"deactivated_edges": len(edges), "projection_version": PROJECTION_VERSION},
            actor=actor,
            source="regulatory_knowledge_graph_v10_5",
        )
    return len(edges)


def project_verified_rule(
    session: Session,
    rule: VerifiedRule,
    *,
    actor: str,
    audit: bool = True,
) -> dict[str, int]:
    context = _published_context(session, rule)
    if not rule.active:
        return {"nodes": 0, "edges": deactivate_rule_projection(session, rule, actor=actor, audit=audit)}

    jurisdiction: Jurisdiction = context["jurisdiction"]
    source: OfficialSource = context["source"]
    snapshot: SourceSnapshot = context["snapshot"]
    change: RegulatoryChange = context["change"]
    authority: Optional[RegulatoryAuthority] = context["authority"]

    nodes: dict[str, RegulatoryKnowledgeNode] = {}
    nodes["jurisdiction"] = _upsert_node(
        session,
        node_key=f"jurisdiction:{jurisdiction.id}",
        node_type="jurisdiction",
        label=jurisdiction.name,
        properties={
            "jurisdiction_id": jurisdiction.id,
            "code": jurisdiction.code,
            "jurisdiction_type": jurisdiction.jurisdiction_type,
            "region": jurisdiction.region,
        },
        rule=rule,
    )
    nodes["domain"] = _upsert_node(
        session,
        node_key=f"regulatory_domain:{rule.domain.strip().lower()}",
        node_type="regulatory_domain",
        label=rule.domain.replace("_", " ").title(),
        properties={"domain": rule.domain},
        rule=rule,
    )
    nodes["source"] = _upsert_node(
        session,
        node_key=f"official_source:{source.id}",
        node_type="official_source",
        label=source.name,
        properties={
            "official_source_id": source.id,
            "url": source.url,
            "source_type": source.source_type,
            "domain": source.domain,
        },
        rule=rule,
    )
    nodes["snapshot"] = _upsert_node(
        session,
        node_key=f"source_snapshot:{snapshot.id}",
        node_type="source_snapshot",
        label=f"Snapshot {str(snapshot.id)[:8]}",
        properties={
            "source_snapshot_id": snapshot.id,
            "content_hash": snapshot.content_hash,
            "captured_at": snapshot.captured_at,
            "url": snapshot.url,
        },
        rule=rule,
    )
    nodes["change"] = _upsert_node(
        session,
        node_key=f"regulatory_change:{change.id}",
        node_type="regulatory_change",
        label=change.title,
        properties={
            "regulatory_change_id": change.id,
            "change_type": change.change_type,
            "materiality": change.materiality,
            "reviewed_by": change.reviewed_by,
            "reviewed_at": change.reviewed_at,
        },
        rule=rule,
    )
    nodes["rule"] = _upsert_node(
        session,
        node_key=f"verified_rule:{rule.id}",
        node_type="verified_rule",
        label=rule.rule_key,
        properties={
            "verified_rule_id": rule.id,
            "rule_key": rule.rule_key,
            "statement": rule.statement,
            "confidence": rule.confidence,
            "approved_by": rule.approved_by,
            "published_at": rule.published_at,
            "effective_from": rule.effective_from,
            "effective_to": rule.effective_to,
        },
        rule=rule,
    )
    if authority:
        nodes["authority"] = _upsert_node(
            session,
            node_key=f"regulatory_authority:{authority.id}",
            node_type="regulatory_authority",
            label=authority.name,
            properties={
                "regulatory_authority_id": authority.id,
                "authority_type": authority.authority_type,
                "website_url": authority.website_url,
            },
            rule=rule,
        )

    relations = [
        ("jurisdiction", "HAS_PUBLISHED_RULE", "rule"),
        ("rule", "IN_REGULATORY_DOMAIN", "domain"),
        ("rule", "DERIVED_FROM_CHANGE", "change"),
        ("change", "EVIDENCED_BY_SNAPSHOT", "snapshot"),
        ("snapshot", "CAPTURED_FROM_SOURCE", "source"),
        ("source", "OFFICIAL_SOURCE_FOR", "jurisdiction"),
    ]
    if authority:
        relations.extend([
            ("source", "GOVERNED_BY_AUTHORITY", "authority"),
            ("authority", "AUTHORITY_FOR", "jurisdiction"),
        ])
    if rule.supersedes_rule_id:
        superseded = session.get(VerifiedRule, rule.supersedes_rule_id)
        if superseded and superseded.approved_by and superseded.published_at:
            nodes["superseded_rule"] = _upsert_node(
                session,
                node_key=f"verified_rule:{superseded.id}",
                node_type="verified_rule",
                label=superseded.rule_key,
                properties={
                    "verified_rule_id": superseded.id,
                    "rule_key": superseded.rule_key,
                    "statement": superseded.statement,
                    "approved_by": superseded.approved_by,
                    "published_at": superseded.published_at,
                    "retired_at": superseded.retired_at,
                },
                rule=superseded,
            )
            relations.append(("rule", "SUPERSEDES", "superseded_rule"))

    edges = [
        _upsert_edge(
            session,
            source=nodes[source_key],
            target=nodes[target_key],
            relation_type=relation,
            rule=rule,
        )
        for source_key, relation, target_key in relations
    ]
    if audit:
        record_audit(
            session,
            action="regulatory_knowledge_graph_projected",
            entity_type="verified_rule",
            entity_id=rule.id,
            after_state={
                "nodes": len(nodes),
                "edges": len(edges),
                "projection_version": PROJECTION_VERSION,
                "source_snapshot_id": rule.source_snapshot_id,
                "regulatory_change_id": rule.regulatory_change_id,
            },
            actor=actor,
            source="regulatory_knowledge_graph_v10_5",
        )
    return {"nodes": len(nodes), "edges": len(edges)}


def sync_published_rules(session: Session, *, actor: str) -> dict[str, Any]:
    rules = session.exec(
        select(VerifiedRule)
        .where(VerifiedRule.published_at.is_not(None))
        .where(VerifiedRule.approved_by.is_not(None))
        .order_by(VerifiedRule.published_at)
    ).all()
    projected = 0
    deactivated = 0
    skipped: list[dict[str, str]] = []
    for rule in rules:
        try:
            if rule.active:
                project_verified_rule(session, rule, actor=actor, audit=False)
                projected += 1
            else:
                deactivated += deactivate_rule_projection(session, rule, actor=actor, audit=False)
        except ValueError as exc:
            skipped.append({"verified_rule_id": str(rule.id), "reason": str(exc)})
    record_audit(
        session,
        action="regulatory_knowledge_graph_synced",
        entity_type="regulatory_knowledge_graph",
        after_state={
            "published_rules_considered": len(rules),
            "projected_rules": projected,
            "deactivated_edges": deactivated,
            "skipped": skipped,
            "projection_version": PROJECTION_VERSION,
        },
        actor=actor,
        source="regulatory_knowledge_graph_v10_5",
    )
    session.commit()
    return {
        "published_rules_considered": len(rules),
        "projected_rules": projected,
        "deactivated_edges": deactivated,
        "skipped": skipped,
        "projection_version": PROJECTION_VERSION,
    }


def knowledge_graph_payload(
    session: Session,
    *,
    jurisdiction_id: Optional[UUID] = None,
    verified_rule_id: Optional[UUID] = None,
    active: Optional[bool] = True,
    limit: int = 500,
) -> dict[str, Any]:
    statement = select(RegulatoryKnowledgeEdge)
    if verified_rule_id:
        statement = statement.where(RegulatoryKnowledgeEdge.verified_rule_id == verified_rule_id)
    elif jurisdiction_id:
        rule_ids = list(session.exec(
            select(VerifiedRule.id).where(VerifiedRule.jurisdiction_id == jurisdiction_id)
        ).all())
        if not rule_ids:
            return {
                "projection_version": PROJECTION_VERSION,
                "human_published_only": True,
                "provenance_complete": True,
                "counts": {"nodes": 0, "edges": 0, "verified_rules": 0},
                "nodes": [],
                "edges": [],
            }
        statement = statement.where(RegulatoryKnowledgeEdge.verified_rule_id.in_(rule_ids))
    if active is not None:
        statement = statement.where(RegulatoryKnowledgeEdge.active == active)
    edges = list(session.exec(
        statement.order_by(RegulatoryKnowledgeEdge.created_at.desc()).limit(min(max(limit, 1), 2000))
    ).all())
    node_ids = {edge.source_node_id for edge in edges} | {edge.target_node_id for edge in edges}
    nodes = list(session.exec(
        select(RegulatoryKnowledgeNode).where(RegulatoryKnowledgeNode.id.in_(node_ids))
    ).all()) if node_ids else []
    rule_ids = {edge.verified_rule_id for edge in edges}
    rules = list(session.exec(
        select(VerifiedRule).where(VerifiedRule.id.in_(rule_ids))
    ).all()) if rule_ids else []
    rules_by_id = {rule.id: rule for rule in rules}
    change_ids = {edge.regulatory_change_id for edge in edges}
    changes = list(session.exec(
        select(RegulatoryChange).where(RegulatoryChange.id.in_(change_ids))
    ).all()) if change_ids else []
    changes_by_id = {change.id: change for change in changes}
    snapshot_ids = {edge.source_snapshot_id for edge in edges}
    snapshots = list(session.exec(
        select(SourceSnapshot).where(SourceSnapshot.id.in_(snapshot_ids))
    ).all()) if snapshot_ids else []
    snapshot_id_set = {snapshot.id for snapshot in snapshots}
    human_published_only = len(rules_by_id) == len(rule_ids) and all(
        rule.approved_by and rule.published_at for rule in rules_by_id.values()
    )
    provenance_complete = all(
        (rule := rules_by_id.get(edge.verified_rule_id)) is not None
        and rule.source_snapshot_id == edge.source_snapshot_id
        and rule.regulatory_change_id == edge.regulatory_change_id
        and edge.source_snapshot_id in snapshot_id_set
        and (change := changes_by_id.get(edge.regulatory_change_id)) is not None
        and change.status == "published"
        and change.reviewed_by is not None
        and change.reviewed_at is not None
        for edge in edges
    )
    return {
        "projection_version": PROJECTION_VERSION,
        "generated_at": now_utc(),
        "human_published_only": human_published_only,
        "provenance_complete": provenance_complete,
        "counts": {"nodes": len(nodes), "edges": len(edges), "verified_rules": len(rules_by_id)},
        "nodes": [{
            **node.model_dump(exclude={"properties_json"}),
            "properties": _load(node.properties_json),
        } for node in nodes],
        "edges": [edge.model_dump() for edge in edges],
    }
