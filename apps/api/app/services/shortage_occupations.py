from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    JurisdictionSourceCertification,
    OfficialSource,
    ShortageOccupationEntry,
    SourceSnapshot,
    now_utc,
)
from app.schemas import (
    OccupationResolutionRead,
    OccupationScopeAssessmentRead,
    ShortageOccupationEntryRead,
    ShortageOccupationLookupRead,
    ShortageOccupationMaterializationRead,
    ShortageOccupationMaterializeRequest,
)
from app.services.audit_log import record_audit


EXTRACTION_VERSION = "austria_migration_shortage_v1"
SUPPORTED_SCOPES = {"national", "regional"}

# Official Austrian federal-province codes (ISO 3166-2:AT).  The migration.gv.at
# regional list names provinces in German, so extraction never has to infer a
# province from free text.
AUSTRIA_PROVINCES = {
    "burgenland": ("AT-1", "Burgenland"),
    "kärnten": ("AT-2", "Kärnten"),
    "niederösterreich": ("AT-3", "Niederösterreich"),
    "oberösterreich": ("AT-4", "Oberösterreich"),
    "salzburg": ("AT-5", "Salzburg"),
    "steiermark": ("AT-6", "Steiermark"),
    "tirol": ("AT-7", "Tirol"),
    "vorarlberg": ("AT-8", "Vorarlberg"),
    "wien": ("AT-9", "Wien"),
}

_HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(\d{1,3})\.\s+(.+?)\s*$")
_YEAR_RE = re.compile(r"\bfor\s+the\s+year\s+(\d{4})\b", re.IGNORECASE)
_FINAL_PARENS_RE = re.compile(r"\(([^()]*)\)\s*$")
_STOP_MARKERS = {
    "help navigation:",
    "mainnavigation:",
    "sub navigation:",
    "service",
    "search",
    "quickcheck",
    "footer:",
    "top",
}
_GENERIC_OCCUPATION_TOKENS = {
    "engineer", "engineers", "engineering", "technician", "technicians",
    "specialist", "specialists", "manager", "managers", "worker", "workers",
    "graduate", "graduates", "higher", "level", "training",
}
_DASH_TRANSLATION = str.maketrans({
    "–": "-",
    "—": "-",
    "−": "-",
    "‑": "-",
    "‒": "-",
})

# The immutable 2026 migration.gv.at snapshot contains two source-format
# boundaries where distinct occupation labels are rendered as one comma-delimited
# item.  Keep the source-derived v1 projection byte-for-byte faithful, and expand
# only the runtime lookup labels.  This must never be used by the materializer or
# entry hashing: the review evidence must continue to reflect the official text.
_SOURCE_ALIAS_LOOKUP_SEGMENTATIONS: dict[str, tuple[str, ...]] = {
    (
        "Facharzt/ ärztin (Kinder- und Jugendchirurgie)"
        "Facharzt/ ärztin (Innere Medizin und Pneumologie)"
    ): (
        "Facharzt/ ärztin (Kinder- und Jugendchirurgie)",
        "Facharzt/ ärztin (Innere Medizin und Pneumologie)",
    ),
    (
        "Werkzeugkonstrukteur/in (DI). Gebäudetechniker/in "
        "(Heizung/Lüftung/Sanitär) (DI)"
    ): (
        "Werkzeugkonstrukteur/in (DI)",
        "Gebäudetechniker/in (Heizung/Lüftung/Sanitär) (DI)",
    ),
}


