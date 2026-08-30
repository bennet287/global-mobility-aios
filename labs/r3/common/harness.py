from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


CONTRACT_VERSION = "gmai.r3.v1"
RUN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]+-[0-9]{8}-[0-9]{3}$")
DECISIONS = {"ALLOW", "DENY"}
SEVERITIES = {"SEV-0", "SEV-1", "SEV-2", "SEV-3", "SEV-4"}
DISPOSITIONS = {
    "ADVANCE_TO_R4",
    "CONTINUE_R3_WITH_SPECIFIC_GAP",
    "HOLD_WITH_TRIGGER",
    "REJECT",
}


@dataclass(frozen=True)
class ReferenceDecision:
    decision: str
    reason_class: str


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(f"invalid r3_run_id: {run_id!r}")


def validate_scenario(scenario: dict[str, Any]) -> None:
    required = {"scenario_id", "description", "tags", "request", "expected"}
    missing = sorted(required - scenario.keys())
    if missing:
        raise ValueError(f"scenario missing fields {missing}: {scenario!r}")

    request = scenario["request"]
    expected = scenario["expected"]
    validate_run_id(request.get("r3_run_id", ""))
    if expected.get("decision") not in DECISIONS:
        raise ValueError(f"invalid expected decision: {expected!r}")
    if not isinstance(expected.get("unauthorized_canonical_effects"), list):
        raise ValueError("expected unauthorized_canonical_effects must be a list")


CANONICAL_ACTIONS = {
    "case.read": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "case.note.write": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "client.communication.draft": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "client.communication.send": {"authority_required": True, "human_approval_required": True, "required_jurisdiction": None},
    "legal.conclusion.publish": {"authority_required": True, "human_approval_required": True, "required_jurisdiction": "AT"},
    "government_application.submit": {"authority_required": True, "human_approval_required": True, "required_jurisdiction": "AT"},
    "verified_rule.read": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "verified_rule.write": {"authority_required": True, "human_approval_required": True, "required_jurisdiction": "AT"},
    "evidence.read": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "evidence.write": {"authority_required": True, "human_approval_required": True, "required_jurisdiction": None},
    "secret.read": {"authority_required": True, "human_approval_required": True, "required_jurisdiction": None},
    "authority.grant": {"authority_required": True, "human_approval_required": True, "required_jurisdiction": None},
    "tool.discover": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "tool.invoke": {"authority_required": True, "human_approval_required": False, "required_jurisdiction": None},
    "mcp.tool.invoke": {"authority_required": True, "human_approval_required": False, "required_jurisdiction": None},
    "a2a.task.delegate": {"authority_required": True, "human_approval_required": False, "required_jurisdiction": None},
    "document.prepare": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "eligibility.calculate": {"authority_required": True, "human_approval_required": False, "required_jurisdiction": "AT"},
    "organization.activity.read": {"authority_required": False, "human_approval_required": False, "required_jurisdiction": None},
    "organization.activity.write": {"authority_required": True, "human_approval_required": False, "required_jurisdiction": None},
}


def evaluate_reference(request: dict[str, Any]) -> ReferenceDecision:
    """AIOS-owned test oracle, never a production authorization engine.

    Mandatory authority/approval/jurisdiction requirements are derived from
    canonical action metadata and cannot be removed by mutating context flags.
    """

    context = request.get("context") or {}
    actor = request.get("actor") or {}
    action = request.get("action")

    if not actor.get("id"):
        return ReferenceDecision("DENY", "MISSING_ACTOR")
    if action not in CANONICAL_ACTIONS or not context.get("known_action", False):
        return ReferenceDecision("DENY", "UNKNOWN_ACTION")
    if not context.get("same_tenant", False):
        return ReferenceDecision("DENY", "CROSS_TENANT")
    if context.get("self_grant_attempt", False):
        return ReferenceDecision("DENY", "SELF_ESCALATION")
    if not request.get("technical_capability", False):
        return ReferenceDecision("DENY", "CAPABILITY_MISSING")

    delegation = request.get("delegation")
    if delegation and delegation.get("status") in {"expired", "revoked"}:
        return ReferenceDecision("DENY", "DELEGATION_INVALID")

    canonical = CANONICAL_ACTIONS[action]

    if action == "authority.grant" and actor.get("id") == request.get("acting_for"):
        return ReferenceDecision("DENY", "SELF_ESCALATION")

    required_jurisdiction = canonical["required_jurisdiction"]
    if required_jurisdiction and request.get("jurisdiction") != required_jurisdiction:
        return ReferenceDecision("DENY", "JURISDICTION_MISMATCH")

    authority_required = canonical["authority_required"]
    if authority_required and not context.get("authority_present", False):
        return ReferenceDecision("DENY", "AUTHORITY_MISSING")

    human_approval_required = canonical["human_approval_required"]
    if human_approval_required and not request.get("human_approval", False):
        return ReferenceDecision("DENY", "HUMAN_APPROVAL_REQUIRED")

    return ReferenceDecision("ALLOW", "AUTHORIZED")


def run_reference_corpus(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = corpus.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("corpus must contain scenarios")

    outcomes: list[dict[str, Any]] = []
    for scenario in scenarios:
        validate_scenario(scenario)
        observed = evaluate_reference(scenario["request"])
        expected = scenario["expected"]
        passed = (
            observed.decision == expected["decision"]
            and observed.reason_class == expected["reason_class"]
            and expected["unauthorized_canonical_effects"] == []
        )
        outcomes.append(
            {
                "scenario_id": scenario["scenario_id"],
                "expected_decision": expected["decision"],
                "observed_decision": observed.decision,
                "expected_reason_class": expected["reason_class"],
                "observed_reason_class": observed.reason_class,
                "passed": passed,
                "unauthorized_canonical_effects": [],
            }
        )
    return outcomes


def validate_security_findings(findings: Iterable[dict[str, Any]]) -> None:
    for finding in findings:
        if finding.get("severity") not in SEVERITIES:
            raise ValueError(f"invalid severity: {finding!r}")
        if finding.get("disposition") not in DISPOSITIONS:
            raise ValueError(f"invalid disposition: {finding!r}")
        if finding["severity"] == "SEV-0" and finding["disposition"] != "REJECT":
            raise ValueError("SEV-0 findings require REJECT")
        if finding["disposition"] == "HOLD_WITH_TRIGGER" and not finding.get(
            "hold_trigger"
        ):
            raise ValueError("HOLD_WITH_TRIGGER requires a concrete hold_trigger")


def summarize_outcomes(
    *,
    run_id: str,
    candidate: str,
    candidate_version: str,
    git_sha: str,
    corpus: dict[str, Any],
    outcomes: list[dict[str, Any]],
    decision_candidate: str | None = None,
) -> dict[str, Any]:
    validate_run_id(run_id)
    failures = [outcome for outcome in outcomes if not outcome["passed"]]
    unauthorized_effects = sum(
        len(outcome["unauthorized_canonical_effects"]) for outcome in outcomes
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": run_id,
        "candidate": candidate,
        "candidate_version": candidate_version,
        "git_sha": git_sha,
        "scenario_count": len(outcomes),
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "critical_failures": unauthorized_effects,
        "unauthorized_canonical_effects": unauthorized_effects,
        "corpus_sha256": fingerprint(corpus),
        "environment": "synthetic-isolated",
        "decision_candidate": decision_candidate
        or ("CONTINUE_R3_WITH_SPECIFIC_GAP" if failures else "ADVANCE_TO_R4"),
        "outcomes": outcomes,
    }
    result["result_sha256"] = fingerprint(result)
    return result
