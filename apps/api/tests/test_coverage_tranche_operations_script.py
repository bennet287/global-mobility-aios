from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_operations_script_preserves_human_review_boundaries() -> None:
    text = _read("scripts/Invoke-CoverageTrancheOperations.ps1")

    assert "SupportsShouldProcess" in text
    assert "DryRun $true" in text
    assert "queue_eligible_baselines" in text
    assert "/assistant/prepare" in text
    assert "/review" not in text
    assert "/publish" not in text
    assert "creates_review_decisions = $false" in text
    assert "creates_assertions = $false" in text
    assert "publishes_verified_rules = $false" in text
    assert "mutates_snapshots = $false" in text
    assert "creates_coverage_claim = $false" in text


def test_manifest_validator_checks_uuid_codes_and_limits() -> None:
    text = _read("scripts/Test-CoverageTrancheManifest.ps1")

    assert "[guid]::TryParse" in text
    assert "^[A-Z]{2}$" in text
    assert "MaxGroups" in text
    assert "MaxCodesPerGroup" in text
    assert "creates_review_decisions = $false" in text


def test_expansion_planner_is_read_only() -> None:
    text = _read("scripts/New-CoverageExpansionPlan.ps1")

    assert "/coverage-worklist" in text
    assert "-Method Get" in text
    assert "-Method Post" not in text
    assert "infers_immigration_relationships = $false" in text
    assert "certifies_sources = $false" in text
    assert "publishes_rules = $false" in text


def test_example_operations_manifest_is_valid_and_non_operational() -> None:
    data = json.loads(
        _read("knowledge/global_coverage/tranches/v10_22_operations_manifest.example.json")
    )

    assert data["schema_version"] == "1.0"
    assert len(data["groups"]) == 2
    assert data["groups"][0]["batch_id"].startswith("00000000-")
    assert data["groups"][0]["alpha2_codes"] == ["FR", "IT"]


def test_v10_22_documentation_and_roadmap_are_present() -> None:
    docs = _read("docs/COVERAGE_TRANCHE_OPERATIONS_V10_22.md")
    roadmap = _read("docs/ROADMAP.md")

    assert "No automatic" in docs or "does **not** add automatic" in docs
    assert "v10.22" in roadmap
    assert "multi-batch tranche operations" in roadmap
    assert "0032_initial_rule_assertions" in roadmap


def test_v10_22_1_uses_powershell_provider_path_resolution() -> None:
    validator = _read("scripts/Test-CoverageTrancheManifest.ps1")
    planner = _read("scripts/New-CoverageExpansionPlan.ps1")
    operations = _read("scripts/Invoke-CoverageTrancheOperations.ps1")

    for text in (validator, planner, operations):
        assert "GetUnresolvedProviderPathFromPSPath" in text

    assert "GetFullPath($ManifestPath)" not in validator
    assert "GetFullPath($OutputPath)" not in planner
    assert "GetFullPath($CsvOutputPath)" not in planner
    assert "GetFullPath($OutputDirectory)" not in operations
