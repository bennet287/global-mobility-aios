from __future__ import annotations

from pathlib import Path
import json

from sqlmodel import Session, select

from app.models.domain import (
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    JurisdictionSourceCertification,
    SourceMonitor,
    SourceSnapshot,
    now_utc,
)
from app.schemas import InitialRuleAssertionCreateRequest, JurisdictionCoverageEvidenceBatchCreate
from app.services.coverage_baseline_capture import coverage_batch_baseline_status
from app.services.coverage_evidence_batches import coverage_batch_payload, create_coverage_evidence_batch
from app.services.initial_rule_assertions import propose_initial_rule_assertion
from app.services.jurisdiction_registry import (
    import_un_m49_registry,
    jurisdiction_coverage_receipt,
    propose_source_certification,
    review_immigration_assessment,
    review_source_certification,
)


SAMPLE_M49 = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>019</td><td>Americas</td><td>021</td><td>Northern America</td><td></td><td></td><td>Canada</td><td>124</td><td>CA</td><td>CAN</td></tr>
</tbody></table></html>
"""


def _primary_batch(session: Session):
    import_un_m49_registry(
        session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=1,
        require_global_scope=False,
    )
    batch, created = create_coverage_evidence_batch(
        session,
        name="Canada primary evidence",
        notes="Primary IRCC authority, source, and relationship evidence for supplemental-source testing.",
        items=[
            {
                "alpha2_code": "CA",
                "immigration_assessment": {
                    "rule_relationship": "independent",
                    "parent_code": None,
                    "evidence_url": "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate.html",
                    "evidence_title": "IRCC mandate",
                    "rationale": "The official mandate supports direct federal immigration administration in Canada.",
                },
                "source_onboarding": {
                    "authority_name": "Immigration, Refugees and Citizenship Canada",
                    "authority_type": "immigration_authority",
                    "authority_website_url": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
                    "authority_domains": ["visa"],
                    "source_name": "IRCC primary portal",
                    "source_url": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
                    "source_domain": "visa",
                    "source_type": "government",
                    "schedule_minutes": 1440,
                    "fetch_method": "http",
                    "allowed_domains": ["canada.ca"],
                    "max_redirects": 3,
                    "parser_profile": "generic",
                    "parser_config": {},
                    "certification_domains": ["visa"],
                    "evidence_notes": "Primary IRCC source requires independent review before use.",
                },
            }
        ],
        actor="primary-proposer",
    )
    assert created is True
    payload = coverage_batch_payload(session, batch)
    item = payload["items"][0]
    review_immigration_assessment(
        session,
        assessment_id=item["immigration_assessment"]["id"],
        decision="approved",
        notes="Relationship independently reviewed.",
        actor="primary-reviewer",
    )
    primary = review_source_certification(
        session,
        certification_id=item["source_certification"]["id"],
        decision="approved",
        notes="Primary IRCC source independently reviewed.",
        actor="primary-reviewer",
    )
    return batch, primary, item["immigration_assessment"]["id"]


def _supplemental_batch(session: Session):
    batch, created = create_coverage_evidence_batch(
        session,
        name="Canada supplemental visitor visa source",
        notes="Adds the official IRCC visitor-visa application page without replacing the primary IRCC certification.",
        items=[
            {
                "alpha2_code": "CA",
                "source_onboarding": {
                    "authority_name": "Immigration, Refugees and Citizenship Canada",
                    "authority_type": "immigration_authority",
                    "authority_website_url": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
                    "authority_domains": ["visa"],
                    "source_name": "IRCC visitor visa application",
                    "source_url": "https://ircc.canada.ca/english/information/applications/visa.asp",
                    "source_domain": "visa",
                    "source_type": "government",
                    "schedule_minutes": 1440,
                    "fetch_method": "http",
                    "allowed_domains": ["ircc.canada.ca"],
                    "max_redirects": 3,
                    "parser_profile": "generic",
                    "parser_config": {},
                    "certification_scope": "supplemental_visa",
                    "certification_domains": ["visa"],
                    "evidence_notes": "Official IRCC visitor-visa application page proposed as a supplemental visa-only source.",
                },
            }
        ],
        actor="supplemental-proposer",
    )
    assert created is True
    return batch


def test_supplemental_certification_preserves_primary_and_reuses_assessment(db_session: Session) -> None:
    _, primary, assessment_id = _primary_batch(db_session)
    supplemental_batch = _supplemental_batch(db_session)
    payload = coverage_batch_payload(db_session, supplemental_batch)
    item = payload["items"][0]

    assert item["immigration_assessment"]["id"] == assessment_id
    assert item["immigration_assessment"]["status"] == "approved"
    assert item["source_certification"]["certification_scope"] == "supplemental_visa"
    assert item["source_certification"]["status"] == "pending_review"

    supplemental = review_source_certification(
        db_session,
        certification_id=item["source_certification"]["id"],
        decision="approved",
        notes="Supplemental visa-only source independently reviewed.",
        actor="supplemental-reviewer",
    )
    db_session.refresh(primary)

    assert supplemental.status == "approved"
    assert supplemental.certification_scope == "supplemental_visa"
    assert primary.status == "approved"
    assert primary.certification_scope == "primary_immigration"
    assert supplemental.supersedes_certification_id is None

    approved = db_session.exec(
        select(JurisdictionSourceCertification).where(
            JurisdictionSourceCertification.jurisdiction_id == primary.jurisdiction_id,
            JurisdictionSourceCertification.status == "approved",
        )
    ).all()
    assert {row.certification_scope for row in approved} == {
        "primary_immigration",
        "supplemental_visa",
    }


def test_supplemental_source_can_supply_fresh_monitor_and_assertion_provenance(db_session: Session) -> None:
    _, primary, _ = _primary_batch(db_session)
    supplemental_batch = _supplemental_batch(db_session)
    item_payload = coverage_batch_payload(db_session, supplemental_batch)["items"][0]
    review_source_certification(
        db_session,
        certification_id=item_payload["source_certification"]["id"],
        decision="approved",
        notes="Supplemental source independently reviewed.",
        actor="supplemental-reviewer",
    )

    item = db_session.get(JurisdictionCoverageEvidenceBatchItem, item_payload["id"])
    assert item is not None and item.source_monitor_id and item.official_source_id
    monitor = db_session.get(SourceMonitor, item.source_monitor_id)
    assert monitor is not None
    monitor.status = "active"
    monitor.last_checked_at = now_utc()
    db_session.add(monitor)
    snapshot = SourceSnapshot(
        official_source_id=item.official_source_id,
        url="https://ircc.canada.ca/english/information/applications/visa.asp",
        content_hash="supplemental-snapshot-hash",
        content_text="Application for a Visitor Visa (Temporary Resident Visa - TRV).",
        http_status=200,
        retrieval_method="http",
        status="baseline",
    )
    db_session.add(snapshot)
    db_session.commit()

    status = coverage_batch_baseline_status(db_session, supplemental_batch.id)
    assert status["baseline_ready"] == 1
    receipt = jurisdiction_coverage_receipt(db_session, primary.jurisdiction_id)
    assert receipt["gates"]["reviewed_primary_authority"] is True
    assert receipt["gates"]["reviewed_primary_source"] is True
    assert receipt["gates"]["fresh_monitor"] is True
    assert receipt["gates"]["verified_rule"] is False

    assertion, created = propose_initial_rule_assertion(
        db_session,
        batch_id=supplemental_batch.id,
        payload=InitialRuleAssertionCreateRequest(
            alpha2_code="CA",
            domain="visa",
            title="Canada visitor visa application page",
            rule_key="canada_visitor_visa_application_page",
            statement="IRCC publishes an official application page for a Canadian visitor visa.",
            rationale="The statement is limited to the exact service identified by the immutable source snapshot.",
            evidence_excerpt="Application for a Visitor Visa (Temporary Resident Visa - TRV).",
            confidence=0.95,
        ),
        actor="assertion-proposer",
    )
    assert created is True
    assert assertion.official_source_id == item.official_source_id
    assert assertion.source_snapshot_id == snapshot.id


def test_supplemental_batch_requires_existing_approved_primary_certification(db_session: Session) -> None:
    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=1,
        require_global_scope=False,
    )
    try:
        _supplemental_batch(db_session)
    except ValueError as exc:
        assert "requires an approved primary immigration certification" in str(exc)
    else:
        raise AssertionError("Supplemental source onboarding unexpectedly succeeded without an approved primary certification")


def test_supplemental_batch_requires_existing_approved_relationship(db_session: Session) -> None:
    import_un_m49_registry(
        db_session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=1,
        require_global_scope=False,
    )
    primary_batch, _ = create_coverage_evidence_batch(
        db_session,
        name="Canada primary source only",
        notes="Primary source certification is approved while the relationship remains pending for safety testing.",
        items=[
            {
                "alpha2_code": "CA",
                "immigration_assessment": {
                    "rule_relationship": "independent",
                    "parent_code": None,
                    "evidence_url": "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate.html",
                    "evidence_title": "IRCC mandate",
                    "rationale": "Relationship proposal remains pending for this negative test.",
                },
                "source_onboarding": {
                    "authority_name": "Immigration, Refugees and Citizenship Canada",
                    "authority_type": "immigration_authority",
                    "authority_website_url": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
                    "authority_domains": ["visa"],
                    "source_name": "IRCC primary portal",
                    "source_url": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
                    "source_domain": "visa",
                    "source_type": "government",
                    "schedule_minutes": 1440,
                    "fetch_method": "http",
                    "allowed_domains": ["canada.ca"],
                    "max_redirects": 3,
                    "parser_profile": "generic",
                    "parser_config": {},
                    "certification_domains": ["visa"],
                    "evidence_notes": "Primary source certification negative-test evidence.",
                },
            }
        ],
        actor="primary-proposer",
    )
    primary_item = coverage_batch_payload(db_session, primary_batch)["items"][0]
    review_source_certification(
        db_session,
        certification_id=primary_item["source_certification"]["id"],
        decision="approved",
        notes="Primary source independently reviewed while relationship remains pending.",
        actor="primary-reviewer",
    )

    try:
        _supplemental_batch(db_session)
    except ValueError as exc:
        assert "requires an approved immigration assessment" in str(exc)
    else:
        raise AssertionError("Supplemental source onboarding unexpectedly succeeded without an approved relationship")



def test_multiple_supplemental_sources_have_isolated_review_lineages(
    db_session: Session,
) -> None:
    """Independent supplemental sources must never supersede each other."""

    _, primary, _ = _primary_batch(db_session)

    # Source A: establish one already-approved supplemental source.
    batch_a = _supplemental_batch(db_session)
    item_a = coverage_batch_payload(
        db_session,
        batch_a,
    )["items"][0]

    source_a = review_source_certification(
        db_session,
        certification_id=item_a["source_certification"]["id"],
        decision="approved",
        notes="Supplemental source A independently reviewed.",
        actor="supplemental-reviewer-a",
    )

    assert source_a.status == "approved"
    assert source_a.certification_version == 1
    assert source_a.supersedes_certification_id is None

    def create_other_supplemental(
        *,
        label: str,
        source_name: str,
        source_url: str,
        hostname: str,
        actor: str,
    ):
        batch, created = create_coverage_evidence_batch(
            db_session,
            name=f"Canada supplemental {label}",
            notes=(
                "Independent supplemental source used to prove "
                "source-scoped certification lineage."
            ),
            items=[
                {
                    "alpha2_code": "CA",
                    "source_onboarding": {
                        "authority_name":
                            "Immigration, Refugees and Citizenship Canada",
                        "authority_type": "immigration_authority",
                        "authority_website_url":
                            "https://www.canada.ca/en/"
                            "immigration-refugees-citizenship.html",
                        "authority_domains": ["visa"],
                        "source_name": source_name,
                        "source_url": source_url,
                        "source_domain": "visa",
                        "source_type": "government",
                        "schedule_minutes": 1440,
                        "fetch_method": "http",
                        "allowed_domains": [hostname],
                        "max_redirects": 3,
                        "parser_profile": "generic",
                        "parser_config": {},
                        "certification_scope":
                            "supplemental_visa",
                        "certification_domains": ["visa"],
                        "evidence_notes": (
                            "Independent supplemental visa source "
                            "requires separate source certification."
                        ),
                    },
                }
            ],
            actor=actor,
        )

        assert created is True

        return (
            batch,
            coverage_batch_payload(
                db_session,
                batch,
            )["items"][0],
        )

    # Sources B and C must be allowed to coexist while both are pending.
    batch_b, item_b = create_other_supplemental(
        label="services source B",
        source_name="IRCC services source B",
        source_url=(
            "https://www.canada.ca/en/"
            "immigration-refugees-citizenship/services/"
            "visit-canada.html"
        ),
        hostname="www.canada.ca",
        actor="supplemental-proposer-b",
    )

    batch_c, item_c = create_other_supplemental(
        label="services source C",
        source_name="IRCC services source C",
        source_url=(
            "https://www.canada.ca/en/"
            "immigration-refugees-citizenship/services/"
            "application.html"
        ),
        hostname="www.canada.ca",
        actor="supplemental-proposer-c",
    )

    del batch_b, batch_c

    source_b_id = item_b["source_certification"]["id"]
    source_c_id = item_c["source_certification"]["id"]

    source_b_pending = db_session.get(
        JurisdictionSourceCertification,
        source_b_id,
    )
    source_c = db_session.get(
        JurisdictionSourceCertification,
        source_c_id,
    )

    assert source_b_pending is not None
    assert source_c is not None

    # Each independent source begins its own version lineage.
    assert source_b_pending.certification_version == 1
    assert source_c.certification_version == 1
    assert source_b_pending.status == "pending_review"
    assert source_c.status == "pending_review"
    assert source_b_pending.supersedes_certification_id is None
    assert source_c.supersedes_certification_id is None

    # Simulate the exact pre-hardening legacy corruption:
    # B incorrectly points at approved source A.
    source_b_pending.supersedes_certification_id = source_a.id
    db_session.add(source_b_pending)
    db_session.commit()

    source_b = review_source_certification(
        db_session,
        certification_id=source_b_pending.id,
        decision="approved",
        notes=(
            "Supplemental source B independently reviewed; "
            "legacy cross-source lineage must be discarded."
        ),
        actor="supplemental-reviewer-b",
    )

    db_session.refresh(source_a)
    db_session.refresh(source_c)
    db_session.refresh(primary)

    # Approving B must not alter A or pending C.
    assert source_a.status == "approved"
    assert source_b.status == "approved"
    assert source_c.status == "pending_review"
    assert primary.status == "approved"

    # Legacy cross-source pointer was removed rather than preserved.
    assert source_b.supersedes_certification_id is None

    assert source_a.official_source_id != source_b.official_source_id
    assert source_b.official_source_id != source_c.official_source_id
    assert source_a.official_source_id != source_c.official_source_id

    # A later version of source B must supersede only B v1.
    source_b_v2 = propose_source_certification(
        db_session,
        jurisdiction_id=source_b.jurisdiction_id,
        regulatory_authority_id=source_b.regulatory_authority_id,
        official_source_id=source_b.official_source_id,
        coverage_domains=["visa"],
        evidence_notes=(
            "Second independently reviewed version of source B."
        ),
        actor="supplemental-proposer-b-v2",
        certification_scope="supplemental_visa",
    )

    assert source_b_v2.certification_version == 2
    assert source_b_v2.status == "pending_review"
    assert source_b_v2.supersedes_certification_id == source_b.id

    source_b_v2 = review_source_certification(
        db_session,
        certification_id=source_b_v2.id,
        decision="approved",
        notes="Source B version 2 independently reviewed.",
        actor="supplemental-reviewer-b-v2",
    )

    db_session.refresh(source_a)
    db_session.refresh(source_b)
    db_session.refresh(source_c)
    db_session.refresh(primary)

    assert source_a.status == "approved"
    assert source_b.status == "superseded"
    assert source_b_v2.status == "approved"
    assert source_c.status == "pending_review"
    assert primary.status == "approved"

    assert source_b_v2.supersedes_certification_id == source_b.id

    # No cross-source certification was mutated by B's v2 review.
    assert source_a.supersedes_certification_id is None
    assert source_c.supersedes_certification_id is None


def test_canada_supplemental_pack_is_pending_review_and_primary_safe() -> None:
    root = Path(__file__).resolve().parents[3]
    pack_path = root / "knowledge" / "global_coverage" / "tranches" / "v10_21_2_canada_supplemental_visa.json"
    raw = json.loads(pack_path.read_text(encoding="utf-8"))
    batch = JurisdictionCoverageEvidenceBatchCreate.model_validate(raw["batch"])
    assert raw["review_status"] == "pending_independent_review"
    assert raw["coverage_claim_ready"] is False
    assert raw["safety"]["auto_approves_evidence"] is False
    assert raw["safety"]["supersedes_primary_certification"] is False
    assert len(batch.items) == 1
    onboarding = batch.items[0].source_onboarding
    assert onboarding is not None
    assert onboarding.certification_scope == "supplemental_visa"
    assert onboarding.source_url == "https://ircc.canada.ca/english/information/applications/visa.asp"
    assert onboarding.allowed_domains == ["ircc.canada.ca"]


def test_supplemental_submission_script_preserves_review_boundaries() -> None:
    root = Path(__file__).resolve().parents[3]
    script = (root / "scripts" / "Submit-SupplementalCoverageSource.ps1").read_text(encoding="utf-8")
    assert "SupportsShouldProcess = $true" in script
    assert "supersedes_primary_certification" in script
    assert "pending_independent_review" in script
    assert "Invoke-RestMethod -Method Post" in script
    assert "Approve" not in script
