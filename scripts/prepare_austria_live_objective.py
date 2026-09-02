#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import create_engine
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database_url import (  # noqa: E402
    is_sqlite_url,
    mask_database_url,
    normalize_database_url,
)
from app.models.domain import (  # noqa: E402
    CountryPolicy,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    OrganizationActorType,
    OrganizationPosition,
    SourceMonitor,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.organization_command import OrganizationCommandContext  # noqa: E402
from app.services.organization_mobility_objective_runtime import (  # noqa: E402
    AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
    AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    create_austria_mobility_objective,
)


CLI_CONTRACT_VERSION = "austria-live-objective-preparation-cli.v1"
_REQUIRED_POSITIONS = (
    AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
)


def _json(value: object) -> str:
    return json.dumps(value, default=str, indent=2, sort_keys=True)


def _engine(database_url: str):
    normalized = normalize_database_url(database_url)
    connect_args = {"check_same_thread": False} if is_sqlite_url(normalized) else {}
    return create_engine(normalized, connect_args=connect_args), normalized


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _effective_now(
    *,
    effective_from: datetime | None,
    effective_to: datetime | None,
    current: datetime,
) -> bool:
    now = _utc(current)
    if effective_from is not None and _utc(effective_from) > now:
        return False
    if effective_to is not None and _utc(effective_to) < now:
        return False
    return True


def _json_object(raw: str | None) -> bool:
    try:
        value = json.loads(raw or "{}")
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(value, dict)


def _uuid_list(raw: str | None) -> tuple[UUID, ...] | None:
    try:
        value = json.loads(raw or "[]")
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(value, list):
        return None
    result: list[UUID] = []
    try:
        for item in value:
            result.append(UUID(str(item)))
    except (TypeError, ValueError, AttributeError):
        return None
    if len(result) != len(set(result)):
        return None
    return tuple(result)


def _canonical_pathway(
    session: Session,
) -> tuple[MobilityPathway | None, list[str]]:
    rows = list(
        session.exec(
            select(MobilityPathway).where(
                MobilityPathway.pathway_key == AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
            )
        ).all()
    )
    rows = [
        row
        for row in rows
        if row.country.strip().casefold() == "austria"
        and row.catalogue_status == "active"
    ]
    if not rows:
        return None, ["canonical_published_austria_pathway_missing"]
    if len(rows) != 1:
        return None, ["canonical_published_austria_pathway_ambiguous"]
    return rows[0], []


def _observed_austria_pathways(session: Session) -> list[dict[str, object]]:
    rows = list(session.exec(select(MobilityPathway)).all())
    result = [
        {
            "pathway_id": str(row.id),
            "pathway_key": row.pathway_key,
            "catalogue_status": row.catalogue_status,
        }
        for row in rows
        if row.country.strip().casefold() == "austria"
    ]
    result.sort(key=lambda item: (str(item["pathway_key"]), str(item["pathway_id"])))
    return result


def _current_published_version(
    session: Session,
    pathway: MobilityPathway,
    *,
    current: datetime,
) -> tuple[MobilityPathwayVersion | None, list[str]]:
    rows = list(
        session.exec(
            select(MobilityPathwayVersion).where(
                MobilityPathwayVersion.pathway_id == pathway.id,
                MobilityPathwayVersion.lifecycle_status == "published",
                MobilityPathwayVersion.published_at.is_not(None),
            )
        ).all()
    )
    rows = [
        row
        for row in rows
        if _effective_now(
            effective_from=row.effective_from,
            effective_to=row.effective_to,
            current=current,
        )
    ]
    if not rows:
        return None, ["current_published_austria_pathway_version_missing"]
    rows.sort(
        key=lambda row: (
            row.version_number,
            _utc(row.published_at) if row.published_at is not None else datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )
    return rows[0], []


def _authority_preflight(
    session: Session,
    pathway: MobilityPathway,
    version: MobilityPathwayVersion,
    *,
    current: datetime,
) -> dict[str, object]:
    blockers: list[str] = []
    evidence_rows = list(
        session.exec(
            select(MobilityPathwayVersionEvidence).where(
                MobilityPathwayVersionEvidence.pathway_version_id == version.id
            )
        ).all()
    )
    if not evidence_rows:
        blockers.append("mobility_pathway_version_evidence_missing")

    for evidence in evidence_rows:
        if not _json_object(evidence.metadata_json):
            blockers.append(f"pathway_evidence_metadata_invalid:{evidence.id}")

    rule_ids = _uuid_list(version.verified_rule_ids_json)
    if rule_ids is None:
        blockers.append("verified_rule_ids_invalid")
        rule_ids = ()
    if not rule_ids:
        blockers.append("verified_rules_missing")

    rules: list[VerifiedRule] = []
    for rule_id in rule_ids:
        rule = session.get(VerifiedRule, rule_id)
        if rule is None:
            blockers.append(f"verified_rule_missing:{rule_id}")
            continue
        rules.append(rule)
        if not rule.active or rule.retired_at is not None:
            blockers.append(f"verified_rule_not_active:{rule.id}")
        if rule.published_at is None:
            blockers.append(f"verified_rule_not_published:{rule.id}")
        if not _effective_now(
            effective_from=rule.effective_from,
            effective_to=rule.effective_to,
            current=current,
        ):
            blockers.append(f"verified_rule_outside_effective_window:{rule.id}")
        if (
            rule.country.strip().casefold() != pathway.country.strip().casefold()
            or rule.domain.strip().casefold() != pathway.domain.strip().casefold()
        ):
            blockers.append(f"verified_rule_scope_mismatch:{rule.id}")
        if rule.source_snapshot_id is None:
            blockers.append(f"verified_rule_snapshot_missing:{rule.id}")

    policy_rows = list(
        session.exec(
            select(CountryPolicy).where(
                CountryPolicy.country == pathway.country,
                CountryPolicy.domain == pathway.domain,
                CountryPolicy.status == "active",
            )
        ).all()
    )
    if not policy_rows:
        blockers.append("active_country_policy_missing")
    elif len(policy_rows) > 1:
        blockers.append("active_country_policy_ambiguous")
    elif not _json_object(policy_rows[0].policy_json):
        blockers.append("active_country_policy_invalid_json")

    snapshot_ids: set[UUID] = set()
    snapshot_expected_source: dict[UUID, set[UUID]] = {}

    def remember_snapshot(snapshot_id: UUID | None, source_id: UUID | None) -> None:
        if snapshot_id is None:
            return
        snapshot_ids.add(snapshot_id)
        if source_id is not None:
            snapshot_expected_source.setdefault(snapshot_id, set()).add(source_id)

    remember_snapshot(version.source_snapshot_id, version.official_source_id)
    for evidence in evidence_rows:
        remember_snapshot(evidence.source_snapshot_id, evidence.official_source_id)
    for rule in rules:
        remember_snapshot(rule.source_snapshot_id, rule.official_source_id)

    if not snapshot_ids:
        blockers.append("governed_source_snapshots_missing")

    official_source_ids: set[UUID] = set()
    snapshots: list[SourceSnapshot] = []
    for snapshot_id in sorted(snapshot_ids, key=str):
        snapshot = session.get(SourceSnapshot, snapshot_id)
        if snapshot is None:
            blockers.append(f"source_snapshot_missing:{snapshot_id}")
            continue
        snapshots.append(snapshot)
        if not (snapshot.content_hash or "").strip():
            blockers.append(f"source_snapshot_content_hash_missing:{snapshot.id}")
        if snapshot.official_source_id is None:
            blockers.append(f"source_snapshot_official_source_missing:{snapshot.id}")
            continue
        expected = snapshot_expected_source.get(snapshot.id, set())
        if expected and expected != {snapshot.official_source_id}:
            blockers.append(f"source_snapshot_official_source_mismatch:{snapshot.id}")
        official_source_ids.add(snapshot.official_source_id)

    if version.official_source_id is not None:
        official_source_ids.add(version.official_source_id)

    sources: list[OfficialSource] = []
    active_monitors: list[SourceMonitor] = []
    for source_id in sorted(official_source_ids, key=str):
        source = session.get(OfficialSource, source_id)
        if source is None:
            blockers.append(f"official_source_missing:{source_id}")
            continue
        sources.append(source)
        if not source.active:
            blockers.append(f"official_source_inactive:{source.id}")
        monitors = list(
            session.exec(
                select(SourceMonitor).where(SourceMonitor.official_source_id == source.id)
            ).all()
        )
        if len(monitors) != 1:
            blockers.append(f"source_monitor_count_invalid:{source.id}:{len(monitors)}")
            continue
        monitor = monitors[0]
        if (monitor.status or "").strip().casefold() != "active":
            blockers.append(f"source_monitor_inactive:{monitor.id}")
        else:
            active_monitors.append(monitor)

    positions: list[OrganizationPosition] = []
    for position_key in _REQUIRED_POSITIONS:
        rows = list(
            session.exec(
                select(OrganizationPosition).where(
                    OrganizationPosition.position_key == position_key,
                    OrganizationPosition.status == "active",
                )
            ).all()
        )
        if len(rows) != 1:
            blockers.append(f"active_organization_position_count_invalid:{position_key}:{len(rows)}")
            continue
        positions.append(rows[0])
        if not _json_object(rows[0].contract_json):
            blockers.append(f"organization_position_contract_invalid:{position_key}")

    unique_blockers = sorted(set(blockers))
    return {
        "authority_ready": not unique_blockers,
        "blockers": unique_blockers,
        "evidence_count": len(evidence_rows),
        "verified_rule_count": len(rules),
        "source_snapshot_count": len(snapshots),
        "official_source_count": len(sources),
        "active_source_monitor_count": len(active_monitors),
        "active_required_position_count": len(positions),
    }


def assess_candidate_creation(
    session: Session,
    *,
    database_url: str,
    tenant_key: str,
    current: datetime | None = None,
) -> dict[str, object]:
    now = current or now_utc()
    blockers: list[str] = []
    observed_austria_pathways = _observed_austria_pathways(session)
    pathway, pathway_blockers = _canonical_pathway(session)
    blockers.extend(pathway_blockers)
    version: MobilityPathwayVersion | None = None
    authority: dict[str, object] = {
        "authority_ready": False,
        "blockers": [],
        "evidence_count": 0,
        "verified_rule_count": 0,
        "source_snapshot_count": 0,
        "official_source_count": 0,
        "active_source_monitor_count": 0,
        "active_required_position_count": 0,
    }
    if pathway is not None:
        version, version_blockers = _current_published_version(
            session,
            pathway,
            current=now,
        )
        blockers.extend(version_blockers)
    if pathway is not None and version is not None:
        authority = _authority_preflight(
            session,
            pathway,
            version,
            current=now,
        )
        blockers.extend(str(item) for item in authority["blockers"])

    unique_blockers = sorted(set(blockers))
    return {
        "contract_version": CLI_CONTRACT_VERSION,
        "mode": "check-source",
        "database_url": mask_database_url(normalize_database_url(database_url)),
        "tenant_key": tenant_key,
        "route_key": AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
        "observed_austria_pathways": observed_austria_pathways,
        "pathway_id": str(pathway.id) if pathway is not None else None,
        "pathway_version_id": str(version.id) if version is not None else None,
        "pathway_version_number": version.version_number if version is not None else None,
        "candidate_creation_ready": not unique_blockers,
        "blockers": unique_blockers,
        "evidence_count": authority["evidence_count"],
        "verified_rule_count": authority["verified_rule_count"],
        "source_snapshot_count": authority["source_snapshot_count"],
        "official_source_count": authority["official_source_count"],
        "active_source_monitor_count": authority["active_source_monitor_count"],
        "active_required_position_count": authority["active_required_position_count"],
        "provider_invoked": False,
        "external_action_authorized": False,
        "secrets_exposed": False,
    }


def _operator_context(tenant_key: str, objective_key: str) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id="local-l-acceptance-operator",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="local-l-acceptance-operator",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
        request_id=str(uuid4()),
        correlation_key=f"l-acceptance-objective:{objective_key}",
    )


def create_candidate(
    session: Session,
    *,
    assessment: dict[str, object],
    tenant_key: str,
    objective_key: str,
) -> dict[str, object]:
    if assessment.get("candidate_creation_ready") is not True:
        raise ValueError("Austria live-objective source preflight is not ready")
    pathway_version_id = assessment.get("pathway_version_id")
    if not isinstance(pathway_version_id, str):
        raise ValueError("Austria live-objective preflight did not resolve a pathway version")
    plan = create_austria_mobility_objective(
        session,
        _operator_context(tenant_key, objective_key),
        objective_key=objective_key,
        pathway_version_id=UUID(pathway_version_id),
    )
    specialists = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: plan.pathway_work_item,
        AUSTRIA_MOBILITY_REGULATORY_POSITION: plan.regulatory_work_item,
    }
    fresh = (
        plan.root_work_item.status not in {"completed", "cancelled", "failed", "rejected", "returned"}
        and all(
            work.status in {"queued", "running"}
            and work.execution_attempts < work.max_execution_attempts
            for work in specialists.values()
        )
    )
    return {
        "contract_version": CLI_CONTRACT_VERSION,
        "mode": "create",
        "tenant_key": tenant_key,
        "route_key": AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
        "objective_key": objective_key,
        "pathway_version_id": pathway_version_id,
        "pathway_version_number": assessment.get("pathway_version_number"),
        "root_work_item_id": str(plan.root_work_item.id),
        "root_status": plan.root_work_item.status,
        "fresh_live_execution_candidate": fresh,
        "specialists": {
            position_key: {
                "work_item_id": str(work.id),
                "status": work.status,
                "execution_attempts": work.execution_attempts,
                "max_execution_attempts": work.max_execution_attempts,
                "source_object_type": work.source_object_type,
                "source_object_id": work.source_object_id,
                "source_object_version": work.source_object_version,
            }
            for position_key, work in specialists.items()
        },
        "provider_invoked": False,
        "external_action_authorized": False,
        "secrets_exposed": False,
    }


