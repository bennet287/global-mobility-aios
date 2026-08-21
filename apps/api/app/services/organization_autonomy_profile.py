from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel, RiskTier
from app.models.autonomy_profile import CapabilityAutonomyEvidence, CapabilityAutonomyProfile
from app.models.domain import OrganizationActivity, OrganizationPosition, now_utc
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    AuditMutation,
    AuthorityDenied,
    DependencyConflict,
    IdempotencyConflict,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    commit_mutations,
    require_human,
    tenant_record,
)


AUTONOMY_PROFILE_ACTIVITY_TYPE = "organization.autonomy_profile.established.v1"
AUTONOMY_PROFILE_SOURCE_TYPE = "capability_autonomy_profile"
AUTONOMY_PROFILE_GOVERNANCE_SOURCE = "human_board"
AUTONOMY_PROFILE_CONTRACT_VERSION = "v1.3-i.1"


class AutonomyProfileIntegrityError(RuntimeError):
    """Raised when durable autonomy truth no longer satisfies its lineage contract."""


@dataclass(frozen=True, slots=True)
class AutonomyEvidenceSnapshot:
    evidence_sequence: int
    source_activity_id: UUID
    source_activity_fingerprint: str
    record_fingerprint: str


@dataclass(frozen=True, slots=True)
class AutonomyProfileRevisionSnapshot:
    profile_id: UUID
    profile_sequence: int
    lifecycle_status: str
    autonomy_level: str
    board_ceiling: str
    authority_requirement: str
    risk_ceiling: str
    evidence_policy_version: str
    governance_source: str
    decision_activity_id: UUID
    supersedes_profile_id: UUID | None
    record_fingerprint: str
    effective_from: datetime
    created_at: datetime
    evidence: tuple[AutonomyEvidenceSnapshot, ...]


@dataclass(frozen=True, slots=True)
class CapabilityAutonomyProfileSnapshot:
    position_key: str
    capability_key: str
    context_scope: str
    current_profile_id: UUID
    current_autonomy_level: str
    revisions: tuple[AutonomyProfileRevisionSnapshot, ...]


