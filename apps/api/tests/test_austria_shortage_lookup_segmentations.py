from __future__ import annotations

import json
from uuid import uuid4

from sqlmodel import Session

from app.models.domain import (
    Jurisdiction,
    OfficialSource,
    ShortageOccupationEntry,
    SourceSnapshot,
)
from app.services.shortage_occupations import (
    EXTRACTION_VERSION,
    lookup_shortage_occupation,
    parse_austria_shortage_occupations,
    resolve_austria_occupation,
)


PHYSICIANS_COMPOSITE = (
    "Facharzt/ ärztin (Kinder- und Jugendchirurgie)"
    "Facharzt/ ärztin (Innere Medizin und Pneumologie)"
)
PHYSICIANS_PNEUMOLOGY = "Facharzt/ ärztin (Innere Medizin und Pneumologie)"

MECHANICAL_COMPOSITE = (
    "Werkzeugkonstrukteur/in (DI). Gebäudetechniker/in "
    "(Heizung/Lüftung/Sanitär) (DI)"
)
MECHANICAL_BUILDING = "Gebäudetechniker/in (Heizung/Lüftung/Sanitär) (DI)"


def _seed_source_faithful_rows(
    session: Session,
) -> tuple[Jurisdiction, list[ShortageOccupationEntry]]:
    jurisdiction = Jurisdiction(
        code="AT",
        name="Austria",
        jurisdiction_type="country",
        active=True,
    )
    session.add(jurisdiction)
    session.flush()

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="austria",
        domain="visa",
        name="Migration.gv.at - Austria-wide shortage occupations",
        url=(
            "https://www.migration.gv.at/en/types-of-immigration/"
            "permanent-immigration/austria-wide-shortage-occupations/"
        ),
        source_type="government",
        active=True,
    )
    session.add(source)
    session.flush()

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="a" * 64,
        content_text="pytest immutable source snapshot",
        http_status=200,
        retrieval_method="http",
        parser_version="pytest",
        status="baseline",
    )
    session.add(snapshot)
    session.flush()

    rows = [
        ShortageOccupationEntry(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            year=2026,
            scope="national",
            source_ordinal=1,
            occupation_group="Physicians (Ärzte/Ärztinnen)",
            normalized_occupation_group="physicians (ärzte/ärztinnen)",
            occupation_aliases_json=json.dumps([PHYSICIANS_COMPOSITE], ensure_ascii=False),
            province_codes_json="[]",
            province_names_json="[]",
            extraction_version=EXTRACTION_VERSION,
            entry_sha256="1" * 64,
            metadata_json="{}",
        ),
        ShortageOccupationEntry(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            year=2026,
            scope="national",
            source_ordinal=2,
            occupation_group=(
                "Graduate mechanical engineers "
                "(DiplomingenieurInnen für Maschinenbau)"
            ),
            normalized_occupation_group=(
                "graduate mechanical engineers "
                "(diplomingenieurinnen für maschinenbau)"
            ),
            occupation_aliases_json=json.dumps([MECHANICAL_COMPOSITE], ensure_ascii=False),
            province_codes_json="[]",
            province_names_json="[]",
            extraction_version=EXTRACTION_VERSION,
            entry_sha256="2" * 64,
            metadata_json="{}",
        ),
        ShortageOccupationEntry(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            year=2026,
            scope="national",
            source_ordinal=3,
            occupation_group="Synthetic control group",
            normalized_occupation_group="synthetic control group",
            occupation_aliases_json=json.dumps(
                ["First source label (DI). Second source label (DI)"],
                ensure_ascii=False,
            ),
            province_codes_json="[]",
            province_names_json="[]",
            extraction_version=EXTRACTION_VERSION,
            entry_sha256="3" * 64,
            metadata_json="{}",
        ),
    ]
    session.add_all(rows)
    session.commit()
    session.refresh(jurisdiction)
    for row in rows:
        session.refresh(row)
    return jurisdiction, rows


def test_lookup_segments_only_known_source_boundaries_without_mutating_evidence(
    db_session: Session,
) -> None:
    jurisdiction, rows = _seed_source_faithful_rows(db_session)
    original_alias_json = [row.occupation_aliases_json for row in rows]
    original_hashes = [row.entry_sha256 for row in rows]

    physicians = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation=PHYSICIANS_PNEUMOLOGY,
    )
    mechanical = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation=MECHANICAL_BUILDING,
    )

    assert physicians.status == "matched"
    assert physicians.match_count == 1
    assert physicians.matches[0].occupation_group == "Physicians (Ärzte/Ärztinnen)"
    assert mechanical.status == "matched"
    assert mechanical.match_count == 1
    assert mechanical.matches[0].occupation_group.startswith("Graduate mechanical engineers")

    db_session.expire_all()
    persisted = [db_session.get(ShortageOccupationEntry, row.id) for row in rows]
    assert [row.occupation_aliases_json for row in persisted if row] == original_alias_json
    assert [row.entry_sha256 for row in persisted if row] == original_hashes


def test_resolver_treats_lookup_only_segments_as_normalized_exact(
    db_session: Session,
) -> None:
    jurisdiction, _ = _seed_source_faithful_rows(db_session)

    physicians = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation=PHYSICIANS_PNEUMOLOGY,
        year=2026,
    )
    mechanical = resolve_austria_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        occupation=MECHANICAL_BUILDING,
        year=2026,
    )

    assert physicians.match_quality == "NORMALIZED_EXACT"
    assert physicians.national.match_quality == "NORMALIZED_EXACT"
    assert physicians.establishes_pathway_eligibility is False
    assert mechanical.match_quality == "NORMALIZED_EXACT"
    assert mechanical.national.match_quality == "NORMALIZED_EXACT"
    assert mechanical.establishes_pathway_eligibility is False


def test_unregistered_period_boundary_is_not_generically_split(
    db_session: Session,
) -> None:
    jurisdiction, _ = _seed_source_faithful_rows(db_session)

    result = lookup_shortage_occupation(
        db_session,
        jurisdiction_id=jurisdiction.id,
        year=2026,
        occupation="Second source label (DI)",
    )

    assert result.status == "not_found"
    assert result.match_count == 0


def test_parser_keeps_source_native_composite_aliases_byte_faithful() -> None:
    snapshot_id = uuid4()
    source_text = "\n".join(
        [
            "For the year 2026, the following occupations are deemed shortage professions:",
            "1. Physicians (Ärzte/Ärztinnen)",
            PHYSICIANS_COMPOSITE,
            "2. Graduate mechanical engineers (DiplomingenieurInnen für Maschinenbau)",
            MECHANICAL_COMPOSITE,
            "Help navigation:",
        ]
    )

    parsed = parse_austria_shortage_occupations(
        source_text,
        source_snapshot_id=snapshot_id,
        year=2026,
        scope="national",
    )

    assert len(parsed) == 2
    assert parsed[0].occupation_aliases == (PHYSICIANS_COMPOSITE,)
    assert parsed[1].occupation_aliases == (MECHANICAL_COMPOSITE,)
    assert parsed[0].entry_sha256
    assert parsed[1].entry_sha256
