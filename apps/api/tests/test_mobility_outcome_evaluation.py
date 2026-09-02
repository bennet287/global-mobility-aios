from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.evaluations.mobility_outcomes import (
    EvaluationRiskTier,
    GovernedWorkflowMeasurement,
    MobilityCaseProvenance,
    MobilityEligibilityLabel,
    MobilityGoldCase,
    MobilityOutcomePrediction,
    evaluate_mobility_case,
    summarize_mobility_evaluations,
    summarize_workflow_economics,
)


AS_OF = datetime(2026, 8, 22, 8, 0, tzinfo=timezone.utc)


def _synthetic_case(**overrides: object) -> MobilityGoldCase:
    values: dict[str, object] = {
        "case_id": "at-synthetic-rwr-001",
        "jurisdiction": "Austria",
        "evaluation_as_of": AS_OF,
        "provenance": MobilityCaseProvenance.SYNTHETIC,
        "expected_pathway_keys": frozenset({"at-rwr-shortage"}),
        "expected_eligibility": MobilityEligibilityLabel.INSUFFICIENT_INFORMATION,
        "expected_required_evidence": frozenset({"passport", "qualification", "job_offer"}),
        "expected_missing_evidence": frozenset({"job_offer"}),
        "expected_contradictions": frozenset(),
        "expected_rule_or_source_refs": frozenset({"vr-at-rwr-1", "source-at-rwr"}),
        "expected_escalation_required": False,
        "notes": "Synthetic harness fixture only; not a legal/domain correctness claim.",
    }
    values.update(overrides)
    return MobilityGoldCase(**values)  # type: ignore[arg-type]


def test_mobility_case_scoring_keeps_explicit_denominators_and_no_universal_score() -> None:
    result = evaluate_mobility_case(
        _synthetic_case(),
        MobilityOutcomePrediction(
            pathway_keys=frozenset({"at-rwr-shortage"}),
            eligibility=MobilityEligibilityLabel.INSUFFICIENT_INFORMATION,
            required_evidence=frozenset({"passport", "qualification"}),
            missing_evidence=frozenset({"job_offer"}),
            contradictions=frozenset(),
            rule_or_source_refs=frozenset({"vr-at-rwr-1", "invented-ref"}),
            escalation_required=False,
        ),
    )

    assert result.metrics["pathway_identification_accuracy"].value == 1.0
    assert result.metrics["eligibility_accuracy"].value == 1.0
    assert result.metrics["required_evidence_recall"].numerator == 2
    assert result.metrics["required_evidence_recall"].denominator == 3
    assert result.metrics["missing_evidence_recall"].value == 1.0
    assert result.metrics["contradiction_recall"].denominator == 0
    assert result.metrics["contradiction_recall"].value is None
    assert result.metrics["citation_precision"].numerator == 1
    assert result.metrics["citation_precision"].denominator == 2
    assert result.metrics["citation_recall"].numerator == 1
    assert result.metrics["citation_recall"].denominator == 2
    assert "score" not in result.__dataclass_fields__


def test_unlabeled_dimensions_remain_undefined_not_failure_or_success() -> None:
    result = evaluate_mobility_case(
        _synthetic_case(
            expected_required_evidence=None,
            expected_missing_evidence=None,
            expected_rule_or_source_refs=None,
            expected_escalation_required=None,
        ),
        MobilityOutcomePrediction(
            required_evidence=frozenset({"anything"}),
            missing_evidence=frozenset({"anything"}),
            rule_or_source_refs=frozenset({"anything"}),
            escalation_required=True,
        ),
    )

    for name in (
        "required_evidence_recall",
        "missing_evidence_recall",
        "citation_precision",
        "citation_recall",
        "escalation_accuracy",
    ):
        assert result.metrics[name].denominator == 0
        assert result.metrics[name].value is None


def test_professionally_reviewed_case_requires_review_provenance() -> None:
    with pytest.raises(ValueError, match="review_reference"):
        _synthetic_case(
            provenance=MobilityCaseProvenance.PROFESSIONALLY_REVIEWED,
            review_reference=None,
        )

    reviewed = _synthetic_case(
        provenance=MobilityCaseProvenance.PROFESSIONALLY_REVIEWED,
        review_reference="professional-review:case-42:v1",
    )
    assert reviewed.provenance is MobilityCaseProvenance.PROFESSIONALLY_REVIEWED


def test_official_source_curated_case_requires_source_provenance() -> None:
    with pytest.raises(ValueError, match="provenance_references"):
        _synthetic_case(provenance=MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED)

    curated = _synthetic_case(
        provenance=MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED,
        provenance_references=("https://www.migration.gv.at/index.php?id=1050",),
    )
    assert curated.provenance is MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED


def test_evaluation_as_of_requires_timezone_awareness() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _synthetic_case(evaluation_as_of=datetime(2026, 8, 22, 8, 0))


