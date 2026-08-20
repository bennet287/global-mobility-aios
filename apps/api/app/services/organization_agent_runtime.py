from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
from typing import Any

from sqlmodel import Session

from app.models.domain import now_utc
from app.services.organization_command import canonical_fingerprint
from app.services.organization_context_broker import (
    ContextBrokerError,
    ContextBundle,
    build_work_item_context_bundle,
)


RUNTIME_BINDING_SCHEMA_VERSION = "employee-runtime-binding.v1"


class AgentRuntimeError(RuntimeError):
    """Base error for AIOS employee/runtime binding."""


class RuntimeProfileInvalid(AgentRuntimeError):
    """The supplied runtime profile is structurally invalid."""


class RuntimeProfileDisabled(AgentRuntimeError):
    """The supplied runtime profile is not eligible for execution."""


class RuntimeCapabilityUnavailable(AgentRuntimeError):
    """The runtime cannot technically satisfy the requested capability."""


class RuntimeBindingStale(AgentRuntimeError):
    """The ContextBundle no longer represents current governed organization state."""


class RuntimeClass(str, Enum):
    HOSTED_API = "hosted_api"
    CLI = "cli"
    LOCAL = "local"
    SPECIALIZED = "specialized"
    DONOR_ADAPTER = "donor_adapter"


