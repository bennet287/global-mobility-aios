from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path("scripts/prepare_austria_professional_review.py")
CASE_ID = "at-rwr-shortage-software-di-no-job-offer-2026-01"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_professional_review_cli_prepares_fingerprint_bound_handoff_packet() -> None:
    result = _run("--prepare-packet", "--case-id", CASE_ID)

    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)
    assert packet["contract_version"] == "austria-professional-review-handoff.v1"
    assert packet["source_professional_review_status"] == "NOT_REVIEWED"
    assert packet["case_count"] == 1
    case = packet["cases"][0]
    assert case["case_id"] == CASE_ID
    assert case["source_case_fingerprint"].startswith("sha256:")
    assert case["facts"]["binding_job_offer_in_austria"] is False
    assert "does not verify the real-world identity" in packet["reviewer_boundary"]


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
                "reviewed_labels": case["source_labels"],
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
