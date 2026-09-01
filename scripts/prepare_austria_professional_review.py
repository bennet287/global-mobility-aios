#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.evaluations.mobility_outcomes import MobilityEligibilityLabel  # noqa: E402
from app.evaluations.professional_review import (  # noqa: E402
    PROFESSIONAL_REVIEW_SCHEMA_VERSION,
    MobilityProfessionalReview,
    MobilityProfessionalReviewBundle,
    MobilityReviewedLabels,
    ProfessionalReviewDecision,
    compile_professional_reviews,
    load_official_source_gold_set,
    load_professional_review_bundle,
)


HANDOFF_CONTRACT_VERSION = "austria-professional-review-handoff.v3"
RETURN_TEMPLATE_CONTRACT_VERSION = "austria-professional-review-return-template.v1"
BLIND_RETURN_TEMPLATE_CONTRACT_VERSION = "austria-professional-review-blind-return-template.v1"
BLIND_RETURN_CONTRACT_VERSION = "austria-professional-review-blind-return.v1"
BLIND_ASSESSMENT_STATUSES = ("ASSESSED", "DISPUTED", "NEEDS_MORE_FACTS")
SUPERSEDED_REVIEWER_HANDOFF_CONTRACTS = ("austria-professional-review-handoff.v1", "austria-professional-review-handoff.v2")
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


def _empty_labels_payload() -> dict[str, object]:
    return {
        "pathway_keys": None,
        "eligibility": None,
        "required_evidence": None,
        "missing_evidence": None,
        "contradictions": None,
        "rule_or_source_refs": None,
        "escalation_required": None,
    }


def _reviewed_label_contract() -> dict[str, object]:
    return {
        "pathway_keys": {
            "tested_route_key": "at-rwr-skilled-worker-shortage-occupation",
            "instruction": (
                "For this tranche, use exactly the tested AIOS route key above. "
                "Alternative-route recommendations belong in notes; if the tested route framing itself is wrong, "
                "use assessment_status=DISPUTED."
            ),
        },
        "eligibility": {
            "allowed_values": [value.value for value in MobilityEligibilityLabel],
            "semantics": {
                "ELIGIBLE": (
                    "On the asserted facts, the mandatory legal criteria for the tested route are satisfied. "
                    "This does not authenticate documents, bind AMS or the residence authority, authorize submission, "
                    "or imply final issuance."
                ),
                "INELIGIBLE": (
                    "On the asserted facts, at least one mandatory legal criterion for the tested route fails."
                ),
                "INSUFFICIENT_INFORMATION": (
                    "The asserted facts do not contain enough information to determine whether the mandatory route "
                    "criteria are satisfied."
                ),
                "REVIEW_REQUIRED": (
                    "A material legal classification or interpretation remains unresolved even after accepting the "
                    "asserted facts. Do not use this label solely because normal document verification, AMS review, "
                    "residence-authority adjudication, or human governance will occur downstream."
                ),
            },
        },
        "required_evidence": {
            "bounded_keys": [
                "shortage_occupation_training",
                "binding_job_offer",
                "applicable_minimum_remuneration",
                "points_evidence",
            ],
            "instruction": (
                "Use only these bounded route-evaluation evidence categories in reviewed_labels. "
                "Passport, photographs, health insurance, criminal-record extracts, employer forms and other "
                "application-document details may be recorded in notes but are outside this benchmark label taxonomy."
            ),
        },
        "missing_evidence": {
            "bounded_keys": [
                "shortage_occupation_training",
                "binding_job_offer",
                "applicable_minimum_remuneration",
                "points_evidence",
            ],
            "instruction": (
                "Use [] when no bounded route-evidence category is missing from the asserted facts. "
                "This does not certify documentary completeness."
            ),
        },
        "contradictions": {
            "instruction": (
                "Use [] when contradictions were assessed and none were found. "
                "Do not use null for an ASSESSED review."
            ),
        },
        "rule_or_source_refs": {
            "instruction": (
                "Use the canonical official_sources[].ref identifiers supplied in the packet. "
                "Put additional prose citations or legal commentary in notes."
            ),
        },
        "escalation_required": {
            "true": (
                "Use true only when the tested route-level outcome itself requires escalation because a material legal "
                "ambiguity or unresolved classification remains."
            ),
            "false": (
                "Use false when the tested route-level outcome is clear on the asserted facts. "
                "Routine authority review and alternative-route suggestions do not by themselves make this true."
            ),
        },
    }


def _required_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null")
    return value


