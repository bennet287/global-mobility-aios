from __future__ import annotations

import pytest

from app.core.organization_constitution import AutonomyLevel, MaterialActionType, RiskTier
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayOutcome,
    GatewayReason,
    MaterialAction,
    PolicyDisposition,
    evaluate_material_action,
    material_action_fingerprint,
    organization_activity_projection,
)


def _context(*, actor: str = "agent-a", tenant: str = "tenant-a") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant,
        actor_id=actor,
        actor_type="agent",
        authenticated_user_id="system",
        role="operator",
    )


def _authority(
    *,
    actor: str = "agent-a",
    tenant: str = "tenant-a",
    actions: frozenset[MaterialActionType] = frozenset(
        {MaterialActionType.WORK_ITEM_ASSIGNMENT}
    ),
    max_risk: RiskTier = RiskTier.R3,
    autonomy: AutonomyLevel = AutonomyLevel.A4,
    scopes: frozenset[str] = frozenset(),
) -> CapabilityAuthority:
    return CapabilityAuthority(
        tenant_key=tenant,
        actor_id=actor,
        capability="operations.work",
        allowed_action_types=actions,
        max_risk_tier=max_risk,
        autonomy_level=autonomy,
        allowed_scopes=scopes,
    )


def _action(
    action_type: MaterialActionType = MaterialActionType.WORK_ITEM_ASSIGNMENT,
    *,
    version: int | None = 3,
    proposed_change: dict | None = None,
    scope: str | None = None,
    risk: RiskTier | None = None,
    key: str = "idem-123456",
) -> MaterialAction:
    return MaterialAction(
        action_type=action_type,
        capability="operations.work",
        subject_type="work_item",
        subject_id="work-1",
        idempotency_key=key,
        expected_version=version,
        proposed_change=proposed_change or {"assignee": "agent-b"},
        scope_key=scope,
        risk_tier=risk,
    )


def test_authorized_low_risk_action_auto_executes() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(),
        _action(),
        current_version=3,
    )

    assert result.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.reason is GatewayReason.AUTHORIZED


def test_authority_grant_must_match_actor() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(actor="different-agent"),
        _action(),
        current_version=3,
    )

    assert result.outcome is GatewayOutcome.BLOCK
    assert result.reason is GatewayReason.OUTSIDE_AUTHORITY


def test_action_type_must_be_inside_capability_authority() -> None:
    authority = _authority(
        actions=frozenset({MaterialActionType.EVIDENCE_CANDIDATE})
    )

    result = evaluate_material_action(
        _context(),
        authority,
        _action(),
        current_version=3,
    )

    assert result.reason is GatewayReason.OUTSIDE_AUTHORITY


def test_scope_must_be_inside_capability_authority() -> None:
    authority = _authority(scopes=frozenset({"AT"}))

    result = evaluate_material_action(
        _context(),
        authority,
        _action(scope="DE"),
        current_version=3,
    )

    assert result.reason is GatewayReason.SCOPE_DENIED


def test_risk_ceiling_blocks_action_above_authority() -> None:
    authority = _authority(
        actions=frozenset({MaterialActionType.ELIGIBILITY_TRANSITION}),
        max_risk=RiskTier.R2,
    )

    result = evaluate_material_action(
        _context(),
        authority,
        _action(MaterialActionType.ELIGIBILITY_TRANSITION),
        current_version=3,
    )

    assert result.reason is GatewayReason.RISK_EXCEEDS_AUTHORITY


def test_declared_risk_cannot_downgrade_constitutional_floor() -> None:
    action = _action(
        MaterialActionType.ELIGIBILITY_TRANSITION,
        risk=RiskTier.R0,
    )

    assert action.effective_risk_tier is RiskTier.R3


def test_expected_version_is_required_for_versioned_aggregate() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(),
        _action(version=None),
        current_version=3,
    )

    assert result.reason is GatewayReason.EXPECTED_VERSION_REQUIRED


def test_stale_expected_version_blocks() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(),
        _action(version=2),
        current_version=3,
    )

    assert result.reason is GatewayReason.STALE_VERSION


