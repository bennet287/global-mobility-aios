from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.evaluations.mobility_outcomes import (
    MobilityCaseProvenance,
    MobilityEligibilityLabel,
    MobilityOutcomePrediction,
    evaluate_mobility_case,
    summarize_mobility_evaluations,
)
from app.evaluations.professional_review import (
    PROFESSIONAL_REVIEW_SCHEMA_VERSION,
    MobilityProfessionalReview,
    MobilityProfessionalReviewBundle,
    MobilityReviewedLabels,
    ProfessionalReviewDecision,
    compile_professional_reviews,
    load_official_source_gold_set,
    load_professional_review_bundle,
)


SOURCE_PATH = Path("apps/api/evaluations/mobility_cases/austria_rwr_shortage_2026_v1.json")
REVIEWED_AT = datetime(2026, 8, 23, 8, 0, tzinfo=timezone.utc)


def _source_set():
    return load_official_source_gold_set(SOURCE_PATH)


def _review(
    source_set,
    case_id: str,
    *,
    decision: ProfessionalReviewDecision = ProfessionalReviewDecision.CONFIRMED,
    reviewed_labels: MobilityReviewedLabels | None = None,
    fingerprint: str | None = None,
    independent_review: bool = True,
) -> MobilityProfessionalReview:
    source = source_set.case_by_id(case_id)
    if reviewed_labels is None and decision in {
        ProfessionalReviewDecision.CONFIRMED,
        ProfessionalReviewDecision.CORRECTED,
    }:
        reviewed_labels = MobilityReviewedLabels.from_gold_case(source)
    return MobilityProfessionalReview(
        review_id=f"test-review:{case_id}:v1",
        source_case_id=case_id,
        source_case_fingerprint=fingerprint or source_set.fingerprint_for(case_id),
        reviewed_at=REVIEWED_AT,
        professional_review_reference=f"test-only:professional-review:{case_id}:v1",
        reviewer_reference="test-only:reviewer:independent-austria-professional",
        reviewer_credential_reference="test-only:credential-reference:not-a-real-credential",
        independent_review=independent_review,
        decision=decision,
        reviewed_labels=reviewed_labels,
        notes="Test fixture only; this is not evidence of a real professional review.",
    )


def _bundle(source_set, *reviews: MobilityProfessionalReview) -> MobilityProfessionalReviewBundle:
    return MobilityProfessionalReviewBundle(
        schema_version=PROFESSIONAL_REVIEW_SCHEMA_VERSION,
        review_batch_id="test-only:austria-review-batch:v1",
        source_benchmark_key=source_set.benchmark_key,
        source_schema_version=source_set.schema_version,
        created_at=REVIEWED_AT,
        reviews=tuple(reviews),
    )


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


def test_austria_source_seed_loads_as_immutable_not_reviewed_input() -> None:
    source_set = _source_set()

    assert source_set.schema_version == "mobility-gold-v1"
    assert source_set.benchmark_key == "austria-rwr-shortage-2026-v1"
    assert source_set.professional_review_status == "NOT_REVIEWED"
    assert len(source_set.cases) == 3
    assert len(source_set.case_fingerprints) == 3
    assert all(case.provenance is MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED for case in source_set.cases)
    assert all(source_set.fingerprint_for(case.case_id).startswith("sha256:") for case in source_set.cases)


def test_source_case_fingerprint_binds_review_to_facts_sources_and_labels(tmp_path: Path) -> None:
    original = _source_set()
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    payload["cases"][0]["facts"]["age_years"] = 30
    changed_path = tmp_path / "changed.json"
    changed_path.write_text(json.dumps(payload), encoding="utf-8")
    changed = load_official_source_gold_set(changed_path)

    case_id = original.cases[0].case_id
    assert original.fingerprint_for(case_id) != changed.fingerprint_for(case_id)


