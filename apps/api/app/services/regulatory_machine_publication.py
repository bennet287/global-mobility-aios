from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    HumanReview,
    Jurisdiction,
    RegulatoryChange,
    ReviewStatus,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.models.regulatory_publication import (
    RegulatoryPublicationSet,
    RegulatoryReviewDisposition,
)
from app.services.audit_log import record_audit
from app.services.official_sources import normalize_country
from app.services.regulatory_publication_execution_adapter import (
    assess_regulatory_publication_execution,
)


PUBLICATION_CONTRACT_VERSION = "regulatory-machine-publication-contract-v1"
PUBLICATION_ACTION = "regulatory_machine_publication_set_published"
MACHINE_PUBLICATION_EXECUTION_ENABLED = False
MAX_RULES_PER_PUBLICATION_SET = 100


class RegulatoryMachinePublicationError(ValueError):
    pass


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


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RegulatoryMachinePublicationError("Invalid effective date in intended rule mutation") from exc


def _statement(mutation: dict[str, Any]) -> str:
    source_text = str(mutation.get("source_text") or "").strip()
    if not source_text:
        raise RegulatoryMachinePublicationError("Intended rule mutation is missing source text")
    return source_text


def _existing_publication(
    session: Session,
    change: RegulatoryChange,
) -> tuple[RegulatoryPublicationSet | None, list[VerifiedRule]]:
    publication_set = session.exec(
        select(RegulatoryPublicationSet).where(
            RegulatoryPublicationSet.regulatory_change_id == change.id
        )
    ).first()
    rules = session.exec(
        select(VerifiedRule)
        .where(VerifiedRule.regulatory_change_id == change.id)
        .order_by(VerifiedRule.rule_key, VerifiedRule.id)
    ).all()
    return publication_set, rules


def _validate_replay(
    publication_set: RegulatoryPublicationSet,
    rules: list[VerifiedRule],
) -> tuple[RegulatoryPublicationSet, tuple[VerifiedRule, ...]]:
    if publication_set.status != "published":
        raise RegulatoryMachinePublicationError("Existing machine publication set is not published")
    if len(rules) != publication_set.intended_rule_count:
        raise RegulatoryMachinePublicationError("Existing machine publication set is incomplete")
    published = _load_json(publication_set.published_rules_json, [])
    if not isinstance(published, list) or len(published) != publication_set.intended_rule_count:
        raise RegulatoryMachinePublicationError("Existing machine publication manifest is invalid")
    expected_ids = {str(item.get("verified_rule_id")) for item in published if isinstance(item, dict)}
    if expected_ids != {str(rule.id) for rule in rules}:
        raise RegulatoryMachinePublicationError("Existing machine publication manifest does not match rules")
    return publication_set, tuple(rules)


