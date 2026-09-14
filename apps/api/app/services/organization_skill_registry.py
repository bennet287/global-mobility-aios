from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationPosition, now_utc
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill


NATIVE_SKILL_VALIDATOR = "native_skill_contract_v1"


@dataclass(frozen=True)
class SkillApplicability:
    skill_id: UUID
    skill_key: str
    version: int
    applicable: bool
    reasons: tuple[str, ...]
    missing_tools: tuple[str, ...]
    missing_permissions: tuple[str, ...]


@dataclass(frozen=True)
class NativeSkillValidation:
    skill_id: UUID
    skill_key: str
    version: int
    passed: bool
    validator: str
    checks: tuple[str, ...]
    failures: tuple[str, ...]
    content_sha256: str


def _string_list(raw: str, *, field_name: str) -> tuple[str, ...]:
    """Parse a registry JSON list fail-closed.

    Registry requirements are executable governance inputs. Malformed or
    non-string values must never be interpreted as an empty requirement set.
    """
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {field_name}: expected JSON string list") from exc
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"invalid {field_name}: expected JSON string list")
    return tuple(value)


def _json_object(raw: str, *, field_name: str) -> dict:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {field_name}: expected JSON object") from exc
    if not isinstance(value, dict):
        raise ValueError(f"invalid {field_name}: expected JSON object")
    return value


def list_active_skills(session: Session) -> list[OrganizationSkill]:
    return list(
        session.exec(
            select(OrganizationSkill)
            .where(OrganizationSkill.status == "active")
            .order_by(OrganizationSkill.capability_family, OrganizationSkill.skill_key)
        ).all()
    )


def bind_skill_to_position(
    session: Session,
    *,
    position_id: UUID,
    skill_id: UUID,
    assignment_reason: str,
    actor: str,
) -> OrganizationPositionSkill:
    position = session.get(OrganizationPosition, position_id)
    if position is None or position.status != "active":
        raise ValueError("active organization position not found")
    skill = session.get(OrganizationSkill, skill_id)
    if skill is None or skill.status != "active":
        raise ValueError("active organization skill not found")
    if not assignment_reason.strip():
        raise ValueError("assignment_reason is required")

    existing = session.exec(
        select(OrganizationPositionSkill).where(
            OrganizationPositionSkill.organization_position_id == position_id,
            OrganizationPositionSkill.organization_skill_id == skill_id,
        )
    ).first()
    if existing is not None:
        if existing.status == "eligible":
            return existing
        existing.status = "eligible"
        existing.assignment_reason = assignment_reason.strip()
        existing.assigned_by = actor
        existing.updated_at = now_utc()
        session.add(existing)
        return existing

    binding = OrganizationPositionSkill(
        organization_position_id=position_id,
        organization_skill_id=skill_id,
        assignment_reason=assignment_reason.strip(),
        assigned_by=actor,
    )
    session.add(binding)
    return binding


def validate_native_skill_contract(
    session: Session,
    *,
    skill_id: UUID,
) -> NativeSkillValidation:
    """Deterministically validate a native skill without granting capability authority.

    Phase 14.3 deliberately validates only organization-authored native skills.
    Imported and learned skill lifecycles require separate provenance gates and are
    not promoted by this service.
    """
    skill = session.get(OrganizationSkill, skill_id)
    if skill is None:
        raise ValueError("organization skill not found")
    if skill.origin != "native":
        raise ValueError("Phase 14.3 validates native skills only")
    if skill.status != "active":
        raise ValueError("only active native skills can be validated")

    checks: list[str] = []
    failures: list[str] = []

    for field_name, value in (
        ("skill_key", skill.skill_key),
        ("name", skill.name),
        ("capability_family", skill.capability_family),
        ("description", skill.description),
    ):
        if isinstance(value, str) and value.strip():
            checks.append(f"{field_name}:present")
        else:
            failures.append(f"{field_name}:missing")

    sha = skill.content_sha256 or ""
    if len(sha) == 64:
        try:
            int(sha, 16)
        except ValueError:
            failures.append("content_sha256:not_hex")
        else:
            checks.append("content_sha256:valid")
    else:
        failures.append("content_sha256:invalid_length")

    list_fields = (
        ("compatible_departments_json", skill.compatible_departments_json),
        ("compatible_position_keys_json", skill.compatible_position_keys_json),
        ("tool_requirements_json", skill.tool_requirements_json),
        ("permission_requirements_json", skill.permission_requirements_json),
        ("evidence_expectations_json", skill.evidence_expectations_json),
    )
    for field_name, raw in list_fields:
        try:
            _string_list(raw, field_name=field_name)
        except ValueError:
            failures.append(f"{field_name}:invalid")
        else:
            checks.append(f"{field_name}:valid")

    object_fields = (
        ("input_schema_json", skill.input_schema_json),
        ("output_schema_json", skill.output_schema_json),
    )
    for field_name, raw in object_fields:
        try:
            _json_object(raw, field_name=field_name)
        except ValueError:
            failures.append(f"{field_name}:invalid")
        else:
            checks.append(f"{field_name}:valid")

    passed = not failures
    summary = {
        "validator": NATIVE_SKILL_VALIDATOR,
        "content_sha256": sha,
        "checks": sorted(checks),
        "failures": sorted(failures),
    }
    skill.validation_status = "passed" if passed else "failed"
    skill.validation_summary_json = json.dumps(summary, sort_keys=True, separators=(",", ":"))
    skill.updated_at = now_utc()
    session.add(skill)

    return NativeSkillValidation(
        skill_id=skill.id,
        skill_key=skill.skill_key,
        version=skill.version,
        passed=passed,
        validator=NATIVE_SKILL_VALIDATOR,
        checks=tuple(summary["checks"]),
        failures=tuple(summary["failures"]),
        content_sha256=sha,
    )


def evaluate_skill_applicability(
    *,
    skill: OrganizationSkill,
    position: OrganizationPosition,
    available_tools: Iterable[str] = (),
    available_permissions: Iterable[str] = (),
) -> SkillApplicability:
    reasons: list[str] = []
    if skill.status != "active":
        reasons.append("skill_not_active")
    if skill.validation_status != "passed":
        reasons.append("skill_not_validated")
    if position.status != "active":
        reasons.append("position_not_active")

    departments = _string_list(skill.compatible_departments_json, field_name="compatible_departments_json")
    position_keys = _string_list(skill.compatible_position_keys_json, field_name="compatible_position_keys_json")
    required_tools = _string_list(skill.tool_requirements_json, field_name="tool_requirements_json")
    required_permissions = _string_list(skill.permission_requirements_json, field_name="permission_requirements_json")

    if departments and position.department not in departments:
        reasons.append("department_not_compatible")
    if position_keys and position.position_key not in position_keys:
        reasons.append("position_not_compatible")

    tool_set = set(available_tools)
    permission_set = set(available_permissions)
    missing_tools = tuple(sorted(set(required_tools) - tool_set))
    missing_permissions = tuple(sorted(set(required_permissions) - permission_set))
    if missing_tools:
        reasons.append("missing_tool_requirements")
    if missing_permissions:
        reasons.append("missing_permission_requirements")

    return SkillApplicability(
        skill_id=skill.id,
        skill_key=skill.skill_key,
        version=skill.version,
        applicable=not reasons,
        reasons=tuple(reasons),
        missing_tools=missing_tools,
        missing_permissions=missing_permissions,
    )
