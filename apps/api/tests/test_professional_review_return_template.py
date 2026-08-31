from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "prepare_austria_professional_review.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def test_professional_review_cli_prepares_fail_closed_return_template_for_full_tranche() -> None:
    result = _run("--prepare-return-template")

    assert result.returncode == 0, result.stderr
    template = json.loads(result.stdout)
    assert template["schema_version"] == "mobility-professional-review-v1"
    assert template["review_batch_id"] is None
    assert template["created_at"] is None
    assert len(template["reviews"]) == 3

    for review in template["reviews"]:
        assert review["source_case_id"]
        assert review["source_case_fingerprint"].startswith("sha256:")
        assert review["review_id"] is None
        assert review["reviewed_at"] is None
        assert review["professional_review_reference"] is None
        assert review["reviewer_reference"] is None
        assert review["reviewer_credential_reference"] is None
        assert review["independent_review"] is None
        assert review["decision"] is None
        assert review["reviewed_labels"] is None
        assert review["notes"] is None


def test_untouched_professional_review_return_template_cannot_validate(tmp_path: Path) -> None:
    prepared = _run("--prepare-return-template")
    assert prepared.returncode == 0, prepared.stderr

    template_path = tmp_path / "review-return-template.json"
    template_path.write_text(prepared.stdout, encoding="utf-8")

    validated = _run("--validate-bundle", str(template_path))

    assert validated.returncode == 2
    error = json.loads(validated.stderr)
    assert error["status"] == "failed"
    assert error["error_type"] == "ValueError"
    assert error["error"].startswith("reviews[0].")
    assert "must be" in error["error"]


def test_professional_review_cli_prepares_blind_reviewer_return_template() -> None:
    result = _run("--prepare-blind-return-template")

    assert result.returncode == 0, result.stderr
    template = json.loads(result.stdout)
    assert template["contract_version"] == "austria-professional-review-blind-return.v1"
    assert template["review_batch_id"] is None
    assert template["created_at"] is None
    assert len(template["reviews"]) == 3

    for review in template["reviews"]:
        assert review["source_case_id"]
        assert review["source_case_fingerprint"].startswith("sha256:")
        assert review["review_id"] is None
        assert review["reviewed_at"] is None
        assert review["professional_review_reference"] is None
        assert review["reviewer_reference"] is None
        assert review["reviewer_credential_reference"] is None
        assert review["independent_review"] is None
        assert review["assessment_status"] is None
        assert review["reviewed_labels"] == {
            "pathway_keys": None,
            "eligibility": None,
            "required_evidence": None,
            "missing_evidence": None,
            "contradictions": None,
            "rule_or_source_refs": None,
            "escalation_required": None,
        }
        assert review["notes"] is None
        assert "decision" not in review


def test_untouched_blind_return_template_cannot_compile(tmp_path: Path) -> None:
    prepared = _run("--prepare-blind-return-template")
    assert prepared.returncode == 0, prepared.stderr

    template_path = tmp_path / "blind-review-return-template.json"
    template_path.write_text(prepared.stdout, encoding="utf-8")
    canonical_path = tmp_path / "canonical.json"

    compiled = _run(
        "--compile-blind-return",
        str(template_path),
        "--output",
        str(canonical_path),
    )

    assert compiled.returncode == 2
    error = json.loads(compiled.stderr)
    assert error["status"] == "failed"
    assert error["error_type"] == "ValueError"
    assert "review_batch_id must be a non-empty string" in error["error"]
    assert not canonical_path.exists()
