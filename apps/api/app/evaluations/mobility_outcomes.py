from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import math
from typing import Iterable, Mapping


class MobilityCaseProvenance(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    PROFESSIONALLY_REVIEWED = "PROFESSIONALLY_REVIEWED"
    HISTORICAL = "HISTORICAL"
    LIVE_SHADOW = "LIVE_SHADOW"


class MobilityEligibilityLabel(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class EvaluationRiskTier(StrEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"


@dataclass(frozen=True)
class MobilityGoldCase:
    """A versioned evaluation label set, never canonical production authority.

    ``None`` means a dimension is not labeled and therefore must not be scored.
    An empty frozenset means the dimension is deliberately labeled as empty.
    """

    case_id: str
    jurisdiction: str
    evaluation_as_of: datetime
    provenance: MobilityCaseProvenance
    expected_pathway_keys: frozenset[str] | None = None
    expected_eligibility: MobilityEligibilityLabel | None = None
    expected_required_evidence: frozenset[str] | None = None
    expected_missing_evidence: frozenset[str] | None = None
    expected_contradictions: frozenset[str] | None = None
    expected_rule_or_source_refs: frozenset[str] | None = None
    expected_escalation_required: bool | None = None
    review_reference: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        if not self.jurisdiction.strip():
            raise ValueError("jurisdiction is required")
        if self.evaluation_as_of.tzinfo is None:
            raise ValueError("evaluation_as_of must be timezone-aware")
        if self.provenance is MobilityCaseProvenance.PROFESSIONALLY_REVIEWED and not (
            self.review_reference and self.review_reference.strip()
        ):
            raise ValueError("professionally reviewed cases require review_reference")


@dataclass(frozen=True)
class MobilityOutcomePrediction:
    pathway_keys: frozenset[str] = field(default_factory=frozenset)
    eligibility: MobilityEligibilityLabel | None = None
    required_evidence: frozenset[str] = field(default_factory=frozenset)
    missing_evidence: frozenset[str] = field(default_factory=frozenset)
    contradictions: frozenset[str] = field(default_factory=frozenset)
    rule_or_source_refs: frozenset[str] = field(default_factory=frozenset)
    escalation_required: bool | None = None


@dataclass(frozen=True)
class FractionMetric:
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator < 0 or self.denominator < 0:
            raise ValueError("metric counts must be non-negative")
        if self.numerator > self.denominator:
            raise ValueError("metric numerator cannot exceed denominator")

    @property
    def value(self) -> float | None:
        if self.denominator == 0:
            return None
        return self.numerator / self.denominator


@dataclass(frozen=True)
class MobilityCaseEvaluation:
    case_id: str
    provenance: MobilityCaseProvenance
    metrics: Mapping[str, FractionMetric]


@dataclass(frozen=True)
class MobilityEvaluationSummary:
    case_count: int
    provenance_counts: Mapping[MobilityCaseProvenance, int]
    metrics: Mapping[str, FractionMetric]


@dataclass(frozen=True)
class GovernedWorkflowMeasurement:
    workflow_id: str
    risk_tier: EvaluationRiskTier
    raw_task_cost_eur: float
    governed_completion_cost_eur: float
    latency_ms: int
    human_interventions: int = 0
    board_interventions: int = 0
    verifier_calls: int = 0
    stale_or_retry_count: int = 0

    def __post_init__(self) -> None:
        if not self.workflow_id.strip():
            raise ValueError("workflow_id is required")
        for name, value in (
            ("raw_task_cost_eur", self.raw_task_cost_eur),
            ("governed_completion_cost_eur", self.governed_completion_cost_eur),
        ):
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        for name, value in (
            ("human_interventions", self.human_interventions),
            ("board_interventions", self.board_interventions),
            ("verifier_calls", self.verifier_calls),
            ("stale_or_retry_count", self.stale_or_retry_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")

    @property
    def governance_amplification_factor(self) -> float | None:
        if self.raw_task_cost_eur == 0:
            return None
        return self.governed_completion_cost_eur / self.raw_task_cost_eur


@dataclass(frozen=True)
class WorkflowEconomicsSummary:
    risk_tier: EvaluationRiskTier
    workflow_count: int
    raw_task_cost_eur: float
    governed_completion_cost_eur: float
    governance_amplification_factor: float | None
    latency_p50_ms: int | None
    latency_p95_ms: int | None
    human_interventions: int
    board_interventions: int
    verifier_calls: int
    stale_or_retry_count: int


def _exact_match(expected: object | None, actual: object) -> FractionMetric:
    if expected is None:
        return FractionMetric(0, 0)
    return FractionMetric(int(expected == actual), 1)


def _set_recall(expected: frozenset[str] | None, actual: frozenset[str]) -> FractionMetric:
    if expected is None:
        return FractionMetric(0, 0)
    if not expected:
        return FractionMetric(0, 0)
    return FractionMetric(len(expected & actual), len(expected))


def _set_precision(expected: frozenset[str] | None, actual: frozenset[str]) -> FractionMetric:
    if expected is None:
        return FractionMetric(0, 0)
    if not actual:
        return FractionMetric(0, 0)
    return FractionMetric(len(expected & actual), len(actual))


def evaluate_mobility_case(
    gold: MobilityGoldCase,
    prediction: MobilityOutcomePrediction,
) -> MobilityCaseEvaluation:
    """Score only labeled dimensions; never produce a universal quality score."""

    metrics = {
        "pathway_identification_accuracy": _exact_match(gold.expected_pathway_keys, prediction.pathway_keys),
        "eligibility_accuracy": _exact_match(gold.expected_eligibility, prediction.eligibility),
        "required_evidence_recall": _set_recall(gold.expected_required_evidence, prediction.required_evidence),
        "missing_evidence_recall": _set_recall(gold.expected_missing_evidence, prediction.missing_evidence),
        "contradiction_recall": _set_recall(gold.expected_contradictions, prediction.contradictions),
        "citation_precision": _set_precision(gold.expected_rule_or_source_refs, prediction.rule_or_source_refs),
        "citation_recall": _set_recall(gold.expected_rule_or_source_refs, prediction.rule_or_source_refs),
        "escalation_accuracy": _exact_match(gold.expected_escalation_required, prediction.escalation_required),
    }
    return MobilityCaseEvaluation(case_id=gold.case_id, provenance=gold.provenance, metrics=metrics)


def summarize_mobility_evaluations(
    evaluations: Iterable[MobilityCaseEvaluation],
) -> MobilityEvaluationSummary:
    rows = list(evaluations)
    provenance_counts: dict[MobilityCaseProvenance, int] = {}
    metric_totals: dict[str, list[int]] = {}

    for row in rows:
        provenance_counts[row.provenance] = provenance_counts.get(row.provenance, 0) + 1
        for name, metric in row.metrics.items():
            counts = metric_totals.setdefault(name, [0, 0])
            counts[0] += metric.numerator
            counts[1] += metric.denominator

    return MobilityEvaluationSummary(
        case_count=len(rows),
        provenance_counts=provenance_counts,
        metrics={name: FractionMetric(*counts) for name, counts in metric_totals.items()},
    )


def _nearest_rank(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def summarize_workflow_economics(
    measurements: Iterable[GovernedWorkflowMeasurement],
) -> Mapping[EvaluationRiskTier, WorkflowEconomicsSummary]:
    grouped: dict[EvaluationRiskTier, list[GovernedWorkflowMeasurement]] = {}
    for measurement in measurements:
        grouped.setdefault(measurement.risk_tier, []).append(measurement)

    summaries: dict[EvaluationRiskTier, WorkflowEconomicsSummary] = {}
    for risk_tier, rows in grouped.items():
        raw_cost = sum(row.raw_task_cost_eur for row in rows)
        governed_cost = sum(row.governed_completion_cost_eur for row in rows)
        gaf = None if raw_cost == 0 else governed_cost / raw_cost
        latencies = [row.latency_ms for row in rows]
        summaries[risk_tier] = WorkflowEconomicsSummary(
            risk_tier=risk_tier,
            workflow_count=len(rows),
            raw_task_cost_eur=raw_cost,
            governed_completion_cost_eur=governed_cost,
            governance_amplification_factor=gaf,
            latency_p50_ms=_nearest_rank(latencies, 0.50),
            latency_p95_ms=_nearest_rank(latencies, 0.95),
            human_interventions=sum(row.human_interventions for row in rows),
            board_interventions=sum(row.board_interventions for row in rows),
            verifier_calls=sum(row.verifier_calls for row in rows),
            stale_or_retry_count=sum(row.stale_or_retry_count for row in rows),
        )
    return summaries
