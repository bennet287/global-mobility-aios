from __future__ import annotations

import pytest

from app.core.organization_constitution import (
    ACTIVITY_TRANSPARENCY_POLICY,
    AUTHORIZATION_INVARIANT,
    BOARD_SUPREMACY_INVARIANT,
    BOARD_TRANSPARENCY_INVARIANT,
    MATERIALITY_REGISTRY,
    AutonomyLevel,
    ConsequenceClass,
    HumanReviewReason,
    MaterialActionType,
    OrganizationActivityClass,
    ReservedAuthorityClass,
    RiskTier,
    materiality_rule,
    transparency_rule,
)


def test_autonomy_levels_are_stable_and_complete() -> None:
    assert [level.value for level in AutonomyLevel] == [
        "A0",
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
    ]


def test_risk_tiers_are_stable_and_complete() -> None:
    assert [tier.value for tier in RiskTier] == [
        "R0",
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
    ]


def test_human_review_reasons_match_v13_contract() -> None:
    assert {reason.value for reason in HumanReviewReason} == {
        "UNCERTAINTY",
        "CONTRADICTION",
        "INSUFFICIENT_EVIDENCE",
        "OUTSIDE_AUTHORITY",
        "POLICY_REQUIRED",
        "LEGAL_REQUIRED",
        "BOARD_RESERVED",
        "ANOMALY",
        "EXCEPTION",
    }


def test_consequence_classes_match_recovery_contract() -> None:
    assert {item.value for item in ConsequenceClass} == {
        "REVERSIBLE",
        "COMPENSATABLE",
        "IRREVERSIBLE",
        "APPEND_ONLY_CORRECTION",
    }


def test_reserved_authority_contract_contains_non_delegable_board_domains() -> None:
    assert ReservedAuthorityClass.CONSTITUTION.value == "CONSTITUTION"
    assert ReservedAuthorityClass.AUTONOMY_CEILING.value == "AUTONOMY_CEILING"
    assert ReservedAuthorityClass.EMERGENCY_CONTROL.value == "EMERGENCY_CONTROL"


def test_materiality_registry_is_total_for_declared_action_types() -> None:
    assert set(MATERIALITY_REGISTRY) == set(MaterialActionType)


def test_non_material_cognition_defaults_to_r0() -> None:
    for action_type in (
        MaterialActionType.OFFICIAL_SOURCE_SEARCH,
        MaterialActionType.DOCUMENT_SUMMARY,
        MaterialActionType.INTERNAL_NOTE,
    ):
        rule = materiality_rule(action_type)
        assert rule.material is False
        assert rule.default_risk_tier is RiskTier.R0
        assert rule.board_reserved is False


def test_government_submission_is_r5_and_board_reserved() -> None:
    rule = materiality_rule(MaterialActionType.GOVERNMENT_SUBMISSION)
    assert rule.material is True
    assert rule.default_risk_tier is RiskTier.R5
    assert rule.board_reserved is True


def test_material_and_authority_activity_require_durable_full_lineage() -> None:
    for activity_class in (
        OrganizationActivityClass.MATERIAL,
        OrganizationActivityClass.AUTHORITY,
    ):
        rule = transparency_rule(activity_class)
        assert rule.board_inspectable is True
        assert rule.requires_durable_record is True
        assert rule.requires_full_lineage is True
        assert rule.may_compact_after_policy_window is False


def test_every_activity_class_is_board_inspectable() -> None:
    assert set(ACTIVITY_TRANSPARENCY_POLICY) == set(OrganizationActivityClass)
    assert all(rule.board_inspectable for rule in ACTIVITY_TRANSPARENCY_POLICY.values())


def test_conversational_activity_can_compact_without_losing_board_right_to_inspect() -> None:
    rule = transparency_rule(OrganizationActivityClass.CONVERSATIONAL)
    assert rule.board_inspectable is True
    assert rule.requires_durable_record is False
    assert rule.requires_full_lineage is False
    assert rule.may_compact_after_policy_window is True


def test_constitutional_registries_are_read_only() -> None:
    with pytest.raises(TypeError):
        MATERIALITY_REGISTRY[MaterialActionType.INTERNAL_NOTE] = materiality_rule(  # type: ignore[index]
            MaterialActionType.INTERNAL_NOTE
        )


def test_frozen_invariants_encode_board_supremacy_transparency_and_hard_gates() -> None:
    assert "supreme authority" in BOARD_SUPREMACY_INVARIANT
    assert "opacity" in BOARD_TRANSPARENCY_INVARIANT
    assert AUTHORIZATION_INVARIANT == "Scores route decisions; deterministic gates authorize decisions."
