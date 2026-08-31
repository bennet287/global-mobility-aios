#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
TARGET = ROOT / "scripts" / "evaluate_austria_ai_domain_review.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

CONTRACT_VERSION = "aios-ai-domain-mutation-strength.v1"
CASE_IDS = ["case-a", "case-b"]
VALID_SOURCE_REFS = {"source-a", "source-b"}
EXPECTED_CLASSIFICATIONS = ("INELIGIBLE", "REVIEW_REQUIRED")


@dataclass(frozen=True)
class SourceMutation:
    key: str
    description: str
    original: str
    replacement: str
    probe: Callable[[types.ModuleType], bool]


def _load_module(source: str, *, name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = str(TARGET)
    module.__package__ = None
    exec(compile(source, str(TARGET), "exec"), module.__dict__)
    return module


def _valid_payload(module: types.ModuleType) -> dict[str, object]:
    return {
        "reviews": [
            {
                "case_id": "case-a",
                "classification": "INELIGIBLE",
                "pathway_key": module.REVIEW_SCOPE_PATHWAY_KEY,
                "points_total": 30,
                "points_breakdown": {"qualification": 30},
                "requirements_satisfied": ["qualifying training"],
                "requirements_failed": ["points below threshold"],
                "source_refs": ["source-a"],
                "reason": "The supplied facts are below the route threshold.",
                "final_authority_decision": False,
            },
            {
                "case_id": "case-b",
                "classification": "REVIEW_REQUIRED",
                "pathway_key": module.REVIEW_SCOPE_PATHWAY_KEY,
                "points_total": 55,
                "points_breakdown": {
                    "qualification": 30,
                    "experience": 20,
                    "language": 5,
                },
                "requirements_satisfied": ["threshold reached"],
                "requirements_failed": [],
                "source_refs": ["source-a", "source-b"],
                "reason": (
                    "The simplified facts meet the threshold but formal assessment "
                    "remains required."
                ),
                "final_authority_decision": False,
            },
        ]
    }


def _provider_run(
    provider: str,
    classifications: tuple[str, str] = EXPECTED_CLASSIFICATIONS,
    *,
    identity_match: object = True,
    structural_valid: bool = True,
    status: str = "completed",
    source_match: bool = True,
) -> dict[str, object]:
    return {
        "provider_key": provider,
        "status": status,
        "structural_valid": structural_valid,
        "response_identity_match": identity_match,
        "reviews": [
            {"case_id": "case-a", "classification": classifications[0]},
            {"case_id": "case-b", "classification": classifications[1]},
        ],
        "comparison": {
            "all_classifications_match": source_match,
            "all_pathways_match": source_match,
        },
    }


def _validation_rejects(module: types.ModuleType, payload: dict[str, object]) -> bool:
    try:
        module._validate_provider_payload(
            payload,
            case_ids=CASE_IDS,
            valid_source_refs=VALID_SOURCE_REFS,
        )
    except ValueError:
        return True
    return False


def _probe_authority_fail_closed(module: types.ModuleType) -> bool:
    payload = _valid_payload(module)
    payload["reviews"][0]["final_authority_decision"] = None  # type: ignore[index]
    return _validation_rejects(module, payload)


def _probe_route_fail_closed(module: types.ModuleType) -> bool:
    payload = _valid_payload(module)
    payload["reviews"][0]["pathway_key"] = "invented-authority-route"  # type: ignore[index]
    return _validation_rejects(module, payload)


def _probe_mixed_source_set_fail_closed(module: types.ModuleType) -> bool:
    payload = _valid_payload(module)
    payload["reviews"][0]["source_refs"] = ["source-a", "forged-source"]  # type: ignore[index]
    return _validation_rejects(module, payload)


def _probe_empty_reason_fail_closed(module: types.ModuleType) -> bool:
    payload = _valid_payload(module)
    payload["reviews"][0]["reason"] = "   "  # type: ignore[index]
    return _validation_rejects(module, payload)


def _probe_two_distinct_providers_qualify(module: types.ModuleType) -> bool:
    summary = module._corroboration_summary(
        [_provider_run("gemini"), _provider_run("deepseek")],
        case_ids=CASE_IDS,
    )
    return summary["multi_model_corroboration_candidate"] is True


def _probe_disagreement_blocks_corroboration(module: types.ModuleType) -> bool:
    summary = module._corroboration_summary(
        [
            _provider_run("gemini"),
            _provider_run("deepseek", ("INELIGIBLE", "ELIGIBLE")),
        ],
        case_ids=CASE_IDS,
    )
    return summary["multi_model_corroboration_candidate"] is False


def _probe_source_mismatch_blocks_corroboration(module: types.ModuleType) -> bool:
    summary = module._corroboration_summary(
        [
            _provider_run("gemini"),
            _provider_run("deepseek", source_match=False),
        ],
        case_ids=CASE_IDS,
    )
    return summary["multi_model_corroboration_candidate"] is False


def _probe_identity_mismatch_blocks_corroboration(module: types.ModuleType) -> bool:
    summary = module._corroboration_summary(
        [
            _provider_run("gemini"),
            _provider_run("deepseek", identity_match=None),
        ],
        case_ids=CASE_IDS,
    )
    return summary["multi_model_corroboration_candidate"] is False


def _mutation_catalog() -> tuple[SourceMutation, ...]:
    return (
        SourceMutation(
            "weaken-authority-false-guard",
            "Weaken the explicit false-only authority guard so null authority values can pass.",
            'if review.get("final_authority_decision") is not False:',
            'if review.get("final_authority_decision") is True:',
            _probe_authority_fail_closed,
        ),
        SourceMutation(
            "invert-route-scope-guard",
            "Invert the declared pathway guard so an undeclared route can pass.",
            "if pathway_key != REVIEW_SCOPE_PATHWAY_KEY:",
            "if pathway_key == REVIEW_SCOPE_PATHWAY_KEY:",
            _probe_route_fail_closed,
        ),
        SourceMutation(
            "weaken-source-membership-any-to-all",
            "Weaken source membership from reject-any-unknown to reject-only-if-all-unknown.",
            "if not normalized_refs or any(item not in valid_source_refs for item in normalized_refs):",
            "if not normalized_refs or all(item not in valid_source_refs for item in normalized_refs):",
            _probe_mixed_source_set_fail_closed,
        ),
        SourceMutation(
            "weaken-empty-reason-guard",
            "Weaken the normalized non-empty rationale requirement.",
            "if not reason:",
            "if reason is None:",
            _probe_empty_reason_fail_closed,
        ),
        SourceMutation(
            "raise-distinct-provider-threshold",
            "Change the exact two-provider corroboration threshold from >= to >.",
            'candidate = len({str(run.get("provider_key")) for run in qualifying}) >= MIN_CORROBORATING_PROVIDERS and all(unanimous.values()) and all_source_labels_match',
            'candidate = len({str(run.get("provider_key")) for run in qualifying}) > MIN_CORROBORATING_PROVIDERS and all(unanimous.values()) and all_source_labels_match',
            _probe_two_distinct_providers_qualify,
        ),
        SourceMutation(
            "weaken-unanimity-cardinality",
            "Allow two distinct classifications to masquerade as unanimous.",
            "unanimous = {case_id: bool(values) and len(set(values)) == 1 for case_id, values in classifications.items()}",
            "unanimous = {case_id: bool(values) and len(set(values)) <= 2 for case_id, values in classifications.items()}",
            _probe_disagreement_blocks_corroboration,
        ),
        SourceMutation(
            "weaken-all-source-labels-to-any",
            "Allow one matching provider to hide another provider's source-label mismatch.",
            'all_source_labels_match = bool(qualifying) and all(bool(run["comparison"].get("all_classifications_match")) and bool(run["comparison"].get("all_pathways_match")) for run in qualifying)',
            'all_source_labels_match = bool(qualifying) and any(bool(run["comparison"].get("all_classifications_match")) and bool(run["comparison"].get("all_pathways_match")) for run in qualifying)',
            _probe_source_mismatch_blocks_corroboration,
        ),
        SourceMutation(
            "weaken-provider-identity-qualification",
            "Allow a non-true provider identity result to qualify for corroboration.",
            'run.get("response_identity_match") is True',
            'run.get("response_identity_match") is not False',
            _probe_identity_mismatch_blocks_corroboration,
        ),
    )


def _apply_exact_mutation(source: str, mutation: SourceMutation) -> str:
    count = source.count(mutation.original)
    if count != 1:
        raise ValueError(
            f"mutation {mutation.key} expected exactly one target occurrence, found {count}"
        )
    return source.replace(mutation.original, mutation.replacement, 1)


def run_mutation_strength_gate() -> dict[str, object]:
    source = TARGET.read_text(encoding="utf-8")
    baseline = _load_module(source, name="_aios_ai_domain_mutation_baseline")
    results: list[dict[str, object]] = []

    for index, mutation in enumerate(_mutation_catalog(), start=1):
        baseline_safe = bool(mutation.probe(baseline))
        mutated_source = _apply_exact_mutation(source, mutation)
        mutant = _load_module(
            mutated_source,
            name=f"_aios_ai_domain_mutant_{index}_{mutation.key.replace('-', '_')}",
        )
        mutant_safe = bool(mutation.probe(mutant))
        killed = baseline_safe and not mutant_safe
        results.append(
            {
                "key": mutation.key,
                "description": mutation.description,
                "baseline_probe_passed": baseline_safe,
                "mutant_probe_passed": mutant_safe,
                "status": "KILLED" if killed else "SURVIVED",
            }
        )

    killed_count = sum(item["status"] == "KILLED" for item in results)
    survived_count = len(results) - killed_count
    return {
        "contract_version": CONTRACT_VERSION,
        "target": str(TARGET.relative_to(ROOT)).replace("\\", "/"),
        "status": "PASS" if survived_count == 0 else "FAIL",
        "mutation_count": len(results),
        "killed_count": killed_count,
        "survived_count": survived_count,
        "mutation_engine": "first-party-bounded-semantic-source-mutation",
        "external_mutation_engine_adopted": False,
        "professional_review_status_effect": "NONE",
        "live_model_security_claim": False,
        "fuzzing_claim": False,
        "red_team_runtime_claim": False,
        "mutations": results,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bounded semantic source-mutation strength gate for the Austria AI-domain "
            "review validator/corroboration seams. This measures whether focused "
            "safety probes kill selected implementation mutations; it is not fuzzing, "
            "live-model security proof, professional review or Red Team proof."
        )
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = run_mutation_strength_gate()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