def test_matching_idempotency_fingerprint_returns_replay() -> None:
    action = _action()
    fingerprint = material_action_fingerprint(_context(), action)

    result = evaluate_material_action(
        _context(),
        _authority(),
        action,
        current_version=3,
        existing_idempotency_fingerprint=fingerprint,
    )

    assert result.outcome is GatewayOutcome.IDEMPOTENT_REPLAY
    assert result.reason is GatewayReason.IDEMPOTENT_REPLAY


def test_conflicting_idempotency_fingerprint_blocks() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(),
        _action(),
        current_version=3,
        existing_idempotency_fingerprint="0" * 64,
    )

    assert result.reason is GatewayReason.IDEMPOTENCY_CONFLICT


def test_policy_denial_blocks() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(),
        _action(),
        current_version=3,
        policy_disposition=PolicyDisposition.DENY,
    )

    assert result.reason is GatewayReason.POLICY_DENIED


def test_policy_can_route_to_human() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(),
        _action(),
        current_version=3,
        policy_disposition=PolicyDisposition.HUMAN_REQUIRED,
    )

    assert result.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.reason is GatewayReason.POLICY_REVIEW_REQUIRED


def test_a0_prohibits_execution() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(autonomy=AutonomyLevel.A0),
        _action(),
        current_version=3,
    )

    assert result.reason is GatewayReason.AUTONOMY_PROHIBITED


def test_a2_routes_to_human_authority() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(autonomy=AutonomyLevel.A2),
        _action(),
        current_version=3,
    )

    assert result.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.reason is GatewayReason.AUTONOMY_REVIEW_REQUIRED


def test_a3_auto_executes_and_marks_post_review() -> None:
    result = evaluate_material_action(
        _context(),
        _authority(autonomy=AutonomyLevel.A3),
        _action(),
        current_version=3,
    )

    assert result.outcome is GatewayOutcome.AUTO_EXECUTE
    assert result.post_review_required is True


def test_board_reserved_never_auto_executes_even_at_a5() -> None:
    authority = CapabilityAuthority(
        tenant_key="tenant-a",
        actor_id="agent-a",
        capability="operations.work",
        allowed_action_types=frozenset({MaterialActionType.GOVERNMENT_SUBMISSION}),
        max_risk_tier=RiskTier.R5,
        autonomy_level=AutonomyLevel.A5,
    )
    action = MaterialAction(
        action_type=MaterialActionType.GOVERNMENT_SUBMISSION,
        capability="operations.work",
        subject_type="application",
        subject_id="application-1",
        idempotency_key="submit-123456",
        expected_version=9,
    )

    result = evaluate_material_action(
        _context(),
        authority,
        action,
        current_version=9,
    )

    assert result.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.reason is GatewayReason.BOARD_RESERVED


def test_activity_projection_is_trace_correlated() -> None:
    action = _action()
    result = evaluate_material_action(
        _context(),
        _authority(),
        action,
        current_version=3,
    )

    projection = organization_activity_projection(_context(), action, result)

    assert projection.activity_class == "operational"
    assert projection.correlation_key == str(result.trace_id)
    assert projection.payload["constitutional_activity_class"] == "MATERIAL"
    assert projection.payload["action_fingerprint"] == result.action_fingerprint


def test_non_material_action_cannot_enter_material_gateway() -> None:
    with pytest.raises(ValueError, match="constitutionally material"):
        MaterialAction(
            action_type=MaterialActionType.DOCUMENT_SUMMARY,
            capability="operations.work",
            subject_type="document",
            subject_id="document-1",
            idempotency_key="summary-123456",
            expected_version=None,
        )


def test_board_reserved_reason_precedes_a2_autonomy_routing() -> None:
    authority = CapabilityAuthority(
        tenant_key="tenant-a",
        actor_id="agent-a",
        capability="operations.work",
        allowed_action_types=frozenset({MaterialActionType.GOVERNMENT_SUBMISSION}),
        max_risk_tier=RiskTier.R5,
        autonomy_level=AutonomyLevel.A2,
    )
    action = MaterialAction(
        action_type=MaterialActionType.GOVERNMENT_SUBMISSION,
        capability="operations.work",
        subject_type="application",
        subject_id="application-1",
        idempotency_key="submit-a2-123456",
        expected_version=9,
    )

    result = evaluate_material_action(
        _context(),
        authority,
        action,
        current_version=9,
    )

    assert result.outcome is GatewayOutcome.REVIEW_REQUIRED
    assert result.reason is GatewayReason.BOARD_RESERVED
