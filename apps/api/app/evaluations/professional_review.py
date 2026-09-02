from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Mapping

from .mobility_outcomes import (
    MobilityCaseProvenance,
    MobilityEligibilityLabel,
    MobilityGoldCase,
)


PROFESSIONAL_REVIEW_SCHEMA_VERSION = "mobility-professional-review-v1"


class ProfessionalReviewDecision(StrEnum):
    CONFIRMED = "CONFIRMED"
    CORRECTED = "CORRECTED"
    DISPUTED = "DISPUTED"
    NEEDS_MORE_FACTS = "NEEDS_MORE_FACTS"


@dataclass(frozen=True)
class MobilityReviewedLabels:
    pathway_keys: frozenset[str] | None = None
    eligibility: MobilityEligibilityLabel | None = None
    required_evidence: frozenset[str] | None = None
    missing_evidence: frozenset[str] | None = None
    contradictions: frozenset[str] | None = None
    rule_or_source_refs: frozenset[str] | None = None
    escalation_required: bool | None = None

    @classmethod
    def from_gold_case(cls, case: MobilityGoldCase) -> "MobilityReviewedLabels":
        return cls(
            pathway_keys=case.expected_pathway_keys,
            eligibility=case.expected_eligibility,
            required_evidence=case.expected_required_evidence,
            missing_evidence=case.expected_missing_evidence,
            contradictions=case.expected_contradictions,
            rule_or_source_refs=case.expected_rule_or_source_refs,
            escalation_required=case.expected_escalation_required,
        )


@dataclass(frozen=True)
class OfficialSourceGoldSet:
    schema_version: str
    benchmark_key: str
    jurisdiction: str
    evaluation_as_of: datetime
    professional_review_status: str
    claim_boundary: str
    source_references: tuple[str, ...]
    cases: tuple[MobilityGoldCase, ...]
    case_fingerprints: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not self.schema_version.strip():
            raise ValueError("schema_version is required")
        if not self.benchmark_key.strip():
            raise ValueError("benchmark_key is required")
        if self.evaluation_as_of.tzinfo is None:
            raise ValueError("evaluation_as_of must be timezone-aware")
        if self.professional_review_status != "NOT_REVIEWED":
            raise ValueError("official source review input must remain NOT_REVIEWED")
        if not self.claim_boundary.strip():
            raise ValueError("claim_boundary is required")
        if not self.source_references:
            raise ValueError("official source review input requires source references")
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("official source review input contains duplicate case_id values")
        fingerprint_ids = [case_id for case_id, _ in self.case_fingerprints]
        if fingerprint_ids != case_ids:
            raise ValueError("case fingerprints must align with source case order")

    def case_by_id(self, case_id: str) -> MobilityGoldCase:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise KeyError(case_id)

    def fingerprint_for(self, case_id: str) -> str:
        for candidate_id, fingerprint in self.case_fingerprints:
            if candidate_id == case_id:
                return fingerprint
        raise KeyError(case_id)


@dataclass(frozen=True)
class MobilityProfessionalReview:
    review_id: str
    source_case_id: str
    source_case_fingerprint: str
    reviewed_at: datetime
    professional_review_reference: str
    reviewer_reference: str
    reviewer_credential_reference: str
    independent_review: bool
    decision: ProfessionalReviewDecision
    reviewed_labels: MobilityReviewedLabels | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("review_id", self.review_id),
            ("source_case_id", self.source_case_id),
            ("source_case_fingerprint", self.source_case_fingerprint),
            ("professional_review_reference", self.professional_review_reference),
            ("reviewer_reference", self.reviewer_reference),
            ("reviewer_credential_reference", self.reviewer_credential_reference),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.source_case_fingerprint.startswith("sha256:"):
            raise ValueError("source_case_fingerprint must use sha256:<hex>")
        if self.reviewed_at.tzinfo is None:
            raise ValueError("reviewed_at must be timezone-aware")
        if self.decision in {
            ProfessionalReviewDecision.CONFIRMED,
            ProfessionalReviewDecision.CORRECTED,
        } and self.reviewed_labels is None:
            raise ValueError("confirmed/corrected professional reviews require reviewed_labels")


