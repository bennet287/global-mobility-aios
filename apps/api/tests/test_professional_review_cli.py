from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "prepare_austria_professional_review.py"
SOURCE_PATH = ROOT / "apps" / "api" / "evaluations" / "mobility_cases" / "austria_rwr_shortage_2026_v1.json"
CASE_ID = "at-rwr-shortage-software-di-no-job-offer-2026-01"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _source_labels(case_id: str) -> dict[str, object]:
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    case = next(item for item in payload["cases"] if item["case_id"] == case_id)
    labels = dict(case["expected"])
    return {
        key: sorted(value) if isinstance(value, list) else value
        for key, value in labels.items()
    }


def _complete_blind_review(
    template: dict[str, object],
    *,
    reviewed_labels: dict[str, object] | None,
    assessment_status: str = "ASSESSED",
) -> dict[str, object]:
    reviewed_at = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc).isoformat()
    template["review_batch_id"] = "test-only:austria-blind-review-batch:v1"
    template["created_at"] = reviewed_at
    review = template["reviews"][0]
    review.update(
        {
            "review_id": "test-only:austria-blind-review:v1",
            "reviewed_at": reviewed_at,
            "professional_review_reference": "test-only:review-record:blind:v1",
            "reviewer_reference": "test-only:reviewer:blind",
            "reviewer_credential_reference": "test-only:credential:blind",
            "independent_review": True,
            "assessment_status": assessment_status,
            "reviewed_labels": reviewed_labels,
            "notes": "Test fixture only; not real professional evidence.",
        }
    )
    return template


def test_professional_review_cli_prepares_blind_fingerprint_bound_handoff_packet() -> None:
    result = _run("--prepare-packet", "--case-id", CASE_ID)

    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)
    assert packet["contract_version"] == "austria-professional-review-handoff.v3"
    assert packet["reviewer_facing_packet"] is True
    assert packet["supersedes_reviewer_handoff_contracts"] == [
        "austria-professional-review-handoff.v1",
        "austria-professional-review-handoff.v2",
    ]
    assert "Reject any reviewer-facing packet" in packet["legacy_packet_rejection"]
    assert packet["blind_review"] is True
    assert packet["expected_labels_excluded"] is True
    assert packet["source_rationale_excluded"] is True
    assert packet["source_professional_review_status"] == "NOT_REVIEWED"
    assert packet["case_count"] == 1
    case = packet["cases"][0]
    assert case["case_id"] == CASE_ID
    assert case["source_case_fingerprint"].startswith("sha256:")
    assert case["facts"]["binding_job_offer_in_austria"] is False
    assert "asserted scenario inputs" in case["fact_evidence_boundary"]
    assert "authenticated documents" in case["reviewer_instruction"]
    assert "source_labels" not in case
    assert "source_rationale" not in case
    assert "Do not ask for or infer" in case["reviewer_instruction"]
    assert "does not verify the real-world identity" in packet["reviewer_boundary"]
    source_refs = {source["ref"] for source in packet["official_sources"]}
    assert {
        "ris.bka.gv.at:auslbg-12a",
        "ris.bka.gv.at:auslbg-annex-b",
        "ris.bka.gv.at:fachkraefteverordnung-2026-1",
    }.issubset(source_refs)
    assert "missing_evidence" in packet["claim_boundary"]
    assert "not authenticated documents" in packet["claim_boundary"]
    label_contract = packet["reviewed_label_contract"]
    assert label_contract["pathway_keys"]["tested_route_key"] == "at-rwr-skilled-worker-shortage-occupation"
    assert "mandatory legal criteria" in label_contract["eligibility"]["semantics"]["ELIGIBLE"]
    assert "Do not use this label solely" in label_contract["eligibility"]["semantics"]["REVIEW_REQUIRED"]
    assert label_contract["required_evidence"]["bounded_keys"] == [
        "shortage_occupation_training",
        "binding_job_offer",
        "applicable_minimum_remuneration",
        "points_evidence",
    ]
    assert "Alternative-route recommendations belong in notes" in label_contract["pathway_keys"]["instruction"]


