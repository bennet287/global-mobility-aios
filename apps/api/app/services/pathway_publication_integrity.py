from __future__ import annotations

from sqlmodel import Session

from app.models.domain import MobilityPathway, MobilityPathwayVersion
from app.services.pathway_catalogue import _publication_evidence_blockers


def pathway_publication_integrity_blockers(
    session: Session,
    pathway: MobilityPathway,
    version: MobilityPathwayVersion,
) -> list[str]:
    """Return the accepted deterministic blockers for pathway publication integrity.

    This module is the public cross-slice contract for consumers such as Decision
    Readiness. The catalogue remains the implementation owner for now so G.4.1 does
    not duplicate publication semantics or alter publication behavior. Only this
    compatibility adapter reaches the catalogue's historical private implementation;
    downstream organization services must import this public contract instead.
    """

    return _publication_evidence_blockers(session, pathway, version)
