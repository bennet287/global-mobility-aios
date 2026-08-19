from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping
from uuid import UUID, uuid4

from app.core.organization_constitution import (
    AutonomyLevel,
    ConsequenceClass,
    HumanReviewReason,
    MaterialActionType,
    OrganizationActivityClass as ConstitutionalActivityClass,
    RiskTier,
    materiality_rule,
)
from app.services.organization_command import OrganizationCommandContext, canonical_fingerprint


class GatewayOutcome(StrEnum):
    AUTO_EXECUTE = "AUTO_EXECUTE"
    BLOCK = "BLOCK"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"


class GatewayReason(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    OUTSIDE_AUTHORITY = "OUTSIDE_AUTHORITY"
    SCOPE_DENIED = "SCOPE_DENIED"
    RISK_EXCEEDS_AUTHORITY = "RISK_EXCEEDS_AUTHORITY"
    EXPECTED_VERSION_REQUIRED = "EXPECTED_VERSION_REQUIRED"
    STALE_VERSION = "STALE_VERSION"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    POLICY_DENIED = "POLICY_DENIED"
    POLICY_REVIEW_REQUIRED = "POLICY_REVIEW_REQUIRED"
    AUTONOMY_PROHIBITED = "AUTONOMY_PROHIBITED"
    AUTONOMY_REVIEW_REQUIRED = "AUTONOMY_REVIEW_REQUIRED"
    BOARD_RESERVED = "BOARD_RESERVED"


class PolicyDisposition(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"


_RISK_ORDER = {
    RiskTier.R0: 0,
    RiskTier.R1: 1,
    RiskTier.R2: 2,
    RiskTier.R3: 3,
    RiskTier.R4: 4,
    RiskTier.R5: 5,
}


@dataclass(frozen=True, slots=True)
class CapabilityAuthority:
    tenant_key: str
    actor_id: str
    capability: str
    allowed_action_types: frozenset[MaterialActionType]
    max_risk_tier: RiskTier
    autonomy_level: AutonomyLevel
    allowed_scopes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.tenant_key.strip() or not self.actor_id.strip() or not self.capability.strip():
            raise ValueError("tenant_key, actor_id, and capability are required")
        if not self.allowed_action_types:
            raise ValueError("at least one allowed action type is required")


@dataclass(frozen=True, slots=True)
class MaterialAction:
    action_type: MaterialActionType
    capability: str
    subject_type: str
    subject_id: str
    idempotency_key: str
    expected_version: int | None
    proposed_change: Mapping[str, Any] = field(default_factory=dict)
    scope_key: str | None = None
    evidence_refs: tuple[str, ...] = ()
    rationale: str = ""
    risk_tier: RiskTier | None = None
    consequence_class: ConsequenceClass = ConsequenceClass.REVERSIBLE
    trace_id: UUID = field(default_factory=uuid4)
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        for name, value in (
            ("capability", self.capability),
            ("subject_type", self.subject_type),
            ("subject_id", self.subject_id),
            ("idempotency_key", self.idempotency_key),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not materiality_rule(self.action_type).material:
            raise ValueError("MaterialAction requires a constitutionally material action type")
        if self.expected_version is not None and self.expected_version < 0:
            raise ValueError("expected_version cannot be negative")

    @property
    def effective_risk_tier(self) -> RiskTier:
        floor = materiality_rule(self.action_type).default_risk_tier
        if self.risk_tier is None:
            return floor
        return self.risk_tier if _RISK_ORDER[self.risk_tier] >= _RISK_ORDER[floor] else floor


@dataclass(frozen=True, slots=True)
class GatewayEvaluation:
    outcome: GatewayOutcome
    reason: GatewayReason
    trace_id: UUID
    action_fingerprint: str
    effective_risk_tier: RiskTier
    constitutional_activity_class: ConstitutionalActivityClass
    human_review_reason: HumanReviewReason | None = None
    post_review_required: bool = False

    @property
    def authorized_for_execution(self) -> bool:
        return self.outcome is GatewayOutcome.AUTO_EXECUTE


@dataclass(frozen=True, slots=True)
class OrganizationActivityProjection:
    activity_key: str
    stream_key: str
    activity_class: str
    activity_type: str
    title: str
    summary: str
    source_object_type: str
    source_object_id: str
    source_object_version: str | None
    correlation_key: str
    payload: Mapping[str, Any]


def material_action_fingerprint(
    context: OrganizationCommandContext,
    action: MaterialAction,
) -> str:
    return canonical_fingerprint(
        {
            "tenant_key": context.tenant_key,
            "actor_id": context.actor_id,
            "action_type": action.action_type,
            "capability": action.capability,
            "subject_type": action.subject_type,
            "subject_id": action.subject_id,
            "scope_key": action.scope_key,
            "expected_version": action.expected_version,
            "proposed_change": action.proposed_change,
            "evidence_refs": tuple(sorted(action.evidence_refs)),
            "rationale": action.rationale,
            "effective_risk_tier": action.effective_risk_tier,
            "consequence_class": action.consequence_class,
        }
    )


def _evaluation(
    action: MaterialAction,
    fingerprint: str,
    outcome: GatewayOutcome,
    reason: GatewayReason,
    *,
    review_reason: HumanReviewReason | None = None,
    post_review_required: bool = False,
) -> GatewayEvaluation:
    constitutional_class = (
        ConstitutionalActivityClass.AUTHORITY
        if materiality_rule(action.action_type).board_reserved
        else ConstitutionalActivityClass.MATERIAL
    )
    return GatewayEvaluation(
        outcome=outcome,
        reason=reason,
        trace_id=action.trace_id,
        action_fingerprint=fingerprint,
        effective_risk_tier=action.effective_risk_tier,
        constitutional_activity_class=constitutional_class,
        human_review_reason=review_reason,
        post_review_required=post_review_required,
    )


def evaluate_material_action(
    context: OrganizationCommandContext,
    authority: CapabilityAuthority,
    action: MaterialAction,
    *,
    current_version: int | None,
    existing_idempotency_fingerprint: str | None = None,
    policy_disposition: PolicyDisposition = PolicyDisposition.ALLOW,
) -> GatewayEvaluation:
    fingerprint = material_action_fingerprint(context, action)

    if authority.tenant_key != context.tenant_key or authority.actor_id != context.actor_id:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.OUTSIDE_AUTHORITY,
            review_reason=HumanReviewReason.OUTSIDE_AUTHORITY,
        )
    if authority.capability != action.capability or action.action_type not in authority.allowed_action_types:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.OUTSIDE_AUTHORITY,
            review_reason=HumanReviewReason.OUTSIDE_AUTHORITY,
        )
    if authority.allowed_scopes and action.scope_key not in authority.allowed_scopes:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.SCOPE_DENIED,
            review_reason=HumanReviewReason.OUTSIDE_AUTHORITY,
        )
    if _RISK_ORDER[action.effective_risk_tier] > _RISK_ORDER[authority.max_risk_tier]:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.RISK_EXCEEDS_AUTHORITY,
            review_reason=HumanReviewReason.OUTSIDE_AUTHORITY,
        )

    if current_version is not None:
        if action.expected_version is None:
            return _evaluation(
                action,
                fingerprint,
                GatewayOutcome.BLOCK,
                GatewayReason.EXPECTED_VERSION_REQUIRED,
            )
        if action.expected_version != current_version:
            return _evaluation(
                action,
                fingerprint,
                GatewayOutcome.BLOCK,
                GatewayReason.STALE_VERSION,
            )
    elif action.expected_version is not None:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.STALE_VERSION,
        )

    if existing_idempotency_fingerprint is not None:
        if existing_idempotency_fingerprint == fingerprint:
            return _evaluation(
                action,
                fingerprint,
                GatewayOutcome.IDEMPOTENT_REPLAY,
                GatewayReason.IDEMPOTENT_REPLAY,
            )
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.IDEMPOTENCY_CONFLICT,
        )

    if policy_disposition is PolicyDisposition.DENY:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.POLICY_DENIED,
            review_reason=HumanReviewReason.POLICY_REQUIRED,
        )

    # Reserved authority is checked before ordinary autonomy routing. A Board-reserved
    # action must remain visibly Board-reserved even when the actor's normal autonomy
    # level would also require human involvement.
    if materiality_rule(action.action_type).board_reserved:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.REVIEW_REQUIRED,
            GatewayReason.BOARD_RESERVED,
            review_reason=HumanReviewReason.BOARD_RESERVED,
        )

    if policy_disposition is PolicyDisposition.HUMAN_REQUIRED:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.REVIEW_REQUIRED,
            GatewayReason.POLICY_REVIEW_REQUIRED,
            review_reason=HumanReviewReason.POLICY_REQUIRED,
        )

    if authority.autonomy_level is AutonomyLevel.A0:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.BLOCK,
            GatewayReason.AUTONOMY_PROHIBITED,
            review_reason=HumanReviewReason.OUTSIDE_AUTHORITY,
        )
    if authority.autonomy_level in {AutonomyLevel.A1, AutonomyLevel.A2}:
        return _evaluation(
            action,
            fingerprint,
            GatewayOutcome.REVIEW_REQUIRED,
            GatewayReason.AUTONOMY_REVIEW_REQUIRED,
            review_reason=HumanReviewReason.OUTSIDE_AUTHORITY,
        )

    return _evaluation(
        action,
        fingerprint,
        GatewayOutcome.AUTO_EXECUTE,
        GatewayReason.AUTHORIZED,
        post_review_required=authority.autonomy_level is AutonomyLevel.A3,
    )


