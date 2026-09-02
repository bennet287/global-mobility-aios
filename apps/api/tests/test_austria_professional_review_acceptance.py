from __future__ import annotations

import json
from pathlib import Path
import re

from app.evaluations.mobility_outcomes import MobilityCaseProvenance
from app.evaluations.professional_review import (
    compile_professional_reviews,
    load_official_source_gold_set,
    load_professional_review_bundle,
)


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = (
    ROOT
    / "apps"
    / "api"
    / "evaluations"
    / "mobility_cases"
    / "austria_rwr_shortage_2026_v1.json"
)
REVIEW_PATH = (
    ROOT
    / "apps"
    / "api"
    / "evaluations"
    / "professional_reviews"
    / "austria_rwr_shortage_2026_v1_review_2026_09_02.json"
)


def test_anonymous_austria_review_promotes_the_complete_current_tranche() -> None:
    source = load_official_source_gold_set(SOURCE_PATH)
    bundle = load_professional_review_bundle(REVIEW_PATH)

    assert source.professional_review_status == "NOT_REVIEWED"
    assert bundle.review_batch_id == "at-rwr-v3-2026-0902-001"
    assert {review.decision.value for review in bundle.reviews} == {"CORRECTED"}
    assert all(review.independent_review for review in bundle.reviews)

    compiled = compile_professional_reviews(source, bundle)

    assert compiled.source_case_count == 3
    assert compiled.review_count == 3
    assert compiled.confirmed_count == 0
    assert compiled.corrected_count == 3
    assert compiled.disputed_count == 0
    assert compiled.needs_more_facts_count == 0
    assert compiled.held_case_ids == ()
    assert compiled.unreviewed_case_ids == ()
    assert len(compiled.promoted_cases) == 3
    assert all(
        case.provenance is MobilityCaseProvenance.PROFESSIONALLY_REVIEWED
        for case in compiled.promoted_cases
    )
    assert {
        case.case_id: case.expected_eligibility.value
        for case in compiled.promoted_cases
    } == {
        "at-rwr-shortage-software-di-no-job-offer-2026-01": "INELIGIBLE",
        "at-rwr-shortage-software-di-strong-points-2026-01": "ELIGIBLE",
        "at-rwr-shortage-software-di-under-points-2026-01": "INELIGIBLE",
    }


def test_committed_austria_review_uses_only_approved_opaque_reviewer_aliases() -> None:
    payload = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    reviews = payload["reviews"]

    assert {review["professional_review_reference"] for review in reviews} == {
        "prof-ref-at-rwr-2026-v3-001"
    }
    assert {review["reviewer_reference"] for review in reviews} == {
        "rev-alias-at-2026-001"
    }
    assert {review["reviewer_credential_reference"] for review in reviews} == {
        "cred-alias-at-2026-001"
    }

    serialized = json.dumps(payload, ensure_ascii=False)
    assert re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", serialized) is None
    assert re.search(r"https?://", serialized) is None
    forbidden_identity_keys = {
        "reviewer_name",
        "registration_number",
        "bar_number",
        "email",
        "phone",
        "address",
        "firm",
        "employer",
        "profile_url",
    }
    assert all(f'"{key}"' not in serialized for key in forbidden_identity_keys)