def test_confirmed_review_promotes_only_reviewed_case_and_preserves_source_truth() -> None:
    source_set = _source_set()
    source = source_set.cases[0]
    review = _review(source_set, source.case_id)

    compiled = compile_professional_reviews(source_set, _bundle(source_set, review))

    assert compiled.source_case_count == 3
    assert compiled.review_count == 1
    assert compiled.confirmed_count == 1
    assert compiled.corrected_count == 0
    assert compiled.professionally_reviewed_case_count == 1
    assert len(compiled.unreviewed_case_ids) == 2
    assert compiled.held_case_ids == ()

    promoted = compiled.promoted_cases[0]
    assert promoted.case_id == source.case_id
    assert promoted.provenance is MobilityCaseProvenance.PROFESSIONALLY_REVIEWED
    assert promoted.review_reference == review.professional_review_reference
    assert promoted.provenance_references == source.provenance_references
    assert MobilityReviewedLabels.from_gold_case(promoted) == MobilityReviewedLabels.from_gold_case(source)
    assert source.provenance is MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED
    assert source.review_reference is None


def test_corrected_review_must_change_labels_and_promotes_corrected_snapshot() -> None:
    source_set = _source_set()
    source = source_set.cases[1]
    source_labels = MobilityReviewedLabels.from_gold_case(source)

    with pytest.raises(ValueError, match="must change at least one"):
        compile_professional_reviews(
            source_set,
            _bundle(
                source_set,
                _review(
                    source_set,
                    source.case_id,
                    decision=ProfessionalReviewDecision.CORRECTED,
                    reviewed_labels=source_labels,
                ),
            ),
        )

    corrected_labels = replace(
        source_labels,
        eligibility=MobilityEligibilityLabel.INSUFFICIENT_INFORMATION,
        escalation_required=True,
    )
    compiled = compile_professional_reviews(
        source_set,
        _bundle(
            source_set,
            _review(
                source_set,
                source.case_id,
                decision=ProfessionalReviewDecision.CORRECTED,
                reviewed_labels=corrected_labels,
            ),
        ),
    )

    assert compiled.corrected_count == 1
    assert compiled.professionally_reviewed_case_count == 1
    promoted = compiled.promoted_cases[0]
    assert promoted.expected_eligibility is MobilityEligibilityLabel.INSUFFICIENT_INFORMATION
    assert promoted.expected_escalation_required is True


def test_confirmed_review_cannot_hide_a_label_change() -> None:
    source_set = _source_set()
    source = source_set.cases[0]
    changed = replace(
        MobilityReviewedLabels.from_gold_case(source),
        eligibility=MobilityEligibilityLabel.REVIEW_REQUIRED,
    )
    review = _review(source_set, source.case_id, reviewed_labels=changed)

    with pytest.raises(ValueError, match="use CORRECTED"):
        compile_professional_reviews(source_set, _bundle(source_set, review))


def test_disputed_and_needs_more_facts_reviews_are_held_out_of_professional_denominator() -> None:
    source_set = _source_set()
    disputed = _review(
        source_set,
        source_set.cases[0].case_id,
        decision=ProfessionalReviewDecision.DISPUTED,
        reviewed_labels=None,
    )
    needs_facts = _review(
        source_set,
        source_set.cases[1].case_id,
        decision=ProfessionalReviewDecision.NEEDS_MORE_FACTS,
        reviewed_labels=None,
    )

    compiled = compile_professional_reviews(source_set, _bundle(source_set, disputed, needs_facts))

    assert compiled.professionally_reviewed_case_count == 0
    assert compiled.disputed_count == 1
    assert compiled.needs_more_facts_count == 1
    assert compiled.held_case_ids == (source_set.cases[0].case_id, source_set.cases[1].case_id)
    assert compiled.unreviewed_case_ids == (source_set.cases[2].case_id,)


def test_review_fails_closed_on_stale_source_fingerprint_or_wrong_source_set() -> None:
    source_set = _source_set()
    case_id = source_set.cases[0].case_id
    stale = _review(source_set, case_id, fingerprint="sha256:" + "0" * 64)

    with pytest.raises(ValueError, match="fingerprint is stale"):
        compile_professional_reviews(source_set, _bundle(source_set, stale))

    wrong_bundle = replace(
        _bundle(source_set, _review(source_set, case_id)),
        source_benchmark_key="different-benchmark",
    )
    with pytest.raises(ValueError, match="source_benchmark_key"):
        compile_professional_reviews(source_set, wrong_bundle)