def _required(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidTransition(f"{field} is required")
    return normalized


def _autonomy_rank(level: AutonomyLevel) -> int:
    return int(level.value[1])


def _scope_statement(
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
):
    return select(CapabilityAutonomyProfile).where(
        CapabilityAutonomyProfile.tenant_key == tenant_key,
        CapabilityAutonomyProfile.position_key == position_key,
        CapabilityAutonomyProfile.capability_key == capability_key,
        CapabilityAutonomyProfile.context_scope == context_scope,
    )


def _existing_idempotent_profile(
    session: Session,
    *,
    tenant_key: str,
    idempotency_key: str,
    record_fingerprint: str,
) -> CapabilityAutonomyProfile | None:
    existing = session.exec(
        select(CapabilityAutonomyProfile).where(
            CapabilityAutonomyProfile.tenant_key == tenant_key,
            CapabilityAutonomyProfile.idempotency_key == idempotency_key,
        )
    ).first()
    if existing is None:
        return None
    if existing.record_fingerprint != record_fingerprint:
        raise IdempotencyConflict(
            "capability autonomy profile idempotency key was already used with different semantics"
        )
    return existing


def establish_capability_autonomy_profile(
    session: Session,
    context: OrganizationCommandContext,
    *,
    position_key: str,
    capability_key: str,
    context_scope: str,
    autonomy_level: AutonomyLevel | str,
    board_ceiling: AutonomyLevel | str,
    authority_requirement: str,
    risk_ceiling: RiskTier | str,
    evidence_policy_version: str,
    evidence_activity_ids: Sequence[UUID],
    idempotency_key: str,
    expected_profile_sequence: int | None = None,
) -> CapabilityAutonomyProfile:
    """Append one Board-established capability autonomy profile revision.

    This is intentionally HTTP-independent and human-Board-only. It records canonical
    autonomy truth; it is not an automatic promotion or dynamic downgrade engine.
    """

    require_human(context, admin=True)
    if context.position_key != "board":
        raise AuthorityDenied("only the persistent Board position may establish autonomy truth")

    position_key = _required(position_key, field="position_key")
    capability_key = _required(capability_key, field="capability_key")
    context_scope = _required(context_scope, field="context_scope")
    authority_requirement = _required(authority_requirement, field="authority_requirement")
    evidence_policy_version = _required(
        evidence_policy_version,
        field="evidence_policy_version",
    )
    idempotency_key = _required(idempotency_key, field="idempotency_key")
    try:
        autonomy = AutonomyLevel(autonomy_level)
        ceiling = AutonomyLevel(board_ceiling)
        risk = RiskTier(risk_ceiling)
    except ValueError as exc:
        raise InvalidTransition("autonomy_level, board_ceiling, or risk_ceiling is invalid") from exc
    if _autonomy_rank(autonomy) > _autonomy_rank(ceiling):
        raise AuthorityDenied("requested autonomy exceeds the Human Board ceiling")

    target_position = session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == position_key,
            OrganizationPosition.status == "active",
        )
    ).first()
    if target_position is None:
        raise InvalidReference("active organization position was not found")

    evidence_ids = tuple(sorted(set(evidence_activity_ids), key=str))
    evidence_activities: list[OrganizationActivity] = []
    for activity_id in evidence_ids:
        evidence_activities.append(
            tenant_record(
                session,
                OrganizationActivity,
                activity_id,
                context.tenant_key,
                label="autonomy evidence activity",
            )
        )

    semantic_command = {
        "contract_version": AUTONOMY_PROFILE_CONTRACT_VERSION,
        "tenant_key": context.tenant_key,
        "position_key": position_key,
        "capability_key": capability_key,
        "context_scope": context_scope,
        "autonomy_level": autonomy.value,
        "board_ceiling": ceiling.value,
        "authority_requirement": authority_requirement,
        "risk_ceiling": risk.value,
        "evidence_policy_version": evidence_policy_version,
        "expected_profile_sequence": expected_profile_sequence,
        "governance_source": AUTONOMY_PROFILE_GOVERNANCE_SOURCE,
        "evidence": [
            {
                "source_activity_id": str(activity.id),
                "source_activity_fingerprint": activity.record_fingerprint,
            }
            for activity in evidence_activities
        ],
    }
    record_fingerprint = canonical_fingerprint(semantic_command)
    replay = _existing_idempotent_profile(
        session,
        tenant_key=context.tenant_key,
        idempotency_key=idempotency_key,
        record_fingerprint=record_fingerprint,
    )
    if replay is not None:
        return replay

    current_statement = _scope_statement(
        tenant_key=context.tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
    ).order_by(CapabilityAutonomyProfile.profile_sequence.desc())
    if session.get_bind().dialect.name == "postgresql":
        current_statement = current_statement.with_for_update()
    current = session.exec(current_statement).first()
    if current is None:
        if expected_profile_sequence not in {None, 0}:
            raise InvalidTransition("expected autonomy profile sequence is stale")
        next_sequence = 1
    else:
        if expected_profile_sequence is None:
            raise InvalidTransition("expected_profile_sequence is required for profile supersession")
        if expected_profile_sequence != current.profile_sequence:
            raise InvalidTransition("expected autonomy profile sequence is stale")
        next_sequence = current.profile_sequence + 1

    profile_id = uuid4()
    occurred_at = now_utc()
    stream_scope = canonical_fingerprint(
        {
            "tenant_key": context.tenant_key,
            "position_key": position_key,
            "capability_key": capability_key,
            "context_scope": context_scope,
        }
    )[:24]
    try:
        decision_activity = stage_activity(
            session,
            context,
            activity_key=f"autonomy-profile:{idempotency_key}",
            stream_key=f"autonomy-profile:{stream_scope}",
            activity_class="decision",
            activity_type=AUTONOMY_PROFILE_ACTIVITY_TYPE,
            title=f"Board autonomy profile: {position_key}/{capability_key}",
            summary=(
                f"Board established {autonomy.value} autonomy within {ceiling.value} ceiling "
                f"for context {context_scope}."
            ),
            source_object_type=AUTONOMY_PROFILE_SOURCE_TYPE,
            source_object_id=str(profile_id),
            source_object_version=str(next_sequence),
            occurred_at=occurred_at,
            supersedes_activity_id=(current.decision_activity_id if current is not None else None),
            payload={
                "governance_contract": AUTONOMY_PROFILE_CONTRACT_VERSION,
                "constitutional_activity_class": "AUTHORITY",
                "governance_source": AUTONOMY_PROFILE_GOVERNANCE_SOURCE,
                "position_key": position_key,
                "capability_key": capability_key,
                "context_scope": context_scope,
                "profile_sequence": next_sequence,
                "autonomy_level": autonomy.value,
                "board_ceiling": ceiling.value,
                "authority_requirement": authority_requirement,
                "risk_ceiling": risk.value,
                "evidence_policy_version": evidence_policy_version,
                "supersedes_profile_id": str(current.id) if current is not None else None,
                "evidence_activity_ids": [str(activity.id) for activity in evidence_activities],
                "record_fingerprint": record_fingerprint,
            },
        )

        profile = CapabilityAutonomyProfile(
            id=profile_id,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
            profile_sequence=next_sequence,
            autonomy_level=autonomy.value,
            board_ceiling=ceiling.value,
            authority_requirement=authority_requirement,
            risk_ceiling=risk.value,
            evidence_policy_version=evidence_policy_version,
            supersedes_profile_id=current.id if current is not None else None,
            governance_source=AUTONOMY_PROFILE_GOVERNANCE_SOURCE,
            decision_activity_id=decision_activity.id,
            idempotency_key=idempotency_key,
            record_fingerprint=record_fingerprint,
            effective_from=occurred_at,
            created_at=occurred_at,
            created_by=context.actor_id,
        )
        session.add(profile)
        evidence_rows: list[CapabilityAutonomyEvidence] = []
        for index, activity in enumerate(evidence_activities, start=1):
            evidence = CapabilityAutonomyEvidence(
                tenant_key=context.tenant_key,
                profile_id=profile.id,
                evidence_sequence=index,
                source_activity_id=activity.id,
                source_activity_fingerprint=activity.record_fingerprint,
                record_fingerprint=canonical_fingerprint(
                    {
                        "profile_record_fingerprint": record_fingerprint,
                        "evidence_sequence": index,
                        "source_activity_id": str(activity.id),
                        "source_activity_fingerprint": activity.record_fingerprint,
                    }
                ),
                created_at=occurred_at,
            )
            evidence_rows.append(evidence)
            session.add(evidence)

        mutations = [
            AuditMutation(
                action="organization.autonomy_profile.establish",
                entity_type="capability_autonomy_profile",
                entity_id=profile.id,
                after_state=profile,
                reason="Human Board established capability-specific autonomy truth.",
            ),
            *[
                AuditMutation(
                    action="organization.autonomy_evidence.link",
                    entity_type="capability_autonomy_evidence",
                    entity_id=evidence.id,
                    after_state=evidence,
                )
                for evidence in evidence_rows
            ],
        ]
        commit_mutations(
            session,
            mutations=mutations,
            context=context,
            refresh=(profile,),
        )
        return profile
    except IntegrityError as exc:
        session.rollback()
        concurrent = _existing_idempotent_profile(
            session,
            tenant_key=context.tenant_key,
            idempotency_key=idempotency_key,
            record_fingerprint=record_fingerprint,
        )
        if concurrent is not None:
            return concurrent
        raise DependencyConflict(
            "capability autonomy profile changed concurrently; retry with current sequence"
        ) from exc
    except Exception:
        session.rollback()
        raise


