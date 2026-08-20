from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.models.domain import OrganizationPosition, OrganizationalWorkItem, now_utc
from app.services.organization_agent_runtime import (
    RUNTIME_BINDING_SCHEMA_VERSION,
    AgentRuntimeProfile,
    RuntimeBindingStale,
    RuntimeCapabilityUnavailable,
    RuntimeClass,
    RuntimeProfileDisabled,
    RuntimeProfileInvalid,
    bind_employee_runtime,
    runtime_contract_field_names,
)
from app.services.organization_command import canonical_json
from app.services.organization_context_broker import build_work_item_context_bundle


def _position(session: Session, *, status: str = "active") -> OrganizationPosition:
    row = OrganizationPosition(
        position_key="austria_mobility_specialist",
        title="Austria Immigration Specialist",
        department="Mobility",
        reports_to_position_key="mobility_operations_lead",
        role_card_name="austria_mobility_specialist",
        authority_level="L2",
        contract_json='{"jurisdiction":"AT","scope":"mobility_case"}',
        status=status,
        version=4,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _work(session: Session) -> OrganizationalWorkItem:
    row = OrganizationalWorkItem(
        idempotency_key=f"runtime-work-{uuid4()}",
        tenant_key="tenant-a",
        title="Assess Austrian mobility pathway",
        objective="Prepare a governed mobility assessment.",
        department="Mobility",
        authority_level="L2",
        assigned_position_key="austria_mobility_specialist",
        risk_level="routine",
        context_json='{"country":"Austria","stage":"assessment"}',
        source_object_type="mobility_case",
        source_object_id="case-at-001",
        source_object_version="v3",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _profile(
    *,
    profile_key: str = "hosted-reasoning-v1",
    provider_key: str = "deepseek",
    model_key: str | None = "deepseek-reasoner",
    runtime_class: RuntimeClass = RuntimeClass.HOSTED_API,
    available_tools: tuple[str, ...] = ("browser", "shell"),
    technical_capabilities: tuple[str, ...] = ("reasoning", "structured_output"),
    enabled: bool = True,
) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=profile_key,
        runtime_class=runtime_class,
        adapter_key=f"{provider_key}-adapter",
        provider_key=provider_key,
        model_key=model_key,
        technical_capabilities=technical_capabilities,
        available_tools=available_tools,
        independence_group=provider_key,
        profile_version=1,
        enabled=enabled,
    )


def _context(session: Session):
    work = _work(session)
    context = build_work_item_context_bundle(
        session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
    )
    return work, context


def test_binds_runtime_without_redefining_persistent_employee_identity(db_session: Session) -> None:
    _position(db_session)
    _, context = _context(db_session)

    binding = bind_employee_runtime(
        db_session,
        context=context,
        profile=_profile(),
        required_capability="reasoning",
    )

    assert binding.schema_version == RUNTIME_BINDING_SCHEMA_VERSION
    assert binding.position_key == context.position.position_key
    assert binding.position_version == context.position.position_version
    assert binding.context_hash == context.context_hash
    assert binding.provider_key == "deepseek"
    assert binding.model_key == "deepseek-reasoner"
    assert binding.runtime_class is RuntimeClass.HOSTED_API


def test_runtime_profile_has_no_authority_autonomy_or_risk_fields() -> None:
    fields = runtime_contract_field_names()
    assert "authority_level" not in fields
    assert "autonomy_level" not in fields
    assert "risk_tier" not in fields
    assert "evidence_refs" not in fields
    assert "policy_version" not in fields
    assert "session_id" not in fields
    assert "process_id" not in fields


def test_alternate_provider_changes_binding_not_employee_or_context_identity(db_session: Session) -> None:
    _position(db_session)
    _, context = _context(db_session)

    hosted = bind_employee_runtime(db_session, context=context, profile=_profile())
    cli = bind_employee_runtime(
        db_session,
        context=context,
        profile=_profile(
            profile_key="cli-reasoning-v1",
            provider_key="anthropic-cli",
            model_key=None,
            runtime_class=RuntimeClass.CLI,
        ),
    )

    assert hosted.position_key == cli.position_key == "austria_mobility_specialist"
    assert hosted.position_version == cli.position_version == 4
    assert hosted.context_hash == cli.context_hash == context.context_hash
    assert hosted.binding_hash != cli.binding_hash
    assert hosted.provider_key != cli.provider_key


def test_runtime_tools_are_intersection_not_authority_grant(db_session: Session) -> None:
    _position(db_session)
    _, context = _context(db_session)
    authorized_context = replace(context, allowed_tools=("browser",))

    binding = bind_employee_runtime(
        db_session,
        context=authorized_context,
        profile=_profile(available_tools=("browser", "shell", "filesystem")),
    )

    assert binding.allowed_tools == ("browser",)
    assert "shell" not in binding.allowed_tools
    assert "filesystem" not in binding.allowed_tools


def test_required_technical_capability_must_exist(db_session: Session) -> None:
    _position(db_session)
    _, context = _context(db_session)

    with pytest.raises(RuntimeCapabilityUnavailable):
        bind_employee_runtime(
            db_session,
            context=context,
            profile=_profile(technical_capabilities=("structured_output",)),
            required_capability="reasoning",
        )


def test_stale_context_cannot_be_bound_after_canonical_work_change(db_session: Session) -> None:
    _position(db_session)
    work, context = _context(db_session)

    work.context_json = canonical_json({"country": "Austria", "stage": "review"})
    work.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(work)
    db_session.commit()

    with pytest.raises(RuntimeBindingStale):
        bind_employee_runtime(db_session, context=context, profile=_profile())


def test_disabled_runtime_profile_fails_closed(db_session: Session) -> None:
    _position(db_session)
    _, context = _context(db_session)

    with pytest.raises(RuntimeProfileDisabled):
        bind_employee_runtime(db_session, context=context, profile=_profile(enabled=False))


def test_runtime_profile_validation_and_binding_hash_are_deterministic(db_session: Session) -> None:
    _position(db_session)
    _, context = _context(db_session)

    with pytest.raises(RuntimeProfileInvalid):
        _profile(provider_key="   ")

    profile = _profile(
        available_tools=("shell", "browser", "browser"),
        technical_capabilities=("structured_output", "reasoning", "reasoning"),
    )
    first = bind_employee_runtime(db_session, context=context, profile=profile)
    second = bind_employee_runtime(db_session, context=context, profile=profile)

    assert profile.available_tools == ("browser", "shell")
    assert profile.technical_capabilities == ("reasoning", "structured_output")
    assert first.binding_hash == second.binding_hash
    assert first.bound_at <= second.bound_at
