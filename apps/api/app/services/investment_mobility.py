from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    InvestmentMobilityProgram,
    InvestmentMobilityProgramVersion,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    SourceSnapshot,
    now_utc,
)
from app.schemas_investment_mobility import (
    InvestmentProgramCreate,
    InvestmentProgramRead,
    InvestmentProgramVersionInput,
    InvestmentProgramVersionRead,
)
from app.services.audit_log import record_audit


ALLOWED_PATHWAY_DOMAINS = {"investment", "wealth", "business", "entrepreneur"}


def _dump(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def _load(value: str | None, default: Any) -> Any:
    return json.loads(value) if value else default


def _normal(value: str) -> str:
    return value.strip().lower()


def investment_version_read(row: InvestmentMobilityProgramVersion) -> InvestmentProgramVersionRead:
    return InvestmentProgramVersionRead(
        **row.model_dump(),
        investment_options=_load(row.investment_options_json, []),
        family_scope=_load(row.family_scope_json, []),
        due_diligence=_load(row.due_diligence_json, []),
        fees=_load(row.fees_json, {}),
        benefits=_load(row.benefits_json, []),
        risks=_load(row.risks_json, []),
    )


def investment_program_read(session: Session, row: InvestmentMobilityProgram) -> InvestmentProgramRead:
    versions = list(session.exec(
        select(InvestmentMobilityProgramVersion)
        .where(InvestmentMobilityProgramVersion.program_id == row.id)
        .order_by(InvestmentMobilityProgramVersion.version_number.desc())
    ).all())
    published = next((item for item in versions if item.lifecycle_status == "published"), None)
    current = published or (versions[0] if versions else None)
    return InvestmentProgramRead(
        **row.model_dump(),
        current_version=investment_version_read(current) if current else None,
        versions=[investment_version_read(version) for version in versions],
    )


def _validate_grounding(
    session: Session,
    *,
    pathway_id: UUID,
    country: str,
    payload: InvestmentProgramVersionInput,
) -> tuple[MobilityPathway, MobilityPathwayVersion, OfficialSource, SourceSnapshot]:
    pathway = session.get(MobilityPathway, pathway_id)
    if pathway is None:
        raise ValueError("Mobility pathway not found")
    if pathway.catalogue_status != "active" or _normal(pathway.domain) not in ALLOWED_PATHWAY_DOMAINS:
        raise ValueError("An active published business, wealth, entrepreneur, or investment pathway is required")
    if _normal(pathway.country) != _normal(country):
        raise ValueError("Program country must match the mobility pathway")

    pathway_version = session.get(MobilityPathwayVersion, payload.pathway_version_id)
    if pathway_version is None or pathway_version.pathway_id != pathway.id:
        raise ValueError("Pathway version does not belong to the selected pathway")
    if pathway_version.lifecycle_status != "published":
        raise ValueError("A published pathway version is required")

    source = session.get(OfficialSource, payload.official_source_id)
    if source is None or not source.active:
        raise ValueError("An active official source is required")
    if _normal(source.country) != _normal(country):
        raise ValueError("Official source country must match the program")

    snapshot = session.get(SourceSnapshot, payload.source_snapshot_id)
    if snapshot is None or snapshot.official_source_id != source.id:
        raise ValueError("A snapshot from the selected official source is required")
    if not snapshot.content_hash or snapshot.status in {"failed", "rejected"}:
        raise ValueError("A content-addressed source snapshot is required")
    return pathway, pathway_version, source, snapshot


def _create_version(
    session: Session,
    program: InvestmentMobilityProgram,
    payload: InvestmentProgramVersionInput,
    *,
    actor: str,
) -> InvestmentMobilityProgramVersion:
    _validate_grounding(session, pathway_id=program.pathway_id, country=program.country, payload=payload)
    existing = list(session.exec(
        select(InvestmentMobilityProgramVersion)
        .where(InvestmentMobilityProgramVersion.program_id == program.id)
        .order_by(InvestmentMobilityProgramVersion.version_number.desc())
    ).all())
    if existing and existing[0].lifecycle_status == "draft":
        raise ValueError("Publish or discard the current draft before creating another version")
    now = now_utc()
    row = InvestmentMobilityProgramVersion(
        program_id=program.id,
        version_number=(existing[0].version_number + 1) if existing else 1,
        supersedes_version_id=existing[0].id if existing else None,
        pathway_version_id=payload.pathway_version_id,
        official_source_id=payload.official_source_id,
        source_snapshot_id=payload.source_snapshot_id,
        minimum_commitment_minor=payload.minimum_commitment_minor,
        currency=payload.currency,
        investment_options_json=_dump(payload.investment_options),
        holding_period_text=payload.holding_period_text,
        physical_presence_text=payload.physical_presence_text,
        family_scope_json=_dump(payload.family_scope),
        due_diligence_json=_dump(payload.due_diligence),
        fees_json=_dump(payload.fees),
        benefits_json=_dump(payload.benefits),
        risks_json=_dump(payload.risks),
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        created_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    return row


def create_investment_program(
    session: Session, payload: InvestmentProgramCreate, *, actor: str,
) -> InvestmentMobilityProgram:
    key = _normal(payload.program_key).replace(" ", "-")
    if session.exec(select(InvestmentMobilityProgram).where(InvestmentMobilityProgram.program_key == key)).first():
        raise ValueError("Investment program key already exists")
    _validate_grounding(session, pathway_id=payload.pathway_id, country=payload.country, payload=payload)
    now = now_utc()
    program = InvestmentMobilityProgram(
        program_key=key,
        name=payload.name.strip(),
        country=_normal(payload.country),
        program_type=payload.program_type,
        pathway_id=payload.pathway_id,
        description=payload.description,
        created_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(program)
    session.flush()
    version = _create_version(session, program, payload, actor=actor)
    record_audit(session, action="investment_mobility_program_created", entity_type="investment_mobility_program",
                 entity_id=program.id, after_state={"program": program.model_dump(mode="json"), "version": version.model_dump(mode="json")},
                 reason="Created evidence-grounded investment program draft", actor=actor, source="investment_mobility_v11_5")
    session.commit()
    session.refresh(program)
    return program


def create_investment_program_version(
    session: Session, program_id: UUID, payload: InvestmentProgramVersionInput, *, actor: str,
) -> InvestmentMobilityProgramVersion:
    program = session.get(InvestmentMobilityProgram, program_id)
    if program is None:
        raise ValueError("Investment program not found")
    if program.catalogue_status == "retired":
        raise ValueError("Retired investment programs cannot receive new versions")
    version = _create_version(session, program, payload, actor=actor)
    program.updated_at = now_utc()
    session.add(program)
    record_audit(session, action="investment_mobility_program_version_created", entity_type="investment_mobility_program_version",
                 entity_id=version.id, after_state=version, reason=f"Created draft version {version.version_number}",
                 actor=actor, source="investment_mobility_v11_5")
    session.commit()
    session.refresh(version)
    return version


def publish_investment_program_version(
    session: Session, version_id: UUID, *, actor: str, review_notes: str,
) -> InvestmentMobilityProgram:
    version = session.get(InvestmentMobilityProgramVersion, version_id)
    if version is None:
        raise ValueError("Investment program version not found")
    if version.lifecycle_status != "draft":
        raise ValueError("Only draft investment program versions can be published")
    if version.created_by == actor:
        raise ValueError("Investment program publication requires an independent reviewer")
    program = session.get(InvestmentMobilityProgram, version.program_id)
    if program is None or program.catalogue_status == "retired":
        raise ValueError("Investment program is not publishable")
    payload = InvestmentProgramVersionInput(
        pathway_version_id=version.pathway_version_id,
        official_source_id=version.official_source_id,
        source_snapshot_id=version.source_snapshot_id,
        minimum_commitment_minor=version.minimum_commitment_minor,
        currency=version.currency,
        investment_options=_load(version.investment_options_json, []),
        holding_period_text=version.holding_period_text,
        physical_presence_text=version.physical_presence_text,
        family_scope=_load(version.family_scope_json, []),
        due_diligence=_load(version.due_diligence_json, []),
        fees=_load(version.fees_json, {}),
        benefits=_load(version.benefits_json, []),
        risks=_load(version.risks_json, []),
        effective_from=version.effective_from,
        effective_to=version.effective_to,
    )
    _validate_grounding(session, pathway_id=program.pathway_id, country=program.country, payload=payload)
    now = now_utc()
    previous_rows = session.exec(select(InvestmentMobilityProgramVersion).where(
        InvestmentMobilityProgramVersion.program_id == program.id,
        InvestmentMobilityProgramVersion.lifecycle_status == "published",
    )).all()
    for previous in previous_rows:
        previous.lifecycle_status = "superseded"
        previous.updated_at = now
        session.add(previous)
    version.lifecycle_status = "published"
    version.approved_by = actor
    version.review_notes = review_notes
    version.published_at = now
    version.updated_at = now
    program.catalogue_status = "active"
    program.updated_at = now
    session.add(version)
    session.add(program)
    record_audit(session, action="investment_mobility_program_version_published", entity_type="investment_mobility_program_version",
                 entity_id=version.id, before_state={"lifecycle_status": "draft"}, after_state=version,
                 reason=review_notes, actor=actor, source="investment_mobility_v11_5")
    session.commit()
    session.refresh(program)
    return program
