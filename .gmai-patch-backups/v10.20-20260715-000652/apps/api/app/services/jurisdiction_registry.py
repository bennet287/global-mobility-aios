from __future__ import annotations

import hashlib
import html
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Any

import httpx
from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    JurisdictionImmigrationAssessment,
    JurisdictionRegistryEntry,
    JurisdictionRegistryRelease,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
    SourceMonitor,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)


UN_M49_SOURCE_URL = "https://unstats.un.org/unsd/methodology/m49/overview/"
ISO_3166_SOURCE_URL = "https://www.iso.org/iso-3166-country-codes.html"
ISO_3166_SUPPLEMENTAL_ENTRIES = ({
    "region": "Asia",
    "subregion": "Eastern Asia",
    "name": "Taiwan, Province of China",
    "m49_code": "158",
    "alpha2_code": "TW",
    "alpha3_code": "TWN",
},)
UN_MEMBER_ALPHA2 = frozenset(
    "AF AL DZ AD AO AG AR AM AU AT AZ BS BH BD BB BY BE BZ BJ BT BO BA BW BR BN BG BF BI CV KH CM CA "
    "CF TD CL CN CO KM CG CD CR CI HR CU CY CZ DK DJ DM DO EC EG SV GQ ER EE SZ ET FJ FI FR GA GM GE DE "
    "GH GR GD GT GN GW GY HT HN HU IS IN ID IR IQ IE IL IT JM JP JO KZ KE KI KP KR KW KG LA LV LB LS LR "
    "LY LI LT LU MG MW MY MV ML MT MH MR MU MX FM MC MN ME MA MZ MM NA NR NP NL NZ NI NE NG MK NO OM PK PW "
    "PA PG PY PE PH PL PT QA MD RO RU RW KN LC VC WS SM ST SA SN RS SC SL SG SK SI SB SO ZA SS ES LK SD SR "
    "SE CH SY TJ TH TL TG TO TT TN TR TM TV UG UA AE GB TZ US UY UZ VU VE VN YE ZM ZW".split()
)
UN_OBSERVER_ALPHA2 = frozenset({"PS", "VA"})
AUTONOMOUS_ALPHA2 = frozenset({"AX", "AW", "CW", "FO", "GL", "GG", "HK", "IM", "JE", "MO", "SX"})
NO_POPULATION_COVERAGE_ALPHA2 = frozenset({"AQ", "BV", "GS", "HM", "TF", "UM"})
CLEAR_IMMIGRATION_RULE_RELATIONSHIPS = frozenset({
    "independent",
    "parent_inherited",
    "shared_or_coordinated",
    "not_applicable",
})


class _M49EnglishTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.in_cell = False
        self.row: list[str] | None = None
        self.cell_parts: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("id", "").strip() == "downloadTableEN":
            self.in_table = True
        elif self.in_table and tag == "tr":
            self.row = []
        elif self.in_table and self.row is not None and tag == "td":
            self.in_cell = True
            self.cell_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.in_table and self.in_cell and tag == "td":
            self.in_cell = False
            if self.row is not None:
                self.row.append(" ".join("".join(self.cell_parts).split()))
        elif self.in_table and tag == "tr" and self.row is not None:
            if len(self.row) >= 12 and len(self.row[10]) == 2 and len(self.row[11]) == 3:
                self.rows.append({
                    "region": html.unescape(self.row[3]),
                    "subregion": html.unescape(self.row[5]),
                    "name": html.unescape(self.row[8]),
                    "m49_code": self.row[9],
                    "alpha2_code": self.row[10].upper(),
                    "alpha3_code": self.row[11].upper(),
                })
            self.row = None
        elif self.in_table and tag == "table":
            self.in_table = False


def parse_un_m49_html(source_text: str) -> list[dict[str, str]]:
    parser = _M49EnglishTableParser()
    parser.feed(source_text)
    rows = sorted(parser.rows, key=lambda row: row["alpha2_code"])
    if len({row["alpha2_code"] for row in rows}) != len(rows):
        raise ValueError("UN M49 source contains duplicate alpha-2 codes")
    return rows


