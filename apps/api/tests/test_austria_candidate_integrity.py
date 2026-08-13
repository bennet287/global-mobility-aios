from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    JurisdictionSourceCertification,
    Lead,
    LeadIntent,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    Profile,
    RegulatoryAuthority,
    ShortageOccupationEntry,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.eligibility_engine import evaluate_lead_eligibility
from app.services.pathway_catalogue import (
    _cost_explanation,
    generate_pathway_comparison,
    match_pathways_for_lead,
    pathway_version_read,
)
from app.services.shortage_occupations import resolve_austria_occupation


def _austria_fixture(session: Session) -> tuple[Jurisdiction, Lead, MobilityPathway, MobilityPathwayVersion]:
    jurisdiction = Jurisdiction(code="AT", name="Austria", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)
    authority = RegulatoryAuthority(
        jurisdiction_id=jurisdiction.id,
        name="Austrian Federal Immigration Authority",
        website_url="https://www.migration.gv.at/",
    )
    session.add(authority)
    session.commit()
    session.refresh(authority)

    sources: dict[str, tuple[OfficialSource, SourceSnapshot]] = {}
    for scope in ("core", "national", "regional"):
        source = OfficialSource(
            jurisdiction_id=jurisdiction.id,
            country="austria",
            domain="visa",
            name=f"Austria {scope} evidence",
            url=f"https://www.migration.gv.at/{scope}",
            regulatory_authority_id=authority.id,
            authority=authority.name,
            source_type="official_portal",
            active=True,
        )
        session.add(source)
        session.commit()
        session.refresh(source)
        snapshot = SourceSnapshot(
            official_source_id=source.id,
            url=source.url,
            content_hash=hashlib.sha256(scope.encode()).hexdigest(),
            content_text=f"Governed {scope} evidence.",
            status="captured",
            retrieval_method="http",
        )
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
        sources[scope] = source, snapshot

    fee_rule = VerifiedRule(
        country="austria",
        domain="visa",
        rule_key="at_rwr_application_fee",
        statement="The government application fee is EUR 218.",
        official_source_id=sources["core"][0].id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=sources["core"][1].id,
        confidence=0.99,
        active=True,
        approved_by="independent-reviewer",
        published_at=now_utc(),
    )
    session.add(fee_rule)
    for scope in ("national", "regional"):
        source, snapshot = sources[scope]
        session.add(JurisdictionSourceCertification(
            jurisdiction_id=jurisdiction.id,
            registry_entry_id=uuid4(),
            regulatory_authority_id=authority.id,
            official_source_id=source.id,
            certification_version=1,
            certification_scope=f"{scope}_occupation_list",
            coverage_domains_json='["visa"]',
            evidence_notes="Pending independent certification.",
            status="pending_review",
            proposed_by="fixture-proposer",
        ))
        labels = ["Software Engineer (Ing) (m./w.)", "Software Engineer (DI)"] if scope == "national" else [
            "Software Engineer (HTL)", "Software Engineer (DI)"
        ]
        for ordinal, label in enumerate(labels, start=1):
            session.add(ShortageOccupationEntry(
                jurisdiction_id=jurisdiction.id,
                official_source_id=source.id,
                source_snapshot_id=snapshot.id,
                year=2026,
                scope=scope,
                source_ordinal=ordinal,
                occupation_group=label,
                normalized_occupation_group=label.casefold(),
                occupation_aliases_json="[]",
                province_codes_json='["AT-9"]' if scope == "regional" else "[]",
                province_names_json='["Wien"]' if scope == "regional" else "[]",
                extraction_version="austria_migration_shortage_v1",
                entry_sha256=hashlib.sha256(f"{scope}:{ordinal}".encode()).hexdigest(),
                metadata_json="{}",
            ))

    skilled = MobilityPathway(
        pathway_key="at-rwr-skilled-worker-shortage-occupation",
        name="RWR Skilled Worker in Shortage Occupation",
        country="Austria",
        domain="visa",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="draft",
    )
    self_employed = MobilityPathway(
        pathway_key="at-self-employed-key-worker",
        name="Austria Self-employed Key Worker",
        country="Austria",
        domain="investment",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="active",
    )
    session.add(skilled)
    session.add(self_employed)
    session.flush()
    draft = MobilityPathwayVersion(
        pathway_id=skilled.id,
        version_number=4,
        lifecycle_status="draft",
        official_source_id=sources["core"][0].id,
        source_snapshot_id=sources["core"][1].id,
        verified_rule_ids_json=json.dumps([str(fee_rule.id)]),
        eligibility_criteria_json=json.dumps({
            "binding_job_offer_in_austria_required": True,
            "case_specific_eligibility_determined": False,
        }),
        required_documents_json=json.dumps(["passport", "qualification evidence", "employer declaration"]),
        costs_json=json.dumps({"currency": "EUR", "government_application_fee_eur": 21800}),
        processing_time_json="{}",
        risks_json=json.dumps([
            "The current 2026 shortage-occupation list is not yet represented by governed evidence in this pathway version.",
        ]),
    )
    published = MobilityPathwayVersion(
        pathway_id=self_employed.id,
        version_number=2,
        lifecycle_status="published",
        official_source_id=sources["core"][0].id,
        source_snapshot_id=sources["core"][1].id,
        published_at=now_utc(),
        required_documents_json=json.dumps([
            "business plan",
            "capital transfer evidence",
            "company agreements",
            "trade authorisations",
        ]),
        costs_json=json.dumps({"currency": "EUR", "government_application_fee_eur": 21800}),
    )
    session.add(draft)
    session.add(published)
    session.flush()
    for role, key in (
        ("core_route", "core"),
        ("national_occupation_list", "national"),
        ("regional_occupation_list", "regional"),
    ):
        source, snapshot = sources[key]
        session.add(MobilityPathwayVersionEvidence(
            pathway_version_id=draft.id,
            evidence_role=role,
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            required_for_publication=True,
            metadata_json=json.dumps({"year": 2026}) if key != "core" else "{}",
        ))
    lead = Lead(
        full_name="Round 5 Austria Test",
        email="round5@example.com",
        intent=LeadIntent.overseas_job,
        target_country="Austria",
        nationality="India",
        current_country="India",
        occupation_title="Software Engineer",
        years_experience=4,
        job_offer_status="none",
        qualification_recognition="unknown",
        german_level="A2",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    session.refresh(draft)
    return jurisdiction, lead, skilled, draft


def test_occupation_resolution_preserves_ambiguity_scope_and_governance(db_session: Session) -> None:
    jurisdiction, lead, _, _ = _austria_fixture(db_session)
    result = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation=lead.occupation_title,
        year=2026,
        province_code=None,
        has_job_offer=False,
    )
    assert result.match_quality == "AMBIGUOUS"
    assert result.national.scope == "national"
    assert result.regional.scope == "regional"
    assert result.national.match_quality == "AMBIGUOUS"
    assert result.regional.match_quality == "INSUFFICIENT_INFORMATION"
    assert result.regional.applicability_status == "NOT_ESTABLISHED"
    assert len(result.regional.candidates) == 2
    assert result.qualification_mapping == "UNRESOLVED"
    assert set(result.national.certification_statuses.values()) == {"pending_review"}
    assert result.establishes_pathway_eligibility is False


