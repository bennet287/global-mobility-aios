from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    JurisdictionSourceCertification,
    OfficialSource,
    ShortageOccupationEntry,
    SourceSnapshot,
    now_utc,
)
from app.schemas import ShortageOccupationMaterializeRequest
from app.services.shortage_occupations import (
    lookup_shortage_occupation,
    materialize_shortage_occupation_snapshot,
    normalize_occupation,
    parse_austria_shortage_occupations,
)


NATIONAL_TEXT = """
Austria-wide shortage occupations
For the year 2026, the following occupations are deemed shortage professions:
1. Graduate nurses (Dipl. Gesundheits- und KrankenpflegerInnen)
Dipl. Krankenpfleger/in, Dipl. Gesundheits- und Krankenpfleger/-schwester
2. Train drivers (TriebfahrzeugführerInnen)
Triebfahrzeugführer/in
3. Restaurant chefs (Gaststättenköche/Gaststättenköchinnen)
Chef de partie, Koch/Köchin (Hotel- und Gastgewerbe), Sushikoch/-köchin
Help navigation:
Sitemap
""".strip()

REGIONAL_TEXT = """
Regional shortage occupations
The following shortage occupations apply only to certain federal provinces.
For the year 2026, the following oppcupations are deemed shortage professtions:
1. Bakers (BäckerInnen) (Kärnten, Oberösterreich, Salzburg)
Bäcker/in, Feinbäcker/in, Bäckermeister/in
2. Appreteurs and Other Textile Finishers (Appreteure/Appreteurinnen, andere TextilveredlerInnen) (ohne StoffdruckerInnen) (Vorarlberg)
Appreturarbeiter/in, Textilveredler/in, Textilchemiker/in
Top
Help navigation:
""".strip()


def _austria_source_snapshot(
    session: Session,
    *,
    scope: str,
    content_text: str,
) -> tuple[Jurisdiction, OfficialSource, SourceSnapshot]:
    jurisdiction = Jurisdiction(code="AT", name="Austria", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)

    slug = "austria-wide-shortage-occupations" if scope == "national" else "regional-shortage-occupations"
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="austria",
        domain="visa",
        name=f"Austria 2026 {scope} shortage occupations",
        url=f"https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/{slug}/",
        source_type="official_portal",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"pytest-{scope}-2026-content-hash",
        content_text=content_text,
        http_status=200,
        retrieval_method="http",
        parser_version="generic-html-v1",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return jurisdiction, source, snapshot


def _materialize_payload(snapshot: SourceSnapshot, scope: str) -> ShortageOccupationMaterializeRequest:
    return ShortageOccupationMaterializeRequest(
        source_snapshot_id=snapshot.id,
        year=2026,
        scope=scope,
        expected_group_count=3 if scope == "national" else 2,
    )


def test_national_snapshot_materialization_is_immutable_and_idempotent(db_session: Session) -> None:
    jurisdiction, source, snapshot = _austria_source_snapshot(
        db_session,
        scope="national",
        content_text=NATIONAL_TEXT,
    )

    first = materialize_shortage_occupation_snapshot(
        db_session,
        _materialize_payload(snapshot, "national"),
        actor="pytest-occupation-operator",
    )
    assert first.created_count == 3
    assert first.existing_count == 0
    assert first.entry_count == 3
    assert first.source_snapshot_content_hash == snapshot.content_hash
    assert [entry.source_ordinal for entry in first.entries] == [1, 2, 3]
    assert first.entries[0].occupation_group.startswith("Graduate nurses")
    assert first.entries[0].province_codes == []
    assert first.entries[0].official_source_id == source.id
    assert first.entries[0].jurisdiction_id == jurisdiction.id

    second = materialize_shortage_occupation_snapshot(
        db_session,
        _materialize_payload(snapshot, "national"),
        actor="pytest-occupation-operator",
    )
    assert second.created_count == 0
    assert second.existing_count == 3
    assert second.entry_set_sha256 == first.entry_set_sha256

    rows = db_session.exec(
        select(ShortageOccupationEntry).where(
            ShortageOccupationEntry.source_snapshot_id == snapshot.id
        )
    ).all()
    assert len(rows) == 3
    audits = db_session.exec(
        select(AuditLog).where(AuditLog.action == "shortage_occupation_snapshot_materialized")
    ).all()
    assert len(audits) == 1