def _optional_string_set(value: object, *, field_name: str) -> frozenset[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list or null")
    normalized: set[str] = set()
    for index, item in enumerate(value):
        normalized.add(_required_text(item, field_name=f"{field_name}[{index}]"))
    return frozenset(normalized)


def _blind_reviewed_labels(value: object, *, field_name: str) -> MobilityReviewedLabels:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object for ASSESSED review")
    required_fields = (
        "pathway_keys",
        "eligibility",
        "required_evidence",
        "missing_evidence",
        "contradictions",
        "rule_or_source_refs",
        "escalation_required",
    )
    missing_fields = [name for name in required_fields if value.get(name) is None]
    if missing_fields:
        raise ValueError(
            f"{field_name} must populate all reviewed label fields for ASSESSED review; "
            f"missing: {', '.join(missing_fields)}"
        )
    eligibility_value = value.get("eligibility")
    eligibility = (
        None
        if eligibility_value is None
        else MobilityEligibilityLabel(_required_text(eligibility_value, field_name=f"{field_name}.eligibility"))
    )
    escalation_required = value.get("escalation_required")
    if escalation_required is not None and not isinstance(escalation_required, bool):
        raise ValueError(f"{field_name}.escalation_required must be boolean or null")
    return MobilityReviewedLabels(
        pathway_keys=_optional_string_set(value.get("pathway_keys"), field_name=f"{field_name}.pathway_keys"),
        eligibility=eligibility,
        required_evidence=_optional_string_set(
            value.get("required_evidence"), field_name=f"{field_name}.required_evidence"
        ),
        missing_evidence=_optional_string_set(
            value.get("missing_evidence"), field_name=f"{field_name}.missing_evidence"
        ),
        contradictions=_optional_string_set(
            value.get("contradictions"), field_name=f"{field_name}.contradictions"
        ),
        rule_or_source_refs=_optional_string_set(
            value.get("rule_or_source_refs"), field_name=f"{field_name}.rule_or_source_refs"
        ),
        escalation_required=escalation_required,
    )


def _requested_case_ids(source_path: Path, case_ids: tuple[str, ...]) -> tuple[object, tuple[str, ...]]:
    source_set = load_official_source_gold_set(source_path)
    requested = case_ids or tuple(case.case_id for case in source_set.cases)
    known = {case.case_id for case in source_set.cases}
    unknown = sorted(set(requested) - known)
    if unknown:
        raise ValueError(f"unknown Austria professional-review case_id values: {', '.join(unknown)}")
    return source_set, requested


def build_review_packet(source_path: Path, case_ids: tuple[str, ...]) -> dict[str, object]:
    source_set, requested = _requested_case_ids(source_path, case_ids)
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    raw_cases = {case["case_id"]: case for case in raw["cases"]}

    cases: list[dict[str, object]] = []
    for case_id in requested:
        raw_case = raw_cases[case_id]
        cases.append(
            {
                "case_id": case_id,
                "source_case_fingerprint": source_set.fingerprint_for(case_id),
                "facts": raw_case.get("facts", {}),
                "fact_evidence_boundary": raw_case.get("fact_evidence_boundary"),
                "source_references": list(source_set.source_references),
                "reviewer_assessment_status_required": list(BLIND_ASSESSMENT_STATUSES),
                "reviewed_label_fields": list(_empty_labels_payload()),
                "reviewer_instruction": (
                    "Independently assess the supplied facts against the cited official sources. "
                    "Treat the facts as asserted scenario inputs under the supplied fact_evidence_boundary, not as "
                    "authenticated documents or authority findings. "
                    "Do not ask for or infer the benchmark's expected labels or rationale. "
                    "Use ASSESSED with your complete independent reviewed_labels when you can reach a professional "
                    "assessment; use DISPUTED when the supplied benchmark framing itself is professionally disputed; "
                    "use NEEDS_MORE_FACTS when the supplied facts are insufficient. AIOS derives CONFIRMED versus "
                    "CORRECTED only after your blind return is received."
                ),
            }
        )

    return {
        "contract_version": HANDOFF_CONTRACT_VERSION,
        "purpose": "Blind independent professional review handoff for the first real Austria benchmark tranche.",
        "reviewer_facing_packet": True,
        "supersedes_reviewer_handoff_contracts": list(SUPERSEDED_REVIEWER_HANDOFF_CONTRACTS),
        "legacy_packet_rejection": (
            "Reject any reviewer-facing packet that uses a superseded v1/v2 handoff contract or exposes "
            "source_labels, expected labels, source_rationale, or benchmark rationale before review."
        ),
        "blind_review": True,
        "expected_labels_excluded": True,
        "source_rationale_excluded": True,
        "source_benchmark_key": source_set.benchmark_key,
        "source_schema_version": source_set.schema_version,
        "canonical_review_schema_version": PROFESSIONAL_REVIEW_SCHEMA_VERSION,
        "blind_return_contract_version": BLIND_RETURN_CONTRACT_VERSION,
        "jurisdiction": source_set.jurisdiction,
        "evaluation_as_of": source_set.evaluation_as_of.isoformat(),
        "source_professional_review_status": source_set.professional_review_status,
        "claim_boundary": source_set.claim_boundary,
        "official_sources": raw.get("sources", []),
        "eligibility_label_values": [value.value for value in MobilityEligibilityLabel],
        "reviewed_label_contract": _reviewed_label_contract(),
        "reviewer_boundary": (
            "AIOS validates source fingerprints, review structure, derived decision semantics and supplied "
            "reviewer/credential references. It does not verify the real-world identity, independence, professional "
            "standing or credential validity of the reviewer; those must be established outside this compiler and "
            "referenced in the submitted record."
        ),
        "submission_requirements": [
            f"Use contract_version {BLIND_RETURN_CONTRACT_VERSION} for the reviewer return.",
            "Bind every review to the exact source_case_fingerprint in this packet.",
            "Supply timezone-aware created_at and reviewed_at timestamps.",
            "Supply durable professional_review_reference, reviewer_reference and reviewer_credential_reference values.",
            "Set independent_review=true only when independence has actually been established outside AIOS.",
            "Do not use test-only, placeholder or fabricated reviewer/credential references for acceptance evidence.",
            "Do not request or reveal source benchmark expected labels or source rationale before the reviewer returns.",
            "Reject obsolete or semantically superseded v1/v2 reviewer packets; only the current blind v3 handoff is reviewer-facing.",
            "Use --prepare-blind-return-template to generate the reviewer-facing fail-closed JSON return skeleton.",
            "Use --compile-blind-return to derive the canonical mobility-professional-review-v1 bundle after return.",
            "Run --validate-bundle on the derived canonical bundle before treating the tranche as structurally promotable.",
        ],
        "case_count": len(cases),
        "cases": cases,
    }


def build_return_template(source_path: Path, case_ids: tuple[str, ...]) -> dict[str, object]:
    """Legacy/internal canonical template retained for compatibility; not reviewer-facing."""
    source_set, requested = _requested_case_ids(source_path, case_ids)
    reviews = [
        {
            "review_id": None,
            "source_case_id": case_id,
            "source_case_fingerprint": source_set.fingerprint_for(case_id),
            "reviewed_at": None,
            "professional_review_reference": None,
            "reviewer_reference": None,
            "reviewer_credential_reference": None,
            "independent_review": None,
            "decision": None,
            "reviewed_labels": None,
            "notes": None,
        }
        for case_id in requested
    ]
    return {
        "schema_version": PROFESSIONAL_REVIEW_SCHEMA_VERSION,
        "review_batch_id": None,
        "source_benchmark_key": source_set.benchmark_key,
        "source_schema_version": source_set.schema_version,
        "created_at": None,
        "reviews": reviews,
    }


def build_blind_return_template(source_path: Path, case_ids: tuple[str, ...]) -> dict[str, object]:
    source_set, requested = _requested_case_ids(source_path, case_ids)
    return {
        "contract_version": BLIND_RETURN_CONTRACT_VERSION,
        "review_batch_id": None,
        "source_benchmark_key": source_set.benchmark_key,
        "source_schema_version": source_set.schema_version,
        "created_at": None,
        "reviews": [
            {
                "review_id": None,
                "source_case_id": case_id,
                "source_case_fingerprint": source_set.fingerprint_for(case_id),
                "reviewed_at": None,
                "professional_review_reference": None,
                "reviewer_reference": None,
                "reviewer_credential_reference": None,
                "independent_review": None,
                "assessment_status": None,
                "reviewed_labels": _empty_labels_payload(),
                "notes": None,
            }
            for case_id in requested
        ],
    }


def compile_blind_review_return(source_path: Path, blind_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    source_set = load_official_source_gold_set(source_path)
    payload = json.loads(blind_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("blind review return root must be an object")
    if payload.get("contract_version") != BLIND_RETURN_CONTRACT_VERSION:
        raise ValueError(f"contract_version must be {BLIND_RETURN_CONTRACT_VERSION}")

    review_batch_id = _required_text(payload.get("review_batch_id"), field_name="review_batch_id")
    source_benchmark_key = _required_text(
        payload.get("source_benchmark_key"), field_name="source_benchmark_key"
    )
    source_schema_version = _required_text(
        payload.get("source_schema_version"), field_name="source_schema_version"
    )
    if source_benchmark_key != source_set.benchmark_key:
        raise ValueError("blind return source_benchmark_key does not match source set")
    if source_schema_version != source_set.schema_version:
        raise ValueError("blind return source_schema_version does not match source set")

    created_at = datetime.fromisoformat(_required_text(payload.get("created_at"), field_name="created_at"))
    reviews_value = payload.get("reviews")
    if not isinstance(reviews_value, list):
        raise ValueError("reviews must be a list")

    reviews: list[MobilityProfessionalReview] = []
    derived_decisions: list[dict[str, str]] = []
    for index, raw_review in enumerate(reviews_value):
        if not isinstance(raw_review, dict):
            raise ValueError(f"reviews[{index}] must be an object")
        source_case_id = _required_text(
            raw_review.get("source_case_id"), field_name=f"reviews[{index}].source_case_id"
        )
        try:
            source_case = source_set.case_by_id(source_case_id)
        except KeyError as exc:
            raise ValueError(f"blind return references unknown source case {source_case_id}") from exc
        fingerprint = _required_text(
            raw_review.get("source_case_fingerprint"),
            field_name=f"reviews[{index}].source_case_fingerprint",
        )
        if fingerprint != source_set.fingerprint_for(source_case_id):
            raise ValueError(f"blind return source fingerprint is stale for case {source_case_id}")

        independent_review = raw_review.get("independent_review")
        if not isinstance(independent_review, bool):
            raise ValueError(f"reviews[{index}].independent_review must be boolean")

        assessment_status = _required_text(
            raw_review.get("assessment_status"), field_name=f"reviews[{index}].assessment_status"
        ).upper()
        if assessment_status not in BLIND_ASSESSMENT_STATUSES:
            raise ValueError(
                f"reviews[{index}].assessment_status must be one of {', '.join(BLIND_ASSESSMENT_STATUSES)}"
            )

        reviewed_labels: MobilityReviewedLabels | None
        if assessment_status == "ASSESSED":
            reviewed_labels = _blind_reviewed_labels(
                raw_review.get("reviewed_labels"), field_name=f"reviews[{index}].reviewed_labels"
            )
            source_labels = MobilityReviewedLabels.from_gold_case(source_case)
            decision = (
                ProfessionalReviewDecision.CONFIRMED
                if reviewed_labels == source_labels
                else ProfessionalReviewDecision.CORRECTED
            )
        else:
            if raw_review.get("reviewed_labels") not in (None, _empty_labels_payload()):
                raise ValueError(
                    f"reviews[{index}].reviewed_labels must be null/empty for {assessment_status}"
                )
            reviewed_labels = None
            decision = ProfessionalReviewDecision(assessment_status)

        review = MobilityProfessionalReview(
            review_id=_required_text(raw_review.get("review_id"), field_name=f"reviews[{index}].review_id"),
            source_case_id=source_case_id,
            source_case_fingerprint=fingerprint,
            reviewed_at=datetime.fromisoformat(
                _required_text(raw_review.get("reviewed_at"), field_name=f"reviews[{index}].reviewed_at")
            ),
            professional_review_reference=_required_text(
                raw_review.get("professional_review_reference"),
                field_name=f"reviews[{index}].professional_review_reference",
            ),
            reviewer_reference=_required_text(
                raw_review.get("reviewer_reference"), field_name=f"reviews[{index}].reviewer_reference"
            ),
            reviewer_credential_reference=_required_text(
                raw_review.get("reviewer_credential_reference"),
                field_name=f"reviews[{index}].reviewer_credential_reference",
            ),
            independent_review=independent_review,
            decision=decision,
            reviewed_labels=reviewed_labels,
            notes=_optional_text(raw_review.get("notes"), field_name=f"reviews[{index}].notes"),
        )
        reviews.append(review)
        derived_decisions.append(
            {
                "source_case_id": source_case_id,
                "assessment_status": assessment_status,
                "derived_decision": decision.value,
            }
        )

    bundle = MobilityProfessionalReviewBundle(
        schema_version=PROFESSIONAL_REVIEW_SCHEMA_VERSION,
        review_batch_id=review_batch_id,
        source_benchmark_key=source_benchmark_key,
        source_schema_version=source_schema_version,
        created_at=created_at,
        reviews=tuple(reviews),
    )
    compiled = compile_professional_reviews(source_set, bundle)

    canonical = {
        "schema_version": bundle.schema_version,
        "review_batch_id": bundle.review_batch_id,
        "source_benchmark_key": bundle.source_benchmark_key,
        "source_schema_version": bundle.source_schema_version,
        "created_at": bundle.created_at.isoformat(),
        "reviews": [
            {
                "review_id": review.review_id,
                "source_case_id": review.source_case_id,
                "source_case_fingerprint": review.source_case_fingerprint,
                "reviewed_at": review.reviewed_at.isoformat(),
                "professional_review_reference": review.professional_review_reference,
                "reviewer_reference": review.reviewer_reference,
                "reviewer_credential_reference": review.reviewer_credential_reference,
                "independent_review": review.independent_review,
                "decision": review.decision.value,
                "reviewed_labels": (
                    None if review.reviewed_labels is None else _labels_payload(review.reviewed_labels)
                ),
                "notes": review.notes,
            }
            for review in bundle.reviews
        ],
    }
    report = {
        "contract_version": HANDOFF_CONTRACT_VERSION,
        "mode": "compile-blind-return",
        "blind_return_contract_version": BLIND_RETURN_CONTRACT_VERSION,
        "source_benchmark_key": source_set.benchmark_key,
        "review_batch_id": bundle.review_batch_id,
        "review_count": compiled.review_count,
        "confirmed_count": compiled.confirmed_count,
        "corrected_count": compiled.corrected_count,
        "disputed_count": compiled.disputed_count,
        "needs_more_facts_count": compiled.needs_more_facts_count,
        "professionally_reviewed_case_count": compiled.professionally_reviewed_case_count,
        "derived_decisions": derived_decisions,
        "expected_labels_revealed_to_reviewer": False,
        "source_rationale_revealed_to_reviewer": False,
        "acceptance_boundary": (
            "AIOS derived CONFIRMED/CORRECTED only after the blind reviewer assessment. "
            "Structural compilation does not prove real-world identity, independence or credential validity."
        ),
    }
    return canonical, report


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
            "Prepare a blind immutable-fingerprint Austria professional-review handoff packet, prepare reviewer/internal "
            "return templates, compile a blind reviewer return into the canonical review bundle, or validate a completed "
            "canonical independent review bundle. This tool never fabricates professional review and never verifies "
            "real-world credentials."
        )
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare-packet", action="store_true")
    modes.add_argument("--prepare-return-template", action="store_true")
    modes.add_argument("--prepare-blind-return-template", action="store_true")
    modes.add_argument("--compile-blind-return", type=Path)
    modes.add_argument("--validate-bundle", type=Path)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _emit_prepared(payload: dict[str, object], *, output: Path | None, contract_version: str) -> None:
    rendered = _json(payload) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(
        _json(
            {
                "contract_version": contract_version,
                "status": "prepared",
                "output": str(output),
                "case_count": len(payload.get("reviews", payload.get("cases", []))),
            }
        )
    )


def main() -> int:
    args = _parse_args()
    try:
        if args.prepare_packet:
            payload = build_review_packet(args.source_path, tuple(args.case_id))
            _emit_prepared(payload, output=args.output, contract_version=HANDOFF_CONTRACT_VERSION)
            return 0

        if args.prepare_return_template:
            payload = build_return_template(args.source_path, tuple(args.case_id))
            _emit_prepared(payload, output=args.output, contract_version=RETURN_TEMPLATE_CONTRACT_VERSION)
            return 0

        if args.prepare_blind_return_template:
            payload = build_blind_return_template(args.source_path, tuple(args.case_id))
            _emit_prepared(
                payload,
                output=args.output,
                contract_version=BLIND_RETURN_TEMPLATE_CONTRACT_VERSION,
            )
            return 0

        if args.case_id:
            raise ValueError(
                "--case-id is only valid with --prepare-packet, --prepare-return-template or "
                "--prepare-blind-return-template"
            )

        if args.compile_blind_return:
            canonical, report = compile_blind_review_return(args.source_path, args.compile_blind_return)
            if args.output is None:
                print(_json(canonical))
                print(_json(report), file=sys.stderr)
            else:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(_json(canonical) + "\n", encoding="utf-8")
                print(_json({**report, "status": "compiled", "output": str(args.output)}))
            return 0

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
