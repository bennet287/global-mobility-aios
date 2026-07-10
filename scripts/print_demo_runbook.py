#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8000"


@dataclass(frozen=True)
class DemoUrl:
    label: str
    path: str
    purpose: str

    def with_base_url(self, base_url: str) -> dict[str, str]:
        return {
            "label": self.label,
            "url": f"{base_url.rstrip('/')}{self.path}",
            "purpose": self.purpose,
        }


DEMO_URLS: tuple[DemoUrl, ...] = (
    DemoUrl("Health", "/health", "Confirm the API is running."),
    DemoUrl("Admin v2", "/admin/v2", "Review the four demo leads and workflow state."),
    DemoUrl("Agent Console", "/admin/controlled-agents", "Run controlled internal agents."),
    DemoUrl("Agent Review Queue", "/admin/agent-output-reviews", "Approve, reject, and convert agent outputs."),
    DemoUrl("Client Communications", "/admin/client-communications", "Review communication draft workflow by lead."),
    DemoUrl("Communication Drafts", "/admin/client-communications/drafts", "Preview, edit, and review draft messages."),
    DemoUrl("Audit Logs", "/admin/audit-logs", "Verify traceability across workflow actions."),
)


DEMO_FLOW = (
    "Run python scripts/check_local_quality.py.",
    "Run python scripts/seed_demo_data.py --reset-all --yes.",
    "Run python scripts/check_demo_readiness.py and confirm status is ready.",
    "Start uvicorn with PYTHONPATH=apps/api.",
    "Open Agent Console and run Draft Client Update for Demo 3.",
    "Approve the client_drafting_agent output in Agent Review Queue.",
    "Convert the approved output into a client communication draft.",
    "Open Communication Drafts and verify Demo 3 appears with status draft.",
    "Preview/Edit the draft, then mark it reviewed.",
    "Open Audit Logs and verify controlled_agent_run, agent_output_approved, agent_output_converted_to_client_draft, and client_draft_reviewed.",
    "Export a clean demo snapshot with python scripts/export_demo_snapshot.py --format markdown.",
)


def build_demo_runbook(base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    return {
        "status": "ready_for_local_demo",
        "base_url": base_url.rstrip("/"),
        "urls": [url.with_base_url(base_url) for url in DEMO_URLS],
        "flow": list(DEMO_FLOW),
        "safety_rules": [
            "Controlled agents produce internal outputs only.",
            "Agent output conversion creates reviewable drafts only.",
            "Client communication drafts require human review.",
            "No automatic email, WhatsApp, portal send, application submission, or lead conversion is performed.",
        ],
    }


def _print_text(runbook: dict[str, Any]) -> None:
    print("Global Mobility AIOS local demo runbook")
    print(f"Base URL: {runbook['base_url']}")
    print()
    print("URLs:")
    for item in runbook["urls"]:
        print(f"- {item['label']}: {item['url']} ({item['purpose']})")
    print()
    print("Flow:")
    for index, step in enumerate(runbook["flow"], start=1):
        print(f"{index}. {step}")
    print()
    print("Safety rules:")
    for rule in runbook["safety_rules"]:
        print(f"- {rule}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the local Global Mobility AIOS demo runbook.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Local API base URL.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    runbook = build_demo_runbook(args.base_url)
    if args.json:
        print(json.dumps(runbook, indent=2))
    else:
        _print_text(runbook)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
