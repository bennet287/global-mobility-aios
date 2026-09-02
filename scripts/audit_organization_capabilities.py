#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database_url import is_sqlite_url, mask_database_url, normalize_database_url  # noqa: E402
from app.models.domain import OrganizationPosition  # noqa: E402
from app.services.organization_capability_architecture import (  # noqa: E402
    CURRENT_EXECUTIVE_POSITIONS,
    MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS,
    ORGANIZATION_CAPABILITY_DOMAINS,
    TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS,
    capability_position_map,
    planned_position_keys,
    review_position_keys,
)
from app.services.organization_governance import POSITION_SPECS  # noqa: E402


def _foundation_map() -> dict[str, dict[str, Any]]:
    return {
        key: {
            "title": title,
            "department": department,
            "reports_to_position_key": reports_to,
            "authority_level": authority,
        }
        for key, title, department, reports_to, authority, _role_card in POSITION_SPECS
    }


def _live_positions(database_url: str) -> list[OrganizationPosition]:
    connect_args = {"check_same_thread": False} if is_sqlite_url(database_url) else {}
    engine = create_engine(database_url, connect_args=connect_args)
    with Session(engine) as session:
        return list(
            session.exec(
                select(OrganizationPosition).where(
                    OrganizationPosition.version == 1,
                    OrganizationPosition.status == "active",
                )
            ).all()
        )


