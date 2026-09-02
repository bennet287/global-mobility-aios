from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Mapping


BOARD_SUPREMACY_INVARIANT: Final[str] = (
    "The Human Owner / Board is the supreme authority of Global Mobility AIOS; "
    "no agent, AI executive, model, runtime, tool, policy engine, or delegated "
    "authority may supersede it."
)

BOARD_TRANSPARENCY_INVARIANT: Final[str] = (
    "Operational autonomy must never create organizational opacity: the Human "
    "Owner / Board must be able to inspect material organizational activity, "
    "decisions, relevant collaboration, evidence, policy, tool actions, "
    "authority changes, incidents, and outcomes subject to lawful sensitivity controls."
)

AUTHORIZATION_INVARIANT: Final[str] = (
    "Scores route decisions; deterministic gates authorize decisions."
)


class AutonomyLevel(StrEnum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


class RiskTier(StrEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"


class HumanReviewReason(StrEnum):
    UNCERTAINTY = "UNCERTAINTY"
    CONTRADICTION = "CONTRADICTION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OUTSIDE_AUTHORITY = "OUTSIDE_AUTHORITY"
    POLICY_REQUIRED = "POLICY_REQUIRED"
    LEGAL_REQUIRED = "LEGAL_REQUIRED"
    BOARD_RESERVED = "BOARD_RESERVED"
    ANOMALY = "ANOMALY"
    EXCEPTION = "EXCEPTION"


class ConsequenceClass(StrEnum):
    REVERSIBLE = "REVERSIBLE"
    COMPENSATABLE = "COMPENSATABLE"
    IRREVERSIBLE = "IRREVERSIBLE"
    APPEND_ONLY_CORRECTION = "APPEND_ONLY_CORRECTION"


class OrganizationActivityClass(StrEnum):
    CONVERSATIONAL = "CONVERSATIONAL"
    COLLABORATIVE = "COLLABORATIVE"
    OPERATIONAL = "OPERATIONAL"
    MATERIAL = "MATERIAL"
    AUTHORITY = "AUTHORITY"


class ReservedAuthorityClass(StrEnum):
    CONSTITUTION = "CONSTITUTION"
    STRATEGIC_DIRECTION = "STRATEGIC_DIRECTION"
    AUTONOMY_CEILING = "AUTONOMY_CEILING"
    MAJOR_POLICY = "MAJOR_POLICY"
    EXECUTIVE_APPOINTMENT = "EXECUTIVE_APPOINTMENT"
    EMERGENCY_CONTROL = "EMERGENCY_CONTROL"
    BOARD_RESERVED_EXTERNAL_ACTION = "BOARD_RESERVED_EXTERNAL_ACTION"


class MaterialActionType(StrEnum):
    OFFICIAL_SOURCE_SEARCH = "official_source.search"
    DOCUMENT_SUMMARY = "document.summary"
    INTERNAL_NOTE = "internal.note"
    WORK_ITEM_ASSIGNMENT = "work_item.assignment"
    EVIDENCE_CANDIDATE = "evidence.candidate"
    ELIGIBILITY_TRANSITION = "eligibility.transition"
    EVIDENCE_CERTIFICATION = "evidence.certification"
    VERIFIED_RULE_PUBLICATION = "verified_rule.publication"
    CONSEQUENTIAL_EXTERNAL_COMMUNICATION = "external_communication.consequential"
    GOVERNMENT_SUBMISSION = "government.submission"


@dataclass(frozen=True, slots=True)
class MaterialityRule:
    material: bool
    default_risk_tier: RiskTier
    board_reserved: bool = False


@dataclass(frozen=True, slots=True)
class ActivityTransparencyRule:
    board_inspectable: bool
    requires_durable_record: bool
    requires_full_lineage: bool
    may_compact_after_policy_window: bool


_MATERIALITY_REGISTRY = {
    MaterialActionType.OFFICIAL_SOURCE_SEARCH: MaterialityRule(False, RiskTier.R0),
    MaterialActionType.DOCUMENT_SUMMARY: MaterialityRule(False, RiskTier.R0),
    MaterialActionType.INTERNAL_NOTE: MaterialityRule(False, RiskTier.R0),
    MaterialActionType.WORK_ITEM_ASSIGNMENT: MaterialityRule(True, RiskTier.R1),
    MaterialActionType.EVIDENCE_CANDIDATE: MaterialityRule(True, RiskTier.R2),
    MaterialActionType.ELIGIBILITY_TRANSITION: MaterialityRule(True, RiskTier.R3),
    MaterialActionType.EVIDENCE_CERTIFICATION: MaterialityRule(True, RiskTier.R4),
    MaterialActionType.VERIFIED_RULE_PUBLICATION: MaterialityRule(True, RiskTier.R4),
    MaterialActionType.CONSEQUENTIAL_EXTERNAL_COMMUNICATION: MaterialityRule(
        True,
        RiskTier.R3,
    ),
    MaterialActionType.GOVERNMENT_SUBMISSION: MaterialityRule(
        True,
        RiskTier.R5,
        board_reserved=True,
    ),
}

MATERIALITY_REGISTRY: Final[Mapping[MaterialActionType, MaterialityRule]] = (
    MappingProxyType(_MATERIALITY_REGISTRY)
)


_ACTIVITY_TRANSPARENCY_POLICY = {
    OrganizationActivityClass.CONVERSATIONAL: ActivityTransparencyRule(
        board_inspectable=True,
        requires_durable_record=False,
        requires_full_lineage=False,
        may_compact_after_policy_window=True,
    ),
    OrganizationActivityClass.COLLABORATIVE: ActivityTransparencyRule(
        board_inspectable=True,
        requires_durable_record=True,
        requires_full_lineage=False,
        may_compact_after_policy_window=True,
    ),
    OrganizationActivityClass.OPERATIONAL: ActivityTransparencyRule(
        board_inspectable=True,
        requires_durable_record=True,
        requires_full_lineage=False,
        may_compact_after_policy_window=True,
    ),
    OrganizationActivityClass.MATERIAL: ActivityTransparencyRule(
        board_inspectable=True,
        requires_durable_record=True,
        requires_full_lineage=True,
        may_compact_after_policy_window=False,
    ),
    OrganizationActivityClass.AUTHORITY: ActivityTransparencyRule(
        board_inspectable=True,
        requires_durable_record=True,
        requires_full_lineage=True,
        may_compact_after_policy_window=False,
    ),
}

ACTIVITY_TRANSPARENCY_POLICY: Final[
    Mapping[OrganizationActivityClass, ActivityTransparencyRule]
] = MappingProxyType(_ACTIVITY_TRANSPARENCY_POLICY)


AUTONOMY_SEMANTICS: Final[Mapping[AutonomyLevel, str]] = MappingProxyType(
    {
        AutonomyLevel.A0: "Prohibited",
        AutonomyLevel.A1: "Human executes",
        AutonomyLevel.A2: "AI prepares; approval required",
        AutonomyLevel.A3: "Autonomous with mandatory review",
        AutonomyLevel.A4: "Autonomous with monitoring and valid recovery controls",
        AutonomyLevel.A5: "Fully autonomous bounded operation",
    }
)


RISK_SEMANTICS: Final[Mapping[RiskTier, str]] = MappingProxyType(
    {
        RiskTier.R0: "Summarization, brainstorming, or other non-material cognition",
        RiskTier.R1: "Routine internal operation with inexpensive deterministic checks",
        RiskTier.R2: "Client-facing preparation requiring evidence validation",
        RiskTier.R3: "Material recommendation or eligibility decision requiring independent verification",
        RiskTier.R4: "Certification or regulatory publication requiring independent verification and fresh-source validation",
        RiskTier.R5: "Government submission or critical reserved action requiring full preparation and Human/Board gate",
    }
)


def materiality_rule(action_type: MaterialActionType) -> MaterialityRule:
    return MATERIALITY_REGISTRY[action_type]


def transparency_rule(activity_class: OrganizationActivityClass) -> ActivityTransparencyRule:
    return ACTIVITY_TRANSPARENCY_POLICY[activity_class]
