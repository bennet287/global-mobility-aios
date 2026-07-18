from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    JurisdictionCoverageEvidenceBatch,
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    OfficialSource,
    RegulatoryAuthority,
    SourceMonitor,
)
from app.services.coverage_evidence_packs import (
    load_coverage_evidence_pack,
    submit_coverage_evidence_pack,
)
from app.services.coverage_evidence_batches import coverage_batch_payload
from app.services.jurisdiction_registry import import_un_m49_registry
from scripts.check_local_quality import build_quality_commands
from scripts.validate_global_coverage_evidence_pack import (
    discover_canonical_evidence_packs,
    validate_pack,
    validate_sha256_receipt,
)


SAMPLE_M49_STARTER = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>150</td><td>Europe</td><td>155</td><td>Western Europe</td><td></td><td></td><td>Austria</td><td>040</td><td>AT</td><td>AUT</td></tr>
<tr><td>001</td><td>World</td><td>150</td><td>Europe</td><td>155</td><td>Western Europe</td><td></td><td></td><td>Germany</td><td>276</td><td>DE</td><td>DEU</td></tr>
<tr><td>001</td><td>World</td><td>019</td><td>Americas</td><td>021</td><td>Northern America</td><td></td><td></td><td>Canada</td><td>124</td><td>CA</td><td>CAN</td></tr>
<tr><td>001</td><td>World</td><td>009</td><td>Oceania</td><td>053</td><td>Australia and New Zealand</td><td></td><td></td><td>Australia</td><td>036</td><td>AU</td><td>AUS</td></tr>
<tr><td>001</td><td>World</td><td>009</td><td>Oceania</td><td>053</td><td>Australia and New Zealand</td><td></td><td></td><td>New Zealand</td><td>554</td><td>NZ</td><td>NZL</td></tr>
</tbody></table></html>
"""


def test_official_starter_pack_is_review_gated_and_source_validated() -> None:
    pack = load_coverage_evidence_pack()
    summary = pack.summary()
    assert summary["pack_version"] == "v10.17"
    assert summary["alpha2_codes"] == ["AT", "DE", "CA", "AU", "NZ"]
    assert summary["jurisdiction_count"] == 5
    assert summary["creates_coverage_claim"] is False
    assert summary["auto_approves_evidence"] is False
    assert summary["requires_separate_reviewer"] is True
    assert len(summary["payload_sha256"]) == 64
    for item in pack.batch.items:
        assert item.immigration_assessment is not None
        assert item.immigration_assessment.rule_relationship == "independent"
        assert item.source_onboarding is not None
        assert item.source_onboarding.source_url.startswith("https://")
        assert item.source_onboarding.allowed_domains
    austria = next(item for item in pack.batch.items if item.alpha2_code == "AT")
    assert austria.source_onboarding is not None
    assert austria.source_onboarding.source_url == "https://www.migration.gv.at/en/welcome/?no_cache=1"


def test_official_starter_pack_submits_atomically_and_links_assessment_source(
    db_session: Session,
) -> None:
    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49_STARTER,
        minimum_entries=5,
        require_global_scope=False,
    )
    pack = load_coverage_evidence_pack()
    batch, created = submit_coverage_evidence_pack(
        db_session,
        pack=pack,
        actor="starter-pack-proposer",
    )
    assert created is True
    payload = coverage_batch_payload(db_session, batch)
    assert payload["status"] == "pending_review"
    assert payload["item_count"] == 5
    assert payload["immigration_assessment_count"] == 5
    assert payload["source_onboarding_count"] == 5
    assert payload["source_certification_count"] == 5
    assert payload["review_counts"]["pending_review"] == 10
    assert len(db_session.exec(select(RegulatoryAuthority)).all()) == 5
    assert len(db_session.exec(select(OfficialSource)).all()) == 5
    assert len(db_session.exec(select(SourceMonitor)).all()) == 5

    items = db_session.exec(
        select(JurisdictionCoverageEvidenceBatchItem).where(
            JurisdictionCoverageEvidenceBatchItem.batch_id == batch.id
        )
    ).all()
    assert len(items) == 5
    for item in items:
        assessment = db_session.get(
            JurisdictionImmigrationAssessment,
            item.immigration_assessment_id,
        )
        assert assessment is not None
        assert assessment.status == "pending_review"
        assert assessment.official_source_id == item.official_source_id
        assert item.source_certification_id is not None
        assert item.source_monitor_id is not None

    repeated, repeated_created = submit_coverage_evidence_pack(
        db_session,
        pack=pack,
        actor="starter-pack-proposer",
    )
    assert repeated_created is False
    assert repeated.id == batch.id
    assert len(db_session.exec(select(JurisdictionCoverageEvidenceBatch)).all()) == 1


def test_pack_validator_rejects_approval_or_coverage_claim(tmp_path: Path) -> None:
    original = load_coverage_evidence_pack().raw
    unsafe = json.loads(json.dumps(original))
    unsafe["review_status"] = "approved"
    unsafe["coverage_claim_ready"] = True
    path = tmp_path / "unsafe-pack.json"
    path.write_text(json.dumps(unsafe), encoding="utf-8")
    with pytest.raises(ValueError, match="pending_independent_review"):
        load_coverage_evidence_pack(path)


def test_all_canonical_evidence_packs_and_receipts_validate() -> None:
    paths = discover_canonical_evidence_packs()

    assert len(paths) >= 2
    assert any(path.name == "v10_17_official_evidence_starter.json" for path in paths)
    assert any("_ready_" in path.name for path in paths)
    for path in paths:
        summary = validate_pack(path)
        assert summary["review_status"] == "pending_independent_review"
        if path.with_name(f"{path.name}.sha256").exists():
            assert summary["file_sha256"] == validate_sha256_receipt(path)


def test_local_quality_gate_validates_all_canonical_evidence_packs() -> None:
    command = next(
        command for command in build_quality_commands() if command.label == "coverage_evidence_packs"
    )

    assert command.argv == (
        sys.executable,
        "scripts/validate_global_coverage_evidence_pack.py",
        "--all",
    )


def test_pack_validator_rejects_mismatched_sha256_receipt(tmp_path: Path) -> None:
    pack_path = tmp_path / "sample.json"
    pack_path.write_text("{}", encoding="utf-8")
    pack_path.with_name("sample.json.sha256").write_text("0" * 64, encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256 receipt mismatch"):
        validate_sha256_receipt(pack_path)
