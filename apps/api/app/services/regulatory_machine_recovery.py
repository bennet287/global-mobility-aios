from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import AuditLog, RegulatoryChange, VerifiedRule, now_utc
from app.models.regulatory_publication import RegulatoryPublicationSet
from app.services.audit_log import record_audit
from app.services.regulatory_graph_publication_provenance import assess_graph_publication_provenance
from app.services.regulatory_knowledge_graph import deactivate_rule_projection


RECOVERY_VERSION = "regulatory-machine-publication-recovery-v1"
RECOVERY_ACTION = "regulatory_machine_publication_emergency_quarantined"
MACHINE_PUBLICATION_RECOVERY_ENABLED = False
MAX_RECOVERY_RULES = 100


class RegulatoryMachineRecoveryError(ValueError):
    pass


@dataclass(frozen=True)
class RegulatoryMachineRecoveryResult:
    publication_set_id: str
    regulatory_change_id: str
    recovery_version: str
    recovery_state: str
    retired_rule_ids: tuple[str, ...]
    deactivated_edge_count: int
    publication_set_status: str
    canonical_write_performed: bool
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["retired_rule_ids"] = list(self.retired_rule_ids)
        payload["reasons"] = list(self.reasons)
        return payload


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _publication_rules(
    session: Session,
    publication_set: RegulatoryPublicationSet,
) -> tuple[list[VerifiedRule], list[dict[str, Any]]]:
    manifest = _load_json(publication_set.published_rules_json, [])
    if not isinstance(manifest, list) or not manifest:
        raise RegulatoryMachineRecoveryError("Machine publication manifest is missing")
    if len(manifest) != publication_set.intended_rule_count:
        raise RegulatoryMachineRecoveryError("Machine publication manifest count is inconsistent")
    if len(manifest) > MAX_RECOVERY_RULES:
        raise RegulatoryMachineRecoveryError("Machine publication recovery exceeds rule bound")
    if any(not isinstance(item, dict) for item in manifest):
        raise RegulatoryMachineRecoveryError("Machine publication manifest contains an invalid entry")

    rules = session.exec(
        select(VerifiedRule)
        .where(VerifiedRule.regulatory_change_id == publication_set.regulatory_change_id)
        .order_by(VerifiedRule.rule_key, VerifiedRule.id)
    ).all()
    manifest_ids = {
        str(item.get("verified_rule_id") or "").strip()
        for item in manifest
    }
    rule_ids = {str(rule.id) for rule in rules}
    if "" in manifest_ids or manifest_ids != rule_ids:
        raise RegulatoryMachineRecoveryError("Machine publication manifest does not match canonical rules")
    return rules, manifest


