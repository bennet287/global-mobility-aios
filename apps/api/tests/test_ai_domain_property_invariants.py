from __future__ import annotations

import copy

import pytest
from hypothesis import given, settings, strategies as st

from scripts.evaluate_austria_ai_domain_review import (
    ALLOWED_CLASSIFICATIONS,
    REVIEW_SCOPE_PATHWAY_KEY,
    _corroboration_summary,
    _validate_provider_payload,
)

CASE_IDS = ["case-a", "case-b"]
VALID_SOURCE_REFS = {"source-a", "source-b"}
EXPECTED_CLASSIFICATIONS = ("INELIGIBLE", "REVIEW_REQUIRED")
PROPERTY_SETTINGS = settings(max_examples=75, deadline=None)


def _valid_payload() -> dict[str, object]:
    return {
        "reviews": [
            {
                "case_id": "case-a",
                "classification": "INELIGIBLE",
                "pathway_key": REVIEW_SCOPE_PATHWAY_KEY,
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
                "pathway_key": REVIEW_SCOPE_PATHWAY_KEY,
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
    identity_match: bool = True,
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


@PROPERTY_SETTINGS
@given(
    st.one_of(
        st.none(),
        st.just(True),
        st.integers(),
        st.text(),
        st.lists(st.integers(), max_size=3),
        st.dictionaries(st.text(max_size=8), st.integers(), max_size=2),
    ).filter(lambda value: value is not False)
)
def test_generated_authority_values_never_escalate(value: object) -> None:
    payload = _valid_payload()
    payload["reviews"][0]["final_authority_decision"] = value  # type: ignore[index]

    with pytest.raises(ValueError, match="final_authority_decision=false"):
        _validate_provider_payload(
            payload,
            case_ids=CASE_IDS,
            valid_source_refs=VALID_SOURCE_REFS,
        )


@PROPERTY_SETTINGS
@given(
    st.text(min_size=1, max_size=80).filter(
        lambda value: value.strip()
        and value.strip() != REVIEW_SCOPE_PATHWAY_KEY
    )
)
def test_generated_route_substitutions_fail_closed(pathway_key: str) -> None:
    payload = _valid_payload()
    payload["reviews"][0]["pathway_key"] = pathway_key  # type: ignore[index]

    with pytest.raises(ValueError, match="declared review scope"):
        _validate_provider_payload(
            payload,
            case_ids=CASE_IDS,
            valid_source_refs=VALID_SOURCE_REFS,
        )


@PROPERTY_SETTINGS
@given(
    st.text(min_size=1, max_size=80).filter(
        lambda value: value.strip() and value.strip() not in VALID_SOURCE_REFS
    )
)
def test_generated_unknown_source_refs_fail_closed(source_ref: str) -> None:
    payload = _valid_payload()
    payload["reviews"][0]["source_refs"] = [source_ref]  # type: ignore[index]

    with pytest.raises(ValueError, match="unknown source"):
        _validate_provider_payload(
            payload,
            case_ids=CASE_IDS,
            valid_source_refs=VALID_SOURCE_REFS,
        )


@PROPERTY_SETTINGS
@given(
    st.text(min_size=1, max_size=80).filter(
        lambda value: value.strip() and value.strip() not in CASE_IDS
    )
)
def test_generated_case_substitution_cannot_escape_benchmark_case_set(
    case_id: str,
) -> None:
    payload = _valid_payload()
    payload["reviews"][0]["case_id"] = case_id  # type: ignore[index]

    with pytest.raises(ValueError, match="case set does not match"):
        _validate_provider_payload(
            payload,
            case_ids=CASE_IDS,
            valid_source_refs=VALID_SOURCE_REFS,
        )


@PROPERTY_SETTINGS
@given(st.permutations([0, 1]))
def test_valid_review_order_is_canonicalized(permutation: list[int]) -> None:
    payload = _valid_payload()
    original = list(payload["reviews"])  # type: ignore[arg-type]
    payload["reviews"] = [copy.deepcopy(original[index]) for index in permutation]

    normalized = _validate_provider_payload(
        payload,
        case_ids=CASE_IDS,
        valid_source_refs=VALID_SOURCE_REFS,
    )

    assert [item["case_id"] for item in normalized] == CASE_IDS
    assert all(item["final_authority_decision"] is False for item in normalized)
    assert all(item["classification"] in ALLOWED_CLASSIFICATIONS for item in normalized)


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=8))
def test_any_number_of_same_provider_runs_cannot_fake_independent_corroboration(
    run_count: int,
) -> None:
    runs = [_provider_run("gemini") for _ in range(run_count)]

    summary = _corroboration_summary(runs, case_ids=CASE_IDS)

    assert summary["qualifying_providers"] == ["gemini"]
    assert summary["multi_model_corroboration_candidate"] is False
    assert summary["professional_review_status_effect"] == "NONE"


@PROPERTY_SETTINGS
@given(
    identity_match=st.booleans(),
    structural_valid=st.booleans(),
    source_match=st.booleans(),
)
def test_second_provider_must_satisfy_every_qualification_gate(
    identity_match: bool,
    structural_valid: bool,
    source_match: bool,
) -> None:
    runs = [
        _provider_run("gemini"),
        _provider_run(
            "deepseek",
            identity_match=identity_match,
            structural_valid=structural_valid,
            source_match=source_match,
        ),
    ]

    summary = _corroboration_summary(runs, case_ids=CASE_IDS)
    expected = identity_match and structural_valid and source_match

    assert summary["multi_model_corroboration_candidate"] is expected
    assert summary["professional_review_status_effect"] == "NONE"


@PROPERTY_SETTINGS
@given(
    st.sampled_from(
        [
            ("ELIGIBLE", "REVIEW_REQUIRED"),
            ("INELIGIBLE", "ELIGIBLE"),
            ("REVIEW_REQUIRED", "REVIEW_REQUIRED"),
            ("INSUFFICIENT_INFORMATION", "REVIEW_REQUIRED"),
        ]
    )
)
def test_cross_provider_classification_disagreement_cannot_corroborate(
    classifications: tuple[str, str],
) -> None:
    runs = [
        _provider_run("gemini"),
        _provider_run("deepseek", classifications),
    ]

    summary = _corroboration_summary(runs, case_ids=CASE_IDS)

    assert summary["multi_model_corroboration_candidate"] is False
    assert summary["professional_review_status_effect"] == "NONE"