def test_regional_lookup_requires_and_applies_exact_province(db_session: Session) -> None:
    jurisdiction, _, snapshot = _austria_source_snapshot(
        db_session,
        scope="regional",
        content_text=REGIONAL_TEXT,
    )
    materialize_shortage_occupation_snapshot(
        db_session,
        _materialize_payload(snapshot, "regional"),
        actor="pytest-occupation-operator",
    )

    province_missing = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation="Bäcker/in",
    )
    assert province_missing.status == "province_required"
    assert province_missing.list_applicability is None

    applicable = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation="Bäcker/in",
        province_code="at-2",
    )
    assert applicable.status == "matched"
    assert applicable.list_applicability is True
    assert applicable.province_code == "AT-2"
    assert applicable.matches[0].province_codes == ["AT-2", "AT-4", "AT-5"]

    not_applicable = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation="Bäcker/in",
        province_code="AT-9",
    )
    assert not_applicable.status == "not_applicable_in_province"
    assert not_applicable.list_applicability is False


def test_lookup_reports_pending_certification_without_converting_it_to_eligibility(db_session: Session) -> None:
    jurisdiction, source, snapshot = _austria_source_snapshot(
        db_session,
        scope="national",
        content_text=NATIONAL_TEXT,
    )
    materialize_shortage_occupation_snapshot(
        db_session,
        _materialize_payload(snapshot, "national"),
        actor="pytest-occupation-operator",
    )
    certification = JurisdictionSourceCertification(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=uuid4(),
        regulatory_authority_id=uuid4(),
        official_source_id=source.id,
        certification_version=1,
        certification_scope="supplemental_visa",
        coverage_domains_json='["visa"]',
        evidence_notes="Pending pytest structured occupation source.",
        status="pending_review",
        proposed_by="pytest-proposer",
    )
    db_session.add(certification)
    db_session.commit()

    pending = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation="Train drivers",
    )
    assert pending.status == "matched"
    assert pending.list_applicability is True
    assert pending.governance_ready is False
    assert pending.certification_statuses[str(source.id)] == "pending_review"
    assert "does not establish case eligibility" in pending.warning

    certification.status = "approved"
    certification.reviewed_by = "pytest-independent-reviewer"
    certification.reviewed_at = now_utc()
    certification.review_notes = "Approved fixture only."
    db_session.add(certification)
    db_session.commit()

    approved = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation="Triebfahrzeugführer/in",
    )
    assert approved.governance_ready is True
    assert approved.certification_statuses[str(source.id)] == "approved"
    assert approved.list_applicability is True


def test_lookup_rejects_unknown_austrian_province_code(db_session: Session) -> None:
    jurisdiction, _, snapshot = _austria_source_snapshot(
        db_session,
        scope="regional",
        content_text=REGIONAL_TEXT,
    )
    materialize_shortage_occupation_snapshot(
        db_session,
        _materialize_payload(snapshot, "regional"),
        actor="pytest-occupation-operator",
    )
    try:
        lookup_shortage_occupation(
            db_session,
            jurisdiction_id=jurisdiction.id,
            year=2026,
            occupation="Bäcker/in",
            province_code="AT-99",
        )
    except ValueError as exc:
        assert "AT-1 through AT-9" in str(exc)
    else:
        raise AssertionError("Expected an unknown Austrian province code to fail closed")


def test_lookup_fails_closed_when_exact_alias_matches_multiple_groups(db_session: Session) -> None:
    text = """
Austria-wide shortage occupations
For the year 2026, the following occupations are deemed shortage professions:
1. First technical group (Erste Gruppe)
Techniker/in, Erste Fachkraft
2. Second technical group (Zweite Gruppe)
Techniker/in, Zweite Fachkraft
Help navigation:
""".strip()
    jurisdiction, _, snapshot = _austria_source_snapshot(
        db_session,
        scope="national",
        content_text=text,
    )
    materialize_shortage_occupation_snapshot(
        db_session,
        ShortageOccupationMaterializeRequest(
            source_snapshot_id=snapshot.id,
            year=2026,
            scope="national",
            expected_group_count=2,
        ),
        actor="pytest-occupation-operator",
    )

    result = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation="Techniker/in",
    )
    assert result.status == "ambiguous"
    assert result.list_applicability is None
    assert result.match_count == 2


def test_materialization_requires_operator_pinned_group_count(db_session: Session) -> None:
    _, _, snapshot = _austria_source_snapshot(
        db_session,
        scope="national",
        content_text=NATIONAL_TEXT,
    )
    try:
        materialize_shortage_occupation_snapshot(
            db_session,
            ShortageOccupationMaterializeRequest(
                source_snapshot_id=snapshot.id,
                year=2026,
                scope="national",
                expected_group_count=64,
            ),
            actor="pytest-occupation-operator",
        )
    except ValueError as exc:
        assert "operator-pinned expected count" in str(exc)
    else:
        raise AssertionError("Expected mismatched structural count to fail before materialization")
    assert db_session.exec(select(ShortageOccupationEntry)).all() == []


