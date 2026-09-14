from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import AuditLog, HumanReview, RegulatoryChange, SourceSnapshot, VerifiedRule
from app.models.regulatory_publication import RegulatoryPublicationSet, RegulatoryReviewDisposition
from app.services.regulatory_machine_publication import (
    PUBLICATION_ACTION,
    PUBLICATION_CONTRACT_VERSION,
)
from app.services.regulatory_promotion_authorization import AUTHORIZATION_ACTION, AUTHORIZATION_VERSION


PROVENANCE_GATE_VERSION = "regulatory-graph-publication-provenance-v1"


@dataclass(frozen=True)
class GraphPublicationProvenance:
    provenance_type: str
    complete: bool
    human_published: bool
    board_delegated_machine: bool
    publication_set_id: str | None
    reasons: tuple[str, ...]


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _stable_json(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _human_regulatory_change_provenance(
    rule: VerifiedRule,
    change: RegulatoryChange,
) -> GraphPublicationProvenance:
    reasons: list[str] = []
    if change.status != "published":
        reasons.append("regulatory_change_not_published")
    if not change.reviewed_by or not change.reviewed_at:
        reasons.append("human_review_missing")
    if not rule.approved_by or rule.approved_by.startswith("agent:") or not rule.published_at:
        reasons.append("human_rule_publication_missing")
    return GraphPublicationProvenance(
        provenance_type="human_regulatory_change",
        complete=not reasons,
        human_published=not reasons,
        board_delegated_machine=False,
        publication_set_id=None,
        reasons=tuple(reasons),
    )


def _machine_regulatory_change_provenance(
    session: Session,
    rule: VerifiedRule,
    change: RegulatoryChange,
    snapshot: SourceSnapshot,
) -> GraphPublicationProvenance:
    reasons: list[str] = []
    publication_set = session.exec(
        select(RegulatoryPublicationSet).where(
            RegulatoryPublicationSet.regulatory_change_id == change.id
        )
    ).first()
    if publication_set is None:
        return GraphPublicationProvenance(
            provenance_type="board_delegated_machine",
            complete=False,
            human_published=False,
            board_delegated_machine=False,
            publication_set_id=None,
            reasons=("machine_publication_set_missing",),
        )

    if publication_set.status != "published":
        reasons.append("machine_publication_set_not_published")
    if publication_set.publication_mode != "board_delegated_machine":
        reasons.append("machine_publication_mode_invalid")
    if publication_set.actor_type != "agent" or not publication_set.actor_key:
        reasons.append("machine_publication_actor_invalid")
    if rule.approved_by != f"agent:{publication_set.actor_key}" or not rule.published_at:
        reasons.append("machine_rule_actor_mismatch")
    if publication_set.source_snapshot_id != snapshot.id:
        reasons.append("machine_publication_snapshot_id_mismatch")
    if publication_set.source_snapshot_hash != snapshot.content_hash:
        reasons.append("machine_publication_snapshot_hash_mismatch")
    if not publication_set.autonomy_profile_id or publication_set.autonomy_profile_sequence < 1:
        reasons.append("machine_publication_autonomy_lineage_missing")

    manifest = _load_json(publication_set.published_rules_json, [])
    if not isinstance(manifest, list) or len(manifest) != publication_set.intended_rule_count:
        reasons.append("machine_publication_manifest_invalid")
    else:
        manifest_ids = {
            str(item.get("verified_rule_id"))
            for item in manifest
            if isinstance(item, dict) and item.get("verified_rule_id")
        }
        if str(rule.id) not in manifest_ids:
            reasons.append("machine_rule_missing_from_manifest")

    authorization_audit = session.get(AuditLog, publication_set.authorization_audit_id)
    if authorization_audit is None:
        reasons.append("machine_authorization_audit_missing")
    else:
        authorization_payload = _load_json(authorization_audit.after_state_json, {})
        if authorization_audit.action != AUTHORIZATION_ACTION:
            reasons.append("machine_authorization_action_mismatch")
        if authorization_payload.get("authorization_version") != AUTHORIZATION_VERSION:
            reasons.append("machine_authorization_version_mismatch")
        if str(authorization_payload.get("regulatory_change_id") or "") != str(change.id):
            reasons.append("machine_authorization_change_mismatch")
        intended_mutations = authorization_payload.get("intended_rule_mutations", [])
        if not isinstance(intended_mutations, list) or not intended_mutations:
            reasons.append("machine_authorization_mutations_missing")
        elif _sha256(intended_mutations) != publication_set.intended_mutations_sha256:
            reasons.append("machine_mutation_fingerprint_mismatch")

    publication_audit = session.exec(
        select(AuditLog)
        .where(AuditLog.action == PUBLICATION_ACTION)
        .where(AuditLog.entity_id == str(publication_set.id))
    ).first()
    if publication_audit is None:
        reasons.append("machine_publication_audit_missing")
    else:
        payload = _load_json(publication_audit.after_state_json, {})
        if payload.get("contract_version") != PUBLICATION_CONTRACT_VERSION:
            reasons.append("machine_publication_contract_mismatch")
        if str(payload.get("publication_set_id") or "") != str(publication_set.id):
            reasons.append("machine_publication_audit_set_mismatch")
        if str(payload.get("authorization_audit_id") or "") != str(publication_set.authorization_audit_id):
            reasons.append("machine_authorization_lineage_mismatch")
        if str(payload.get("authority_bridge_audit_id") or "") != str(publication_set.authority_bridge_audit_id):
            reasons.append("machine_authority_bridge_lineage_mismatch")
        if str(payload.get("source_snapshot_id") or "") != str(snapshot.id):
            reasons.append("machine_publication_audit_snapshot_mismatch")
        if payload.get("source_snapshot_hash") != snapshot.content_hash:
            reasons.append("machine_publication_audit_hash_mismatch")
        if str(payload.get("autonomy_profile_id") or "") != publication_set.autonomy_profile_id:
            reasons.append("machine_publication_audit_autonomy_profile_mismatch")
        if payload.get("autonomy_profile_sequence") != publication_set.autonomy_profile_sequence:
            reasons.append("machine_publication_audit_autonomy_sequence_mismatch")
        if payload.get("intended_mutations_sha256") != publication_set.intended_mutations_sha256:
            reasons.append("machine_publication_audit_mutation_fingerprint_mismatch")
        published_rules = payload.get("published_rules", [])
        if not isinstance(published_rules, list) or _stable_json(published_rules) != _stable_json(manifest):
            reasons.append("machine_publication_audit_manifest_mismatch")

    all_rules = session.exec(
        select(VerifiedRule)
        .where(VerifiedRule.regulatory_change_id == change.id)
        .order_by(VerifiedRule.rule_key, VerifiedRule.id)
    ).all()
    if len(all_rules) != publication_set.intended_rule_count:
        reasons.append("machine_publication_rule_set_incomplete")
    elif manifest:
        manifest_ids = {str(item.get("verified_rule_id")) for item in manifest if isinstance(item, dict)}
        if manifest_ids != {str(item.id) for item in all_rules}:
            reasons.append("machine_publication_rule_set_manifest_mismatch")

    reviews = session.exec(
        select(HumanReview)
        .where(HumanReview.regulatory_change_id == change.id)
        .order_by(HumanReview.created_at, HumanReview.id)
    ).all()
    review_ids = {str(review.id) for review in reviews}
    dispositions = session.exec(
        select(RegulatoryReviewDisposition).where(
            RegulatoryReviewDisposition.regulatory_change_id == change.id
        )
    ).all()
    disposition_review_ids: list[str] = []
    for disposition in dispositions:
        disposition_review_ids.append(str(disposition.human_review_id))
        if (
            disposition.publication_set_id != publication_set.id
            or str(disposition.human_review_id) not in review_ids
            or disposition.disposition != "waived_board_delegation"
            or disposition.actor_type != "agent"
            or disposition.actor_key != publication_set.actor_key
            or disposition.authority_bridge_audit_id != publication_set.authority_bridge_audit_id
        ):
            reasons.append("machine_review_disposition_invalid")
    if not reviews:
        reasons.append("machine_review_requirement_missing")
    elif len(disposition_review_ids) != len(set(disposition_review_ids)):
        reasons.append("machine_review_disposition_duplicate")
    if set(disposition_review_ids) != review_ids:
        reasons.append("machine_review_disposition_coverage_incomplete")

    return GraphPublicationProvenance(
        provenance_type="board_delegated_machine",
        complete=not reasons,
        human_published=False,
        board_delegated_machine=not reasons,
        publication_set_id=str(publication_set.id),
        reasons=tuple(sorted(set(reasons))),
    )


def assess_graph_publication_provenance(
    session: Session,
    rule: VerifiedRule,
    change: RegulatoryChange,
    snapshot: SourceSnapshot,
) -> GraphPublicationProvenance:
    """Validate the publication provenance allowed to feed the regulatory graph.

    Human-reviewed publication keeps its existing contract. Non-human publication is
    accepted only as a complete Board-delegated atomic publication set whose actor,
    snapshot, authorization, audit lineage, manifest, mutation fingerprint, and full
    review-waiver coverage remain intact. This gate never grants publication authority
    and never writes canonical state.
    """

    if rule.regulatory_change_id != change.id:
        return GraphPublicationProvenance(
            provenance_type="invalid",
            complete=False,
            human_published=False,
            board_delegated_machine=False,
            publication_set_id=None,
            reasons=("rule_change_mismatch",),
        )
    if rule.source_snapshot_id != snapshot.id or change.current_snapshot_id != snapshot.id:
        return GraphPublicationProvenance(
            provenance_type="invalid",
            complete=False,
            human_published=False,
            board_delegated_machine=False,
            publication_set_id=None,
            reasons=("snapshot_lineage_mismatch",),
        )

    if change.reviewed_by and change.reviewed_at and rule.approved_by and not rule.approved_by.startswith("agent:"):
        return _human_regulatory_change_provenance(rule, change)
    if rule.approved_by and rule.approved_by.startswith("agent:"):
        return _machine_regulatory_change_provenance(session, rule, change, snapshot)

    return GraphPublicationProvenance(
        provenance_type="invalid",
        complete=False,
        human_published=False,
        board_delegated_machine=False,
        publication_set_id=None,
        reasons=("recognized_publication_provenance_missing",),
    )
