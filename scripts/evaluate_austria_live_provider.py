#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

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
from app.models.domain import OrganizationalActionOutput, OrganizationalWorkItem  # noqa: E402
from app.services.organization_command import OrganizationCommandError  # noqa: E402
from app.services.organization_mobility_live_provider_cycle import (  # noqa: E402
    execute_austria_live_provider_cycle,
)
from app.services.organization_mobility_live_provider_evaluation import (  # noqa: E402
    configured_live_provider_selection,
)
from app.services.organization_mobility_objective_runtime import (  # noqa: E402
    AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    austria_specialist_output_key,
)


CLI_CONTRACT_VERSION = "austria-live-provider-evaluation-cli.v2"
_TERMINAL_ROOT_STATUSES = {"completed", "cancelled", "failed", "rejected", "returned"}


def _json(value: object) -> str:
    return json.dumps(value, default=str, indent=2, sort_keys=True)


def _engine(database_url: str):
    normalized = normalize_database_url(database_url)
    connect_args = {"check_same_thread": False} if is_sqlite_url(normalized) else {}
    return create_engine(normalized, connect_args=connect_args), normalized


def _configuration_report(database_url: str) -> dict[str, object]:
    provider = (settings.llm_provider or "").strip().casefold()
    api_key_present = False
    model: str | None = None
    if provider == "deepseek":
        api_key_present = bool((settings.deepseek_api_key or "").strip())
        model = (settings.deepseek_model or "").strip() or None
    elif provider == "moonshot":
        api_key_present = bool((settings.moonshot_api_key or "").strip())
        model = (settings.moonshot_model or "").strip() or None
    selection_ready = False
    try:
        selection = configured_live_provider_selection(require_api_key=True)
        provider = selection.provider_key
        model = selection.model_key
        selection_ready = True
    except OrganizationCommandError:
        pass
    return {
        "contract_version": CLI_CONTRACT_VERSION,
        "mode": "check-config",
        "database_url": mask_database_url(normalize_database_url(database_url)),
        "provider_key": provider or None,
        "model_key": model,
        "api_key_configured": api_key_present,
        "fallback_to_template": settings.llm_fallback_to_template,
        "live_provider_ready": selection_ready,
        "fresh_retrieval_required_for_execute_live": True,
        "secrets_exposed": False,
    }


def _candidate_roots(session: Session, tenant_key: str) -> list[dict[str, object]]:
    roots = list(
        session.exec(
            select(OrganizationalWorkItem)
            .where(
                OrganizationalWorkItem.tenant_key == tenant_key,
                OrganizationalWorkItem.work_type == "mobility_objective",
                OrganizationalWorkItem.phase_key == "J.1",
                OrganizationalWorkItem.assigned_position_key
                == AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
                OrganizationalWorkItem.parent_work_item_id.is_(None),
            )
            .order_by(OrganizationalWorkItem.created_at.desc())
        ).all()
    )
    items: list[dict[str, object]] = []
    for root in roots:
        children = list(
            session.exec(
                select(OrganizationalWorkItem).where(
                    OrganizationalWorkItem.tenant_key == tenant_key,
                    OrganizationalWorkItem.parent_work_item_id == root.id,
                )
            ).all()
        )
        child_by_position = {
            child.assigned_position_key: child
            for child in children
            if child.assigned_position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS
        }
        specialist_state: dict[str, object] = {}
        fresh_execution_candidate = root.status not in _TERMINAL_ROOT_STATUSES
        for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
            child = child_by_position.get(position_key)
            if child is None:
                specialist_state[position_key] = {"present": False}
                fresh_execution_candidate = False
                continue
            output_exists = session.exec(
                select(OrganizationalActionOutput.id).where(
                    OrganizationalActionOutput.output_key
                    == austria_specialist_output_key(child.id)
                )
            ).first() is not None
            attempts_exhausted = child.execution_attempts >= child.max_execution_attempts
            specialist_state[position_key] = {
                "present": True,
                "work_item_id": str(child.id),
                "status": child.status,
                "execution_attempts": child.execution_attempts,
                "max_execution_attempts": child.max_execution_attempts,
                "execution_attempts_exhausted": attempts_exhausted,
                "current_k1_output_exists": output_exists,
            }
            if (
                output_exists
                or child.status not in {"queued", "running"}
                or attempts_exhausted
            ):
                fresh_execution_candidate = False
        items.append(
            {
                "root_work_item_id": str(root.id),
                "objective_key": root.objective_key,
                "root_status": root.status,
                "created_at": root.created_at,
                "fresh_live_execution_candidate": fresh_execution_candidate,
                "fresh_retrieval_will_be_verified_before_k1": fresh_execution_candidate,
                "specialists": specialist_state,
            }
        )
    return items


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the Austria K.1 runtime through a guarded L cycle: verify current official-source "
            "content against governed snapshots, then execute the configured live LLM provider. "
            "This tool never creates an objective and never grants external-action authority."
        )
    )
    parser.add_argument("--database-url", default=settings.database_url)
    parser.add_argument("--tenant-key")
    parser.add_argument("--root-work-item-id")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check-config", action="store_true")
    modes.add_argument("--list-candidates", action="store_true")
    modes.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    if (args.list_candidates or args.execute_live) and not args.tenant_key:
        parser.error("--tenant-key is required for candidate discovery and live execution")
    if args.execute_live and not args.root_work_item_id:
        parser.error("--root-work-item-id is required with --execute-live")
    return args


def main() -> int:
    args = _parse_args()
    if args.check_config:
        print(_json(_configuration_report(args.database_url)))
        return 0

    engine, normalized_url = _engine(args.database_url)
    try:
        with Session(engine) as session:
            if args.list_candidates:
                print(
                    _json(
                        {
                            "contract_version": CLI_CONTRACT_VERSION,
                            "mode": "list-candidates",
                            "database_url": mask_database_url(normalized_url),
                            "tenant_key": args.tenant_key,
                            "roots": _candidate_roots(session, args.tenant_key),
                        }
                    )
                )
                return 0

            root_work_item_id = UUID(args.root_work_item_id)
            evaluation = execute_austria_live_provider_cycle(
                session,
                tenant_key=args.tenant_key,
                root_work_item_id=root_work_item_id,
            )
            payload = asdict(evaluation)
            payload["mode"] = "execute-live"
            payload["database_url"] = mask_database_url(normalized_url)
            print(_json(payload))
            return 0 if evaluation.full_l_reasoning_evidence_candidate else 2
    except (OrganizationCommandError, ValueError) as exc:
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
    except Exception as exc:
        print(
            _json(
                {
                    "contract_version": CLI_CONTRACT_VERSION,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": "live-provider/retrieval evaluation failed; inspect durable execution evidence",
                }
            ),
            file=sys.stderr,
        )
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