def test_parser_rejects_wrong_year_and_noncontiguous_source_ordinals() -> None:
    snapshot_id = uuid4()
    try:
        parse_austria_shortage_occupations(
            NATIONAL_TEXT,
            source_snapshot_id=snapshot_id,
            year=2025,
            scope="national",
        )
    except ValueError as exc:
        assert "does not declare" in str(exc)
    else:
        raise AssertionError("Expected wrong-year extraction to fail closed")

    noncontiguous = NATIONAL_TEXT.replace(
        "2. Train drivers",
        "3. Train drivers",
    ).replace(
        "3. Restaurant chefs",
        "4. Restaurant chefs",
    )
    try:
        parse_austria_shortage_occupations(
            noncontiguous,
            source_snapshot_id=snapshot_id,
            year=2026,
            scope="national",
        )
    except ValueError as exc:
        assert "not contiguous" in str(exc)
    else:
        raise AssertionError("Expected noncontiguous source ordinals to fail closed")


def test_regional_parser_requires_recognized_province_list() -> None:
    invalid = REGIONAL_TEXT.replace(
        "(Kärnten, Oberösterreich, Salzburg)",
        "(Unknown Province)",
    )
    try:
        parse_austria_shortage_occupations(
            invalid,
            source_snapshot_id=uuid4(),
            year=2026,
            scope="regional",
        )
    except ValueError as exc:
        assert "recognized Austrian province list" in str(exc)
    else:
        raise AssertionError("Expected unknown regional province evidence to fail closed")


def test_normalization_handles_source_dash_and_spacing_variants_without_semantic_guessing() -> None:
    assert normalize_occupation("  Koch/Köchin – Hotel  ") == normalize_occupation("Koch / Köchin - Hotel")
    assert normalize_occupation("Train driver") != normalize_occupation("Triebfahrzeugführer/in")


def test_shortage_occupation_api_materializes_and_looks_up_exact_source_labels(
    client: TestClient,
    db_session: Session,
) -> None:
    jurisdiction, source, snapshot = _austria_source_snapshot(
        db_session,
        scope="regional",
        content_text=REGIONAL_TEXT,
    )
    certification = JurisdictionSourceCertification(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=uuid4(),
        regulatory_authority_id=uuid4(),
        official_source_id=source.id,
        certification_version=1,
        certification_scope="supplemental_visa",
        coverage_domains_json='["visa"]',
        evidence_notes="API fixture remains pending.",
        status="pending_review",
        proposed_by="pytest-proposer",
    )
    db_session.add(certification)
    db_session.commit()

    materialized = client.post(
        "/api/v1/regulatory-intelligence/shortage-occupations/materialize",
        json={
            "source_snapshot_id": str(snapshot.id),
            "year": 2026,
            "scope": "regional",
            "expected_group_count": 2,
        },
    )
    assert materialized.status_code == 201, materialized.text
    assert materialized.json()["entry_count"] == 2
    assert materialized.json()["source_snapshot_content_hash"] == snapshot.content_hash

    lookup = client.get(
        "/api/v1/regulatory-intelligence/shortage-occupations/lookup",
        params={
            "jurisdiction_id": str(jurisdiction.id),
            "year": 2026,
            "occupation": "Textilveredler/in",
            "province_code": "AT-8",
        },
    )
    assert lookup.status_code == 200, lookup.text
    payload = lookup.json()
    assert payload["status"] == "matched"
    assert payload["list_applicability"] is True
    assert payload["governance_ready"] is False
    assert payload["certification_statuses"][str(source.id)] == "pending_review"
    assert payload["matches"][0]["source_snapshot_content_hash"] == snapshot.content_hash


def test_0071_migration_declares_structured_occupation_invariants() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0071_structured_shortage_occupation_evidence.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "0071_structured_shortage_occupation_evidence"' in migration
    assert 'down_revision = "0070_pathway_version_evidence_provenance"' in migration
    assert "uq_shortage_occupation_snapshot_scope_ordinal" in migration
    assert "uq_shortage_occupation_entry_sha256" in migration
    assert "ck_shortage_occupation_scope" in migration
    assert "ck_shortage_occupation_year" in migration
    assert "ck_shortage_occupation_source_ordinal" in migration
