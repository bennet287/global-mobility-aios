from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.evaluate_austria_ai_domain_review import (
    _corroboration_summary,
    _validate_provider_payload,
    prepare_blind_packet,
)

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "evaluate_austria_ai_domain_review.py"
SOURCE = (
    ROOT
    / "apps"
    / "api"
    / "evaluations"
    / "mobility_cases"
    / "austria_rwr_shortage_2026_v1.json"
)
PATHWAY_KEY = "at-rwr-skilled-worker-shortage-occupation"


def test_blind_packet_excludes_expected_labels_and_rationale() -> None:
    packet = prepare_blind_packet(SOURCE)

    assert packet["contract_version"] == "austria-ai-domain-review-blind-packet.v1"
    assert packet["expected_labels_excluded"] is True
    assert packet["professional_review_status_effect"] == "NONE"
    assert packet["review_scope_pathway_key"] == PATHWAY_KEY
    assert len(packet["cases"]) == 3

    serialized = json.dumps(packet, sort_keys=True)
    assert '"expected"' not in serialized
    assert '"rationale"' not in serialized


def test_prepare_packet_cli_writes_external_artifact(tmp_path: Path) -> None:
    output = tmp_path / "blind.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--prepare-packet",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    status = json.loads(result.stdout)
    assert status["status"] == "prepared"
    assert status["case_count"] == 3
    assert status["expected_labels_excluded"] is True

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["professional_review_status_effect"] == "NONE"
    assert payload["review_scope_pathway_key"] == PATHWAY_KEY


def test_provider_payload_requires_exact_case_set_scope_and_non_authority() -> None:
    case_ids = ["case-a"]
    refs = {"source-a"}
    valid = {
        "reviews": [
            {
                "case_id": "case-a",
                "classification": "INELIGIBLE",
                "pathway_key": PATHWAY_KEY,
                "points_total": 30,
                "points_breakdown": {"qualification": 30},
                "requirements_satisfied": ["training"],
                "requirements_failed": ["points threshold"],
                "source_refs": ["source-a"],
                "reason": "Below the threshold.",
                "final_authority_decision": False,
            }
        ]
    }

    reviews = _validate_provider_payload(
        valid,
        case_ids=case_ids,
        valid_source_refs=refs,
    )
    assert reviews[0]["classification"] == "INELIGIBLE"
    assert reviews[0]["pathway_key"] == PATHWAY_KEY

    wrong_scope = json.loads(json.dumps(valid))
    wrong_scope["reviews"][0]["pathway_key"] = "invented-route"
    try:
        _validate_provider_payload(
            wrong_scope,
            case_ids=case_ids,
            valid_source_refs=refs,
        )
    except ValueError as exc:
        assert "declared review scope" in str(exc)
    else:
        raise AssertionError("wrong pathway scope must fail closed")

    authority_claim = json.loads(json.dumps(valid))
    authority_claim["reviews"][0]["final_authority_decision"] = True
    try:
        _validate_provider_payload(
            authority_claim,
            case_ids=case_ids,
            valid_source_refs=refs,
        )
    except ValueError as exc:
        assert "final_authority_decision=false" in str(exc)
    else:
        raise AssertionError("authority-claiming AI review must fail closed")


def _run(
    provider: str,
    classifications: tuple[str, str, str],
) -> dict[str, object]:
    case_ids = ["a", "b", "c"]
    expected = ("INELIGIBLE", "REVIEW_REQUIRED", "INELIGIBLE")
    return {
        "provider_key": provider,
        "status": "completed",
        "structural_valid": True,
        "response_identity_match": True,
        "reviews": [
            {
                "case_id": case_id,
                "classification": classification,
            }
            for case_id, classification in zip(
                case_ids,
                classifications,
                strict=True,
            )
        ],
        "comparison": {
            "all_classifications_match": classifications == expected,
            "all_pathways_match": True,
        },
    }


def test_multi_model_candidate_requires_two_distinct_unanimous_matching_providers() -> None:
    expected = ("INELIGIBLE", "REVIEW_REQUIRED", "INELIGIBLE")

    one = _corroboration_summary(
        [_run("gemini", expected)],
        case_ids=["a", "b", "c"],
    )
    assert one["multi_model_corroboration_candidate"] is False

    two = _corroboration_summary(
        [
            _run("gemini", expected),
            _run("deepseek", expected),
        ],
        case_ids=["a", "b", "c"],
    )
    assert two["multi_model_corroboration_candidate"] is True
    assert two["professional_review_status_effect"] == "NONE"

    disagreed = _corroboration_summary(
        [
            _run("gemini", expected),
            _run(
                "deepseek",
                ("INELIGIBLE", "ELIGIBLE", "INELIGIBLE"),
            ),
        ],
        case_ids=["a", "b", "c"],
    )
    assert disagreed["multi_model_corroboration_candidate"] is False
