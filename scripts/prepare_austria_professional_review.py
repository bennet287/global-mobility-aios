#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.evaluations.professional_review import (  # noqa: E402
    PROFESSIONAL_REVIEW_SCHEMA_VERSION,
    MobilityReviewedLabels,
    ProfessionalReviewDecision,
    compile_professional_reviews,
    load_official_source_gold_set,
    load_professional_review_bundle,
)


HANDOFF_CONTRACT_VERSION = "austria-professional-review-handoff.v1"
DEFAULT_SOURCE_PATH = ROOT / "apps" / "api" / "evaluations" / "mobility_cases" / "austria_rwr_shortage_2026_v1.json"


def _json(value: object) -> str:
    return json.dumps(value, default=str, indent=2, sort_keys=True, ensure_ascii=False)


def _labels_payload(labels: MobilityReviewedLabels) -> dict[str, object]:
    return {
        "pathway_keys": None if labels.pathway_keys is None else sorted(labels.pathway_keys),
        "eligibility": None if labels.eligibility is None else labels.eligibility.value,
        "required_evidence": None if labels.required_evidence is None else sorted(labels.required_evidence),
        "missing_evidence": None if labels.missing_evidence is None else sorted(labels.missing_evidence),
        "contradictions": None if labels.contradictions is None else sorted(labels.contradictions),
        "rule_or_source_refs": None if labels.rule_or_source_refs is None else sorted(labels.rule_or_source_refs),
        "escalation_required": labels.escalation_required,
    }


def build_review_packet(source_path: Path, case_ids: tuple[str, ...]) -> dict[str, object]:
    source_set = load_official_source_gold_set(source_path)
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    raw_cases = {case["case_id"]: case for case in raw["cases"]}

    requested = case_ids or tuple(case.case_id for case in source_set.cases)
    unknown = sorted(set(requested) - set(raw_cases))
    if unknown:
        raise ValueError(f"unknown Austria professional-review case_id values: {', '.join(unknown)}")

    cases: list[dict[str, object]] = []
    for case_id in requested:
        source_case = source_set.case_by_id(case_id)
        raw_case = raw_cases[case_id]
        cases.append(
            {
                "case_id": case_id,
                "source_case_fingerprint": source_set.fingerprint_for(case_id),
                "facts": raw_case.get("facts", {}),
                "source_labels": _labels_payload(MobilityReviewedLabels.from_gold_case(source_case)),
                "source_rationale": raw_case.get("rationale"),
                "source_references": list(source_set.source_references),
                "reviewer_decision_required": [decision.value for decision in ProfessionalReviewDecision],
                "reviewer_instruction": (
                    "Independently assess the supplied facts and cited official sources. CONFIRMED must retain "
                    "the source labels exactly; CORRECTED must provide the complete corrected reviewed_labels; "
                    "DISPUTED and NEEDS_MORE_FACTS are held outside the promoted professional denominator."
                ),
            }
        )

    return {
        "contract_version": HANDOFF_CONTRACT_VERSION,
        "purpose": "Independent professional review handoff for the first real Austria benchmark tranche.",
        "source_benchmark_key": source_set.benchmark_key,
        "source_schema_version": source_set.schema_version,
        "review_schema_version": PROFESSIONAL_REVIEW_SCHEMA_VERSION,
        "jurisdiction": source_set.jurisdiction,
        "evaluation_as_of": source_set.evaluation_as_of.isoformat(),
        "source_professional_review_status": source_set.professional_review_status,
        "claim_boundary": source_set.claim_boundary,
        "reviewer_boundary": (
            "AIOS validates source fingerprints, review structure, decision semantics and supplied reviewer/credential "
            "references. It does not verify the real-world identity, independence, professional standing or credential "
            "validity of the reviewer; those must be established outside this compiler and referenced in the submitted record."
        ),
        "submission_requirements": [
            "Use schema_version mobility-professional-review-v1.",
            "Bind every review to the exact source_case_fingerprint in this packet.",
            "Supply timezone-aware created_at and reviewed_at timestamps.",
            "Supply durable professional_review_reference, reviewer_reference and reviewer_credential_reference values.",
            "Set independent_review=true only when independence has actually been established outside AIOS.",
            "Do not use test-only, placeholder or fabricated reviewer/credential references for acceptance evidence.",
            "Run this tool with --validate-bundle before treating the tranche as structurally promotable.",
        ],
        "case_count": len(cases),
        "cases": cases,
    }


def validate_review_bundle(source_path: Path, review_path: Path) -> dict[str, object]:
    source_set = load_official_source_gold_set(source_path)
    review_bundle = load_professional_review_bundle(review_path)
    compiled = compile_professional_reviews(source_set, review_bundle)
    return {
        "contract_version": HANDOFF_CONTRACT_VERSION,
        "mode": "validate-bundle",
        "source_benchmark_key": source_set.benchmark_key,
        "review_batch_id": review_bundle.review_batch_id,
        "source_case_count": compiled.source_case_count,
        "review_count": compiled.review_count,
        "confirmed_count": compiled.confirmed_count,
        "corrected_count": compiled.corrected_count,
        "disputed_count": compiled.disputed_count,
        "needs_more_facts_count": compiled.needs_more_facts_count,
        "professionally_reviewed_case_count": compiled.professionally_reviewed_case_count,
        "promoted_case_ids": [case.case_id for case in compiled.promoted_cases],
        "held_case_ids": list(compiled.held_case_ids),
        "unreviewed_case_ids": list(compiled.unreviewed_case_ids),
        "first_real_tranche_structural_candidate": compiled.professionally_reviewed_case_count > 0,
        "credential_references_structural_only": True,
        "acceptance_boundary": (
            "A structurally promotable bundle is not by itself proof that the reviewer identity, independence or credential "
            "is genuine; retain independently verifiable external evidence for those references."
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare an immutable-fingerprint Austria professional-review handoff packet or validate a completed "
            "independent review bundle. This tool never fabricates professional review and never verifies real-world credentials."
        )
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare-packet", action="store_true")
    modes.add_argument("--validate-bundle", type=Path)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.prepare_packet:
            payload = build_review_packet(args.source_path, tuple(args.case_id))
            rendered = _json(payload) + "\n"
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
                print(
                    _json(
                        {
                            "contract_version": HANDOFF_CONTRACT_VERSION,
                            "status": "prepared",
                            "output": str(args.output),
                            "case_count": payload["case_count"],
                        }
                    )
                )
            else:
                print(rendered, end="")
            return 0

        if args.case_id:
            raise ValueError("--case-id is only valid with --prepare-packet")
        report = validate_review_bundle(args.source_path, args.validate_bundle)
        print(_json(report))
        return 0 if report["first_real_tranche_structural_candidate"] else 2
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(
            _json(
                {
                    "contract_version": HANDOFF_CONTRACT_VERSION,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