@dataclass(frozen=True)
class ParsedShortageOccupation:
    source_ordinal: int
    occupation_group: str
    normalized_occupation_group: str
    occupation_aliases: tuple[str, ...]
    province_codes: tuple[str, ...]
    province_names: tuple[str, ...]
    entry_sha256: str


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def normalize_occupation(value: str) -> str:
    """Normalize only presentation differences; do not perform semantic matching."""
    normalized = unicodedata.normalize("NFKC", value or "").translate(_DASH_TRANSLATION)
    normalized = normalized.replace("\u00a0", " ").replace("\u202f", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip().casefold()
    normalized = re.sub(r"\s*([/,-])\s*", r"\1", normalized)
    return normalized


def _group_lookup_labels(value: str) -> set[str]:
    labels = {normalize_occupation(value)}
    english_prefix = re.split(r"\s+\(", value, maxsplit=1)[0].strip()
    if english_prefix:
        labels.add(normalize_occupation(english_prefix))
    return {label for label in labels if label}


def _lookup_alias_labels(values: Iterable[str]) -> set[str]:
    """Return source-faithful aliases plus explicit lookup-only segmentations."""
    labels: set[str] = set()
    for value in values:
        normalized = normalize_occupation(value)
        if normalized:
            labels.add(normalized)
        for segmented in _SOURCE_ALIAS_LOOKUP_SEGMENTATIONS.get(value, ()):
            segmented_normalized = normalize_occupation(segmented)
            if segmented_normalized:
                labels.add(segmented_normalized)
    return labels


def _split_top_level_commas(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in value:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            item = "".join(current).strip(" \t\r\n,;")
            if item:
                parts.append(item)
            current = []
        else:
            current.append(char)
    item = "".join(current).strip(" \t\r\n,;")
    if item:
        parts.append(item)
    return parts


def _province_payload(heading: str) -> tuple[str, tuple[str, ...], tuple[str, ...]] | None:
    match = _FINAL_PARENS_RE.search(heading)
    if not match:
        return None
    raw_names = [item.strip() for item in match.group(1).split(",") if item.strip()]
    if not raw_names:
        return None
    resolved: list[tuple[str, str]] = []
    for raw_name in raw_names:
        resolved_province = AUSTRIA_PROVINCES.get(normalize_occupation(raw_name))
        if resolved_province is None:
            return None
        resolved.append(resolved_province)
    group = heading[: match.start()].strip()
    return group, tuple(code for code, _ in resolved), tuple(name for _, name in resolved)


def _canonical_entry_hash(
    *,
    source_snapshot_id: UUID,
    year: int,
    scope: str,
    source_ordinal: int,
    occupation_group: str,
    occupation_aliases: Iterable[str],
    province_codes: Iterable[str],
) -> str:
    payload = {
        "extraction_version": EXTRACTION_VERSION,
        "source_snapshot_id": str(source_snapshot_id),
        "year": year,
        "scope": scope,
        "source_ordinal": source_ordinal,
        "occupation_group": occupation_group,
        "occupation_aliases": list(occupation_aliases),
        "province_codes": list(province_codes),
    }
    return hashlib.sha256(_dump(payload).encode("utf-8")).hexdigest()


def _entry_set_hash(entries: Iterable[ParsedShortageOccupation]) -> str:
    values = [entry.entry_sha256 for entry in entries]
    return hashlib.sha256(_dump(values).encode("utf-8")).hexdigest()


def shortage_occupation_projection_summary(
    session: Session,
    *,
    source_snapshot_id: UUID,
    year: int,
    scope: str,
) -> dict[str, Any]:
    """Return the deterministic identity of an already materialized projection.

    This helper never parses or creates rows. It verifies the persisted projection is
    internally consistent and returns the exact immutable identity that downstream
    pathway evidence must pin.
    """
    if scope not in SUPPORTED_SCOPES:
        raise ValueError("Shortage-occupation scope must be national or regional")
    rows = list(
        session.exec(
            select(ShortageOccupationEntry)
            .where(
                ShortageOccupationEntry.source_snapshot_id == source_snapshot_id,
                ShortageOccupationEntry.year == year,
                ShortageOccupationEntry.scope == scope,
            )
            .order_by(ShortageOccupationEntry.source_ordinal)
        ).all()
    )
    if not rows:
        raise ValueError(
            f"No structured shortage-occupation projection exists for snapshot {source_snapshot_id}, "
            f"year {year}, scope {scope}"
        )

    expected_ordinals = list(range(1, len(rows) + 1))
    actual_ordinals = [row.source_ordinal for row in rows]
    if actual_ordinals != expected_ordinals:
        raise ValueError("Structured shortage-occupation projection has non-contiguous source ordinals")

    jurisdiction_ids = {row.jurisdiction_id for row in rows}
    source_ids = {row.official_source_id for row in rows}
    extraction_versions = {row.extraction_version for row in rows}
    if len(jurisdiction_ids) != 1 or len(source_ids) != 1 or len(extraction_versions) != 1:
        raise ValueError("Structured shortage-occupation projection has inconsistent provenance")

    snapshot = session.get(SourceSnapshot, source_snapshot_id)
    if snapshot is None or not snapshot.content_hash:
        raise ValueError("Structured shortage-occupation projection snapshot provenance is unavailable")
    source_id = next(iter(source_ids))
    jurisdiction_id = next(iter(jurisdiction_ids))
    if snapshot.official_source_id != source_id:
        raise ValueError("Structured shortage-occupation projection source does not match its snapshot")
    source = session.get(OfficialSource, source_id)
    if source is None or source.jurisdiction_id != jurisdiction_id:
        raise ValueError("Structured shortage-occupation projection jurisdiction does not match its official source")

    values = [row.entry_sha256 for row in rows]
    entry_set_sha256 = hashlib.sha256(_dump(values).encode("utf-8")).hexdigest()
    return {
        "jurisdiction_id": jurisdiction_id,
        "official_source_id": source_id,
        "source_snapshot_id": source_snapshot_id,
        "source_snapshot_content_hash": snapshot.content_hash,
        "year": year,
        "scope": scope,
        "entry_count": len(rows),
        "entry_set_sha256": entry_set_sha256,
        "extraction_version": next(iter(extraction_versions)),
    }


def _validate_parser_source(
    jurisdiction: Jurisdiction,
    source: OfficialSource,
    *,
    scope: str,
) -> None:
    if jurisdiction.code.strip().upper() != "AT":
        raise ValueError("The supported shortage-occupation parser is restricted to Austria (AT)")
    if source.jurisdiction_id != jurisdiction.id:
        raise ValueError("Official source jurisdiction does not match its structured occupation evidence")
    hostname = (urlparse(source.url).hostname or "").lower().rstrip(".")
    if hostname != "migration.gv.at" and not hostname.endswith(".migration.gv.at"):
        raise ValueError("The supported shortage-occupation parser requires an official migration.gv.at source")
    path = urlparse(source.url).path.lower()
    expected_fragment = "austria-wide-shortage-occupations" if scope == "national" else "regional-shortage-occupations"
    if expected_fragment not in path:
        raise ValueError(f"Source URL does not match the requested {scope} shortage-occupation scope")


def parse_austria_shortage_occupations(
    content_text: str,
    *,
    source_snapshot_id: UUID,
    year: int,
    scope: str,
) -> list[ParsedShortageOccupation]:
    if scope not in SUPPORTED_SCOPES:
        raise ValueError("Shortage-occupation scope must be national or regional")
    if not content_text or not content_text.strip():
        raise ValueError("Source snapshot has no text to structure")

    declared_years = {int(match.group(1)) for match in _YEAR_RE.finditer(content_text)}
    if year not in declared_years:
        raise ValueError(f"Source snapshot does not declare the requested shortage-occupation year {year}")
    if len(declared_years) != 1:
        raise ValueError("Source snapshot contains multiple declared shortage-occupation years; review is required")

    groups: list[tuple[int, str, list[str]]] = []
    current_ordinal: int | None = None
    current_heading: str | None = None
    detail_lines: list[str] = []

    def flush() -> None:
        nonlocal current_ordinal, current_heading, detail_lines
        if current_ordinal is None or current_heading is None:
            return
        groups.append((current_ordinal, current_heading, detail_lines[:]))
        current_ordinal = None
        current_heading = None
        detail_lines = []

    for raw_line in content_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush()
            current_ordinal = int(heading_match.group(1))
            current_heading = heading_match.group(2).strip()
            continue
        if current_ordinal is not None:
            if normalize_occupation(line) in _STOP_MARKERS:
                flush()
                break
            detail_lines.append(line)

    flush()
    if not groups:
        raise ValueError("No numbered shortage-occupation groups were found in the immutable snapshot")

    ordinals = [ordinal for ordinal, _, _ in groups]
    expected_ordinals = list(range(1, len(groups) + 1))
    if ordinals != expected_ordinals:
        raise ValueError("Shortage-occupation source ordinals are not contiguous from 1; review is required")

    parsed: list[ParsedShortageOccupation] = []
    for ordinal, heading, raw_details in groups:
        province_codes: tuple[str, ...] = ()
        province_names: tuple[str, ...] = ()
        occupation_group = heading
        if scope == "regional":
            province_payload = _province_payload(heading)
            if province_payload is None:
                raise ValueError(
                    f"Regional shortage-occupation group {ordinal} has no recognized Austrian province list"
                )
            occupation_group, province_codes, province_names = province_payload

        alias_text = " ".join(raw_details).strip()
        aliases = _split_top_level_commas(alias_text)
        deduped_aliases: list[str] = []
        seen_aliases: set[str] = set()
        for alias in aliases:
            normalized_alias = normalize_occupation(alias)
            if not normalized_alias or normalized_alias in seen_aliases:
                continue
            seen_aliases.add(normalized_alias)
            deduped_aliases.append(alias)
        if not deduped_aliases:
            raise ValueError(f"Shortage-occupation group {ordinal} contains no structured occupation aliases")

        normalized_group = normalize_occupation(occupation_group)
        entry_hash = _canonical_entry_hash(
            source_snapshot_id=source_snapshot_id,
            year=year,
            scope=scope,
            source_ordinal=ordinal,
            occupation_group=occupation_group,
            occupation_aliases=deduped_aliases,
            province_codes=province_codes,
        )
        parsed.append(
            ParsedShortageOccupation(
                source_ordinal=ordinal,
                occupation_group=occupation_group,
                normalized_occupation_group=normalized_group,
                occupation_aliases=tuple(deduped_aliases),
                province_codes=province_codes,
                province_names=province_names,
                entry_sha256=entry_hash,
            )
        )

    return parsed


def shortage_occupation_entry_read(
    session: Session,
    row: ShortageOccupationEntry,
) -> ShortageOccupationEntryRead:
    snapshot = session.get(SourceSnapshot, row.source_snapshot_id)
    source = session.get(OfficialSource, row.official_source_id)
    return ShortageOccupationEntryRead(
        id=row.id,
        jurisdiction_id=row.jurisdiction_id,
        official_source_id=row.official_source_id,
        source_snapshot_id=row.source_snapshot_id,
        source_snapshot_content_hash=snapshot.content_hash if snapshot else None,
        source_url=source.url if source else None,
        year=row.year,
        scope=row.scope,
        source_ordinal=row.source_ordinal,
        occupation_group=row.occupation_group,
        normalized_occupation_group=row.normalized_occupation_group,
        occupation_aliases=list(_load(row.occupation_aliases_json, [])),
        province_codes=list(_load(row.province_codes_json, [])),
        province_names=list(_load(row.province_names_json, [])),
        extraction_version=row.extraction_version,
        entry_sha256=row.entry_sha256,
        metadata=dict(_load(row.metadata_json, {})),
        created_at=row.created_at,
    )


def materialize_shortage_occupation_snapshot(
    session: Session,
    payload: ShortageOccupationMaterializeRequest,
    *,
    actor: str,
) -> ShortageOccupationMaterializationRead:
    snapshot = session.get(SourceSnapshot, payload.source_snapshot_id)
    if snapshot is None:
        raise ValueError("Source snapshot not found")
    if not snapshot.content_hash:
        raise ValueError("Source snapshot must carry an immutable content hash before structuring")
    if not snapshot.official_source_id:
        raise ValueError("Source snapshot has no official-source provenance")
    source = session.get(OfficialSource, snapshot.official_source_id)
    if source is None or not source.active:
        raise ValueError("Source snapshot does not resolve to an active official source")
    if not source.jurisdiction_id:
        raise ValueError("Official source has no jurisdiction provenance")
    jurisdiction = session.get(Jurisdiction, source.jurisdiction_id)
    if jurisdiction is None:
        raise ValueError("Official source jurisdiction not found")

    _validate_parser_source(jurisdiction, source, scope=payload.scope)
    parsed = parse_austria_shortage_occupations(
        snapshot.content_text or "",
        source_snapshot_id=snapshot.id,
        year=payload.year,
        scope=payload.scope,
    )
    if len(parsed) != payload.expected_group_count:
        raise ValueError(
            f"Structured extraction found {len(parsed)} groups but the operator-pinned expected count is "
            f"{payload.expected_group_count}; review the immutable snapshot before materialization"
        )

    existing = list(
        session.exec(
            select(ShortageOccupationEntry)
            .where(
                ShortageOccupationEntry.source_snapshot_id == snapshot.id,
                ShortageOccupationEntry.year == payload.year,
                ShortageOccupationEntry.scope == payload.scope,
            )
            .order_by(ShortageOccupationEntry.source_ordinal)
        ).all()
    )
    parsed_hashes = [entry.entry_sha256 for entry in parsed]
    if existing:
        existing_hashes = [row.entry_sha256 for row in existing]
        if existing_hashes != parsed_hashes:
            raise ValueError(
                "Existing structured occupation entries conflict with deterministic extraction for this immutable snapshot"
            )
        return ShortageOccupationMaterializationRead(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            source_snapshot_content_hash=snapshot.content_hash,
            year=payload.year,
            scope=payload.scope,
            extraction_version=EXTRACTION_VERSION,
            entry_set_sha256=_entry_set_hash(parsed),
            created_count=0,
            existing_count=len(existing),
            entry_count=len(existing),
            entries=[shortage_occupation_entry_read(session, row) for row in existing],
        )

    now = now_utc()
    rows: list[ShortageOccupationEntry] = []
    for entry in parsed:
        row = ShortageOccupationEntry(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            year=payload.year,
            scope=payload.scope,
            source_ordinal=entry.source_ordinal,
            occupation_group=entry.occupation_group,
            normalized_occupation_group=entry.normalized_occupation_group,
            occupation_aliases_json=_dump(list(entry.occupation_aliases)),
            province_codes_json=_dump(list(entry.province_codes)),
            province_names_json=_dump(list(entry.province_names)),
            extraction_version=EXTRACTION_VERSION,
            entry_sha256=entry.entry_sha256,
            metadata_json=_dump({
                "parser_profile": payload.parser_profile,
                "source_content_hash": snapshot.content_hash,
                "derived_from_immutable_snapshot": True,
            }),
            created_at=now,
        )
        session.add(row)
        rows.append(row)
    session.flush()

    entry_set_sha256 = _entry_set_hash(parsed)
    record_audit(
        session,
        action="shortage_occupation_snapshot_materialized",
        entity_type="source_snapshot",
        entity_id=snapshot.id,
        after_state={
            "jurisdiction_id": str(jurisdiction.id),
            "official_source_id": str(source.id),
            "source_snapshot_id": str(snapshot.id),
            "source_content_hash": snapshot.content_hash,
            "year": payload.year,
            "scope": payload.scope,
            "extraction_version": EXTRACTION_VERSION,
            "entry_count": len(rows),
            "entry_set_sha256": entry_set_sha256,
        },
        reason="Deterministic structured projection of an immutable official-source snapshot.",
        actor=actor,
        source="shortage_occupation_structuring_v13_10_2_6",
    )
    session.commit()
    for row in rows:
        session.refresh(row)

    return ShortageOccupationMaterializationRead(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        source_snapshot_content_hash=snapshot.content_hash,
        year=payload.year,
        scope=payload.scope,
        extraction_version=EXTRACTION_VERSION,
        entry_set_sha256=entry_set_sha256,
        created_count=len(rows),
        existing_count=0,
        entry_count=len(rows),
        entries=[shortage_occupation_entry_read(session, row) for row in rows],
    )


def _source_certification_status(
    session: Session,
    *,
    jurisdiction_id: UUID,
    source_id: UUID,
) -> tuple[str, bool]:
    rows = list(
        session.exec(
            select(JurisdictionSourceCertification)
            .where(
                JurisdictionSourceCertification.jurisdiction_id == jurisdiction_id,
                JurisdictionSourceCertification.official_source_id == source_id,
            )
            .order_by(JurisdictionSourceCertification.certification_version.desc())
        ).all()
    )
    if any(row.status == "approved" for row in rows):
        return "approved", True
    if rows:
        return rows[0].status, False
    return "not_certified", False


def lookup_shortage_occupation(
    session: Session,
    *,
    jurisdiction_id: UUID,
    year: int,
    occupation: str,
    province_code: str | None = None,
) -> ShortageOccupationLookupRead:
    jurisdiction = session.get(Jurisdiction, jurisdiction_id)
    if jurisdiction is None:
        raise ValueError("Jurisdiction not found")
    normalized_query = normalize_occupation(occupation)
    if not normalized_query:
        raise ValueError("Occupation lookup requires a non-empty occupation label")
    normalized_province = province_code.strip().upper() if province_code else None
    valid_province_codes = {code for code, _ in AUSTRIA_PROVINCES.values()}
    if normalized_province and normalized_province not in valid_province_codes:
        raise ValueError("Province code must be an Austrian ISO 3166-2 code from AT-1 through AT-9")

    candidates = list(
        session.exec(
            select(ShortageOccupationEntry)
            .where(
                ShortageOccupationEntry.jurisdiction_id == jurisdiction_id,
                ShortageOccupationEntry.year == year,
            )
            .order_by(
                ShortageOccupationEntry.scope,
                ShortageOccupationEntry.source_ordinal,
            )
        ).all()
    )
    matched: list[ShortageOccupationEntry] = []
    for row in candidates:
        aliases = _lookup_alias_labels(_load(row.occupation_aliases_json, []))
        if normalized_query in _group_lookup_labels(row.occupation_group) or normalized_query in aliases:
            matched.append(row)

    certification_statuses: dict[str, str] = {}
    governance_ready = False
    list_applicability: bool | None = None
    status = "not_found"

    if matched:
        source_readiness: list[bool] = []
        for source_id in dict.fromkeys(row.official_source_id for row in matched):
            cert_status, ready = _source_certification_status(
                session,
                jurisdiction_id=jurisdiction_id,
                source_id=source_id,
            )
            certification_statuses[str(source_id)] = cert_status
            source_readiness.append(ready)
        governance_ready = bool(source_readiness) and all(source_readiness)

        if len(matched) > 1:
            status = "ambiguous"
            list_applicability = None
        else:
            row = matched[0]
            if row.scope == "national":
                status = "matched"
                list_applicability = True
            else:
                province_codes = [str(value).upper() for value in _load(row.province_codes_json, [])]
                if not normalized_province:
                    status = "province_required"
                    list_applicability = None
                elif normalized_province in province_codes:
                    status = "matched"
                    list_applicability = True
                else:
                    status = "not_applicable_in_province"
                    list_applicability = False

    return ShortageOccupationLookupRead(
        jurisdiction_id=jurisdiction_id,
        year=year,
        occupation=occupation.strip(),
        normalized_occupation=normalized_query,
        province_code=normalized_province,
        status=status,
        list_applicability=list_applicability,
        governance_ready=governance_ready,
        certification_statuses=certification_statuses,
        match_count=len(matched),
        matches=[shortage_occupation_entry_read(session, row) for row in matched],
        warning=(
            "Structured source-list matching is exact and deterministic. It does not establish case eligibility, "
            "qualification equivalence, job-offer sufficiency, or authority outcome."
        ),
    )


def _raw_label(value: str) -> str:
    return unicodedata.normalize("NFKC", value or "").strip().casefold()


def _unqualified_label(value: str) -> str:
    """Remove only a trailing qualification marker; never infer an occupation family."""
    stripped = (value or "").strip()
    while _FINAL_PARENS_RE.search(stripped):
        stripped = _FINAL_PARENS_RE.sub("", stripped).strip()
    return normalize_occupation(stripped)


def _has_distinctive_lexical_overlap(query: str, label: str) -> bool:
    """Return a cautious lexical inference without inventing a regulatory alias.

    This is intentionally narrower than semantic matching. It only recognizes a
    distinctive token already present in both strings (including compounds such
    as ``softwareentwickler``). Generic profession words never establish a match.
    """
    query_tokens = {
        token for token in re.findall(r"[a-z0-9]+", normalize_occupation(query))
        if len(token) >= 5 and token not in _GENERIC_OCCUPATION_TOKENS
    }
    normalized_label = normalize_occupation(label)
    return any(token in normalized_label for token in query_tokens)


def _scope_resolution(
    session: Session,
    *,
    rows: list[ShortageOccupationEntry],
    scope: str,
    occupation: str,
    year: int,
    province_code: str | None,
) -> OccupationScopeAssessmentRead:
    raw_query = _raw_label(occupation)
    normalized_query = normalize_occupation(occupation)
    exact: list[ShortageOccupationEntry] = []
    normalized: list[ShortageOccupationEntry] = []
    inferred: list[ShortageOccupationEntry] = []
    lexical: list[ShortageOccupationEntry] = []
    for row in rows:
        aliases = _load(row.occupation_aliases_json, [])
        labels = [row.occupation_group, *aliases]
        lookup_normalized_labels = {
            normalize_occupation(row.occupation_group),
            *_lookup_alias_labels(aliases),
        }
        if any(raw_query == _raw_label(label) for label in labels):
            exact.append(row)
        elif normalized_query in lookup_normalized_labels:
            normalized.append(row)
        elif any(normalized_query == _unqualified_label(label) for label in labels):
            inferred.append(row)
        elif any(_has_distinctive_lexical_overlap(occupation, label) for label in labels):
            lexical.append(row)

    candidates = exact or normalized or inferred or lexical
    base_quality = (
        "AMBIGUOUS" if len(candidates) > 1
        else "EXACT" if exact
        else "NORMALIZED_EXACT" if normalized
        else "INFERRED" if inferred or lexical
        else "NO_MATCH"
    )
    reason = {
        "AMBIGUOUS": (
            "The supplied occupation title overlaps multiple governed occupation entries "
            "with potentially different qualification or regional implications."
        ),
        "EXACT": "The supplied title exactly matches one governed occupation label.",
        "NORMALIZED_EXACT": "The supplied title matches one governed label after presentation-only normalization.",
        "INFERRED": (
            "The supplied title has a cautious lexical overlap with governed occupation labels; "
            "the occupation and qualification mapping still requires confirmation."
        ),
        "NO_MATCH": "No governed occupation entry matches the supplied title.",
    }[base_quality]
    quality = base_quality

    certification_statuses: dict[str, str] = {}
    for source_id in dict.fromkeys(row.official_source_id for row in candidates):
        status, _ = _source_certification_status(
            session,
            jurisdiction_id=rows[0].jurisdiction_id if rows else candidates[0].jurisdiction_id,
            source_id=source_id,
        )
        certification_statuses[str(source_id)] = status

    normalized_province = province_code.strip().upper() if province_code else None
    applicability = "NOT_FOUND" if quality == "NO_MATCH" else "NOT_ESTABLISHED"
    if candidates and scope == "national" and quality in {"EXACT", "NORMALIZED_EXACT"}:
        applicability = "POSSIBLE"
    elif candidates and scope == "regional":
        if not normalized_province:
            quality = "INSUFFICIENT_INFORMATION"
            applicability = "NOT_ESTABLISHED"
            reason = (
                "Potential governed regional occupation entries are present, but the employment province is unknown. "
                "Regional shortage applicability cannot yet be determined."
            )
        else:
            province_candidates = [
                row for row in candidates
                if normalized_province in {str(value).upper() for value in _load(row.province_codes_json, [])}
            ]
            candidates = province_candidates
            if not province_candidates:
                quality = "NO_MATCH"
                applicability = "NOT_FOUND"
                reason = "Relevant governed occupation entries do not apply to the supplied province."
            elif len(province_candidates) > 1:
                quality = "AMBIGUOUS"
                applicability = "NOT_ESTABLISHED"
                reason = (
                    "Multiple governed occupation entries apply in the supplied province, "
                    "and the qualification mapping is unresolved."
                )
            else:
                quality = base_quality
                applicability = "POSSIBLE" if quality in {"EXACT", "NORMALIZED_EXACT"} else "NOT_ESTABLISHED"

    return OccupationScopeAssessmentRead(
        scope=scope,
        year=year,
        match_quality=quality,
        province_code=normalized_province,
        qualification_mapping="RESOLVED" if quality in {"EXACT", "NORMALIZED_EXACT"} and len(candidates) == 1 else "UNRESOLVED",
        applicability_status=applicability,
        candidates=[shortage_occupation_entry_read(session, row) for row in candidates],
        certification_statuses=certification_statuses,
        reason=reason,
    )


def resolve_austria_occupation(
    session: Session,
    *,
    jurisdiction_id: UUID,
    occupation: str | None,
    year: int = 2026,
    province_code: str | None = None,
    has_job_offer: bool | None = None,
) -> OccupationResolutionRead:
    """Return a governed, non-eligibility occupation assessment for an Austria case."""
    value = (occupation or "").strip()
    rows = list(session.exec(
        select(ShortageOccupationEntry)
        .where(
            ShortageOccupationEntry.jurisdiction_id == jurisdiction_id,
            ShortageOccupationEntry.year == year,
        )
        .order_by(ShortageOccupationEntry.scope, ShortageOccupationEntry.source_ordinal)
    ).all())
    national_rows = [row for row in rows if row.scope == "national"]
    regional_rows = [row for row in rows if row.scope == "regional"]
    if not value:
        empty_reason = "Occupation title is required before governed occupation evidence can be assessed."
        national = OccupationScopeAssessmentRead(
            scope="national", year=year, match_quality="INSUFFICIENT_INFORMATION",
            applicability_status="NOT_ESTABLISHED", reason=empty_reason,
        )
        regional = OccupationScopeAssessmentRead(
            scope="regional", year=year, match_quality="INSUFFICIENT_INFORMATION",
            province_code=province_code, applicability_status="NOT_ESTABLISHED", reason=empty_reason,
        )
        overall = "INSUFFICIENT_INFORMATION"
    else:
        national = _scope_resolution(
            session, rows=national_rows, scope="national", occupation=value,
            year=year, province_code=None,
        )
        regional = _scope_resolution(
            session, rows=regional_rows, scope="regional", occupation=value,
            year=year, province_code=province_code,
        )
        qualities = {national.match_quality, regional.match_quality}
        if "AMBIGUOUS" in qualities:
            overall = "AMBIGUOUS"
        elif "INFERRED" in qualities:
            overall = "INFERRED"
        elif "NORMALIZED_EXACT" in qualities:
            overall = "NORMALIZED_EXACT"
        elif "EXACT" in qualities:
            overall = "EXACT"
        elif qualities == {"NO_MATCH"}:
            overall = "NO_MATCH"
        else:
            overall = "INSUFFICIENT_INFORMATION"

    job_status = "PRESENT" if has_job_offer is True else "ABSENT" if has_job_offer is False else "UNKNOWN"
    qualification_mapping = (
        "RESOLVED"
        if national.qualification_mapping == "RESOLVED" or regional.qualification_mapping == "RESOLVED"
        else "UNRESOLVED"
    )
    return OccupationResolutionRead(
        occupation_input=value,
        year=year,
        match_quality=overall,
        qualification_mapping=qualification_mapping,
        employment_province=province_code,
        job_offer_status=job_status,
        national=national,
        regional=regional,
        conclusion=(
            "Occupation-list applicability is not established. This assessment does not establish pathway eligibility."
            if overall in {"AMBIGUOUS", "INFERRED", "INSUFFICIENT_INFORMATION"}
            else "A governed occupation label was found, but pathway eligibility is not established."
            if overall in {"EXACT", "NORMALIZED_EXACT"}
            else "No governed occupation match was found. This does not determine eligibility for other pathways."
        ),
        establishes_pathway_eligibility=False,
    )
