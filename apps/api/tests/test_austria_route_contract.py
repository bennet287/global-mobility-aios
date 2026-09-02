from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
)
from app.services.pathway_catalogue import PATHWAY_REQUIRED_EVIDENCE_ROLES


CANONICAL_AUSTRIA_SHORTAGE_PATHWAY_KEY = "at-rwr-skilled-worker-shortage-occupation"


def test_austria_objective_route_matches_production_catalogue_identity() -> None:
    assert AUSTRIA_MOBILITY_OBJECTIVE_ROUTE == CANONICAL_AUSTRIA_SHORTAGE_PATHWAY_KEY
    assert AUSTRIA_MOBILITY_OBJECTIVE_ROUTE in PATHWAY_REQUIRED_EVIDENCE_ROLES