def organization_activity_projection(
    context: OrganizationCommandContext,
    action: MaterialAction,
    evaluation: GatewayEvaluation,
) -> OrganizationActivityProjection:
    version = None if action.expected_version is None else str(action.expected_version)
    return OrganizationActivityProjection(
        activity_key=f"governance:{action.idempotency_key}",
        stream_key=f"governance:{action.subject_type}:{action.subject_id}",
        activity_class="operational",
        activity_type=f"governance.{action.action_type.value}.{evaluation.outcome.value.lower()}",
        title=f"Governance evaluation: {action.action_type.value}",
        summary=(
            f"{evaluation.outcome.value}: {evaluation.reason.value}; "
            f"risk={evaluation.effective_risk_tier.value}; trace={evaluation.trace_id}"
        ),
        source_object_type=action.subject_type,
        source_object_id=action.subject_id,
        source_object_version=version,
        correlation_key=str(evaluation.trace_id),
        payload={
            "governance_contract": "v1.3-b.1",
            "actor_id": context.actor_id,
            "capability": action.capability,
            "action_type": action.action_type.value,
            "outcome": evaluation.outcome.value,
            "reason": evaluation.reason.value,
            "constitutional_activity_class": evaluation.constitutional_activity_class.value,
            "effective_risk_tier": evaluation.effective_risk_tier.value,
            "consequence_class": action.consequence_class.value,
            "human_review_reason": (
                evaluation.human_review_reason.value if evaluation.human_review_reason else None
            ),
            "post_review_required": evaluation.post_review_required,
            "action_fingerprint": evaluation.action_fingerprint,
            "idempotency_key": action.idempotency_key,
            "trace_id": str(evaluation.trace_id),
        },
    )