def _membership_status(alpha2: str) -> str:
    if alpha2 in UN_MEMBER_ALPHA2:
        return "un_member"
    if alpha2 in UN_OBSERVER_ALPHA2:
        return "un_observer"
    return "territory_or_area"


def _jurisdiction_type(alpha2: str, membership_status: str) -> str:
    if alpha2 in AUTONOMOUS_ALPHA2:
        return "autonomous_jurisdiction"
    return "country" if membership_status in {"un_member", "un_observer"} else "territory"


def fetch_un_m49_source() -> tuple[str, datetime]:
    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            response = client.get(
                UN_M49_SOURCE_URL,
                headers={"User-Agent": "Global-Mobility-AIOS/10.1 registry-import"},
            )
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                raise ValueError("UN M49 source did not return HTML")
            return response.text, now_utc()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"UN M49 registry retrieval failed: {exc}") from exc


def import_un_m49_registry(
    session: Session,
    *,
    actor: str,
    source_text: str | None = None,
    source_retrieved_at: datetime | None = None,
    minimum_entries: int = 240,
    require_global_scope: bool = True,
) -> tuple[JurisdictionRegistryRelease, bool]:
    if source_text is None:
        source_text, source_retrieved_at = fetch_un_m49_source()
    retrieved_at = source_retrieved_at or now_utc()
    rows = parse_un_m49_html(source_text)
    present_codes = {row["alpha2_code"] for row in rows}
    rows.extend(row for row in ISO_3166_SUPPLEMENTAL_ENTRIES if row["alpha2_code"] not in present_codes)
    rows.sort(key=lambda row: row["alpha2_code"])
    if len(rows) < minimum_entries:
        raise ValueError(f"UN M49 registry import refused: expected at least {minimum_entries} entries, found {len(rows)}")
    if require_global_scope and len(UN_MEMBER_ALPHA2 & {row['alpha2_code'] for row in rows}) != 193:
        raise ValueError("UN M49 registry import refused: the 193-member-state scope is incomplete")
    if require_global_scope and len(UN_OBSERVER_ALPHA2 & {row['alpha2_code'] for row in rows}) != 2:
        raise ValueError("UN M49 registry import refused: the two observer-state entries are incomplete")

    canonical_json = json.dumps(rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    source_sha256 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    existing = session.exec(
        select(JurisdictionRegistryRelease).where(
            JurisdictionRegistryRelease.source_sha256 == source_sha256
        )
    ).first()
    if existing:
        return existing, False

    for previous in session.exec(
        select(JurisdictionRegistryRelease).where(JurisdictionRegistryRelease.status == "active")
    ).all():
        previous.status = "superseded"
        session.add(previous)

    release = JurisdictionRegistryRelease(
        version=f"un-m49-{retrieved_at.date().isoformat()}-{source_sha256[:8]}",
        source_name="United Nations M49 + ISO 3166-1",
        source_url=UN_M49_SOURCE_URL,
        source_sha256=source_sha256,
        source_retrieved_at=retrieved_at,
        expected_entries=len(rows),
        imported_entries=len(rows),
        status="active",
        released_by=actor,
        released_at=now_utc(),
    )
    session.add(release)
    session.flush()

    for row in rows:
        alpha2 = row["alpha2_code"]
        membership = _membership_status(alpha2)
        kind = _jurisdiction_type(alpha2, membership)
        jurisdiction = session.exec(select(Jurisdiction).where(Jurisdiction.code == alpha2)).first()
        metadata = {
            "alpha3_code": row["alpha3_code"],
            "m49_code": row["m49_code"],
            "membership_status": membership,
            "subregion": row["subregion"],
            "registry_version": release.version,
            "registry_source_url": UN_M49_SOURCE_URL,
            "iso_3166_source_url": ISO_3166_SOURCE_URL,
        }
        if jurisdiction is None:
            jurisdiction = Jurisdiction(
                code=alpha2,
                name=row["name"],
                jurisdiction_type=kind,
                region=row["region"],
                metadata_json=json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            )
        else:
            jurisdiction.name = row["name"]
            jurisdiction.region = row["region"]
            jurisdiction.active = True
            if jurisdiction.jurisdiction_type != "autonomous_jurisdiction":
                jurisdiction.jurisdiction_type = kind
            try:
                previous_metadata = json.loads(jurisdiction.metadata_json or "{}")
            except (TypeError, ValueError):
                previous_metadata = {}
            jurisdiction.metadata_json = json.dumps(
                {**previous_metadata, **metadata}, ensure_ascii=False, sort_keys=True
            )
            jurisdiction.updated_at = now_utc()
        session.add(jurisdiction)
        session.flush()
        entry_payload = {
            **row,
            "jurisdiction_type": jurisdiction.jurisdiction_type,
            "membership_status": membership,
            "coverage_required": alpha2 not in NO_POPULATION_COVERAGE_ALPHA2,
        }
        session.add(JurisdictionRegistryEntry(
            registry_release_id=release.id,
            jurisdiction_id=jurisdiction.id,
            alpha2_code=alpha2,
            alpha3_code=row["alpha3_code"],
            m49_code=row["m49_code"],
            canonical_name=row["name"],
            jurisdiction_type=jurisdiction.jurisdiction_type,
            membership_status=membership,
            parent_code=jurisdiction.parent_code,
            region=row["region"],
            subregion=row["subregion"],
            immigration_rule_status="unassessed",
            coverage_required=alpha2 not in NO_POPULATION_COVERAGE_ALPHA2,
            payload_sha256=hashlib.sha256(
                json.dumps(entry_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest(),
        ))
    session.commit()
    session.refresh(release)
    return release, True


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def immigration_assessment_payload(assessment: JurisdictionImmigrationAssessment) -> dict[str, Any]:
    return {
        "id": assessment.id,
        "jurisdiction_id": assessment.jurisdiction_id,
        "registry_entry_id": assessment.registry_entry_id,
        "assessment_version": assessment.assessment_version,
        "rule_relationship": assessment.rule_relationship,
        "parent_code": assessment.parent_code,
        "evidence_url": assessment.evidence_url,
        "evidence_title": assessment.evidence_title,
        "official_source_id": assessment.official_source_id,
        "source_snapshot_id": assessment.source_snapshot_id,
        "rationale": assessment.rationale,
        "status": assessment.status,
        "proposed_by": assessment.proposed_by,
        "reviewed_by": assessment.reviewed_by,
        "reviewed_at": assessment.reviewed_at,
        "review_notes": assessment.review_notes,
        "supersedes_assessment_id": assessment.supersedes_assessment_id,
        "created_at": assessment.created_at,
        "updated_at": assessment.updated_at,
    }


def source_certification_payload(certification: JurisdictionSourceCertification) -> dict[str, Any]:
    try:
        coverage_domains = json.loads(certification.coverage_domains_json)
    except (TypeError, ValueError):
        coverage_domains = []
    return {
        "id": certification.id,
        "jurisdiction_id": certification.jurisdiction_id,
        "registry_entry_id": certification.registry_entry_id,
        "regulatory_authority_id": certification.regulatory_authority_id,
        "official_source_id": certification.official_source_id,
        "certification_version": certification.certification_version,
        "certification_scope": certification.certification_scope,
        "coverage_domains": coverage_domains,
        "evidence_notes": certification.evidence_notes,
        "status": certification.status,
        "proposed_by": certification.proposed_by,
        "reviewed_by": certification.reviewed_by,
        "reviewed_at": certification.reviewed_at,
        "review_notes": certification.review_notes,
        "supersedes_certification_id": certification.supersedes_certification_id,
        "created_at": certification.created_at,
        "updated_at": certification.updated_at,
    }


def propose_immigration_assessment(
    session: Session,
    *,
    jurisdiction_id: Any,
    rule_relationship: str,
    parent_code: str | None,
    evidence_url: str,
    evidence_title: str,
    rationale: str,
    actor: str,
    official_source_id: Any | None = None,
    source_snapshot_id: Any | None = None,
    commit: bool = True,
) -> JurisdictionImmigrationAssessment:
    allowed = CLEAR_IMMIGRATION_RULE_RELATIONSHIPS | {"unclear"}
    if rule_relationship not in allowed:
        raise ValueError("Unsupported immigration-rule relationship")
    if not evidence_url.lower().startswith("https://"):
        raise ValueError("Assessment evidence must use an HTTPS URL")
    jurisdiction = session.get(Jurisdiction, jurisdiction_id)
    if jurisdiction is None or not jurisdiction.active:
        raise ValueError("Jurisdiction not found")
    release = session.exec(
        select(JurisdictionRegistryRelease).where(JurisdictionRegistryRelease.status == "active")
    ).first()
    if release is None:
        raise ValueError("No active jurisdiction registry release")
    entry = session.exec(
        select(JurisdictionRegistryEntry).where(
            JurisdictionRegistryEntry.registry_release_id == release.id,
            JurisdictionRegistryEntry.jurisdiction_id == jurisdiction.id,
        )
    ).first()
    if entry is None:
        raise ValueError("Jurisdiction is not part of the active registry release")
    pending = session.exec(
        select(JurisdictionImmigrationAssessment).where(
            JurisdictionImmigrationAssessment.jurisdiction_id == jurisdiction.id,
            JurisdictionImmigrationAssessment.status == "pending_review",
        )
    ).first()
    if pending:
        raise ValueError("Jurisdiction already has an assessment pending review")
    parent = parent_code.strip().upper() if parent_code else None
    if rule_relationship in {"parent_inherited", "shared_or_coordinated"}:
        if not parent:
            raise ValueError("A parent jurisdiction code is required for inherited or shared rules")
        if parent == jurisdiction.code:
            raise ValueError("A jurisdiction cannot be its own parent")
        if session.exec(select(Jurisdiction).where(Jurisdiction.code == parent)).first() is None:
            raise ValueError("Parent jurisdiction is not in the registry")
    elif rule_relationship == "independent":
        parent = None
    if official_source_id is not None:
        source = session.get(OfficialSource, official_source_id)
        if source is None or not source.active:
            raise ValueError("Official source not found")
    if source_snapshot_id is not None:
        snapshot = session.get(SourceSnapshot, source_snapshot_id)
        if snapshot is None:
            raise ValueError("Source snapshot not found")
        if official_source_id is not None and snapshot.official_source_id != official_source_id:
            raise ValueError("Source snapshot does not belong to the selected official source")
    latest = session.exec(
        select(JurisdictionImmigrationAssessment)
        .where(JurisdictionImmigrationAssessment.jurisdiction_id == jurisdiction.id)
        .order_by(JurisdictionImmigrationAssessment.assessment_version.desc())
    ).first()
    assessment = JurisdictionImmigrationAssessment(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=entry.id,
        assessment_version=(latest.assessment_version + 1) if latest else 1,
        rule_relationship=rule_relationship,
        parent_code=parent,
        evidence_url=evidence_url.strip(),
        evidence_title=evidence_title.strip(),
        official_source_id=official_source_id,
        source_snapshot_id=source_snapshot_id,
        rationale=rationale.strip(),
        status="pending_review",
        proposed_by=actor,
        supersedes_assessment_id=latest.id if latest and latest.status == "approved" else None,
    )
    session.add(assessment)
    if commit:
        session.commit()
        session.refresh(assessment)
    else:
        session.flush()
    return assessment


def review_immigration_assessment(
    session: Session,
    *,
    assessment_id: Any,
    decision: str,
    notes: str,
    actor: str,
) -> JurisdictionImmigrationAssessment:
    assessment = session.get(JurisdictionImmigrationAssessment, assessment_id)
    if assessment is None:
        raise ValueError("Immigration assessment not found")
    if assessment.status != "pending_review":
        raise ValueError("Only pending assessments can be reviewed")
    if assessment.proposed_by == actor:
        raise ValueError("Assessment reviewer must be different from the proposer")
    if decision not in {"approved", "rejected"}:
        raise ValueError("Review decision must be approved or rejected")
    if decision == "approved":
        previous = session.exec(
            select(JurisdictionImmigrationAssessment).where(
                JurisdictionImmigrationAssessment.jurisdiction_id == assessment.jurisdiction_id,
                JurisdictionImmigrationAssessment.status == "approved",
            )
        ).all()
        for row in previous:
            row.status = "superseded"
            row.updated_at = now_utc()
            session.add(row)
            if assessment.supersedes_assessment_id is None:
                assessment.supersedes_assessment_id = row.id
    assessment.status = decision
    assessment.reviewed_by = actor
    assessment.reviewed_at = now_utc()
    assessment.review_notes = notes.strip()
    assessment.updated_at = now_utc()
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment


def propose_source_certification(
    session: Session,
    *,
    jurisdiction_id: Any,
    regulatory_authority_id: Any,
    official_source_id: Any,
    coverage_domains: list[str],
    evidence_notes: str,
    actor: str,
    commit: bool = True,
) -> JurisdictionSourceCertification:
    jurisdiction = session.get(Jurisdiction, jurisdiction_id)
    if jurisdiction is None or not jurisdiction.active:
        raise ValueError("Jurisdiction not found")
    release = session.exec(
        select(JurisdictionRegistryRelease).where(JurisdictionRegistryRelease.status == "active")
    ).first()
    if release is None:
        raise ValueError("No active jurisdiction registry release")
    entry = session.exec(
        select(JurisdictionRegistryEntry).where(
            JurisdictionRegistryEntry.registry_release_id == release.id,
            JurisdictionRegistryEntry.jurisdiction_id == jurisdiction.id,
        )
    ).first()
    if entry is None:
        raise ValueError("Jurisdiction is not part of the active registry release")
    authority = session.get(RegulatoryAuthority, regulatory_authority_id)
    if authority is None or not authority.active or authority.jurisdiction_id != jurisdiction.id:
        raise ValueError("Active authority does not belong to the jurisdiction")
    source = session.get(OfficialSource, official_source_id)
    if (
        source is None
        or not source.active
        or source.jurisdiction_id != jurisdiction.id
        or source.regulatory_authority_id != authority.id
    ):
        raise ValueError("Active official source does not belong to the selected authority and jurisdiction")
    if not source.url.lower().startswith("https://"):
        raise ValueError("Primary official source must use HTTPS")
    domains = sorted({str(domain).strip().lower() for domain in coverage_domains if str(domain).strip()})
    if not domains:
        raise ValueError("At least one coverage domain is required")
    if source.domain.lower() not in domains:
        raise ValueError("The official source domain must be included in coverage domains")
    pending = session.exec(
        select(JurisdictionSourceCertification).where(
            JurisdictionSourceCertification.jurisdiction_id == jurisdiction.id,
            JurisdictionSourceCertification.certification_scope == "primary_immigration",
            JurisdictionSourceCertification.status == "pending_review",
        )
    ).first()
    if pending:
        raise ValueError("Jurisdiction already has a primary-source certification pending review")
    latest = session.exec(
        select(JurisdictionSourceCertification)
        .where(
            JurisdictionSourceCertification.jurisdiction_id == jurisdiction.id,
            JurisdictionSourceCertification.certification_scope == "primary_immigration",
        )
        .order_by(JurisdictionSourceCertification.certification_version.desc())
    ).first()
    certification = JurisdictionSourceCertification(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=entry.id,
        regulatory_authority_id=authority.id,
        official_source_id=source.id,
        certification_version=(latest.certification_version + 1) if latest else 1,
        certification_scope="primary_immigration",
        coverage_domains_json=json.dumps(domains, sort_keys=True),
        evidence_notes=evidence_notes.strip(),
        status="pending_review",
        proposed_by=actor,
        supersedes_certification_id=latest.id if latest and latest.status == "approved" else None,
    )
    session.add(certification)
    if commit:
        session.commit()
        session.refresh(certification)
    else:
        session.flush()
    return certification


def review_source_certification(
    session: Session,
    *,
    certification_id: Any,
    decision: str,
    notes: str,
    actor: str,
) -> JurisdictionSourceCertification:
    certification = session.get(JurisdictionSourceCertification, certification_id)
    if certification is None:
        raise ValueError("Source certification not found")
    if certification.status != "pending_review":
        raise ValueError("Only pending source certifications can be reviewed")
    if certification.proposed_by == actor:
        raise ValueError("Source certification reviewer must be different from the proposer")
    if decision not in {"approved", "rejected"}:
        raise ValueError("Review decision must be approved or rejected")
    if decision == "approved":
        authority = session.get(RegulatoryAuthority, certification.regulatory_authority_id)
        source = session.get(OfficialSource, certification.official_source_id)
        if authority is None or not authority.active or source is None or not source.active:
            raise ValueError("Authority and source must remain active at review time")
        previous = session.exec(
            select(JurisdictionSourceCertification).where(
                JurisdictionSourceCertification.jurisdiction_id == certification.jurisdiction_id,
                JurisdictionSourceCertification.certification_scope == certification.certification_scope,
                JurisdictionSourceCertification.status == "approved",
            )
        ).all()
        for row in previous:
            row.status = "superseded"
            row.updated_at = now_utc()
            session.add(row)
            if certification.supersedes_certification_id is None:
                certification.supersedes_certification_id = row.id
    certification.status = decision
    certification.reviewed_by = actor
    certification.reviewed_at = now_utc()
    certification.review_notes = notes.strip()
    certification.updated_at = now_utc()
    session.add(certification)
    session.commit()
    session.refresh(certification)
    return certification


def jurisdiction_registry_coverage(session: Session) -> dict[str, Any]:
    release = session.exec(
        select(JurisdictionRegistryRelease)
        .where(JurisdictionRegistryRelease.status == "active")
        .order_by(JurisdictionRegistryRelease.released_at.desc())
    ).first()
    if release is None:
        return {
            "release": None,
            "summary": {"registry_entries": 0, "coverage_required": 0},
            "release_gate": {
                "registry_complete": False,
                "authority_coverage_complete": False,
                "source_coverage_complete": False,
                "monitor_coverage_complete": False,
                "verified_rule_coverage_complete": False,
                "global_coverage_claim_ready": False,
            },
            "regions": [],
            "entries": [],
        }

    entries = list(session.exec(
        select(JurisdictionRegistryEntry)
        .where(JurisdictionRegistryEntry.registry_release_id == release.id)
        .order_by(JurisdictionRegistryEntry.canonical_name)
    ).all())
    authorities = list(session.exec(select(RegulatoryAuthority).where(RegulatoryAuthority.active == True)).all())  # noqa: E712
    sources = list(session.exec(select(OfficialSource).where(OfficialSource.active == True)).all())  # noqa: E712
    monitors = list(session.exec(select(SourceMonitor)).all())
    rules = list(session.exec(select(VerifiedRule).where(VerifiedRule.active == True)).all())  # noqa: E712
    assessments = list(session.exec(
        select(JurisdictionImmigrationAssessment)
        .order_by(JurisdictionImmigrationAssessment.assessment_version.desc())
    ).all())
    certifications = list(session.exec(
        select(JurisdictionSourceCertification)
        .order_by(JurisdictionSourceCertification.certification_version.desc())
    ).all())
    approved_assessments: dict[Any, JurisdictionImmigrationAssessment] = {}
    pending_assessments: dict[Any, JurisdictionImmigrationAssessment] = {}
    active_entry_ids = {entry.id for entry in entries}
    for assessment in assessments:
        if assessment.registry_entry_id not in active_entry_ids:
            continue
        if assessment.status == "approved" and assessment.jurisdiction_id not in approved_assessments:
            approved_assessments[assessment.jurisdiction_id] = assessment
        elif assessment.status == "pending_review" and assessment.jurisdiction_id not in pending_assessments:
            pending_assessments[assessment.jurisdiction_id] = assessment
    approved_certifications: dict[Any, JurisdictionSourceCertification] = {}
    pending_certifications: dict[Any, JurisdictionSourceCertification] = {}
    for certification in certifications:
        if certification.registry_entry_id not in active_entry_ids:
            continue
        if certification.status == "approved" and certification.jurisdiction_id not in approved_certifications:
            approved_certifications[certification.jurisdiction_id] = certification
        elif certification.status == "pending_review" and certification.jurisdiction_id not in pending_certifications:
            pending_certifications[certification.jurisdiction_id] = certification
    authority_jurisdictions = {row.jurisdiction_id for row in authorities}
    source_jurisdictions = {row.jurisdiction_id for row in sources if row.jurisdiction_id}
    sources_by_id = {row.id: row for row in sources}
    fresh_monitor_source_ids: set[Any] = set()
    now = now_utc()
    for monitor in monitors:
        source = sources_by_id.get(monitor.official_source_id)
        last_checked = _aware(monitor.last_checked_at)
        if (
            source
            and source.jurisdiction_id
            and monitor.status == "active"
            and last_checked
            and last_checked >= now - timedelta(minutes=max(monitor.schedule_minutes * 2, 1440))
        ):
            fresh_monitor_source_ids.add(source.id)
    rule_jurisdictions = {row.jurisdiction_id for row in rules if row.jurisdiction_id}

    rows = []
    for entry in entries:
        has_authority = entry.jurisdiction_id in authority_jurisdictions
        has_source = entry.jurisdiction_id in source_jurisdictions
        approved_certification = approved_certifications.get(entry.jurisdiction_id)
        pending_certification = pending_certifications.get(entry.jurisdiction_id)
        has_reviewed_primary_authority = approved_certification is not None
        has_reviewed_primary_source = approved_certification is not None
        has_fresh_monitor = bool(
            approved_certification
            and approved_certification.official_source_id in fresh_monitor_source_ids
        )
        has_rule = entry.jurisdiction_id in rule_jurisdictions
        approved_assessment = approved_assessments.get(entry.jurisdiction_id)
        pending_assessment = pending_assessments.get(entry.jurisdiction_id)
        rule_status = approved_assessment.rule_relationship if approved_assessment else "unassessed"
        has_clear_assessment = rule_status in CLEAR_IMMIGRATION_RULE_RELATIONSHIPS
        missing = []
        if entry.coverage_required:
            if not has_reviewed_primary_authority:
                missing.append("reviewed_primary_authority")
            if not has_reviewed_primary_source:
                missing.append("reviewed_primary_source")
            if not has_fresh_monitor:
                missing.append("fresh_monitor")
            if not has_rule:
                missing.append("verified_rule")
            if not has_clear_assessment:
                missing.append("immigration_rule_assessment")
        rows.append({
            "id": entry.id,
            "jurisdiction_id": entry.jurisdiction_id,
            "alpha2_code": entry.alpha2_code,
            "alpha3_code": entry.alpha3_code,
            "m49_code": entry.m49_code,
            "name": entry.canonical_name,
            "jurisdiction_type": entry.jurisdiction_type,
            "membership_status": entry.membership_status,
            "parent_code": approved_assessment.parent_code if approved_assessment else entry.parent_code,
            "region": entry.region,
            "subregion": entry.subregion,
            "coverage_required": entry.coverage_required,
            "immigration_rule_status": rule_status,
            "approved_assessment": immigration_assessment_payload(approved_assessment) if approved_assessment else None,
            "pending_assessment": immigration_assessment_payload(pending_assessment) if pending_assessment else None,
            "has_authority": has_authority,
            "has_official_source": has_source,
            "has_reviewed_primary_authority": has_reviewed_primary_authority,
            "has_reviewed_primary_source": has_reviewed_primary_source,
            "approved_source_certification": source_certification_payload(approved_certification) if approved_certification else None,
            "pending_source_certification": source_certification_payload(pending_certification) if pending_certification else None,
            "has_fresh_monitor": has_fresh_monitor,
            "has_verified_rule": has_rule,
            "coverage_ready": entry.coverage_required and not missing,
            "missing": missing,
        })

    required = [row for row in rows if row["coverage_required"]]
    count_ready = lambda key: sum(bool(row[key]) for row in required)
    membership_counts = Counter(row["membership_status"] for row in rows)
    type_counts = Counter(row["jurisdiction_type"] for row in rows)
    regions = []
    for region in sorted({row["region"] or "Unassigned" for row in rows}):
        region_rows = [row for row in rows if (row["region"] or "Unassigned") == region]
        region_required = [row for row in region_rows if row["coverage_required"]]
        regions.append({
            "region": region,
            "entries": len(region_rows),
            "coverage_required": len(region_required),
            "coverage_ready": sum(row["coverage_ready"] for row in region_required),
        })
    registry_complete = (
        len(entries) == release.expected_entries == release.imported_entries
        and membership_counts["un_member"] == 193
        and membership_counts["un_observer"] == 2
    )
    authority_complete = bool(required) and count_ready("has_reviewed_primary_authority") == len(required)
    source_complete = bool(required) and count_ready("has_reviewed_primary_source") == len(required)
    monitor_complete = bool(required) and count_ready("has_fresh_monitor") == len(required)
    rule_complete = bool(required) and count_ready("has_verified_rule") == len(required)
    assessment_complete = bool(required) and all(
        row["immigration_rule_status"] in CLEAR_IMMIGRATION_RULE_RELATIONSHIPS for row in required
    )
    global_ready = all((
        registry_complete,
        authority_complete,
        source_complete,
        monitor_complete,
        rule_complete,
        assessment_complete,
    ))
    return {
        "generated_at": now,
        "release": {
            "id": release.id,
            "version": release.version,
            "source_name": release.source_name,
            "source_url": release.source_url,
            "source_sha256": release.source_sha256,
            "source_retrieved_at": release.source_retrieved_at,
            "released_at": release.released_at,
            "released_by": release.released_by,
            "status": release.status,
        },
        "summary": {
            "registry_entries": len(rows),
            "coverage_required": len(required),
            "un_members": membership_counts["un_member"],
            "un_observers": membership_counts["un_observer"],
            "countries": type_counts["country"],
            "territories": type_counts["territory"],
            "autonomous_jurisdictions": type_counts["autonomous_jurisdiction"],
            "with_authority_onboarded": count_ready("has_authority"),
            "with_official_source_onboarded": count_ready("has_official_source"),
            "with_authority": count_ready("has_reviewed_primary_authority"),
            "with_official_source": count_ready("has_reviewed_primary_source"),
            "with_fresh_monitor": count_ready("has_fresh_monitor"),
            "with_verified_rule": count_ready("has_verified_rule"),
            "coverage_ready": sum(row["coverage_ready"] for row in required),
            "immigration_rule_assessed": sum(
                row["immigration_rule_status"] in CLEAR_IMMIGRATION_RULE_RELATIONSHIPS
                for row in required
            ),
            "assessments_pending_review": len(pending_assessments),
            "source_certifications_pending_review": len(pending_certifications),
        },
        "release_gate": {
            "registry_complete": registry_complete,
            "authority_coverage_complete": authority_complete,
            "source_coverage_complete": source_complete,
            "monitor_coverage_complete": monitor_complete,
            "verified_rule_coverage_complete": rule_complete,
            "immigration_rule_assessment_complete": assessment_complete,
            "global_coverage_claim_ready": global_ready,
            "message": (
                "Global coverage release gate passed."
                if global_ready
                else "Global coverage cannot be claimed until every required registry entry passes authority, source, freshness, rule, and immigration-rule assessment gates."
            ),
        },
        "regions": regions,
        "entries": rows,
    }
