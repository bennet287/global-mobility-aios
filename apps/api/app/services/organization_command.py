from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence, TypeVar
from uuid import UUID

from sqlmodel import Session, SQLModel, select

from app.core.auth_policy import ROLES
from app.models.domain import OrganizationActorType
from app.services.audit_log import record_audit, to_audit_dict


class OrganizationCommandError(RuntimeError):
    """Base error for HTTP-independent organization commands."""


class NotFound(OrganizationCommandError):
    pass


class TenantMismatch(NotFound):
    """Internal diagnostic; routers should translate this to a non-disclosing 404."""


class InvalidTransition(OrganizationCommandError):
    pass


class IdempotencyConflict(OrganizationCommandError):
    pass


class AuthorityDenied(OrganizationCommandError):
    pass


class InvalidHumanActor(AuthorityDenied):
    pass


class InvalidReference(OrganizationCommandError):
    pass


class DependencyConflict(OrganizationCommandError):
    pass


class ConcurrentWriteConflict(DependencyConflict):
    """A safe retry may succeed after a concurrent transaction commits canonical state."""


class ContributionSourceRejected(OrganizationCommandError):
    pass


@dataclass(frozen=True)
class OrganizationCommandContext:
    tenant_key: str
    actor_id: str
    actor_type: OrganizationActorType | str
    authenticated_user_id: str
    role: str
    department: str | None = None
    position_key: str | None = None
    authority_level: str | None = None
    correlation_key: str | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        tenant = self.tenant_key.strip()
        actor = self.actor_id.strip()
        authenticated = self.authenticated_user_id.strip()
        if not tenant or not actor or not authenticated:
            raise AuthorityDenied("tenant, actor, and authenticated user are required")
        try:
            actor_type = OrganizationActorType(self.actor_type)
        except ValueError as exc:
            raise AuthorityDenied("unsupported organization actor type") from exc
        if self.role not in ROLES:
            raise AuthorityDenied("unsupported authenticated role")
        object.__setattr__(self, "tenant_key", tenant)
        object.__setattr__(self, "actor_id", actor)
        object.__setattr__(self, "authenticated_user_id", authenticated)
        object.__setattr__(self, "actor_type", actor_type)


def system_bound_agent_command_context(
    *,
    tenant_key: str,
    position_key: str,
    department: str | None,
    authority_level: str | None,
    correlation_key: str | None = None,
    request_id: str | None = None,
) -> OrganizationCommandContext:
    """Build the canonical command context for an AIOS employee acting as an agent.

    ``authenticated_user_id='system'`` and ``role='operator'`` describe the trusted
    system execution boundary only. Organizational authority remains the supplied
    persistent ``OrganizationPosition.position_key``; provider/model/runtime identity
    never becomes the actor and this helper never grants CapabilityAuthority.
    """

    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id=position_key,
        actor_type=OrganizationActorType.agent,
        authenticated_user_id="system",
        role="operator",
        department=department,
        position_key=position_key,
        authority_level=authority_level,
        correlation_key=correlation_key,
        request_id=request_id,
    )


@dataclass(frozen=True)
class AuditMutation:
    action: str
    entity_type: str
    entity_id: Any
    before_state: Any = None
    after_state: Any = None
    reason: str | None = None


def require_role(context: OrganizationCommandContext, *roles: str) -> None:
    if context.role not in roles:
        raise AuthorityDenied(f"role {context.role!r} is not authorized for this command")


def require_mutation_role(context: OrganizationCommandContext) -> None:
    require_role(context, "admin", "operator")


def require_human(context: OrganizationCommandContext, *, admin: bool = False) -> None:
    if context.actor_type is not OrganizationActorType.human:
        raise InvalidHumanActor("an authenticated internal human actor is required")
    if context.actor_id != context.authenticated_user_id:
        raise InvalidHumanActor("human actor must match the authenticated user")
    if admin:
        require_role(context, "admin")


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if is_dataclass(value):
        return {
            item.name: _canonical(getattr(value, item.name))
            for item in fields(value)
            if not item.name.startswith("_")
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, set):
        return sorted((_canonical(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, SQLModel):
        return _canonical(value.model_dump())
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_payload_json(value: Mapping[str, Any] | None) -> str:
    return canonical_json(value or {})


ModelT = TypeVar("ModelT", bound=SQLModel)


def tenant_record(
    session: Session,
    model: type[ModelT],
    record_id: UUID,
    tenant_key: str,
    *,
    label: str,
) -> ModelT:
    record = session.exec(
        select(model).where(model.id == record_id, model.tenant_key == tenant_key)  # type: ignore[attr-defined]
    ).first()
    if record is not None:
        return record
    # This distinction is retained only for internal diagnostics. Future HTTP callers
    # must map both errors to 404 so a tenant cannot probe another tenant's IDs.
    other = session.exec(select(model).where(model.id == record_id)).first()  # type: ignore[attr-defined]
    if other is not None:
        raise TenantMismatch(f"{label} does not belong to the command tenant")
    raise NotFound(f"{label} was not found")


def idempotent_existing(
    existing: ModelT | None,
    fingerprint: str,
    *,
    fingerprint_field: str,
    label: str,
) -> ModelT | None:
    if existing is None:
        return None
    if getattr(existing, fingerprint_field) != fingerprint:
        raise IdempotencyConflict(f"{label} key was already used with a different command")
    return existing


def snapshot(obj: Any) -> dict[str, Any]:
    return to_audit_dict(obj)


def stage_mutations(
    session: Session,
    *,
    mutations: Sequence[AuditMutation],
    context: OrganizationCommandContext,
) -> None:
    """Flush domain changes and their audit rows without owning the transaction.

    This is an internal composition primitive for a caller that already owns the
    surrounding transaction. It deliberately does not commit, refresh, or roll back
    the session. Any exception propagates to the transaction owner, which must decide
    whether to roll back the complete unit of work.
    """

    session.flush()
    for mutation in mutations:
        record_audit(
            session,
            action=mutation.action,
            entity_type=mutation.entity_type,
            entity_id=mutation.entity_id,
            before_state=mutation.before_state,
            after_state=mutation.after_state,
            reason=mutation.reason,
            actor=context.actor_id,
            source="organization_command_v13.16.1b",
            commit=False,
        )
    # Flush the audit rows as part of the same caller-owned transaction so audit
    # storage failures surface before control returns to an integrating source service.
    session.flush()


def commit_mutations(
    session: Session,
    *,
    mutations: Sequence[AuditMutation],
    context: OrganizationCommandContext,
    refresh: Iterable[SQLModel] = (),
) -> None:
    """Stage domain/audit changes, then commit as one standalone transaction."""

    try:
        stage_mutations(session, mutations=mutations, context=context)
        session.commit()
        for record in refresh:
            session.refresh(record)
    except Exception:
        session.rollback()
        raise