def test_batch_summary_aggregates_counts_without_collapsing_provenance() -> None:
    perfect = evaluate_mobility_case(
        _synthetic_case(case_id="synthetic-1"),
        MobilityOutcomePrediction(
            pathway_keys=frozenset({"at-rwr-shortage"}),
            eligibility=MobilityEligibilityLabel.INSUFFICIENT_INFORMATION,
            required_evidence=frozenset({"passport", "qualification", "job_offer"}),
            missing_evidence=frozenset({"job_offer"}),
            rule_or_source_refs=frozenset({"vr-at-rwr-1", "source-at-rwr"}),
            escalation_required=False,
        ),
    )
    reviewed = evaluate_mobility_case(
        _synthetic_case(
            case_id="reviewed-1",
            provenance=MobilityCaseProvenance.PROFESSIONALLY_REVIEWED,
            review_reference="professional-review:reviewed-1:v1",
        ),
        MobilityOutcomePrediction(
            pathway_keys=frozenset({"wrong-pathway"}),
            eligibility=MobilityEligibilityLabel.REVIEW_REQUIRED,
        ),
    )

    summary = summarize_mobility_evaluations([perfect, reviewed])
    assert summary.case_count == 2
    assert summary.provenance_counts[MobilityCaseProvenance.SYNTHETIC] == 1
    assert summary.provenance_counts[MobilityCaseProvenance.PROFESSIONALLY_REVIEWED] == 1
    assert summary.metrics["pathway_identification_accuracy"].numerator == 1
    assert summary.metrics["pathway_identification_accuracy"].denominator == 2
    assert summary.metrics["eligibility_accuracy"].numerator == 1
    assert summary.metrics["eligibility_accuracy"].denominator == 2


def test_governance_amplification_and_latency_are_reported_by_risk_tier() -> None:
    rows = [
        GovernedWorkflowMeasurement(
            workflow_id="r1-a",
            risk_tier=EvaluationRiskTier.R1,
            raw_task_cost_eur=0.10,
            governed_completion_cost_eur=0.12,
            latency_ms=100,
        ),
        GovernedWorkflowMeasurement(
            workflow_id="r1-b",
            risk_tier=EvaluationRiskTier.R1,
            raw_task_cost_eur=0.20,
            governed_completion_cost_eur=0.24,
            latency_ms=200,
            stale_or_retry_count=1,
        ),
        GovernedWorkflowMeasurement(
            workflow_id="r3-a",
            risk_tier=EvaluationRiskTier.R3,
            raw_task_cost_eur=0.10,
            governed_completion_cost_eur=0.30,
            latency_ms=800,
            human_interventions=1,
            verifier_calls=1,
        ),
    ]

    summary = summarize_workflow_economics(rows)
    r1 = summary[EvaluationRiskTier.R1]
    r3 = summary[EvaluationRiskTier.R3]

    assert r1.workflow_count == 2
    assert r1.governance_amplification_factor == pytest.approx(1.2)
    assert r1.latency_p50_ms == 100
    assert r1.latency_p95_ms == 200
    assert r1.stale_or_retry_count == 1

    assert r3.workflow_count == 1
    assert r3.governance_amplification_factor == pytest.approx(3.0)
    assert r3.latency_p50_ms == 800
    assert r3.human_interventions == 1
    assert r3.verifier_calls == 1


def test_zero_raw_cost_leaves_gaf_undefined() -> None:
    measurement = GovernedWorkflowMeasurement(
        workflow_id="measurement-only",
        risk_tier=EvaluationRiskTier.R0,
        raw_task_cost_eur=0.0,
        governed_completion_cost_eur=0.01,
        latency_ms=5,
    )
    assert measurement.governance_amplification_factor is None
    assert summarize_workflow_economics([measurement])[EvaluationRiskTier.R0].governance_amplification_factor is None


def test_workflow_measurement_rejects_invalid_costs() -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        GovernedWorkflowMeasurement(
            workflow_id="bad",
            risk_tier=EvaluationRiskTier.R1,
            raw_task_cost_eur=float("nan"),
            governed_completion_cost_eur=0.1,
            latency_ms=10,
        )


def test_austria_official_source_curated_seed_is_explicitly_non_professional_and_structured() -> None:
    path = Path("apps/api/evaluations/mobility_cases/austria_rwr_shortage_2026_v1.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "mobility-gold-v1"
    assert payload["provenance"] == MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED.value
    assert payload["professional_review_status"] == "NOT_REVIEWED"
    assert "not professional legal review" in payload["claim_boundary"].lower()
    assert len(payload["sources"]) >= 3
    assert {source["url"].split("/")[2] for source in payload["sources"]} <= {
        "www.migration.gv.at",
        "www.oesterreich.gv.at",
        "www.ris.bka.gv.at",
    }
    assert len(payload["cases"]) == 3

    source_refs = tuple(source["url"] for source in payload["sources"])
    for item in payload["cases"]:
        expected = item["expected"]
        case = MobilityGoldCase(
            case_id=item["case_id"],
            jurisdiction=payload["jurisdiction"],
            evaluation_as_of=datetime.fromisoformat(payload["evaluation_as_of"]),
            provenance=MobilityCaseProvenance(payload["provenance"]),
            expected_pathway_keys=frozenset(expected["pathway_keys"]),
            expected_eligibility=MobilityEligibilityLabel(expected["eligibility"]),
            expected_required_evidence=frozenset(expected["required_evidence"]),
            expected_missing_evidence=frozenset(expected["missing_evidence"]),
            expected_contradictions=frozenset(expected["contradictions"]),
            expected_rule_or_source_refs=frozenset(expected["rule_or_source_refs"]),
            expected_escalation_required=expected["escalation_required"],
            provenance_references=source_refs,
            notes=item["rationale"],
        )
        assert case.provenance is MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED

    by_id = {item["case_id"]: item for item in payload["cases"]}
    assert by_id["at-rwr-shortage-software-di-no-job-offer-2026-01"]["expected"]["eligibility"] == "INELIGIBLE"
    assert by_id["at-rwr-shortage-software-di-strong-points-2026-01"]["expected"]["eligibility"] == "ELIGIBLE"
    assert by_id["at-rwr-shortage-software-di-strong-points-2026-01"]["expected"]["escalation_required"] is False
    assert by_id["at-rwr-shortage-software-di-under-points-2026-01"]["expected"]["eligibility"] == "INELIGIBLE"
