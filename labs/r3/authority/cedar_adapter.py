from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CANONICAL_ACTIONS, evaluate_reference


DEFAULT_POLICY_DIR = Path(__file__).resolve().parent / "cedar"


@dataclass(frozen=True)
class CedarDecision:
    decision: str
    reason_class: str
    provider_called: bool
    used_reference_fallback: bool


def _cedar_entity_uid(entity_type: str, entity_id: object) -> str:
    """Render Cedar CLI request-json entity UID syntax.

    Cedar's request-json contract expects principal/action/resource as strings
    like User::"alice", not objects with separate type/id fields.
    """

    return f"{entity_type}::{json.dumps(str(entity_id), ensure_ascii=False)}"


def _cedar_request_payload(request: dict[str, Any]) -> dict[str, Any]:
    action = request.get("action")
    canonical = CANONICAL_ACTIONS.get(action)
    actor = request.get("actor") or {}
    resource = request.get("resource") or {}
    context = request.get("context") or {}
    delegation = request.get("delegation") or {}

    tenant_id = request.get("tenant_id")
    resource_tenant_id = resource.get("tenant_id")
    self_grant_attempt = bool(context.get("self_grant_attempt", False)) or (
        action == "authority.grant"
        and bool(actor.get("id"))
        and actor.get("id") == request.get("acting_for")
    )
    required_jurisdiction = (
        canonical["required_jurisdiction"] if canonical is not None else None
    )

    return {
        "principal": _cedar_entity_uid(
            "Agent",
            actor.get("id") or "missing-actor",
        ),
        "action": _cedar_entity_uid(
            "Action",
            action or "missing-action",
        ),
        "resource": _cedar_entity_uid(
            "Resource",
            resource.get("id") or "missing-resource",
        ),
        "context": {
            "actor_present": bool(actor.get("id")),
            "known_action": canonical is not None,
            "same_tenant": bool(
                tenant_id
                and resource_tenant_id
                and tenant_id == resource_tenant_id
            ),
            "self_grant_attempt": self_grant_attempt,
            "technical_capability": bool(
                request.get("technical_capability", False)
            ),
            "delegation_valid": delegation.get("status")
            not in {"expired", "revoked"},
            "jurisdiction_valid": canonical is not None
            and (
                required_jurisdiction is None
                or request.get("jurisdiction") == required_jurisdiction
            ),
            "authority_required": bool(
                canonical and canonical["authority_required"]
            ),
            "authority_present": bool(context.get("authority_present", False)),
            "human_approval_required": bool(
                canonical and canonical["human_approval_required"]
            ),
            "human_approval": bool(request.get("human_approval", False)),
        },
    }


def _parse_cedar_decision(stdout: str) -> str | None:
    for line in stdout.splitlines():
        value = line.strip().upper()
        if value in {"ALLOW", "DENY"}:
            return value
    return None


class CedarAdapter:
    """Real Cedar CLI challenger with explicit diagnostic fallback.

    A missing Cedar CLI fails closed. Reference-oracle fallback is available only
    when explicitly requested and can never qualify as empirical Cedar evidence.
    """

    def __init__(
        self,
        *,
        policy_dir: Path | None = None,
        use_reference_fallback: bool = False,
        cedar_binary: str = "cedar",
    ) -> None:
        self._policy_dir = policy_dir or DEFAULT_POLICY_DIR
        self._use_reference_fallback = use_reference_fallback
        self._cedar_binary = cedar_binary
        self._cedar_available: bool | None = None

    def _cedar_cli_exists(self) -> bool:
        if self._cedar_available is not None:
            return self._cedar_available
        try:
            completed = subprocess.run(
                [self._cedar_binary, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._cedar_available = completed.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
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
        policy_path = self._policy_dir / "policy.cedar"
        if not policy_path.is_file():
            return CedarDecision(
                "DENY",
                "ENGINE_UNAVAILABLE",
                False,
                False,
            )

        payload = _cedar_request_payload(request)
        try:
            with tempfile.TemporaryDirectory(prefix="gmai-r3-cedar-") as directory:
                request_path = Path(directory) / "request.cedarauth.json"
                request_path.write_text(
                    json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                completed = subprocess.run(
                    [
                        self._cedar_binary,
                        "authorize",
                        "--policies",
                        str(policy_path),
                        "--request-json",
                        str(request_path),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            return CedarDecision(
                "DENY",
                "ENGINE_UNAVAILABLE",
                True,
                False,
            )

        decision = _parse_cedar_decision(completed.stdout)
        if completed.returncode != 0 or decision is None:
            return CedarDecision(
                "DENY",
                "MALFORMED_RESPONSE",
                True,
                False,
            )

        reference = evaluate_reference(request)
        if decision == "ALLOW":
            reason_class = "AUTHORIZED"
        elif reference.decision == "DENY":
            reason_class = reference.reason_class
        else:
            reason_class = "CEDAR_POLICY_DISAGREEMENT"

        return CedarDecision(
            decision=decision,
            reason_class=reason_class,
            provider_called=True,
            used_reference_fallback=False,
        )

    def decide(self, request: dict[str, Any]) -> CedarDecision:
        if self._use_reference_fallback:
            return self._reference_oracle_decide(request)
        if not self._cedar_cli_exists():
            return CedarDecision(
                "DENY",
                "ENGINE_UNAVAILABLE",
                False,
                False,
            )
        return self._cedar_cli_decide(request)


def run_challenger_corpus(
    *,
    scenarios: list[dict[str, Any]],
    use_reference_fallback: bool = False,
    policy_dir: Path | None = None,
) -> list[dict[str, Any]]:
    adapter = CedarAdapter(
        policy_dir=policy_dir,
        use_reference_fallback=use_reference_fallback,
    )
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
