from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    OfficialSource,
    RegulatoryAuthority,
    SourceMonitor,
    VerifiedRule,
    now_utc,
)
from app.services.jurisdiction_registry import (
    import_un_m49_registry,
    jurisdiction_registry_coverage,
    parse_un_m49_html,
    propose_immigration_assessment,
    propose_source_certification,
    review_immigration_assessment,
    review_source_certification,
)


SAMPLE_M49 = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>002</td><td>Africa</td><td>014</td><td>Eastern Africa</td><td></td><td></td><td>Afghanistan</td><td>004</td><td>AF</td><td>AFG</td></tr>
<tr><td>001</td><td>World</td><td>142</td><td>Asia</td><td>145</td><td>Western Asia</td><td></td><td></td><td>State of Palestine</td><td>275</td><td>PS</td><td>PSE</td></tr>
<tr><td>001</td><td>World</td><td>142</td><td>Asia</td><td>030</td><td>Eastern Asia</td><td></td><td></td><td>China, Hong Kong SAR</td><td>344</td><td>HK</td><td>HKG</td></tr>
</tbody></table></html>
"""


def test_m49_parser_reads_only_the_canonical_english_table() -> None:
    rows = parse_un_m49_html(SAMPLE_M49 + '<table id="other"><tr><td>ignored</td></tr></table>')
    assert [row["alpha2_code"] for row in rows] == ["AF", "HK", "PS"]
    assert rows[1]["name"] == "China, Hong Kong SAR"
    assert rows[2]["m49_code"] == "275"


def test_registry_import_is_versioned_idempotent_and_exposes_coverage_gaps(
    db_session: Session,
) -> None:
    release, created = import_un_m49_registry(
        db_session,
        actor="pytest-registry",
        source_text=SAMPLE_M49,
        minimum_entries=3,
        require_global_scope=False,
    )
    repeated, repeated_created = import_un_m49_registry(
        db_session,
        actor="pytest-registry",
        source_text=SAMPLE_M49,
        minimum_entries=3,
        require_global_scope=False,
    )
    assert created is True
    assert repeated_created is False
    assert repeated.id == release.id
    jurisdictions = {
        row.code: row for row in db_session.exec(select(Jurisdiction)).all()
    }
    assert jurisdictions["AF"].jurisdiction_type == "country"
    assert jurisdictions["PS"].jurisdiction_type == "country"
    assert jurisdictions["HK"].jurisdiction_type == "autonomous_jurisdiction"
    assert jurisdictions["TW"].jurisdiction_type == "territory"

    authority = RegulatoryAuthority(
        jurisdiction_id=jurisdictions["AF"].id,
        name="Afghanistan Immigration Authority",
        website_url="https://example.gov.af/immigration",
    )
    db_session.add(authority)
    db_session.commit()
    db_session.refresh(authority)
    source = OfficialSource(
        jurisdiction_id=jurisdictions["AF"].id,
        regulatory_authority_id=authority.id,
        country="afghanistan",
        domain="visa",
        name="Afghanistan immigration portal",
        url="https://example.gov.af/immigration",
        source_type="government",
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    db_session.add(SourceMonitor(
        official_source_id=source.id,
        status="active",
        last_checked_at=now_utc(),
    ))
    db_session.add(VerifiedRule(
        country="afghanistan",
        domain="visa",
        rule_key="af-registry-test",
        statement="A reviewed test rule exists.",
        jurisdiction_id=jurisdictions["AF"].id,
        official_source_id=source.id,
        confidence=1.0,
        active=True,
        approved_by="pytest-reviewer",
    ))
    db_session.commit()

    uncertified_registry = jurisdiction_registry_coverage(db_session)
    uncertified_afghanistan = next(
        row for row in uncertified_registry["entries"] if row["alpha2_code"] == "AF"
    )
    assert uncertified_afghanistan["has_authority"] is True
    assert uncertified_afghanistan["has_official_source"] is True
    assert uncertified_afghanistan["has_reviewed_primary_source"] is False
    assert "reviewed_primary_source" in uncertified_afghanistan["missing"]

    certification = propose_source_certification(
        db_session,
        jurisdiction_id=jurisdictions["AF"].id,
        regulatory_authority_id=authority.id,
        official_source_id=source.id,
        coverage_domains=["visa"],
        evidence_notes="Authority ownership, HTTPS source identity, and immigration scope were checked.",
        actor="pytest-source-proposer",
    )
    with pytest.raises(ValueError, match="different from the proposer"):
        review_source_certification(
            db_session,
            certification_id=certification.id,
            decision="approved",
            notes="Self-review must fail.",
            actor="pytest-source-proposer",
        )
    certification = review_source_certification(
        db_session,
        certification_id=certification.id,
        decision="approved",
        notes="Primary authority and official immigration source independently reviewed.",
        actor="pytest-source-reviewer",
    )
    assert certification.status == "approved"

    proposal = propose_immigration_assessment(
        db_session,
        jurisdiction_id=jurisdictions["AF"].id,
        rule_relationship="independent",
        parent_code=None,
        evidence_url="https://example.gov.af/immigration/legal-framework",
        evidence_title="Afghanistan immigration legal framework",
        rationale="The official authority material describes a directly administered immigration framework.",
        actor="pytest-proposer",
        official_source_id=source.id,
    )
    with pytest.raises(ValueError, match="different from the proposer"):
        review_immigration_assessment(
            db_session,
            assessment_id=proposal.id,
            decision="approved",
            notes="Self-review must fail.",
            actor="pytest-proposer",
        )
    approved = review_immigration_assessment(
        db_session,
        assessment_id=proposal.id,
        decision="approved",
        notes="Official evidence and classification reviewed.",
        actor="pytest-reviewer",
    )
    assert approved.status == "approved"

    registry = jurisdiction_registry_coverage(db_session)
    afghanistan = next(row for row in registry["entries"] if row["alpha2_code"] == "AF")
    hong_kong = next(row for row in registry["entries"] if row["alpha2_code"] == "HK")
    assert registry["summary"]["registry_entries"] == 4
    assert afghanistan["has_authority"] is True
    assert afghanistan["has_official_source"] is True
    assert afghanistan["has_reviewed_primary_authority"] is True
    assert afghanistan["has_reviewed_primary_source"] is True
    assert afghanistan["has_fresh_monitor"] is True
    assert afghanistan["has_verified_rule"] is True
    assert afghanistan["immigration_rule_status"] == "independent"
    assert afghanistan["approved_assessment"]["reviewed_by"] == "pytest-reviewer"
    assert afghanistan["coverage_ready"] is True
    assert afghanistan["missing"] == []
    assert "reviewed_primary_authority" in hong_kong["missing"]
    assert registry["release_gate"]["global_coverage_claim_ready"] is False

    replacement = propose_immigration_assessment(
        db_session,
        jurisdiction_id=jurisdictions["AF"].id,
        rule_relationship="unclear",
        parent_code=None,
        evidence_url="https://example.gov.af/immigration/update",
        evidence_title="Updated immigration responsibility notice",
        rationale="The updated material does not conclusively identify the administering jurisdiction.",
        actor="pytest-second-proposer",
    )
    replacement = review_immigration_assessment(
        db_session,
        assessment_id=replacement.id,
        decision="approved",
        notes="Reviewed, but the evidence remains inconclusive.",
        actor="pytest-second-reviewer",
    )
    db_session.refresh(approved)
    assert replacement.assessment_version == 2
    assert replacement.supersedes_assessment_id == approved.id
    assert approved.status == "superseded"
    updated = jurisdiction_registry_coverage(db_session)
    updated_afghanistan = next(row for row in updated["entries"] if row["alpha2_code"] == "AF")
    assert updated_afghanistan["coverage_ready"] is False
    assert "immigration_rule_assessment" in updated_afghanistan["missing"]


def test_registry_endpoint_reports_missing_release(client) -> None:
    response = client.get("/api/v1/global-intelligence/registry")
    assert response.status_code == 200
    assert response.json()["release"] is None
    assert response.json()["release_gate"]["global_coverage_claim_ready"] is False
