from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Any, Protocol

from labs.r3.common.harness import fingerprint


FORBIDDEN_ARGUMENT_KEYS = {
    "api_key",
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
}
FORBIDDEN_ARTIFACT_TYPES = {"executable", "script", "shell", "unknown-binary"}


@dataclass(frozen=True)
class TrustedIdentity:
    actor_id: str
    tenant_id: str


@dataclass(frozen=True)
class ToolDescriptor:
    tool_id: str
    description: str
    allowed_argument_keys: frozenset[str]
    risk_class: str


@dataclass(frozen=True)
class GatewayResult:
    allowed: bool
    reason_class: str
    provider_called: bool = False
    replayed: bool = False
    output: dict[str, Any] | None = None


class AuthorityPort(Protocol):
    def is_allowed(
        self, *, identity: TrustedIdentity, action: str, resource: str
    ) -> bool: ...


class ToolProviderPort(Protocol):
    def call(self, *, tool_id: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class StaticAuthority:
    grants: set[tuple[str, str, str]] = field(default_factory=set)

    def is_allowed(
        self, *, identity: TrustedIdentity, action: str, resource: str
    ) -> bool:
        return (identity.actor_id, action, resource) in self.grants


class McpGateway:
    def __init__(
        self,
        *,
        authority: AuthorityPort,
        provider: ToolProviderPort,
        catalog: list[ToolDescriptor],
    ) -> None:
        self._authority = authority
        self._provider = provider
        self._catalog = {tool.tool_id: tool for tool in catalog}
        self._replays: dict[str, tuple[str, GatewayResult]] = {}

    def list_tools(self, *, identity: TrustedIdentity) -> list[ToolDescriptor]:
        visible = []
        for tool in self._catalog.values():
            if self._authority.is_allowed(
                identity=identity, action="tool.discover", resource=tool.tool_id
            ):
                visible.append(tool)
        return sorted(visible, key=lambda tool: tool.tool_id)

    def invoke(
        self,
        *,
        identity: TrustedIdentity,
        tool_id: str,
        arguments: dict[str, Any],
        idempotency_key: str,
        untrusted_headers: dict[str, str] | None = None,
    ) -> GatewayResult:
        del untrusted_headers
        tool = self._catalog.get(tool_id)
        if tool is None:
            return GatewayResult(False, "UNKNOWN_TOOL")
        command_fingerprint = fingerprint(
            {
                "actor_id": identity.actor_id,
                "tenant_id": identity.tenant_id,
                "tool_id": tool_id,
                "arguments": arguments,
            }
        )
        existing = self._replays.get(idempotency_key)
        if existing:
            prior_fingerprint, prior_result = existing
            if prior_fingerprint != command_fingerprint:
                return GatewayResult(False, "IDEMPOTENCY_CONFLICT")
            return GatewayResult(
                prior_result.allowed,
                prior_result.reason_class,
                prior_result.provider_called,
                True,
                prior_result.output,
            )
        argument_keys = set(arguments)
        if any(key.lower() in FORBIDDEN_ARGUMENT_KEYS for key in argument_keys):
            return GatewayResult(False, "CREDENTIAL_FORWARDING_DENIED")
        if argument_keys - tool.allowed_argument_keys:
            return GatewayResult(False, "ARGUMENT_SCHEMA_VIOLATION")
        resource_tenant = arguments.get("tenant_id")
        if resource_tenant and resource_tenant != identity.tenant_id:
            return GatewayResult(False, "CROSS_TENANT")
        if not self._authority.is_allowed(
            identity=identity, action="tool.invoke", resource=tool_id
        ):
            return GatewayResult(False, "AUTHORITY_MISSING")
        output = self._provider.call(tool_id=tool_id, arguments=arguments)
        if output.get("requested_authority") or output.get("human_approval"):
            return GatewayResult(False, "PROVIDER_AUTHORITY_CLAIM", True)
        result = GatewayResult(True, "AUTHORIZED", True, False, output)
        self._replays[idempotency_key] = (command_fingerprint, result)
        return result


@dataclass(frozen=True)
class AgentCard:
    agent_id: str
    issuer: str
    tenant_id: str
    skills: tuple[str, ...]
    endpoint: str
    signature: str

    def unsigned(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "issuer": self.issuer,
            "tenant_id": self.tenant_id,
            "skills": self.skills,
            "endpoint": self.endpoint,
        }


def sign_agent_card(
    *,
    agent_id: str,
    issuer: str,
    tenant_id: str,
    skills: tuple[str, ...],
    endpoint: str,
    synthetic_key: str,
) -> AgentCard:
    unsigned = {
        "agent_id": agent_id,
        "issuer": issuer,
        "tenant_id": tenant_id,
        "skills": skills,
        "endpoint": endpoint,
    }
    signature = hmac.new(
        synthetic_key.encode("utf-8"),
        fingerprint(unsigned).encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return AgentCard(signature=signature, **unsigned)


class A2AGateway:
    def __init__(
        self, *, authority: AuthorityPort, synthetic_trust_store: dict[str, str]
    ) -> None:
        self._authority = authority
        self._trust_store = synthetic_trust_store
        self._trusted_cards: dict[str, str] = {}
        self._cards: dict[str, AgentCard] = {}
        self._replays: dict[str, str] = {}

    def observe_card(self, card: AgentCard) -> GatewayResult:
        key = self._trust_store.get(card.issuer)
        if key is None:
            return GatewayResult(False, "UNTRUSTED_ISSUER")
        expected = hmac.new(
            key.encode("utf-8"),
            fingerprint(card.unsigned()).encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, card.signature):
            return GatewayResult(False, "INVALID_AGENT_CARD_SIGNATURE")
        card_fingerprint = fingerprint(card.unsigned())
        prior = self._trusted_cards.get(card.agent_id)
        if prior is not None and prior != card_fingerprint:
            return GatewayResult(False, "AGENT_CARD_CHANGED_REVIEW_REQUIRED")
        self._trusted_cards[card.agent_id] = card_fingerprint
        self._cards[card.agent_id] = card
        return GatewayResult(True, "IDENTITY_OBSERVED_CAPABILITIES_UNTRUSTED")

    def delegate(
        self,
        *,
        identity: TrustedIdentity,
        remote_agent_id: str,
        skill: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> GatewayResult:
        card = self._cards.get(remote_agent_id)
        if card is None:
            return GatewayResult(False, "REMOTE_AGENT_UNTRUSTED")
        if card.tenant_id != identity.tenant_id or payload.get(
            "tenant_id"
        ) != identity.tenant_id:
            return GatewayResult(False, "CROSS_TENANT")
        if skill not in card.skills:
            return GatewayResult(False, "SKILL_NOT_ADVERTISED")
        if payload.get("artifact_type") in FORBIDDEN_ARTIFACT_TYPES:
            return GatewayResult(False, "MALICIOUS_ARTIFACT_DENIED")
        if payload.get("requested_local_tool"):
            return GatewayResult(False, "REMOTE_PRIVILEGED_TOOL_REQUEST_DENIED")
        command_fingerprint = fingerprint(
            {
                "identity": {
                    "actor_id": identity.actor_id,
                    "tenant_id": identity.tenant_id,
                },
                "remote_agent_id": remote_agent_id,
                "skill": skill,
                "payload": payload,
            }
        )
        prior = self._replays.get(idempotency_key)
        if prior is not None:
            if prior != command_fingerprint:
                return GatewayResult(False, "IDEMPOTENCY_CONFLICT")
            return GatewayResult(True, "AUTHORIZED", False, True)
        if not self._authority.is_allowed(
            identity=identity,
            action="a2a.delegate",
            resource=f"{remote_agent_id}:{skill}",
        ):
            return GatewayResult(False, "AUTHORITY_MISSING")
        self._replays[idempotency_key] = command_fingerprint
        return GatewayResult(True, "AUTHORIZED")
