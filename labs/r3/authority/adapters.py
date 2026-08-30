from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from labs.r3.common.harness import ReferenceDecision, CANONICAL_ACTIONS


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
class CandidateDecision:
    decision: str
    reason_class: str
    provider_called: bool


def evaluate_aios_preflight(request: dict[str, Any]) -> ReferenceDecision | None:
    """Return a constitutional hard deny, or None when a candidate may be consulted.

    Mandatory action requirements are derived from AIOS-owned CANONICAL_ACTIONS.
    Caller-controlled context flags may not remove authority, approval, tenant,
    or jurisdiction requirements.
    """

    actor = request.get("actor") or {}
    action = request.get("action")
    canonical = CANONICAL_ACTIONS.get(action)
    context = request.get("context") or {}
    resource = request.get("resource") or {}

    if not actor.get("id"):
        return ReferenceDecision("DENY", "MISSING_ACTOR")
    if canonical is None or action not in ACTION_RELATIONS:
        return ReferenceDecision("DENY", "UNKNOWN_ACTION")

    tenant_id = request.get("tenant_id")
    resource_tenant_id = resource.get("tenant_id")
    if not tenant_id or not resource_tenant_id or tenant_id != resource_tenant_id:
        return ReferenceDecision("DENY", "CROSS_TENANT")

    if context.get("self_grant_attempt", False):
        return ReferenceDecision("DENY", "SELF_ESCALATION")
    if action == "authority.grant" and actor.get("id") == request.get("acting_for"):
        return ReferenceDecision("DENY", "SELF_ESCALATION")
    if not request.get("technical_capability", False):
        return ReferenceDecision("DENY", "CAPABILITY_MISSING")

    delegation = request.get("delegation")
    if delegation and delegation.get("status") in {"expired", "revoked"}:
        return ReferenceDecision("DENY", "DELEGATION_INVALID")

    required_jurisdiction = canonical["required_jurisdiction"]
    if required_jurisdiction and request.get("jurisdiction") != required_jurisdiction:
        return ReferenceDecision("DENY", "JURISDICTION_MISMATCH")

    if canonical["human_approval_required"] and not request.get(
        "human_approval", False
    ):
        return ReferenceDecision("DENY", "HUMAN_APPROVAL_REQUIRED")

    return None


class OpaAdapter:
    def __init__(self, *, base_url: str, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=2.0)

    def decide(self, request: dict[str, Any]) -> CandidateDecision:
        try:
            response = self._client.post(
                "/v1/data/gmai/r3/authority/decision", json={"input": request}
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return CandidateDecision("DENY", "ENGINE_UNAVAILABLE", True)

        try:
            body = response.json()
        except (ValueError, TypeError):
            return CandidateDecision("DENY", "MALFORMED_RESPONSE", True)

        result = body.get("result") if isinstance(body, dict) else None
        if not isinstance(result, dict):
            return CandidateDecision("DENY", "MALFORMED_RESPONSE", True)
        decision = result.get("decision")
        reason = result.get("reason_class")
        if decision not in {"ALLOW", "DENY"} or not isinstance(reason, str):
            return CandidateDecision("DENY", "MALFORMED_RESPONSE", True)
        return CandidateDecision(decision, reason, True)


class OpenFgaAdapter:
    def __init__(
        self,
        *,
        base_url: str,
        store_id: str,
        authorization_model_id: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=2.0)
        self._store_id = store_id
        self._authorization_model_id = authorization_model_id

    def decide(self, request: dict[str, Any]) -> CandidateDecision:
        preflight = evaluate_aios_preflight(request)
        if preflight is not None:
            return CandidateDecision(preflight.decision, preflight.reason_class, False)

        action = request["action"]
        if not CANONICAL_ACTIONS[action]["authority_required"]:
            return CandidateDecision("ALLOW", "AUTHORIZED", False)

        relation = ACTION_RELATIONS[action]
        context = request.get("context") or {}
        tuple_key = {
            "user": request["actor"]["id"],
            "relation": relation,
            "object": "resource:synthetic-at-001",
        }
        payload: dict[str, Any] = {
            "tuple_key": tuple_key,
            "authorization_model_id": self._authorization_model_id,
        }
        if context.get("authority_present", False):
            payload["contextual_tuples"] = {"tuple_keys": [tuple_key]}

        try:
            response = self._client.post(
                f"/stores/{self._store_id}/check", json=payload
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return CandidateDecision("DENY", "ENGINE_UNAVAILABLE", True)

        try:
            body = response.json()
        except (ValueError, TypeError):
            return CandidateDecision("DENY", "MALFORMED_RESPONSE", True)

        allowed = body.get("allowed") if isinstance(body, dict) else None
        if not isinstance(allowed, bool):
            return CandidateDecision("DENY", "MALFORMED_RESPONSE", True)
        return CandidateDecision(
            "ALLOW" if allowed else "DENY",
            "AUTHORIZED" if allowed else "AUTHORITY_MISSING",
            True,
        )