def capability_autonomy_profile_snapshot(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
) -> CapabilityAutonomyProfileSnapshot | None:
    """Return a validated append-only Board read model for one autonomy scope."""

    profiles = list(
        session.exec(
            _scope_statement(
                tenant_key=tenant_key,
                position_key=position_key,
                capability_key=capability_key,
                context_scope=context_scope,
            ).order_by(CapabilityAutonomyProfile.profile_sequence.asc())
        ).all()
    )
    if not profiles:
        return None

    previous: CapabilityAutonomyProfile | None = None
    revisions: list[AutonomyProfileRevisionSnapshot] = []
    for expected_sequence, profile in enumerate(profiles, start=1):
        if profile.profile_sequence != expected_sequence:
            raise AutonomyProfileIntegrityError("autonomy profile sequence is not contiguous")
        if previous is None:
            if profile.supersedes_profile_id is not None:
                raise AutonomyProfileIntegrityError("first autonomy profile unexpectedly supersedes a profile")
        elif profile.supersedes_profile_id != previous.id:
            raise AutonomyProfileIntegrityError("autonomy profile supersession chain is inconsistent")
        try:
            if _autonomy_rank(AutonomyLevel(profile.autonomy_level)) > _autonomy_rank(
                AutonomyLevel(profile.board_ceiling)
            ):
                raise AutonomyProfileIntegrityError("autonomy profile exceeds its Board ceiling")
            RiskTier(profile.risk_ceiling)
        except ValueError as exc:
            raise AutonomyProfileIntegrityError("autonomy profile contains invalid constitutional tiers") from exc

        decision = tenant_record(
            session,
            OrganizationActivity,
            profile.decision_activity_id,
            tenant_key,
            label="autonomy profile decision activity",
        )
        if (
            decision.activity_type != AUTONOMY_PROFILE_ACTIVITY_TYPE
            or decision.source_object_type != AUTONOMY_PROFILE_SOURCE_TYPE
            or decision.source_object_id != str(profile.id)
            or decision.source_object_version != str(profile.profile_sequence)
        ):
            raise AutonomyProfileIntegrityError("autonomy profile decision Activity lineage is inconsistent")

        evidence_rows = list(
            session.exec(
                select(CapabilityAutonomyEvidence)
                .where(
                    CapabilityAutonomyEvidence.tenant_key == tenant_key,
                    CapabilityAutonomyEvidence.profile_id == profile.id,
                )
                .order_by(CapabilityAutonomyEvidence.evidence_sequence.asc())
            ).all()
        )
        evidence_snapshots: list[AutonomyEvidenceSnapshot] = []
        for evidence_sequence, evidence in enumerate(evidence_rows, start=1):
            if evidence.evidence_sequence != evidence_sequence:
                raise AutonomyProfileIntegrityError("autonomy evidence sequence is not contiguous")
            source = tenant_record(
                session,
                OrganizationActivity,
                evidence.source_activity_id,
                tenant_key,
                label="autonomy evidence source activity",
            )
            if source.record_fingerprint != evidence.source_activity_fingerprint:
                raise AutonomyProfileIntegrityError("autonomy evidence source fingerprint drifted")
            expected_fingerprint = canonical_fingerprint(
                {
                    "profile_record_fingerprint": profile.record_fingerprint,
                    "evidence_sequence": evidence.evidence_sequence,
                    "source_activity_id": str(evidence.source_activity_id),
                    "source_activity_fingerprint": evidence.source_activity_fingerprint,
                }
            )
            if evidence.record_fingerprint != expected_fingerprint:
                raise AutonomyProfileIntegrityError("autonomy evidence record fingerprint is inconsistent")
            evidence_snapshots.append(
                AutonomyEvidenceSnapshot(
                    evidence_sequence=evidence.evidence_sequence,
                    source_activity_id=evidence.source_activity_id,
                    source_activity_fingerprint=evidence.source_activity_fingerprint,
                    record_fingerprint=evidence.record_fingerprint,
                )
            )

        revisions.append(
            AutonomyProfileRevisionSnapshot(
                profile_id=profile.id,
                profile_sequence=profile.profile_sequence,
                lifecycle_status="current" if profile is profiles[-1] else "superseded",
                autonomy_level=profile.autonomy_level,
                board_ceiling=profile.board_ceiling,
                authority_requirement=profile.authority_requirement,
                risk_ceiling=profile.risk_ceiling,
                evidence_policy_version=profile.evidence_policy_version,
                governance_source=profile.governance_source,
                decision_activity_id=profile.decision_activity_id,
                supersedes_profile_id=profile.supersedes_profile_id,
                record_fingerprint=profile.record_fingerprint,
                effective_from=profile.effective_from,
                created_at=profile.created_at,
                evidence=tuple(evidence_snapshots),
            )
        )
        previous = profile

    current = profiles[-1]
    return CapabilityAutonomyProfileSnapshot(
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        current_profile_id=current.id,
        current_autonomy_level=current.autonomy_level,
        revisions=tuple(revisions),
    )
