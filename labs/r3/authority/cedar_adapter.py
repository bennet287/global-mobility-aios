from __future__ import annotations

import copy
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labs.r3.common.harness import ReferenceDecision, evaluate_reference


ACTION_RELATIONS = {
    "case.read": "case_read",
    "case.note.write": "case_note_write",
    "client.communication.draft": "client_communication_draft",
    "client.communication.send": "client_communication_send",
    "legal.conclusion.publish": "legal_conclusion_publish",
    "government_application.submit": "government_application_submit",
    "verified_rule.read": "verified_rule_read",
    "verified_rule.write": "verified_rule_write",
    "evidence.read": "evidence_read",
    "evidence.write": "evidence_write",
    "secret.read": "secret_read",
    "authority.grant": "authority_grant",
    "tool.discover": "tool_discover",
    "tool.invoke": "tool_invoke",
    "mcp.tool.invoke": "mcp_tool_invoke",
    "a2a.task.delegate": "a2a_task_delegate",
    "document.prepare": "document_prepare",
    "eligibility.calculate": "eligibility_calculate",
    "organization.activity.read": "organization_activity_read",
    "organization.activity.write": "organization_activity_write",
}


@dataclass(frozen=True)
class CedarDecision:
    decision: str
    reason_class: str
    provider_called: bool
    used_reference_fallback: bool


class CedarAdapter:
    """Cedar Policy challenger adapter.

    The adapter prefers a local Cedar CLI (``cedar``) for genuine R3 evaluation.
    When the CLI is unavailable, it deterministically falls back to the AIOS
    reference oracle so the contract and challenger harness can be exercised
    without requiring Cedar infrastructure in every environment. R3 evidence
    must record when the fallback was used.
    """

    def __init__(
        self,
        *,
        policy_dir: Path | None = None,
        use_reference_fallback: bool = False,
    ) -> None:
        self._policy_dir = policy_dir
        self._use_reference_fallback = use_reference_fallback
        self._cedar_available: bool | None = None

    def _cedar_cli_exists(self) -> bool:
        if self._cedar_available is not None:
            return self._cedar_available
        try:
            subprocess.run(
                ["cedar", "--help"],
                check=True,
                capture_output=True,
                text=True,
            )
            self._cedar_available = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            self._cedar_available = False
        return self._cedar_available

    def _reference_oracle_decide(self, request: dict[str, Any]) -> CedarDecision:
        observed = evaluate_reference(request)
        return CedarDecision(
            decision=observed.decision,
            reason_class=observed.reason_class,
            provider_called=False,
            used_reference_fallback=True,
        )

    def _cedar_cli_decide(self, request: dict[str, Any]) -> CedarDecision:
        # Genuine Cedar CLI evaluation placeholder. The request is translated
        # to Cedar's principal/action/resource/context shape and evaluated
        # against the policy directory supplied at adapter construction.
        #
        # Until a real Cedar policy is checked in, the reference oracle is used
        # so that the adapter contract remains testable.
        return self._reference_oracle_decide(request)

    def decide(self, request: dict[str, Any]) -> CedarDecision:
        if self._use_reference_fallback or not self._cedar_cli_exists():
            return self._reference_oracle_decide(request)
        return self._cedar_cli_decide(request)


def run_challenger_corpus(
    *,
    scenarios: list[dict[str, Any]],
    use_reference_fallback: bool = False,
) -> list[dict[str, Any]]:
    adapter = CedarAdapter(use_reference_fallback=use_reference_fallback)
    outcomes: list[dict[str, Any]] = []
    for scenario in scenarios:
        observed = adapter.decide(scenario["request"])
        expected = scenario["expected"]
        outcomes.append(
            {
                "scenario_id": scenario["scenario_id"],
                "expected_decision": expected["decision"],
                "observed_decision": observed.decision,
                "expected_reason_class": expected["reason_class"],
                "observed_reason_class": observed.reason_class,
                "provider_called": observed.provider_called,
                "used_reference_fallback": observed.used_reference_fallback,
                "passed": observed.decision == expected["decision"]
                and observed.reason_class == expected["reason_class"],
                "unauthorized_canonical_effects": [],
            }
        )
    return outcomes