def test_case_specific_candidate_integrity_gaps_fee_and_simulation_audit(db_session: Session) -> None:
    _, lead, skilled, draft = _austria_fixture(db_session)
    result = match_pathways_for_lead(db_session, lead.id, include_draft_pathways=True)
    assert result["matches"][0]["pathway"].id == skilled.id
    assert result["matches"][0]["recommendation_status"] == "simulation_candidate"
    assert result["matches"][0]["compatibility_status"] == "INTERNAL_SIMULATION_ONLY"
    excluded = next(item for item in result["matches"] if item["recommendation_status"] == "excluded")
    assert "self-employment route" in excluded["exclusion_reasons"][0]
    assert excluded["match_score"] == 0.0

    gaps = result["matches"][0]["evidence_gaps"]
    assert len(gaps) > 0
    assert any(gap.category == "FACT" and gap.code == "binding_job_offer" and gap.status == "BLOCKING" for gap in gaps)
    assert any(gap.category == "DOCUMENT" and gap.code == "language_certificate" for gap in gaps)
    assert any(gap.category == "CERTIFICATION" and gap.status == "PENDING_REVIEW" for gap in gaps)

    comparison = generate_pathway_comparison(
        db_session,
        lead.id,
        actor="pytest-operator",
        include_draft_pathways=True,
        simulation_role="operator",
        simulation_context="Round 5 synthetic Austria candidate review",
    )
    assert comparison.primary is not None
    assert comparison.primary.pathway.current_version.id == draft.id
    assert comparison.primary.production_recommendation is False
    assert comparison.primary.cost.government_application_fee == 218
    assert comparison.primary.cost.government_application_fee_scope == "application_fee_only"
    assert comparison.primary.cost.government_application_fee_source_rule_id is not None
    assert comparison.primary.cost.one_time_total == 218
    assert "EUR 218.00" in comparison.primary.tradeoffs[0]
    assert all("21,800" not in value for value in comparison.primary.tradeoffs)
    assert comparison.primary.cost.estimated_total_status == "not_established"
    assert comparison.primary.processing_evidence_status == "not_established"
    assert comparison.primary.publication_ready is False
    assert comparison.primary.certification_statuses["national_occupation_list"] == "pending_review"
    assert comparison.primary.certification_statuses["regional_occupation_list"] == "pending_review"
    expected_readiness = (
        "The 2026 national/regional occupation evidence is linked to this pathway version "
        "but remains pending independent certification."
    )
    assert expected_readiness in comparison.primary.risk.declared_risks
    assert all("not yet represented" not in risk.casefold() for risk in comparison.primary.risk.declared_risks)
    assert len(comparison.primary.evidence_gaps) == 14
    assert len(comparison.primary.missing_evidence) == 14
    assert "14 case evidence gap(s)" in comparison.primary.explanation
    assert any("14 case evidence gap(s)" in value for value in comparison.primary.tradeoffs)
    assert comparison.profile_id is not None
    assert comparison.profile_version == 1
    assert db_session.get(Profile, comparison.profile_id) is not None
    excluded_comparison = next(item for item in comparison.alternatives if item.recommendation_status == "excluded")
    assert excluded_comparison.cost.one_time_total is None
    assert excluded_comparison.cost.components == {}
    assert all("21,800" not in value for value in excluded_comparison.tradeoffs)
    traces = comparison.primary.evidence_trace
    assert any(trace.trace_type == "verified_rule" and trace.certification_status == "approved" for trace in traces)
    occupation_traces = [trace for trace in traces if trace.evidence_role in {"national_occupation_list", "regional_occupation_list"}]
    assert len(occupation_traces) == 2
    assert {trace.certification_status for trace in occupation_traces} == {"pending_review"}
    assert all(trace.structured_pack_sha256 and len(trace.structured_pack_sha256) == 64 for trace in occupation_traces)
    assert all(trace.review_workspace_path for trace in occupation_traces)
    assert all(len(str(trace.source_snapshot_id)) == 36 for trace in occupation_traces)
    assert "eligible" not in comparison.summary.casefold()
    audit = db_session.exec(
        select(AuditLog).where(AuditLog.action == "internal_draft_pathway_simulation_generated")
    ).one()
    assert "Round 5 synthetic Austria candidate review" in (audit.reason or "")


