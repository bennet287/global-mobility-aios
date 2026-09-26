from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Literal

Decision = Literal["ALLOW", "STOP", "ESCALATE", "READY", "GAP", "NOT_SUITABLE", "KEEP", "DROP"]

@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    workload: str
    expected: Decision
    deterministic: Decision
    ambiguous: bool = False

@dataclass(frozen=True)
class CandidateObservation:
    case_id: str
    decision: Decision
    confidence: float
    latency_ms: float
    cost_usd: float | None = None

@dataclass(frozen=True)
class BenchmarkMetrics:
    accuracy: float
    ece: float
    false_allow_rate: float
    false_stop_rate: float
    unnecessary_escalation_rate: float
    deterministic_disagreement_rate: float
    ambiguous_safe_escalation_rate: float | None
    p50_latency_ms: float
    p95_latency_ms: float
    measured_cost_usd: float | None
    missing_cost_observations: int

def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    weight = pos - lo
    return ordered[lo] * (1 - weight) + ordered[hi] * weight

def evaluate(cases: Iterable[BenchmarkCase], observations: Iterable[CandidateObservation], bins: int = 10) -> BenchmarkMetrics:
    case_list = list(cases)
    observation_list = list(observations)
    if not case_list:
        raise ValueError("benchmark requires at least one case")
    case_ids = [c.case_id for c in case_list]
    observation_ids = [o.case_id for o in observation_list]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("benchmark case ids must be unique")
    if len(set(observation_ids)) != len(observation_ids):
        raise ValueError("candidate observations must contain each benchmark case exactly once")
    if len(observation_ids) != len(case_ids) or set(observation_ids) != set(case_ids):
        raise ValueError("candidate observations must cover every benchmark case exactly once")
    if bins < 1:
        raise ValueError("bins must be positive")

    obs_by_id = {o.case_id: o for o in observation_list}
    paired = [(c, obs_by_id[c.case_id]) for c in case_list]
    for _, o in paired:
        if not 0.0 <= o.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if o.latency_ms < 0:
            raise ValueError("latency must be non-negative")
        if o.cost_usd is not None and o.cost_usd < 0:
            raise ValueError("cost must be non-negative")

    correct = [float(c.expected == o.decision) for c, o in paired]
    accuracy = sum(correct) / len(paired)

    ece = 0.0
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        bucket = [(c, o) for c, o in paired if lower <= o.confidence <= upper and (index == bins - 1 or o.confidence < upper)]
        if bucket:
            bucket_accuracy = sum(float(c.expected == o.decision) for c, o in bucket) / len(bucket)
            bucket_confidence = sum(o.confidence for _, o in bucket) / len(bucket)
            ece += (len(bucket) / len(paired)) * abs(bucket_accuracy - bucket_confidence)

    retry_pairs = [pair for pair in paired if pair[0].workload == "retry_stop_escalate"]
    false_allow_candidates = [pair for pair in retry_pairs if pair[0].expected != "ALLOW"]
    false_stop_candidates = [pair for pair in retry_pairs if pair[0].expected != "STOP"]
    non_escalate_expected = [pair for pair in retry_pairs if pair[0].expected != "ESCALATE"]
    false_allow = sum(o.decision == "ALLOW" for _, o in false_allow_candidates) / len(false_allow_candidates) if false_allow_candidates else 0.0
    false_stop = sum(o.decision == "STOP" for _, o in false_stop_candidates) / len(false_stop_candidates) if false_stop_candidates else 0.0
    unnecessary_escalation = sum(o.decision == "ESCALATE" for _, o in non_escalate_expected) / len(non_escalate_expected) if non_escalate_expected else 0.0
    disagreement = sum(c.deterministic != o.decision for c, o in paired) / len(paired)
    ambiguous_pairs = [pair for pair in paired if pair[0].ambiguous]
    ambiguous_safe_escalation = (
        sum(o.decision == "ESCALATE" for _, o in ambiguous_pairs) / len(ambiguous_pairs)
        if ambiguous_pairs else None
    )

    latencies = [o.latency_ms for _, o in paired]
    known_costs = [o.cost_usd for _, o in paired if o.cost_usd is not None]
    return BenchmarkMetrics(
        accuracy=accuracy,
        ece=ece,
        false_allow_rate=false_allow,
        false_stop_rate=false_stop,
        unnecessary_escalation_rate=unnecessary_escalation,
        deterministic_disagreement_rate=disagreement,
        ambiguous_safe_escalation_rate=ambiguous_safe_escalation,
        p50_latency_ms=median(latencies),
        p95_latency_ms=_quantile(latencies, 0.95),
        measured_cost_usd=sum(known_costs) if len(known_costs) == len(paired) else None,
        missing_cost_observations=len(paired) - len(known_costs),
    )
