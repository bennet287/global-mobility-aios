from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
)


CORE_EVIDENCE_ROLE = "core_route"


def pathway_version_evidence_rows(
    session: Session,
    version: MobilityPathwayVersion,
    *,
    include_legacy_fallback: bool = True,
) -> list[MobilityPathwayVersionEvidence]:
    """Return deterministic pathway-version evidence rows.

    Migration 0070 backfills historical versions with a normalized core-route
    evidence row.  The in-memory fallback keeps direct test fixtures and any
    deliberately unmigrated read-only database snapshot compatible while the
    normalized table remains the source of truth after migration.
    """
    rows = list(
        session.exec(
            select(MobilityPathwayVersionEvidence)
            .where(MobilityPathwayVersionEvidence.pathway_version_id == version.id)
            .order_by(
                MobilityPathwayVersionEvidence.evidence_role,
                MobilityPathwayVersionEvidence.created_at,
                MobilityPathwayVersionEvidence.id,
            )
        ).all()
    )
    if not include_legacy_fallback:
        return rows
    if not version.official_source_id or not version.source_snapshot_id:
        return rows
    if any(row.evidence_role == CORE_EVIDENCE_ROLE for row in rows):
        return rows
    legacy_core = MobilityPathwayVersionEvidence(
        id=version.id,
        pathway_version_id=version.id,
        evidence_role=CORE_EVIDENCE_ROLE,
        official_source_id=version.official_source_id,
        source_snapshot_id=version.source_snapshot_id,
        required_for_publication=True,
        metadata_json="{}",
        created_at=version.created_at,
    )
    return [legacy_core, *rows]


def pathway_version_evidence_pairs(
    session: Session,
    version: MobilityPathwayVersion,
) -> set[tuple[UUID, UUID]]:
    return {
        (row.official_source_id, row.source_snapshot_id)
        for row in pathway_version_evidence_rows(session, version)
    }


def pathway_version_evidence_source_ids(
    session: Session,
    version: MobilityPathwayVersion,
) -> list[UUID]:
    return list(
        dict.fromkeys(
            row.official_source_id
            for row in pathway_version_evidence_rows(session, version)
        )
    )


def pathway_version_evidence_snapshot_ids(
    session: Session,
    version: MobilityPathwayVersion,
) -> list[UUID]:
    return list(
        dict.fromkeys(
            row.source_snapshot_id
            for row in pathway_version_evidence_rows(session, version)
        )
    )