def quarantine_board_delegated_machine_publication_set(
    session: Session,
    publication_set_id: UUID,
    *,
    reason: str,
    actor: str = "regulatory-recovery-agent",
    recovery_enabled: bool | None = None,
) -> RegulatoryMachineRecoveryResult:
    """Fail closed by retiring an entire Board-delegated machine publication set atomically.

    This is a recovery primitive, not a truth rewrite. The original publication and
    provenance records remain durable. All rules in the set are retired together and
    their graph projections are deactivated in the same transaction. Production
    execution remains disabled until the recovery contract is explicitly accepted.
    """

    enabled = MACHINE_PUBLICATION_RECOVERY_ENABLED if recovery_enabled is None else recovery_enabled
    if not enabled:
        raise RegulatoryMachineRecoveryError("Machine publication recovery execution is disabled")

    reason = reason.strip()
    actor = actor.strip()
    if not reason:
        raise RegulatoryMachineRecoveryError("Emergency quarantine reason is required")
    if not actor:
        raise RegulatoryMachineRecoveryError("Emergency quarantine actor is required")

    publication_set = session.get(RegulatoryPublicationSet, publication_set_id)
    if publication_set is None:
        raise RegulatoryMachineRecoveryError("Machine publication set not found")
    if publication_set.publication_mode != "board_delegated_machine":
        raise RegulatoryMachineRecoveryError("Only Board-delegated machine publication sets can use this recovery path")
    if publication_set.actor_type != "agent" or not publication_set.actor_key:
        raise RegulatoryMachineRecoveryError("Machine publication actor provenance is incomplete")

    rules, _ = _publication_rules(session, publication_set)
    if publication_set.status == "quarantined":
        if any(rule.active or rule.retired_at is None for rule in rules):
            raise RegulatoryMachineRecoveryError("Quarantined publication set has inconsistent active rules")
        return RegulatoryMachineRecoveryResult(
            publication_set_id=str(publication_set.id),
            regulatory_change_id=str(publication_set.regulatory_change_id),
            recovery_version=RECOVERY_VERSION,
            recovery_state="already_quarantined",
            retired_rule_ids=tuple(str(rule.id) for rule in rules),
            deactivated_edge_count=0,
            publication_set_status=publication_set.status,
            canonical_write_performed=False,
            reasons=("publication_set_already_quarantined",),
        )
    if publication_set.status != "published":
        raise RegulatoryMachineRecoveryError("Machine publication set is not in a recoverable published state")

    change = session.get(RegulatoryChange, publication_set.regulatory_change_id)
    if change is None:
        raise RegulatoryMachineRecoveryError("Regulatory change for machine publication set could not be resolved")

    for rule in rules:
        if not rule.active or rule.retired_at is not None:
            raise RegulatoryMachineRecoveryError("Machine publication set contains a partially retired rule")
        provenance = assess_graph_publication_provenance(
            session,
            rule,
            change,
            session.get(type(change).__mro__[0], change.id) if False else session.get(__import__("app.models.domain", fromlist=["SourceSnapshot"]).SourceSnapshot, rule.source_snapshot_id),
        )
        if not provenance.complete or not provenance.board_delegated_machine:
            raise RegulatoryMachineRecoveryError(
                "Machine publication provenance is not complete enough for atomic recovery: "
                + ",".join(provenance.reasons)
            )

    retired_at = now_utc()
    deactivated_edges = 0
    retired_rule_ids: list[str] = []
    try:
        for rule in rules:
            rule.active = False
            rule.retired_at = retired_at
            rule.retired_by = actor
            rule.retirement_reason = f"Emergency quarantine of Board-delegated machine publication: {reason}"
            rule.updated_at = retired_at
            session.add(rule)
            session.flush()
            deactivated_edges += deactivate_rule_projection(
                session,
                rule,
                actor=actor,
                audit=True,
            )
            retired_rule_ids.append(str(rule.id))

        publication_set.status = "quarantined"
        session.add(publication_set)
        record_audit(
            session,
            action=RECOVERY_ACTION,
            entity_type="regulatory_publication_set",
            entity_id=publication_set.id,
            after_state={
                "recovery_version": RECOVERY_VERSION,
                "publication_set_id": str(publication_set.id),
                "regulatory_change_id": str(publication_set.regulatory_change_id),
                "publication_mode": publication_set.publication_mode,
                "actor_type": publication_set.actor_type,
                "publication_actor_key": publication_set.actor_key,
                "recovery_actor": actor,
                "recovery_reason": reason,
                "retired_rule_ids": retired_rule_ids,
                "deactivated_edge_count": deactivated_edges,
                "publication_set_status": publication_set.status,
                "source_snapshot_id": str(publication_set.source_snapshot_id),
                "source_snapshot_hash": publication_set.source_snapshot_hash,
            },
            reason=reason,
            actor=actor,
            source=RECOVERY_VERSION,
        )
        session.commit()
        session.refresh(publication_set)
        return RegulatoryMachineRecoveryResult(
            publication_set_id=str(publication_set.id),
            regulatory_change_id=str(publication_set.regulatory_change_id),
            recovery_version=RECOVERY_VERSION,
            recovery_state="quarantined",
            retired_rule_ids=tuple(retired_rule_ids),
            deactivated_edge_count=deactivated_edges,
            publication_set_status=publication_set.status,
            canonical_write_performed=True,
            reasons=(),
        )
    except Exception:
        session.rollback()
        raise