def test_professional_review_cli_validates_structural_first_tranche_candidate(tmp_path: Path) -> None:
    prepared = _run("--prepare-packet", "--case-id", CASE_ID)
    assert prepared.returncode == 0, prepared.stderr
    packet = json.loads(prepared.stdout)
    case = packet["cases"][0]
    reviewed_at = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc).isoformat()
    bundle = {
        "schema_version": "mobility-professional-review-v1",
        "review_batch_id": "test-only:austria-cli-review-batch:v1",
        "source_benchmark_key": packet["source_benchmark_key"],
        "source_schema_version": packet["source_schema_version"],
        "created_at": reviewed_at,
        "reviews": [
            {
                "review_id": "test-only:austria-cli-review:v1",
                "source_case_id": case["case_id"],
                "source_case_fingerprint": case["source_case_fingerprint"],
                "reviewed_at": reviewed_at,
                "professional_review_reference": "test-only:review-record:cli:v1",
                "reviewer_reference": "test-only:reviewer:cli",
                "reviewer_credential_reference": "test-only:credential:cli",
                "independent_review": True,
                "decision": "CONFIRMED",
                "reviewed_labels": _source_labels(CASE_ID),
                "notes": "Test fixture only; not real professional evidence.",
            }
        ],
    }
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(bundle), encoding="utf-8")

    validated = _run("--validate-bundle", str(review_path))

    assert validated.returncode == 0, validated.stderr
    report = json.loads(validated.stdout)
    assert report["professionally_reviewed_case_count"] == 1
    assert report["promoted_case_ids"] == [CASE_ID]
    assert report["first_real_tranche_structural_candidate"] is True
    assert report["credential_references_structural_only"] is True
    assert "not by itself proof" in report["acceptance_boundary"]


def test_blind_assessment_derives_confirmed_only_after_return(tmp_path: Path) -> None:
    prepared = _run("--prepare-blind-return-template", "--case-id", CASE_ID)
    assert prepared.returncode == 0, prepared.stderr
    template = _complete_blind_review(
        json.loads(prepared.stdout),
        reviewed_labels=_source_labels(CASE_ID),
    )
    blind_path = tmp_path / "blind-review.json"
    blind_path.write_text(json.dumps(template), encoding="utf-8")
    canonical_path = tmp_path / "canonical-review.json"

    compiled = _run("--compile-blind-return", str(blind_path), "--output", str(canonical_path))

    assert compiled.returncode == 0, compiled.stderr
    report = json.loads(compiled.stdout)
    assert report["confirmed_count"] == 1
    assert report["corrected_count"] == 0
    assert report["expected_labels_revealed_to_reviewer"] is False
    assert report["source_rationale_revealed_to_reviewer"] is False
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    assert canonical["schema_version"] == "mobility-professional-review-v1"
    assert canonical["reviews"][0]["decision"] == "CONFIRMED"
    assert canonical["reviews"][0]["reviewed_labels"] == _source_labels(CASE_ID)

    validated = _run("--validate-bundle", str(canonical_path))
    assert validated.returncode == 0, validated.stderr
    assert json.loads(validated.stdout)["professionally_reviewed_case_count"] == 1


def test_blind_assessed_review_requires_all_label_fields(tmp_path: Path) -> None:
    prepared = _run("--prepare-blind-return-template", "--case-id", CASE_ID)
    assert prepared.returncode == 0, prepared.stderr
    labels = _source_labels(CASE_ID)
    labels["contradictions"] = None
    template = _complete_blind_review(json.loads(prepared.stdout), reviewed_labels=labels)
    blind_path = tmp_path / "blind-review-incomplete.json"
    blind_path.write_text(json.dumps(template), encoding="utf-8")

    compiled = _run("--compile-blind-return", str(blind_path))

    assert compiled.returncode == 2
    assert "must populate all reviewed label fields" in compiled.stderr


def test_blind_assessment_derives_corrected_when_independent_labels_differ(tmp_path: Path) -> None:
    prepared = _run("--prepare-blind-return-template", "--case-id", CASE_ID)
    assert prepared.returncode == 0, prepared.stderr
    corrected = _source_labels(CASE_ID)
    corrected["eligibility"] = "REVIEW_REQUIRED"
    template = _complete_blind_review(json.loads(prepared.stdout), reviewed_labels=corrected)
    blind_path = tmp_path / "blind-review-corrected.json"
    blind_path.write_text(json.dumps(template), encoding="utf-8")
    canonical_path = tmp_path / "canonical-review-corrected.json"

    compiled = _run("--compile-blind-return", str(blind_path), "--output", str(canonical_path))

    assert compiled.returncode == 0, compiled.stderr
    report = json.loads(compiled.stdout)
    assert report["confirmed_count"] == 0
    assert report["corrected_count"] == 1
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    assert canonical["reviews"][0]["decision"] == "CORRECTED"
    assert canonical["reviews"][0]["reviewed_labels"]["eligibility"] == "REVIEW_REQUIRED"
