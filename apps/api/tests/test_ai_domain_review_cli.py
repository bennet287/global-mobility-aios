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
SOURCE = ROOT / "apps" / "api" / "evaluations" / "mobility_cases" / "austria_rwr_shortage_2026_v1.json"


def test_blind_packet_excludes_expected_labels_and_rationale() -> None:
    packet = prepare_blind_packet(SOURCE)

    assert packet["contract_version"] == "austria-ai-domain-review-blind-packet.v1"
    assert packet["expected_labels_excluded"] is True
    assert packet["professional_review_status_effect"] == "NONE"
    assert len(packet["cases"]) == 3

    serialized = json.dumps(packet, sort_keys=True)
    assert '"expected"' not in serialized
    assert '"rationale"' not in serialized


def test_prepare_packet_cli_writes_external_artifact(tmp_path: Path) -> None:
    output = tmp_path / "blind.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--prepare-packet", "--output", str(output)],
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


def test_provider_payload_requires_exact_case_set_and_non_authority() -> None:
    case_ids = ["case-a"]
    refs = {"source-a"}
    valid = {
        "reviews": [
            {
                "case_id": "case-a",
                "classification": "INELIGIBLE",
                "pathway_key": "pathway-a",
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

    reviews = _validate_provider_payload(valid, case_ids=case_ids, valid_source_refs=refs)
    assert reviews[0]["classification"] == "INELIGIBLE"

    invalid = json.loads(json.dumps(valid))
    invalid["reviews"][0]["final_authority_decision"] = True

    try:
        _validate_provider_payload(invalid, case_ids=case_ids, valid_source_refs=refs)
    except ValueError as exc:
        assert "final_authority_decision=false" in str(exc)
    else:
        raise AssertionError("authority-claiming AI review must fail closed")


def _run(provider: str, classifications: tuple[str, str, str]) -> dict[str, object]:
    case_ids = ["a", "b", "c"]
    return {
        "provider_key": provider,
        "status": "completed",
        "structural_valid": True,
        "response_identity_match": True,
        "reviews": [
            {"case_id": case_id, "classification": classification}
            for case_id, classification in zip(case_ids, classifications, strict=True)
        ],
        "comparison": {
            "all_classifications_match": classifications
            == ("INELIGIBLE", "REVIEW_REQUIRED", "INELIGIBLE"),
            "all_pathways_match": True,
        },
    }


def test_multi_model_candidate_requires_two_distinct_unanimous_matching_providers() -> None:
    expected = ("INELIGIBLE", "REVIE]}IEU%Iˆ°€‰%91%%	1ˆ¤(€€€½¹”€ô}½ÉÉ½‰½É…Ñ¥½¹}ÍÕµµ…Éä¡m}ÉÕ¸ ‰•µ¥¹¤ˆ°•áÁ•Ñ•¥t°…Í•}¥‘Ìõl‰„ˆ°€‰ˆˆ°€‰Œ‰t¤(€€€…ÍÍ•ÉÐ½¹•l‰µÕ±Ñ¥}µ½‘•±}½ÉÉ½‰½É…Ñ¥½¹}…¹‘¥‘…Ñ”‰t¥Ì…±Í”((€€€ÑÝ¼€ô}½ÉÉ½‰½É…Ñ¥½¹}ÍÕµµ…Éä (€€€€€€€m}ÉÕ¸ ‰•µ¥¹¤ˆ°•áÁ•Ñ•¤°}ÉÕ¸ ‰‘••ÁÍ••¬ˆ°•áÁ•Ñ•¥t°(€€€€€€€…Í•}¥‘Ìõl‰„ˆ°€‰ˆˆ°€‰Œ‰t°(€€€€¤(€€€…ÍÍ•ÉÐÑÝ½l‰µÕ±Ñ¥}µ½‘•±}½ÉÉ½‰½É…Ñ¥½¹}…¹‘¥‘…Ñ”‰t¥ÌQÉÕ”(€€€…ÍÍ•ÉÐÑÝ½l‰ÁÉ½™•ÍÍ¥½¹…±}É•Ù¥•Ý}ÍÑ…ÑÕÍ}•™™•Ð‰t€ôô€‰9=9ˆ((€€€‘¥Í…É••€ô}½ÉÉ½‰½É…Ñ¥½¹}ÍÕµµ…Éä (€€€€€€€l(€€€€€€€€€€€}ÉÕ¸ ‰•µ¥¹¤ˆ°•áÁ•Ñ•¤°(€€€€€€€€€€€}ÉÕ¸ ‰‘••ÁÍ••¬ˆ°€ ‰%91%%	1ˆ°€‰1%%	1ˆ°€‰%91%%	1ˆ¤¤°(€€€€€€€t°(€€€€€€€…Í•}¥‘Ìõl‰„ˆ°€‰ˆˆ°€‰Œ‰t°(€€€€¤(€€€…ÍÍ•ÉÐ‘¥Í…É••‘l‰µÕ±Ñ¥}µ½‘•±}½ÉÉ½‰½É…Ñ¥½¹}…¹‘¥‘…Ñ”‰t¥Ì…±Í”(