def _default_objective_key() -> str:
    timestamp = now_utc().astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"l-acceptance-at-rwr-shortage-{timestamp}-{uuid4().hex[:8]}"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight and create one source-grounded, untouched Austria J.1 objective for L live-provider "
            "acceptance. Source readiness is checked before durable WorkItems are created. This command "
            "never invokes a model/provider and never authorizes external action."
        )
    )
    parser.add_argument("--database-url", default=settings.database_url)
    parser.add_argument("--tenant-key", default="default")
    parser.add_argument("--objective-key")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check-source", action="store_true")
    modes.add_argument("--create", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    tenant_key = args.tenant_key.strip()
    if not tenant_key:
        print(
            _json(
                {
                    "contract_version": CLI_CONTRACT_VERSION,
                    "status": "failed",
                    "error": "tenant key is required",
                }
            ),
            file=sys.stderr,
        )
        return 2

    engine, normalized_url = _engine(args.database_url)
    try:
        with Session(engine) as session:
            assessment = assess_candidate_creation(
                session,
                database_url=normalized_url,
                tenant_key=tenant_key,
            )
            if args.check_source:
                print(_json(assessment))
                return 0 if assessment["candidate_creation_ready"] else 2

            objective_key = (args.objective_key or "").strip() or _default_objective_key()
            if not assessment["candidate_creation_ready"]:
                print(_json(assessment), file=sys.stderr)
                return 2
            result = create_candidate(
                session,
                assessment=assessment,
                tenant_key=tenant_key,
                objective_key=objective_key,
            )
            result["database_url"] = mask_database_url(normalized_url)
            print(_json(result))
            return 0 if result["fresh_live_execution_candidate"] else 2
    except (ValueError, TypeError) as exc:
        print(
            _json(
                {
                    "contract_version": CLI_CONTRACT_VERSION,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 2
    except Exception:
        print(
            _json(
                {
                    "contract_version": CLI_CONTRACT_VERSION,
                    "status": "failed",
                    "error_type": "unexpected_runtime_failure",
                    "error": "Austria live-objective preparation failed; inspect local database/application logs",
                }
            ),
            file=sys.stderr,
        )
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