@dataclass(frozen=True)
class MobilityProfessionalReviewBundle:
    schema_version: str
    review_batch_id: str
    source_benchmark_key: str
    source_schema_version: str
    created_at: datetime
    reviews: tuple[MobilityProfessionalReview, ...]

    def __post_init__(self) -> None:
        if self.schema_version != PROFESSIONAL_REVIEW_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {PROFESSIONAL_REVIEW_SCHEMA_VERSION}"
            )
        for name, value in (
            ("review_batch_id", self.review_batch_id),
            ("source_benchmark_key", self.source_benchmark_key),
            ("source_schema_version", self.source_schema_version),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        review_ids = [review.review_id for review in self.reviews]
        if len(review_ids) != len(set(review_ids)):
            raise ValueError("review bundle contains duplicate review_id values")
        source_case_ids = [review.source_case_id for review in self.reviews]
        if len(source_case_ids) != len(set(source_case_ids)):
            raise ValueError("review bundle may contain only one active review per source case")


@dataclass(frozen=True)
class ProfessionalReviewCompilation:
    source_case_count: int
    review_count: int
    confirmed_count: int
    corrected_count: int
    disputed_count: int
    needs_more_facts_count: int
    promoted_cases: tuple[MobilityGoldCase, ...]
    held_case_ids: tuple[str, ...]
    unreviewed_case_ids: tuple[str, ...]

    @property
    def professionally_reviewed_case_count(self) -> int:
        return len(self.promoted_cases)


def _require_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _require_list(value: object, *, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_text(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null")
    return value


def _string_set(value: object, *, field_name: str) -> frozenset[str] | None:
    if value is None:
        return None
    items = _require_list(value, field_name=field_name)
    result: set[str] = set()
    for item in items:
        result.add(_require_text(item, field_name=field_name))
    return frozenset(result)


def _reviewed_labels_from_mapping(value: object) -> MobilityReviewedLabels | None:
    if value is None:
        return None
    payload = _require_mapping(value, field_name="reviewed_labels")
    eligibility_value = payload.get("eligibility")
    eligibility = (
        None
        if eligibility_value is None
        else MobilityEligibilityLabel(_require_text(eligibility_value, field_name="eligibility"))
    )
    escalation_value = payload.get("escalation_required")
    if escalation_value is not None and not isinstance(escalation_value, bool):
        raise ValueError("escalation_required must be boolean or null")
    return MobilityReviewedLabels(
        pathway_keys=_string_set(payload.get("pathway_keys"), field_name="pathway_keys"),
        eligibility=eligibility,
        required_evidence=_string_set(payload.get("required_evidence"), field_name="required_evidence"),
        missing_evidence=_string_set(payload.get("missing_evidence"), field_name="missing_evidence"),
        contradictions=_string_set(payload.get("contradictions"), field_name="contradictions"),
        rule_or_source_refs=_string_set(payload.get("rule_or_source_refs"), field_name="rule_or_source_refs"),
        escalation_required=escalation_value,
    )


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def load_official_source_gold_set(path: Path) -> OfficialSourceGoldSet:
    """Load the immutable source-curated benchmark used as professional-review input."""

    payload = _require_mapping(json.loads(path.read_text(encoding="utf-8")), field_name="root")
    schema_version = _require_text(payload.get("schema_version"), field_name="schema_version")
    benchmark_key = _require_text(payload.get("benchmark_key"), field_name="benchmark_key")
    jurisdiction = _require_text(payload.get("jurisdiction"), field_name="jurisdiction")
    evaluation_as_of = datetime.fromisoformat(
        _require_text(payload.get("evaluation_as_of"), field_name="evaluation_as_of")
    )
    provenance = MobilityCaseProvenance(
        _require_text(payload.get("provenance"), field_name="provenance")
    )
    if provenance is not MobilityCaseProvenance.OFFICIAL_SOURCE_CURATED:
        raise ValueError("professional review input must be OFFICIAL_SOURCE_CURATED")
    review_status = _require_text(
        payload.get("professional_review_status"), field_name="professional_review_status"
    )
    claim_boundary = _require_text(payload.get("claim_boundary"), field_name="claim_boundary")

    sources = _require_list(payload.get("sources"), field_name="sources")
    source_references: list[str] = []
    for index, source_value in enumerate(sources):
        source = _require_mapping(source_value, field_name=f"sources[{index}]")
        source_references.append(
            _require_text(source.get("url"), field_name=f"sources[{index}].url")
        )

    cases: list[MobilityGoldCase] = []
    fingerprints: list[tuple[str, str]] = []
    case_values = _require_list(payload.get("cases"), field_name="cases")
    fingerprint_context = {
        "schema_version": schema_version,
        "benchmark_key": benchmark_key,
        "jurisdiction": jurisdiction,
        "evaluation_as_of": payload.get("evaluation_as_of"),
        "provenance": provenance.value,
        "professional_review_status": review_status,
        "claim_boundary": claim_boundary,
        "sources": sources,
    }

    for index, case_value in enumerate(case_values):
        case_payload = _require_mapping(case_value, field_name=f"cases[{index}]")
        case_id = _require_text(case_payload.get("case_id"), field_name=f"cases[{index}].case_id")
        expected = _require_mapping(
            case_payload.get("expected"), field_name=f"cases[{index}].expected"
        )
        eligibility_value = expected.get("eligibility")
        eligibility = (
            None
            if eligibility_value is None
            else MobilityEligibilityLabel(
                _require_text(eligibility_value, field_name=f"cases[{index}].expected.eligibility")
            )
        )
        escalation_value = expected.get("escalation_required")
        if escalation_value is not None and not isinstance(escalation_value, bool):
            raise ValueError(f"cases[{index}].expected.escalation_required must be boolean or null")

        cases.append(
            MobilityGoldCase(
                case_id=case_id,
                jurisdiction=jurisdiction,
                evaluation_as_of=evaluation_as_of,
                provenance=provenance,
                expected_pathway_keys=_string_set(
                    expected.get("pathway_keys"), field_name=f"cases[{index}].expected.pathway_keys"
                ),
                expected_eligibility=eligibility,
                expected_required_evidence=_string_set(
                    expected.get("required_evidence"),
                    field_name=f"cases[{index}].expected.required_evidence",
                ),
                expected_missing_evidence=_string_set(
                    expected.get("missing_evidence"),
                    field_name=f"cases[{index}].expected.missing_evidence",
                ),
                expected_contradictions=_string_set(
                    expected.get("contradictions"),
                    field_name=f"cases[{index}].expected.contradictions",
                ),
                expected_rule_or_source_refs=_string_set(
                    expected.get("rule_or_source_refs"),
                    field_name=f"cases[{index}].expected.rule_or_source_refs",
                ),
                expected_escalation_required=escalation_value,
                provenance_references=tuple(source_references),
                notes=_optional_text(case_payload.get("rationale"), field_name=f"cases[{index}].rationale"),
            )
        )
        fingerprints.append(
            (
                case_id,
                _canonical_sha256({**fingerprint_context, "case": case_payload}),
            )
        )

    return OfficialSourceGoldSet(
        schema_version=schema_version,
        benchmark_key=benchmark_key,
        jurisdiction=jurisdiction,
        evaluation_as_of=evaluation_as_of,
        professional_review_status=review_status,
        claim_boundary=claim_boundary,
        source_references=tuple(source_references),
        cases=tuple(cases),
        case_fingerprints=tuple(fingerprints),
    )


def load_professional_review_bundle(path: Path) -> MobilityProfessionalReviewBundle:
    """Load independent-review metadata without claiming external credential verification."""

    payload = _require_mapping(json.loads(path.read_text(encoding="utf-8")), field_name="root")
    reviews: list[MobilityProfessionalReview] = []
    for index, review_value in enumerate(_require_list(payload.get("reviews"), field_name="reviews")):
        review = _require_mapping(review_value, field_name=f"reviews[{index}]")
        independent_review = review.get("independent_review")
        if not isinstance(independent_review, bool):
            raise ValueError(f"reviews[{index}].independent_review must be boolean")
        reviews.append(
            MobilityProfessionalReview(
                review_id=_require_text(review.get("review_id"), field_name=f"reviews[{index}].review_id"),
                source_case_id=_require_text(
                    review.get("source_case_id"), field_name=f"reviews[{index}].source_case_id"
                ),
                source_case_fingerprint=_require_text(
                    review.get("source_case_fingerprint"),
                    field_name=f"reviews[{index}].source_case_fingerprint",
                ),
                reviewed_at=datetime.fromisoformat(
                    _require_text(review.get("reviewed_at"), field_name=f"reviews[{index}].reviewed_at")
                ),
                professional_review_reference=_require_text(
                    review.get("professional_review_reference"),
                    field_name=f"reviews[{index}].professional_review_reference",
                ),
                reviewer_reference=_require_text(
                    review.get("reviewer_reference"), field_name=f"reviews[{index}].reviewer_reference"
                ),
                reviewer_credential_reference=_require_text(
                    review.get("reviewer_credential_reference"),
                    field_name=f"reviews[{index}].reviewer_credential_reference",
                ),
                independent_review=independent_review,
                decision=ProfessionalReviewDecision(
                    _require_text(review.get("decision"), field_name=f"reviews[{index}].decision")
                ),
                reviewed_labels=_reviewed_labels_from_mapping(review.get("reviewed_labels")),
                notes=_optional_text(review.get("notes"), field_name=f"reviews[{index}].notes"),
            )
        )

    return MobilityProfessionalReviewBundle(
        schema_version=_require_text(payload.get("schema_version"), field_name="schema_version"),
        review_batch_id=_require_text(payload.get("review_batch_id"), field_name="review_batch_id"),
        source_benchmark_key=_require_text(
            payload.get("source_benchmark_key"), field_name="source_benchmark_key"
        ),
        source_schema_version=_require_text(
            payload.get("source_schema_version"), field_name="source_schema_version"
        ),
        created_at=datetime.fromisoformat(
            _require_text(payload.get("created_at"), field_name="created_at")
        ),
        reviews=tuple(reviews),
    )


def _promoted_case(
    source: MobilityGoldCase,
    review: MobilityProfessionalReview,
) -> MobilityGoldCase:
    labels = review.reviewed_labels
    if labels is None:
        raise ValueError("promoted professional review requires reviewed_labels")
    return MobilityGoldCase(
        case_id=source.case_id,
        jurisdiction=source.jurisdiction,
        evaluation_as_of=source.evaluation_as_of,
        provenance=MobilityCaseProvenance.PROFESSIONALLY_REVIEWED,
        expected_pathway_keys=labels.pathway_keys,
        expected_eligibility=labels.eligibility,
        expected_required_evidence=labels.required_evidence,
        expected_missing_evidence=labels.missing_evidence,
        expected_contradictions=labels.contradictions,
        expected_rule_or_source_refs=labels.rule_or_source_refs,
        expected_escalation_required=labels.escalation_required,
        provenance_references=source.provenance_references,
        review_reference=review.professional_review_reference,
        notes=source.notes,
    )


def compile_professional_reviews(
    source_set: OfficialSourceGoldSet,
    review_bundle: MobilityProfessionalReviewBundle,
) -> ProfessionalReviewCompilation:
    """Derive professionally reviewed labels while leaving the source set immutable."""

    if review_bundle.source_benchmark_key != source_set.benchmark_key:
        raise ValueError("review bundle source_benchmark_key does not match source set")
    if review_bundle.source_schema_version != source_set.schema_version:
        raise ValueError("review bundle source_schema_version does not match source set")

    promoted: list[MobilityGoldCase] = []
    held: list[str] = []
    reviewed_case_ids: set[str] = set()
    counts = {decision: 0 for decision in ProfessionalReviewDecision}

    for review in review_bundle.reviews:
        try:
            source_case = source_set.case_by_id(review.source_case_id)
        except KeyError as exc:
            raise ValueError(f"review references unknown source case {review.source_case_id}") from exc
        reviewed_case_ids.add(review.source_case_id)
        expected_fingerprint = source_set.fingerprint_for(review.source_case_id)
        if review.source_case_fingerprint != expected_fingerprint:
            raise ValueError(
                f"review source fingerprint is stale for case {review.source_case_id}"
            )

        counts[review.decision] += 1
        source_labels = MobilityReviewedLabels.from_gold_case(source_case)
        if review.decision is ProfessionalReviewDecision.CONFIRMED:
            if not review.independent_review:
                raise ValueError("confirmed professional review must be independently reviewed")
            if review.reviewed_labels != source_labels:
                raise ValueError("CONFIRMED review labels must match source labels; use CORRECTED")
            promoted.append(_promoted_case(source_case, review))
        elif review.decision is ProfessionalReviewDecision.CORRECTED:
            if not review.independent_review:
                raise ValueError("corrected professional review must be independently reviewed")
            if review.reviewed_labels == source_labels:
                raise ValueError("CORRECTED review must change at least one labeled dimension")
            promoted.append(_promoted_case(source_case, review))
        else:
            held.append(review.source_case_id)

    unreviewed = tuple(
        case.case_id for case in source_set.cases if case.case_id not in reviewed_case_ids
    )
    return ProfessionalReviewCompilation(
        source_case_count=len(source_set.cases),
        review_count=len(review_bundle.reviews),
        confirmed_count=counts[ProfessionalReviewDecision.CONFIRMED],
        corrected_count=counts[ProfessionalReviewDecision.CORRECTED],
        disputed_count=counts[ProfessionalReviewDecision.DISPUTED],
        needs_more_facts_count=counts[ProfessionalReviewDecision.NEEDS_MORE_FACTS],
        promoted_cases=tuple(promoted),
        held_case_ids=tuple(held),
        unreviewed_case_ids=unreviewed,
    )
