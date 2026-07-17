from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    JurisdictionCoverageEvidenceBatch,
    JurisdictionCoverageEvidenceBatchItem,
    OfficialSource,
    RegulatoryAuthority,
)
from app.services.coverage_evidence_batches import (
    coverage_batch_payload,
    create_coverage_evidence_batch,
    jurisdiction_coverage_worklist,
)
from app.services.jurisdiction_registry import (
    import_un_m49_registry,
    review_immigration_assessment,
    review_source_certification,
)


SAMPLE_M49 = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>002</td><td>Africa</td><td>014</td><td>Eastern Africa</td><td></td><td></td><td>Afghanistan</td><td>004</td><td>AF</td><td>AFG</td></tr>
<tr><td>001</td><td>World</td><td>142</td><td>Asia</td><td>145</td><td>Western Asia</td><td></td><td></td><td>State of Palestine</td><td>275</td><td>PS</td><td>PSE</td></tr>
</tbody></table></html>
"""


def _source_fixture(session: Session) -> tuple[Jurisdiction, RegulatoryAuthority, OfficialSource]:
    jurisdiction = session.exec(select(Jurisdiction).where(Jurisdiction.code == "AF")).one()
    authority = RegulatoryAuthority(
        jurisdiction_id=jurisdiction.id,
        name="Afghanistan Immigration Authority",
        website_url="https://example.gov.af/immigration",
    )
    session.add(authority)
    session.commit()
    session.refresh(authority)
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        regulatory_authority_id=authority.id,
        country="afghanistan",
        domain="visa",
        name="Afghanistan immigration portal",
        url="https://example.gov.af/immigration",
        source_type="government",
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return jurisdiction, authority, source


def test_coverage_evidence_batch_is_atomic_idempotent_and_review_gated(db_session: Session) -> None:
    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    _, authority, source = _source_fixture(db_session)
    items = [
        {
            "alpha2_code": "AF",
            "immigration_assessment": {
                "rule_relationship": "independent",
                "parent_code": None,
                "evidence_url": "https://example.gov.af/immigration/legal-framework",
                "evidence_title": "Official immigration legal framework",
                "rationale": "The official authority describes a directly administered immigration framework.",
                "official_source_id": source.id,
                "source_snapshot_id": None,
            },
            "source_certification": {
                "regulatory_authority_id": authority.id,
                "official_source_id": source.id,
                "coverage_domains": ["visa"],
                "evidence_notes": "Authority ownership, official status, and primary immigration scope were checked.",
            },
        }
    ]

    batch, created = create_coverage_evidence_batch(
        db_session,
        name="Afghanistan evidence package",
        notes="Prepared from the reviewed official authority portal for independent reviewer handoff.",
        items=items,
        actor="coverage-proposer",
    )
    assert created is True
    payload = coverage_batch_payload(db_session, batch)
    assert payload["status"] == "pending_review"
    assert payload["item_count"] == 1
    assert payload["immigration_assessment_count"] == 1
    assert payload["source_certification_count"] == 1
    assert payload["review_counts"]["pending_review"] == 2

    repeated, repeated_created = create_coverage_evidence_batch(
        db_session,
        name="Duplicate display name is ignored by idempotency",
        notes="The canonical evidence payload remains the same and must not duplicate proposals.",
        items=items,
        actor="coverage-proposer",
    )
    assert repeated_created is False
    assert repeated.id == batch.id
    assert len(db_session.exec(select(JurisdictionCoverageEvidenceBatch)).all()) == 1
    assert len(db_session.exec(select(JurisdictionCoverageEvidenceBatchItem)).all()) == 1

    item = payload["items"][0]
    review_immigration_assessment(
        db_session,
        assessment_id=item["immigration_assessment"]["id"],
        decision="approved",
        notes="Official evidence independently reviewed.",
        actor="coverage-reviewer",
    )
    review_source_certification(
        db_session,
        certification_id=item["source_certification"]["id"],
        decision="approved",
        notes="Authority and primary official source independently reviewed.",
        actor="coverage-reviewer",
    )
    approved = coverage_batch_payload(db_session, batch)
    assert approved["status"] == "approved"
    assert approved["review_counts"]["approved"] == 2


def test_coverage_batch_validation_rolls_back_every_item(db_session: Session) -> None:
    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    _, authority, source = _source_fixture(db_session)
    before_batches = len(db_session.exec(select(JurisdictionCoverageEvidenceBatch)).all())
    try:
        create_coverage_evidence_batch(
            db_session,
            name="Invalid duplicate batch",
            notes="This batch must fail atomically because the same jurisdiction appears twice.",
            items=[
                {
                    "alpha2_code": "AF",
                    "source_certification": {
                        "regulatory_authority_id": authority.id,
                        "official_source_id": source.id,
                        "coverage_domains": ["visa"],
                        "evidence_notes": "Valid first row that must still be rolled back after validation fails.",
                    },
                },
                {
                    "alpha2_code": "AF",
                    "immigration_assessment": {
                        "rule_relationship": "independent",
                        "parent_code": None,
                        "evidence_url": "https://example.gov.af/immigration/framework",
                        "evidence_title": "Duplicate jurisdiction evidence",
                        "rationale": "This duplicate row should prevent the complete batch from being persisted.",
                    },
                },
            ],
            actor="coverage-proposer",
        )
    except ValueError as exc:
        assert "duplicate jurisdiction AF" in str(exc)
    else:
        raise AssertionError("Duplicate jurisdiction batch should fail")
    assert len(db_session.exec(select(JurisdictionCoverageEvidenceBatch)).all()) == before_batches
    assert db_session.exec(select(JurisdictionCoverageEvidenceBatchItem)).all() == []


def test_coverage_worklist_prioritizes_specific_release_gaps(db_session: Session) -> None:
    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    result = jurisdiction_coverage_worklist(
        db_session,
        gap="immigration_rule_assessment",
        region="Asia",
        limit=10,
    )
    assert result["total"] >= 1
    assert all("immigration_rule_assessment" in row["missing"] for row in result["items"])
    assert all(row["region"] == "Asia" for row in result["items"])
    assert result["safety"]["creates_coverage_claim"] is False
    assert result["safety"]["human_review_required"] is True


def test_coverage_batch_api_exposes_worklist_and_idempotent_submission(client, db_session: Session) -> None:
    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    worklist = client.get(
        "/api/v1/global-intelligence/registry/coverage-worklist",
        params={"gap": "immigration_rule_assessment", "limit": 10},
    )
    assert worklist.status_code == 200
    assert worklist.json()["safety"]["human_review_required"] is True

    body = {
        "name": "API coverage batch",
        "notes": "Official evidence package prepared for independent reviewer validation.",
        "items": [
            {
                "alpha2_code": "AF",
                "immigration_assessment": {
                    "rule_relationship": "independent",
                    "parent_code": None,
                    "evidence_url": "https://example.gov.af/immigration/framework",
                    "evidence_title": "Official immigration framework",
                    "rationale": "Official evidence identifies the directly administering immigration authority.",
                },
            }
        ],
    }
    created = client.post("/api/v1/global-intelligence/registry/coverage-batches", json=body)
    assert created.status_code == 201
    assert created.json()["created"] is True
    assert created.json()["status"] == "pending_review"

    repeated = client.post("/api/v1/global-intelligence/registry/coverage-batches", json=body)
    assert repeated.status_code == 201
    assert repeated.json()["created"] is False
    assert repeated.json()["id"] == created.json()["id"]


def test_coverage_batch_can_atomically_onboard_source_monitor_and_pending_certification(
    db_session: Session,
) -> None:
    from app.models.domain import SourceMonitor

    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    items = [
        {
            "alpha2_code": "AF",
            "source_onboarding": {
                "authority_name": "Afghanistan Immigration Authority",
                "authority_type": "immigration_authority",
                "authority_website_url": "https://example.gov.af/immigration",
                "authority_domains": ["visa"],
                "source_name": "Afghanistan immigration portal",
                "source_url": "https://example.gov.af/immigration",
                "source_domain": "visa",
                "source_type": "government",
                "schedule_minutes": 1440,
                "fetch_method": "http",
                "allowed_domains": ["example.gov.af"],
                "max_redirects": 3,
                "parser_profile": "generic",
                "parser_config": {},
                "certification_domains": ["visa"],
                "evidence_notes": "Official ownership and primary immigration scope require independent reviewer certification.",
            },
        }
    ]

    batch, created = create_coverage_evidence_batch(
        db_session,
        name="Afghanistan source onboarding",
        notes="Onboard the authority, source, and monitor atomically before independent certification review.",
        items=items,
        actor="coverage-source-proposer",
    )
    assert created is True
    payload = coverage_batch_payload(db_session, batch)
    assert payload["source_onboarding_count"] == 1
    assert payload["source_certification_count"] == 1
    assert payload["status"] == "pending_review"
    item = payload["items"][0]
    assert item["source_onboarding"]["authority_name"] == "Afghanistan Immigration Authority"
    assert item["source_onboarding"]["source_url"] == "https://example.gov.af/immigration"
    assert item["source_onboarding"]["monitor_status"] == "active"
    assert item["source_certification"]["status"] == "pending_review"
    assert len(db_session.exec(select(RegulatoryAuthority)).all()) == 1
    assert len(db_session.exec(select(OfficialSource)).all()) == 1
    assert len(db_session.exec(select(SourceMonitor)).all()) == 1

    repeated, repeated_created = create_coverage_evidence_batch(
        db_session,
        name="Display name does not affect canonical idempotency",
        notes="The identical onboarding evidence must return the existing batch.",
        items=items,
        actor="coverage-source-proposer",
    )
    assert repeated_created is False
    assert repeated.id == batch.id
    assert len(db_session.exec(select(RegulatoryAuthority)).all()) == 1
    assert len(db_session.exec(select(OfficialSource)).all()) == 1
    assert len(db_session.exec(select(SourceMonitor)).all()) == 1

    with pytest.raises(ValueError, match="different from the proposer"):
        review_source_certification(
            db_session,
            certification_id=item["source_certification"]["id"],
            decision="approved",
            notes="Self-review must remain prohibited.",
            actor="coverage-source-proposer",
        )
    review_source_certification(
        db_session,
        certification_id=item["source_certification"]["id"],
        decision="approved",
        notes="Authority ownership and official source scope independently reviewed.",
        actor="coverage-source-reviewer",
    )
    assert coverage_batch_payload(db_session, batch)["status"] == "approved"


def test_source_onboarding_batch_rolls_back_all_rows_when_one_source_is_invalid(
    db_session: Session,
) -> None:
    from app.models.domain import SourceMonitor

    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    common = {
        "authority_type": "immigration_authority",
        "authority_domains": ["visa"],
        "source_domain": "visa",
        "source_type": "government",
        "schedule_minutes": 1440,
        "fetch_method": "http",
        "max_redirects": 3,
        "parser_profile": "generic",
        "parser_config": {},
        "certification_domains": ["visa"],
        "evidence_notes": "Official ownership and primary immigration scope require independent certification review.",
    }
    with pytest.raises(ValueError, match="source domain must be included"):
        create_coverage_evidence_batch(
            db_session,
            name="Atomic source onboarding validation",
            notes="A malformed second row must roll back the complete batch and every source record.",
            items=[
                {
                    "alpha2_code": "AF",
                    "source_onboarding": {
                        **common,
                        "authority_name": "Afghanistan Immigration Authority",
                        "authority_website_url": "https://example.gov.af/immigration",
                        "source_name": "Afghanistan immigration portal",
                        "source_url": "https://example.gov.af/immigration",
                        "allowed_domains": ["example.gov.af"],
                    },
                },
                {
                    "alpha2_code": "PS",
                    "source_onboarding": {
                        **common,
                        "authority_name": "Palestine Immigration Authority",
                        "authority_website_url": "https://example.ps/immigration",
                        "authority_domains": ["work"],
                        "source_name": "Palestine immigration portal",
                        "source_url": "https://example.ps/immigration",
                        "allowed_domains": ["example.ps"],
                    },
                },
            ],
            actor="coverage-source-proposer",
        )
    assert db_session.exec(select(JurisdictionCoverageEvidenceBatch)).all() == []
    assert db_session.exec(select(JurisdictionCoverageEvidenceBatchItem)).all() == []
    assert db_session.exec(select(RegulatoryAuthority)).all() == []
    assert db_session.exec(select(OfficialSource)).all() == []
    assert db_session.exec(select(SourceMonitor)).all() == []