def _required_text(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise RuntimeProfileInvalid(f"{label} is required")
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalized_names(values: tuple[str, ...], *, label: str) -> tuple[str, ...]:
    normalized = tuple(sorted({_required_text(item, label=label) for item in values}))
    return normalized


@dataclass(frozen=True)
class AgentRuntimeProfile:
    """Technical runtime capability profile, deliberately separate from authority.

    This describes *how* an AIOS employee may be executed, not what the employee is
    allowed to do. Authority, autonomy, risk, Evidence status and policy are owned by
    AIOS governance/context contracts and are intentionally absent from this type.
    """

    profile_key: str
    runtime_class: RuntimeClass | str
    adapter_key: str
    provider_key: str
    model_key: str | None = None
    technical_capabilities: tuple[str, ...] = ()
    available_tools: tuple[str, ...] = ()
    independence_group: str = "default"
    profile_version: int = 1
    enabled: bool = True

    def __post_init__(self) -> None:
        try:
            runtime_class = RuntimeClass(self.runtime_class)
        except ValueError as exc:
            raise RuntimeProfileInvalid("unsupported runtime class") from exc
        if self.profile_version < 1:
            raise RuntimeProfileInvalid("runtime profile version must be positive")

        object.__setattr__(self, "runtime_class", runtime_class)
        object.__setattr__(self, "profile_key", _required_text(self.profile_key, label="profile key"))
        object.__setattr__(self, "adapter_key", _required_text(self.adapter_key, label="adapter key"))
        object.__setattr__(self, "provider_key", _required_text(self.provider_key, label="provider key"))
        object.__setattr__(self, "model_key", _optional_text(self.model_key))
        object.__setattr__(
            self,
            "technical_capabilities",
            _normalized_names(self.technical_capabilities, label="technical capability"),
        )
        object.__setattr__(
            self,
            "available_tools",
            _normalized_names(self.available_tools, label="available tool"),
        )
        object.__setattr__(
            self,
            "independence_group",
            _required_text(self.independence_group, label="independence group"),
        )


@dataclass(frozen=True)
class EmployeeRuntimeBinding:
    """Provider-neutral binding between persistent employee context and a runtime.

    Runtime/session/process identity is intentionally not persistent employee identity.
    This binding is a technical execution choice and is not an authorization decision.
    """

    schema_version: str
    tenant_key: str
    position_key: str
    position_version: int
    context_hash: str
    context_purpose: str
    runtime_profile_key: str
    runtime_profile_version: int
    runtime_class: RuntimeClass
    adapter_key: str
    provider_key: str
    model_key: str | None
    technical_capabilities: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    independence_group: str
    binding_hash: str
    bound_at: datetime


def runtime_profile_fingerprint(profile: AgentRuntimeProfile) -> str:
    return canonical_fingerprint(
        {
            "profile_key": profile.profile_key,
            "runtime_class": profile.runtime_class,
            "adapter_key": profile.adapter_key,
            "provider_key": profile.provider_key,
            "model_key": profile.model_key,
            "technical_capabilities": profile.technical_capabilities,
            "available_tools": profile.available_tools,
            "independence_group": profile.independence_group,
            "profile_version": profile.profile_version,
            "enabled": profile.enabled,
        }
    )


def _current_context(session: Session, context: ContextBundle) -> ContextBundle:
    try:
        return build_work_item_context_bundle(
            session,
            tenant_key=context.tenant_key,
            position_key=context.position.position_key,
            work_item_id=context.work_item.work_item_id,
            purpose=context.purpose,
        )
    except ContextBrokerError as exc:
        raise RuntimeBindingStale("employee context is no longer eligible for runtime binding") from exc


def bind_employee_runtime(
    session: Session,
    *,
    context: ContextBundle,
    profile: AgentRuntimeProfile,
    required_capability: str | None = None,
) -> EmployeeRuntimeBinding:
    """Bind a fresh ContextBundle to a technical runtime without granting authority.

    The function re-resolves the governed ContextBundle before binding. A caller cannot
    bind stale employee/work state to a runtime after assignment, contract or work
    context changes. Runtime tools are intersected with ContextBundle.allowed_tools;
    a runtime profile can never grant tools that AIOS context did not authorize.
    """

    if not profile.enabled:
        raise RuntimeProfileDisabled("runtime profile is disabled")

    current = _current_context(session, context)
    if current.context_hash != context.context_hash:
        raise RuntimeBindingStale("context hash is stale")
    if current.position.position_version != context.position.position_version:
        raise RuntimeBindingStale("employee position version is stale")

    capability = _optional_text(required_capability)
    if capability is not None and capability not in profile.technical_capabilities:
        raise RuntimeCapabilityUnavailable(
            f"runtime profile does not provide required capability {capability!r}"
        )

    allowed_tools = tuple(sorted(set(context.allowed_tools).intersection(profile.available_tools)))
    profile_fingerprint = runtime_profile_fingerprint(profile)
    binding_payload: dict[str, Any] = {
        "schema_version": RUNTIME_BINDING_SCHEMA_VERSION,
        "tenant_key": context.tenant_key,
        "position_key": context.position.position_key,
        "position_version": context.position.position_version,
        "context_hash": context.context_hash,
        "context_purpose": context.purpose,
        "runtime_profile_fingerprint": profile_fingerprint,
        "required_capability": capability,
        "allowed_tools": allowed_tools,
    }
    binding_hash = canonical_fingerprint(binding_payload)

    return EmployeeRuntimeBinding(
        schema_version=RUNTIME_BINDING_SCHEMA_VERSION,
        tenant_key=context.tenant_key,
        position_key=context.position.position_key,
        position_version=context.position.position_version,
        context_hash=context.context_hash,
        context_purpose=context.purpose.value,
        runtime_profile_key=profile.profile_key,
        runtime_profile_version=profile.profile_version,
        runtime_class=profile.runtime_class,
        adapter_key=profile.adapter_key,
        provider_key=profile.provider_key,
        model_key=profile.model_key,
        technical_capabilities=profile.technical_capabilities,
        allowed_tools=allowed_tools,
        independence_group=profile.independence_group,
        binding_hash=binding_hash,
        bound_at=now_utc(),
    )


def runtime_contract_field_names() -> frozenset[str]:
    """Expose the frozen D.2 profile surface for invariant-focused regression tests."""

    return frozenset(item.name for item in fields(AgentRuntimeProfile))