def test_regional_resolution_requires_province_before_no_match(db_session: Session) -> None:
    jurisdiction, lead, _, _ = _austria_fixture(db_session)
    unknown = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation=lead.occupation_title,
        province_code=None,
        has_job_offer=False,
    )
    assert unknown.regional.match_quality == "INSUFFICIENT_INFORMATION"
    assert unknown.regional.candidates
    assert "cannot yet be determined" in unknown.regional.reason

    applicable = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation=lead.occupation_title,
        province_code="AT-9",
        has_job_offer=False,
    )
    assert applicable.regional.match_quality == "AMBIGUOUS"

    non_applicable = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation=lead.occupation_title,
        province_code="AT-1",
        has_job_offer=False,
    )
    assert non_applicable.regional.match_quality == "NO_MATCH"
    assert non_applicable.regional.candidates == []

    no_entries = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation="Marine Biologist",
        province_code=None,
        has_job_offer=False,
    )
    assert no_entries.regional.match_quality == "NO_MATCH"


def test_regional_software_aliases_remain_conditional_when_province_unknown(db_session: Session) -> None:
    jurisdiction, lead, _, _ = _austria_fixture(db_session)
    regional_rows = list(db_session.exec(
        select(ShortageOccupationEntry).where(
            ShortageOccupationEntry.jurisdiction_id == jurisdiction.id,
            ShortageOccupationEntry.scope == "regional",
        ).order_by(ShortageOccupationEntry.source_ordinal)
    ).all())
    regional_rows[0].occupation_group = "TechnikerInnen für Datenverarbeitung"
    regional_rows[0].normalized_occupation_group = "technikerinnen für datenverarbeitung"
    regional_rows[0].occupation_aliases_json = json.dumps([
        "Softwaretechniker/in (Softwareentwickler/in)",
    ])
    regional_rows[1].occupation_group = "Carpenters"
    regional_rows[1].normalized_occupation_group = "carpenters"
    regional_rows[1].occupation_aliases_json = "[]"
    db_session.add_all(regional_rows)
    db_session.commit()

    result = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation=lead.occupation_title,
        province_code=None,
        has_job_offer=False,
    )
    assert result.regional.match_quality == "INSUFFICIENT_INFORMATION"
    assert [item.occupation_group for item in result.regional.candidates] == [
        "TechnikerInnen für Datenverarbeitung",
    ]


