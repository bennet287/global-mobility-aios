#!/usr/bin/env python3
"""Create or resolve the immutable Austria v4 occupation-evidence draft.

The operation is idempotent and deliberately performs no certification review,
publication, or external action. It derives every pinned projection identity from
the already materialized 2026 national and regional evidence rows.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

API_PATH = Path(__file__).resolve().parents[1] / "apps" / "api"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from sqlmodel import Session, select  # noqa: E402

from app.core.db import engine, register_models  # noqa: E402
from app.models.domain import (  # noqa: E402
    MobilityPathway,
    MobilityPathwayVersion,
    ShortageOccupationEntry,
)
from app.schemas import PathwayStructuredOccupationIntegrationRequest  # noqa: E402
from app.services.pathway_catalogue import integrate_structured_occupation_evidence  # noqa: E402
from app.services.shortage_occupations import shortage_occupation_projection_summary  # noqa: E402


PATHWAY_KEY = "at-rwr-skilled-worker-shortage-occupation"


def _snapshot_id(session: Session, scope: str):
    rows = list(session.exec(
        select(ShortageOccupationEntry).where(
            ShortageOccupationEntry.year == 2026,
            ShortageOccupationEntry.scope == scope,
        )
    ).all())
    snapshot_ids = {row.source_snapshot_id for row in rows}
    if len(snapshot_ids) != 1:
        raise RuntimeError(
            f"Expected exactly one materialized Austria 2026 {scope} snapshot; found {len(snapshot_ids)}"
        )
    return next(iter(snapshot_ids))


def main() -> None:
    register_models()
    with Session(engine) as session:
        pathway = session.exec(
            select(MobilityPathway).where(MobilityPathway.pathway_key == PATHWAY_KEY)
        ).one()
        source_version = session.exec(
            select(MobilityPathwayVersion).where(
                MobilityPathwayVersion.pathway_id == pathway.id,
                MobilityPathwayVersion.version_number == 3,
            )
        ).one()
        national = shortage_occupation_projection_summary(
            session,
            source_snapshot_id=_snapshot_id(session, "national"),
            year=2026,
            scope="national",
        )
        regional = shortage_occupation_projection_summary(
            session,
            source_snapshot_id=_snapshot_id(session, "regional"),
            year=2026,
            scope="regional",
        )
        payload = PathwayStructuredOccupationIntegrationRequest(
            source_version_id=source_version.id,
            year=2026,
            national_source_snapshot_id=national["source_snapshot_id"],
            regional_source_snapshot_id=regional["source_snapshot_id"],
            expected_national_entry_count=national["entry_count"],
            expected_regional_entry_count=regional["entry_count"],
            expected_national_entry_set_sha256=national["entry_set_sha256"],
            expected_regional_entry_set_sha256=regional["entry_set_sha256"],
            expected_national_snapshot_content_hash=national["source_snapshot_content_hash"],
            expected_regional_snapshot_content_hash=regional["source_snapshot_content_hash"],
        )
        result = integrate_structured_occupation_evidence(
            session,
            pathway.id,
            payload,
            actor="phase-13.10.2.13-integration",
        )
        print(json.dumps({
            "created": result.created,
            "pathway_id": str(pathway.id),
            "pathway_version_id": str(result.pathway_version.id),
            "version_number": result.pathway_version.version_number,
            "lifecycle_status": result.pathway_version.lifecycle_status,
            "publication_ready": result.publication_readiness.ready,
            "publication_blockers": result.publication_readiness.blockers,
            "evidence_roles": [
                link.evidence_role for link in result.pathway_version.evidence_links
            ],
            "certification_statuses": result.publication_readiness.evidence_certification_statuses,
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
