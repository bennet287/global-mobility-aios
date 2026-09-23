from __future__ import annotations

import pytest

from app.services.system1_benchmark import BenchmarkCase, CandidateObservation, evaluate


def _cases() -> list[BenchmarkCase]:
    return [
        BenchmarkCase("retry-transport", "retry_stop_escalate", "ALLOW", "ALLOW"),
        BenchmarkCase("stop-config", "retry_stop_escalate", "STOP", "STOP"),
        BenchmarkCase("escalate-unknown", "retry_stop_escalate", "ESCALATE", "ESCALATE", ambiguous=True),
        BenchmarkCase("competency-ready", "competency_preflight", "READY", "READY"),
        BenchmarkCase("competency-gap", "competency_preflight", "GAP", "GAP"),
        BenchmarkCase("competency-no", "competency_preflight", "NOT_SUITABLE", "NOT_SUITABLE"),
        BenchmarkCase("context-keep", "context_compaction", "KEEP", "KEEP"),
        BenchmarkCase("context-drop", "context_compaction", "DROP", "DROP"),
    ]


def test_perfect_candidate_reports_accuracy_calibration_latency_and_cost() -> None:
    cases = _cases()
    observations = [
        CandidateObservation(c.case_id, c.expected, 1.0, 10.0 + i, 0.001)
        for i, c in enumerate(cases)
    ]
    metrics = evaluate(cases, observations)

    assert metrics.accuracy == 1.0
    assert metrics.ece == 0.0
    assert metrics.false_allow_rate == 0.0
    assert metrics.false_stop_rate == 0.0
    assert metrics.unnecessary_escalation_rate == 0.0
    assert metrics.deterministic_disagreement_rate == 0.0
    assert metrics.p50_latency_ms == 13.5
    assert metrics.p95_latency_ms == pytest.approx(16.65)
    assert metrics.measured_cost_usd == pytest.approx(0.008)
    assert metrics.missing_cost_observations == 0


def test_wrong_candidate_exposes_safety_errors_and_does_not_invent_cost() -> None:
    cases = _cases()
    decisions = ["ALLOW", "ALLOW", "STOP", "GAP", "READY", "READY", "DROP", "KEEP"]
    observations = [
        CandidateObservation(c.case_id, decision, 0.9, 5.0 + i)
        for i, (c, decision) in enumerate(zip(cases, decisions, strict=True))
    ]
    metrics = evaluate(cases, observations)

    assert metrics.accuracy == pytest.approx(1 / 8)
    assert metrics.false_allow_rate > 0
    assert metrics.false_stop_rate > 0
    assert metrics.deterministic_disagreement_rate == pytest.approx(7 / 8)
    assert metrics.measured_cost_usd is None
    assert metrics.missing_cost_observations == 8


def test_missing_observation_fails_closed() -> None:
    cases = _cases()
    with pytest.raises(ValueError, match="cover every benchmark case exactly once"):
        evaluate(cases, [CandidateObservation(cases[0].case_id, "ALLOW", 0.8, 2.0)])


def test_invalid_confidence_fails_closed() -> None:
    cases = _cases()
    observations = [
        CandidateObservation(c.case_id, c.expected, 1.1 if i == 0 else 0.8, 2.0)
        for i, c in enumerate(cases)
    ]
    with pytest.raises(ValueError, match="confidence"):
        evaluate(cases, observations)