def test_promotable_review_requires_independent_review_and_structural_provenance() -> None:
    source_set = _source_set()
    case_id = source_set.cases[0].case_id

    with pytest.raises(ValueError, match="independently reviewed"):
        compile_professional_reviews(
            source_set,
            _bundle(source_set, _review(source_set, case_id, independent_review=False)),
        )

    with pytest.raises(ValueError, match="reviewer_credential_reference is required"):
        replace(_review(source_set, case_id), reviewer_credential_reference="")

    with pytest.raises(ValueError, match="timezone-aware"):
        replace(_review(source_set, case_id), reviewed_at=datetime(2026, 8, 23, 8, 0))


def test_review_bundle_rejects_duplicate_active_reviews_for_same_case() -> None:
    source_set = _source_set()
    case_id = source_set.cases[0].case_id
    first = _review(source_set, case_id)
    second = replace(first, review_id="test-review:second:v1")

    with pytest.raises(ValueError, match="one active review per source case"):
        _bundle(source_set, first, second)


def test_json_review_bundle_loader_compiles_partial_professional_tranche(tmp_path: Path) -> None:
    source_set = _source_set()
    source = source_set.cases[0]
    labels = MobilityReviewedLabels.from_gold_case(source)
    payload = {
        "schema_version": PROFESSIONAL_REVIEW_SCHEMA_VERSION,
        "review_batch_id": "test-only:austria-review-batch:json:v1",
        "source_benchmark_key": source_set.benchmark_key,
        "source_schema_version": source_set.schema_version,
        "created_at": REVIEWED_AT.isoformat(),
        "reviews": [
            {
                "review_id": "test-only:json-review:v1",
                "source_case_id": source.case_id,
                "source_case_fingerprint": source_set.fingerprint_for(source.case_id),
                "reviewed_at": REVIEWED_AT.isoformat(),
                "professional_review_reference": "test-only:review-record:json:v1",
                "reviewer_reference": "test-only:reviewer:json",
                "reviewer_credential_reference": "test-only:credential:not-real",
                "independent_review": True,
                "decision": "CONFIRMED",
                "reviewed_labels": _labels_payload(labels),
                "notes": "Test fixture only; no real professional review is claimed.",
            }
        ],
    }
    path = tmp_path / "professional-review.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    bundle = load_professional_review_bundle(path)
    compiled = compile_professional_reviews(source_set, bundle)

    assert compiled.professionally_reviewed_case_count == 1
    assert compiled.unreviewed_case_ids == tuple(case.case_id for case in source_set.cases[1:])


def test_professionally_reviewed_evaluation_is_counted_separately_from_source_curated_labels() -> None:
    source_set = _source_set()
    source = source_set.cases[0]
    compiled = compile_professional_reviews(
        source_set,
        _bundle(source_set, _review(source_set, source.case_id)),
    )
    reviewed = compiled.promoted_cases[0]
    prediction = MobilityOutcomePrediction(
        pathway_keys=reviewed.expected_pathway_keys or frozenset(),
        eligibility=reviewed.expected_eligibility,
        required_evidence=reviewed.expected_required_evidence or frozenset(),
        missing_evidence=reviewed.expected_missing_evidence or frozenset(),
        contradictions=reviewed.expected_contradictions or frozenset(),
        rule_or_source_refs=reviewed.expected_rule_or_source_refs or frozenset(),
        escalation_required=reviewed.expected_escalation_required,
    )

    summary = summarize_mobility_evaluations(
        [
            evaluate_mobility_case(source, prediction),
            evaluate_mobility_case(reviewed, prediction),
        ]
    )

    assert summary.case_count == 2
    assert summary.provenance_counts[MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED] == 1
    assert summary.provenance_counts[MobilityCaseProvenance.PROFESSIONALLY_REVIEWED] == 1
    assert summary.metrics["eligibility_accuracy"].denominator == 2