def publish_board_delegated_machine_rule_set(
    session: Session,
    change_id: UUID,
    *,
    actor_key: str = "regulatory-publication-agent",
) -> tuple[RegulatoryPublicationSet, tuple[VerifiedRule, ...]]:
    """Persist one Board-delegated deterministic publication set atomically.

    Production execution is deliberately disabled. Tests may enable the module-level
    kill switch to prove transaction semantics, review-disposition truth, idempotency,
    and rollback behavior before the derived regulatory graph is adapted to consume
    this non-human publication provenance.
    """

    change = session.get(RegulatoryChange, change_id)
    if change is None:
        raise RegulatoryMachinePublicationError("Regulatory change not found")

    existing_set, existing_rules = _existing_publication(session, change)
    if existing_set is not None:
        return _validate_replay(existing_set, existing_rules)
    if existing_rules:
        raise RegulatoryMachinePublicationError("Verified rules already exist without a machine publication set")

    if not MACHINE_PUBLICATION_EXECUTION_ENABLED:
        raise RegulatoryMachinePublicationError("Machine publication execution is disabled")

    actor_key = actor_key.strip()
    if not actor_key:
        raise RegulatoryMachinePublicationError("Machine publication actor is required")

    preflight = assess_regulatory_publication_execution(
        session,
        change,
        machine_publication_enabled=True,
    )
    if not preflight.execution_authority or not preflight.canonical_write_allowed:
        raise RegulatoryMachinePublicationError(
            f"Machine publication preflight is not authorized: {','.join(preflight.reasons)}"
        )
    if not preflight.authorization_audit_id or not preflight.bridge_audit_id:
        raise RegulatoryMachinePublicationError("Publication lineage audits are missing")

    authorization_audit = session.get(AuditLog, UUID(preflight.authorization_audit_id))
    bridge_audit = session.get(AuditLog, UUID(preflight.bridge_audit_id))
    if authorization_audit is None or bridge_audit is None:
        raise RegulatoryMachinePublicationError("Publication lineage audits could not be resolved")
    authorization = _load_json(authorization_audit.after_state_json, {})
    bridge = _load_json(bridge_audit.after_state_json, {})

    intended = authorization.get("intended_rule_mutations", [])
    if not isinstance(intended, list) or not intended:
        raise RegulatoryMachinePublicationError("Authorization contains no intended rule mutations")
    if len(intended) > MAX_RULES_PER_PUBLICATION_SET:
        raise RegulatoryMachinePublicationError("Publication set exceeds the deterministic rule bound")
    if len(intended) != preflight.intended_rule_count:
        raise RegulatoryMachinePublicationError("Preflight rule count no longer matches authorization")

    snapshot = session.get(SourceSnapshot, change.current_snapshot_id)
    if snapshot is None or not snapshot.content_hash:
        raise RegulatoryMachinePublicationError("Current source snapshot provenance is incomplete")
    if str(snapshot.id) != preflight.source_snapshot_id:
        raise RegulatoryMachinePublicationError("Current source snapshot no longer matches authorization")
    if snapshot.content_hash != preflight.source_snapshot_content_hash:
        raise RegulatoryMachinePublicationError("Current source snapshot hash no longer matches authorization")

    profile_id = bridge.get("autonomy_profile_id")
    profile_sequence = bridge.get("autonomy_profile_sequence")
    if not profile_id or not isinstance(profile_sequence, int) or profile_sequence < 1:
        raise RegulatoryMachinePublicationError("Board autonomy profile lineage is incomplete")

    jurisdiction = session.get(Jurisdiction, change.jurisdiction_id)
    if jurisdiction is None:
        raise RegulatoryMachinePublicationError("Jurisdiction not found")

    normalized_mutations = [dict(item) for item in intended if isinstance(item, dict)]
    if len(normalized_mutations) != len(intended):
        raise RegulatoryMachinePublicationError("Authorization contains an invalid intended rule mutation")
    mutation_fingerprint = _sha256(normalized_mutations)
    published_at = now_utc()

    try:
        publication_set = RegulatoryPublicationSet(
            regulatory_change_id=change.id,
            source_snapshot_id=snapshot.id,
            source_snapshot_hash=snapshot.content_hash,
            publication_mode="board_delegated_machine",
            actor_type="agent",
            actor_key=actor_key,
            authorization_audit_id=authorization_audit.id,
            authority_bridge_audit_id=bridge_audit.id,
            autonomy_profile_id=UUID(str(profile_id)),
            autonomy_profile_sequence=profile_sequence,
            intended_rule_count=len(normalized_mutations),
            intended_mutations_sha256=mutation_fingerprint,
            published_rules_json="[]",
            status="published",
            published_at=published_at,
        )
        session.add(publication_set)
        session.flush()

        pending_reviews = session.exec(
            select(HumanReview)
            .where(HumanReview.regulatory_change_id == change.id)
            .where(HumanReview.status == ReviewStatus.pending)
            .order_by(HumanReview.created_at, HumanReview.id)
        ).all()
        for review in pending_reviews:
            review.status = ReviewStatus.resolved
            review.reviewer_notes = (
                "Human review waived under current Human Board A4/R4 delegation; "
                "no human review was performed. See regulatory review disposition."
            )
            review.updated_at = published_at
            session.add(review)
            session.add(
                RegulatoryReviewDisposition(
                    human_review_id=review.id,
                    regulatory_change_id=change.id,
                    publication_set_id=publication_set.id,
                    disposition="waived_board_delegation",
                    actor_type="agent",
                    actor_key=actor_key,
                    authority_bridge_audit_id=bridge_audit.id,
                    disposition_reason=(
                        "Board-delegated deterministic publication satisfied the governed machine publication preflight; human review was waived, not performed."
                    ),
                    created_at=published_at,
                )
            )

        rule_keys: set[str] = set()
        rules: list[VerifiedRule] = []
        manifest: list[dict[str, Any]] = []
        for ordinal, mutation in enumerate(normalized_mutations, start=1):
            rule_key = str(mutation.get("rule_key") or "").strip()
            if not rule_key or rule_key in rule_keys:
                raise RegulatoryMachinePublicationError("Publication set contains duplicate or empty rule keys")
            rule_keys.add(rule_key)
            conflict = session.exec(
                select(VerifiedRule)
                .where(VerifiedRule.jurisdiction_id == change.jurisdiction_id)
                .where(VerifiedRule.domain == change.domain)
                .where(VerifiedRule.rule_key == rule_key)
                .where(VerifiedRule.active == True)  # noqa: E712
            ).first()
            if conflict is not None:
                raise RegulatoryMachinePublicationError(
                    f"Active verified rule already exists for rule key '{rule_key}'"
                )

            rule = VerifiedRule(
                country=normalize_country(jurisdiction.name),
                domain=change.domain,
                rule_key=rule_key,
                statement=_statement(mutation),
                official_source_id=change.official_source_id,
                jurisdiction_id=change.jurisdiction_id,
                regulatory_change_id=change.id,
                source_snapshot_id=snapshot.id,
                confidence=1.0,
                active=True,
                effective_from=_parse_datetime(mutation.get("effective_from")) or change.effective_at,
                effective_to=_parse_datetime(mutation.get("effective_to")),
                approved_by=f"agent:{actor_key}",
                published_at=published_at,
            )
            session.add(rule)
            session.flush()
            rules.append(rule)
            manifest.append(
                {
                    "ordinal": ordinal,
                    "verified_rule_id": str(rule.id),
                    "rule_key": rule.rule_key,
                    "mutation_sha256": _sha256(mutation),
                }
            )

        publication_set.published_rules_json = _stable_json(manifest)
        session.add(publication_set)
        change.status = "published"
        change.published_at = published_at
        change.review_notes = (
            "Published by Board-delegated deterministic machine publication; human review was waived under explicit autonomy governance."
        )
        session.add(change)
        session.flush()

        record_audit(
            session,
            action=PUBLICATION_ACTION,
            entity_type="regulatory_publication_set",
            entity_id=publication_set.id,
            after_state={
                "contract_version": PUBLICATION_CONTRACT_VERSION,
                "regulatory_change_id": str(change.id),
                "publication_set_id": str(publication_set.id),
                "publication_mode": publication_set.publication_mode,
                "actor_type": publication_set.actor_type,
                "actor_key": publication_set.actor_key,
                "authorization_audit_id": str(publication_set.authorization_audit_id),
                "authority_bridge_audit_id": str(publication_set.authority_bridge_audit_id),
                "autonomy_profile_id": str(publication_set.autonomy_profile_id),
                "autonomy_profile_sequence": publication_set.autonomy_profile_sequence,
                "source_snapshot_id": str(snapshot.id),
                "source_snapshot_hash": snapshot.content_hash,
                "intended_rule_count": publication_set.intended_rule_count,
                "intended_mutations_sha256": publication_set.intended_mutations_sha256,
                "published_rules": manifest,
            },
            reason=(
                "Atomic Board-delegated machine publication set persisted under current deterministic evidence and authority lineage."
            ),
            actor=f"agent:{actor_key}",
            source=PUBLICATION_CONTRACT_VERSION,
        )
        for rule in rules:
            record_audit(
                session,
                action="verified_rule_published",
                entity_type="verified_rule",
                entity_id=rule.id,
                after_state=rule,
                reason=change.review_notes,
                actor=f"agent:{actor_key}",
                source=PUBLICATION_CONTRACT_VERSION,
            )

        session.commit()
        session.refresh(publication_set)
        for rule in rules:
            session.refresh(rule)
        return publication_set, tuple(rules)
    except Exception:
        session.rollback()
        raise