def audit(database_url: str | None) -> dict[str, Any]:
    foundation = _foundation_map()
    architecture = capability_position_map()
    foundation_non_exec = set(foundation) - {"board", "ceo"} - set(CURRENT_EXECUTIVE_POSITIONS)
    mapped_existing = {
        key for key, position in architecture.items() if position.status in {"existing", "review"}
    }

    domains_by_owner: dict[str, int] = Counter(
        domain.executive_position for domain in ORGANIZATION_CAPABILITY_DOMAINS
    )
    planned_by_owner: dict[str, int] = Counter()
    for domain in ORGANIZATION_CAPABILITY_DOMAINS:
        planned_by_owner[domain.executive_position] += sum(
            1 for position in domain.positions if position.status == "planned"
        )

    result: dict[str, Any] = {
        "foundation_position_count": len(foundation),
        "foundation_executive_count": len(CURRENT_EXECUTIVE_POSITIONS),
        "foundation_non_executive_position_count": len(foundation_non_exec),
        "mapped_existing_or_review_position_count": len(mapped_existing),
        "unmapped_foundation_position_keys": sorted(foundation_non_exec - mapped_existing),
        "architecture_domain_count": len(ORGANIZATION_CAPABILITY_DOMAINS),
        "planned_position_count": len(planned_position_keys()),
        "review_position_keys": sorted(review_position_keys()),
        "domains_by_owner": dict(sorted(domains_by_owner.items())),
        "planned_positions_by_owner": dict(sorted(planned_by_owner.items())),
        "technology_security_foundation_tranche_keys": sorted(TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS),
        "mobility_operations_intelligence_legal_foundation_tranche_keys": sorted(
            MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS
        ),
        "runtime_mutation_performed": False,
    }

    if database_url is not None:
        normalized = normalize_database_url(database_url)
        live = _live_positions(normalized)
        live_by_key = {position.position_key: position for position in live}
        live_rows_by_key: dict[str, list[OrganizationPosition]] = defaultdict(list)
        for position in live:
            live_rows_by_key[position.position_key].append(position)
        duplicate_rows = {
            key: rows for key, rows in live_rows_by_key.items() if len(rows) > 1
        }
        duplicate_keys = sorted(duplicate_rows)
        redundant_row_count = sum(len(rows) - 1 for rows in duplicate_rows.values())
        extra_keys = set(live_by_key) - set(foundation)
        missing_keys = set(foundation) - set(live_by_key)
        result.update(
            {
                "database_url": mask_database_url(normalized),
                "live_active_position_row_count": len(live),
                "live_active_position_count": len(live_by_key),
                "live_duplicate_active_position_keys": duplicate_keys,
                "live_duplicate_active_position_row_count": redundant_row_count,
                "live_duplicate_active_position_ids_by_key": {
                    key: [str(row.id) for row in sorted(rows, key=lambda item: (item.created_at, str(item.id)))]
                    for key, rows in sorted(duplicate_rows.items())
                },
                "live_extra_position_keys": sorted(extra_keys),
                "live_missing_foundation_keys": sorted(missing_keys),
                "live_missing_technology_security_tranche_keys": sorted(
                    TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS - set(live_by_key)
                ),
                "live_missing_mobility_operations_intelligence_legal_tranche_keys": sorted(
                    MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS
                    - set(live_by_key)
                ),
                "live_status": "reconcile_required"
                if extra_keys or missing_keys or duplicate_keys
                else "matches_foundation",
            }
        )
    else:
        result["database_url"] = None
        result["live_status"] = "not_checked"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only audit of the current organization foundation against the Phase 13.16.3 "
            "capability architecture. This script never creates, updates, or deletes positions."
        )
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional database URL for live active-position reconciliation. Omit for code-only audit.",
    )
    parser.add_argument("--use-configured-database", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    database_url = settings.database_url if args.use_configured_database else args.database_url
    result = audit(database_url)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Organization capability architecture audit")
    print(f"foundation_positions={result['foundation_position_count']}")
    print(f"foundation_executives={result['foundation_executive_count']}")
    print(f"foundation_non_executive_positions={result['foundation_non_executive_position_count']}")
    print(f"mapped_existing_or_review={result['mapped_existing_or_review_position_count']}")
    print(f"architecture_domains={result['architecture_domain_count']}")
    print(f"planned_positions={result['planned_position_count']}")
    print("review_position_keys=" + json.dumps(result["review_position_keys"]))
    print("unmapped_foundation_position_keys=" + json.dumps(result["unmapped_foundation_position_keys"]))
    print("domains_by_owner=" + json.dumps(result["domains_by_owner"], sort_keys=True))
    print("planned_positions_by_owner=" + json.dumps(result["planned_positions_by_owner"], sort_keys=True))
    print("technology_security_foundation_tranche_keys=" + json.dumps(result["technology_security_foundation_tranche_keys"]))
    print(
        "mobility_operations_intelligence_legal_foundation_tranche_keys="
        + json.dumps(result["mobility_operations_intelligence_legal_foundation_tranche_keys"])
    )
    print(f"live_status={result['live_status']}")
    if result["database_url"]:
        print(f"database_url={result['database_url']}")
        print(f"live_active_position_rows={result['live_active_position_row_count']}")
        print(f"live_active_positions={result['live_active_position_count']}")
        print(
            "live_duplicate_active_position_keys="
            + json.dumps(result["live_duplicate_active_position_keys"])
        )
        print(
            f"live_duplicate_active_position_row_count="
            f"{result['live_duplicate_active_position_row_count']}"
        )
        print(
            "live_duplicate_active_position_ids_by_key="
            + json.dumps(result["live_duplicate_active_position_ids_by_key"], sort_keys=True)
        )
        print("live_extra_position_keys=" + json.dumps(result["live_extra_position_keys"]))
        print("live_missing_foundation_keys=" + json.dumps(result["live_missing_foundation_keys"]))
        print(
            "live_missing_technology_security_tranche_keys="
            + json.dumps(result["live_missing_technology_security_tranche_keys"])
        )
        print(
            "live_missing_mobility_operations_intelligence_legal_tranche_keys="
            + json.dumps(result["live_missing_mobility_operations_intelligence_legal_tranche_keys"])
        )
    print("runtime_mutation_performed=false")
    print(
        "next=Resolve any duplicate active position identity first; otherwise, if live drift is limited "
        "to the currently reviewed bounded tranche, run scripts/apply_organization_foundation_tranche.py "
        "with the matching --tranche in preflight mode before --apply."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