def test_money_units_are_explicit_and_converted_once(db_session: Session) -> None:
    _, _, _, draft = _austria_fixture(db_session)

    fee_rule = db_session.exec(
        select(VerifiedRule).where(VerifiedRule.rule_key == "at_rwr_application_fee")
    ).one()
    fee_rule.statement = "The governed government application fee is EUR 175.50."
    draft.costs_json = json.dumps({"currency": "EUR", "government_application_fee_eur": 99999})
    db_session.add(fee_rule)
    db_session.add(draft)
    db_session.commit()
    governed = _cost_explanation(db_session, pathway_version_read(db_session, draft))
    assert governed.government_application_fee == 175.5
    assert governed.one_time_total == 175.5

    draft.verified_rule_ids_json = "[]"

    draft.costs_json = json.dumps({"currency": "EUR", "filing_fee": 218})
    db_session.add(draft)
    db_session.commit()
    major = _cost_explanation(db_session, pathway_version_read(db_session, draft))
    assert major.one_time_total == 218

    draft.costs_json = json.dumps({"currency": "EUR", "filing_fee_minor": 21800})
    db_session.add(draft)
    db_session.commit()
    minor = _cost_explanation(db_session, pathway_version_read(db_session, draft))
    assert minor.one_time_total == 218

    draft.costs_json = json.dumps({
        "currency": "EUR",
        "filing_fee": {"amount": 21800, "unit": "minor"},
    })
    db_session.add(draft)
    db_session.commit()
    typed_minor = _cost_explanation(db_session, pathway_version_read(db_session, draft))
    assert typed_minor.one_time_total == 218


def test_excluded_self_employment_documents_do_not_leak_into_work_preview(db_session: Session) -> None:
    _, lead, _, _ = _austria_fixture(db_session)
    result = evaluate_lead_eligibility(db_session, lead.id, include_draft_pathways=False)
    lowered = {value.casefold() for value in result["required_documents"]}
    assert "business plan" not in lowered
    assert "capital transfer evidence" not in lowered
    assert "company agreements" not in lowered
    assert "trade authorisations" not in lowered
    assert all("if available" not in value.casefold() for value in result["required_documents"])
    excluded = result["factors"]["pathway_evidence"][0]
    assert excluded["recommendation_status"] == "excluded"
    assert excluded["eligibility_preview_contribution"] == {
        "required_documents": [],
        "eligibility_requirements": [],
        "costs": {},
    }


def test_binding_job_offer_is_a_blocking_material_fact_not_an_optional_document(db_session: Session) -> None:
    _, lead, _, _ = _austria_fixture(db_session)
    result = evaluate_lead_eligibility(db_session, lead.id, include_draft_pathways=True)

    assert result["factors"]["eligibility_preview_version"] == "v13_10_2_15"
    requirements = result["factors"]["eligibility_requirements"]
    assert requirements == [{
        "code": "binding_austrian_job_offer",
        "label": "Binding Austrian job offer",
        "kind": "material_fact",
        "required": True,
        "blocking": True,
        "status": "missing",
        "detail": "A binding Austrian job offer is required and is currently missing.",
    }]
    assert all("job offer" not in document.casefold() for document in result["required_documents"])
    assert "employer declaration" in {document.casefold() for document in result["required_documents"]}
    excluded = next(
        item for item in result["factors"]["pathway_evidence"]
        if item["recommendation_status"] == "excluded"
    )
    assert excluded["eligibility_preview_contribution"]["required_documents"] == []
    assert excluded["eligibility_preview_contribution"]["eligibility_requirements"] == []
    assert excluded["eligibility_preview_contribution"]["costs"] == {}
