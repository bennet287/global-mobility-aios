from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import now_utc
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill


@dataclass(frozen=True)
class NativeSkillDefinition:
    skill_key: str
    name: str
    capability_family: str
    description: str
    compatible_departments: tuple[str, ...] = ()
    compatible_position_keys: tuple[str, ...] = ()
    tool_requirements: tuple[str, ...] = ()
    permission_requirements: tuple[str, ...] = ()
    input_schema: dict | None = None
    output_schema: dict | None = None
    evidence_expectations: tuple[str, ...] = ()


def _clean(value: str, *, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} is required")
    return value


def _strings(values: tuple[str, ...], *, field_name: str) -> tuple[str, ...]:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return tuple(sorted(set(value.strip() for value in values)))


def _canonical_contract(definition: NativeSkillDefinition) -> dict:
    return {
        "skill_key": _clean(definition.skill_key, field_name="skill_key"),
        "name": _clean(definition.name, field_name="name"),
        "capability_family": _clean(definition.capability_family, field_name="capability_family"),
        "description": _clean(definition.description, field_name="description"),
        "compatible_departments": _strings(definition.compatible_departments, field_name="compatible_departments"),
        "compatible_position_keys": _strings(definition.compatible_position_keys, field_name="compatible_position_keys"),
        "tool_requirements": _strings(definition.tool_requirements, field_name="tool_requirements"),
        "permission_requirements": _strings(definition.permission_requirements, field_name="permission_requirements"),
        "input_schema": definition.input_schema or {},
        "output_schema": definition.output_schema or {},
        "evidence_expectations": _strings(definition.evidence_expectations, field_name="evidence_expectations"),
    }


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _build_skill(*, contract: dict, version: int, actor: str, supersedes_skill_id: UUID | None = None) -> OrganizationSkill:
    serialized = _json(contract)
    return OrganizationSkill(
        skill_key=contract["skill_key"],
        name=contract["name"],
        capability_family=contract["capability_family"],
        description=contract["description"],
        origin="native",
        version=version,
        content_sha256=hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        compatible_departments_json=_json(contract["compatible_departments"]),
        compatible_position_keys_json=_json(contract["compatible_position_keys"]),
        tool_requirements_json=_json(contract["tool_requirements"]),
        permission_requirements_json=_json(contract["permission_requirements"]),
        input_schema_json=_json(contract["input_schema"]),
        output_schema_json=_json(contract["output_schema"]),
        evidence_expectations_json=_json(contract["evidence_expectations"]),
        validation_status="unvalidated",
        status="active",
        supersedes_skill_id=supersedes_skill_id,
        created_by=_clean(actor, field_name="actor"),
    )


def create_native_skill(session: Session, *, definition: NativeSkillDefinition, actor: str) -> OrganizationSkill:
    contract = _canonical_contract(definition)
    existing = session.exec(select(OrganizationSkill).where(OrganizationSkill.skill_key == contract["skill_key"])).first()
    if existing is not None:
        raise ValueError("skill_key already exists; create a new version instead")
    skill = _build_skill(contract=contract, version=1, actor=actor)
    session.add(skill)
    return skill


def create_native_skill_version(
    session: Session,
    *,
    skill_id: UUID,
    definition: NativeSkillDefinition,
    actor: str,
) -> OrganizationSkill:
    current = session.get(OrganizationSkill, skill_id)
    if current is None or current.origin != "native":
        raise ValueError("native organization skill not found")
    if current.status != "active":
        raise ValueError("only the active native skill can be versioned")
    contract = _canonical_contract(definition)
    if contract["skill_key"] != current.skill_key:
        raise ValueError("skill_key is immutable across versions")

    current.status = "superseded"
    current.updated_at = now_utc()
    session.add(current)
    session.flush()

    next_version = current.version + 1
    if session.exec(
        select(OrganizationSkill).where(
            OrganizationSkill.skill_key == current.skill_key,
            OrganizationSkill.version == next_version,
        )
    ).first() is not None:
        raise ValueError("next skill version already exists")

    successor = _build_skill(
        contract=contract,
        version=next_version,
        actor=actor,
        supersedes_skill_id=current.id,
    )
    session.add(successor)
    return successor


def deprecate_native_skill(session: Session, *, skill_id: UUID) -> OrganizationSkill:
    skill = session.get(OrganizationSkill, skill_id)
    if skill is None or skill.origin != "native":
        raise ValueError("native organization skill not found")
    if skill.status == "deprecated":
        return skill
    if skill.status != "active":
        raise ValueError("only an active native skill can be deprecated")

    skill.status = "deprecated"
    skill.updated_at = now_utc()
    session.add(skill)
    bindings = session.exec(
        select(OrganizationPositionSkill).where(
            OrganizationPositionSkill.organization_skill_id == skill.id,
            OrganizationPositionSkill.status == "eligible",
        )
    ).all()
    for binding in bindings:
        binding.status = "disabled"
        binding.updated_at = now_utc()
        session.add(binding)
    return skill
