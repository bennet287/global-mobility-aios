from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from labs.r3.common.harness import fingerprint


ALLOWED_STATUSES = {"REVIEWED", "ACTIVE", "DEPRECATED", "REVOKED"}
PROHIBITED_IMPORT_MARKERS = (
    "bypass command gateway",
    "grant authority",
    "self-authorize",
    "read secret",
    "ignore human approval",
    "disable evidence checks",
)


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    version: str
    status: str
    content_sha256: str
    jurisdiction: str
    capabilities: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    risk_class: str
    output_contracts: tuple[str, ...]
    authority_requirements: tuple[str, ...]
    provenance_ref: str
    reviewer_ref: str

    def manifest(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "content_sha256": self.content_sha256,
            "jurisdiction": self.jurisdiction,
            "capabilities": list(self.capabilities),
            "evidence_requirements": list(self.evidence_requirements),
            "risk_class": self.risk_class,
            "output_contracts": list(self.output_contracts),
            "authority_requirements": list(self.authority_requirements),
        }


@dataclass
class SkillAssignment:
    assignment_id: str
    tenant_id: str
    position_key: str
    skill_id: str
    version: str
    content_sha256: str
    jurisdiction: str
    status: str = "ACTIVE"


@dataclass
class QuarantinedCandidate:
    candidate_id: str
    source_ref: str
    content_sha256: str
    payload: dict[str, Any]
    findings: tuple[str, ...]


class SkillRegistry:
    """Synthetic R3 registry. It owns skill lineage, never authority."""

    def __init__(self) -> None:
        self._quarantine: dict[str, QuarantinedCandidate] = {}
        self._definitions: dict[tuple[str, str], SkillDefinition] = {}
        self._assignments: dict[str, SkillAssignment] = {}

    def quarantine_external(
        self,
        *,
        candidate_id: str,
        source_ref: str,
        payload: dict[str, Any],
    ) -> QuarantinedCandidate:
        serialized = copy.deepcopy(payload)
        text = str(serialized).lower()
        findings = tuple(
            marker for marker in PROHIBITED_IMPORT_MARKERS if marker in text
        )
        candidate = QuarantinedCandidate(
            candidate_id=candidate_id,
            source_ref=source_ref,
            content_sha256=fingerprint(serialized),
            payload=serialized,
            findings=findings,
        )
        self._quarantine[candidate_id] = candidate
        return candidate

    def review_candidate(
        self,
        *,
        candidate_id: str,
        reviewer_ref: str,
    ) -> SkillDefinition:
        candidate = self._quarantine[candidate_id]
        if candidate.findings:
            raise ValueError(
                "candidate contains prohibited authority/security instructions"
            )

        payload = candidate.payload
        required = {
            "skill_id",
            "version",
            "jurisdiction",
            "capabilities",
            "evidence_requirements",
            "risk_class",
            "output_contracts",
            "authority_requirements",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"candidate missing required fields: {missing}")

        definition = SkillDefinition(
            skill_id=str(payload["skill_id"]),
            version=str(payload["version"]),
            status="REVIEWED",
            content_sha256=candidate.content_sha256,
            jurisdiction=str(payload["jurisdiction"]),
            capabilities=tuple(sorted(set(payload["capabilities"]))),
            evidence_requirements=tuple(
                sorted(set(payload["evidence_requirements"]))
            ),
            risk_class=str(payload["risk_class"]),
            output_contracts=tuple(sorted(set(payload["output_contracts"]))),
            authority_requirements=tuple(
                sorted(set(payload["authority_requirements"]))
            ),
            provenance_ref=candidate.source_ref,
            reviewer_ref=reviewer_ref,
        )
        key = (definition.skill_id, definition.version)
        existing = self._definitions.get(key)
        if existing and existing.content_sha256 != definition.content_sha256:
            raise ValueError("immutable skill version already exists with another hash")
        self._definitions[key] = definition
        return definition

    def activate(self, *, skill_id: str, version: str) -> SkillDefinition:
        key = (skill_id, version)
        definition = self._definitions[key]
        if definition.status != "REVIEWED":
            raise ValueError("only reviewed definitions can become active")
        active = SkillDefinition(
            **{**definition.__dict__, "status": "ACTIVE"}
        )
        self._definitions[key] = active
        return active

    def deprecate(self, *, skill_id: str, version: str) -> SkillDefinition:
        key = (skill_id, version)
        definition = self._definitions[key]
        if definition.status != "ACTIVE":
            raise ValueError("only active definitions can be deprecated")
        updated = SkillDefinition(
            **{**definition.__dict__, "status": "DEPRECATED"}
        )
        self._definitions[key] = updated
        return updated

    def revoke_definition(
        self,
        *,
        skill_id: str,
        version: str,
    ) -> SkillDefinition:
        key = (skill_id, version)
        definition = self._definitions[key]
        updated = SkillDefinition(
            **{**definition.__dict__, "status": "REVOKED"}
        )
        self._definitions[key] = updated
        return updated

    def assign(
        self,
        *,
        assignment_id: str,
        tenant_id: str,
        position_key: str,
        skill_id: str,
        version: str,
        jurisdiction: str,
    ) -> SkillAssignment:
        definition = self._definitions[(skill_id, version)]
        if definition.status != "ACTIVE":
            raise ValueError("only active skill versions can be assigned")
        if definition.jurisdiction != jurisdiction:
            raise ValueError("assignment jurisdiction does not match skill")
        assignment = SkillAssignment(
            assignment_id=assignment_id,
            tenant_id=tenant_id,
            position_key=position_key,
            skill_id=skill_id,
            version=version,
            content_sha256=definition.content_sha256,
            jurisdiction=jurisdiction,
        )
        self._assignments[assignment_id] = assignment
        return assignment

    def revoke_assignment(self, assignment_id: str) -> SkillAssignment:
        assignment = self._assignments[assignment_id]
        assignment.status = "REVOKED"
        return assignment

    def resolve_execution_manifest(
        self,
        *,
        assignment_id: str,
        tenant_id: str,
        position_key: str,
        jurisdiction: str,
    ) -> dict[str, Any]:
        assignment = self._assignments[assignment_id]
        if assignment.status != "ACTIVE":
            raise ValueError("assignment is not active")
        if assignment.tenant_id != tenant_id:
            raise ValueError("cross-tenant skill assignment denied")
        if assignment.position_key != position_key:
            raise ValueError("skill assignment belongs to another position")
        if assignment.jurisdiction != jurisdiction:
            raise ValueError("skill assignment jurisdiction mismatch")

        definition = self._definitions[
            (assignment.skill_id, assignment.version)
        ]
        if definition.status != "ACTIVE":
            raise ValueError("skill definition is not active")
        if assignment.content_sha256 != definition.content_sha256:
            raise ValueError("skill content hash mismatch")

        return {
            "assignment_id": assignment.assignment_id,
            "tenant_id": assignment.tenant_id,
            "position_key": assignment.position_key,
            "skill": definition.manifest(),
            "authority_granted": False,
            "autonomy_granted": False,
            "credential_refs": [],
        }

    def project_a2a(
        self,
        *,
        skill_id: str,
        version: str,
    ) -> dict[str, Any]:
        definition = self._definitions[(skill_id, version)]
        if definition.status != "ACTIVE":
            raise ValueError("only active skills may be projected")
        return {
            "id": definition.skill_id,
            "version": definition.version,
            "description": f"governed skill for {definition.jurisdiction}",
            "capabilities": list(definition.capabilities),
        }

    def historical_definition(
        self,
        *,
        skill_id: str,
        version: str,
        content_sha256: str,
    ) -> SkillDefinition:
        definition = self._definitions[(skill_id, version)]
        if definition.content_sha256 != content_sha256:
            raise ValueError("historical skill hash does not match")
        return definition


def execution_gate(
    *,
    skill_present: bool,
    capability_available: bool,
    authority_granted: bool,
) -> str:
    if not skill_present:
        return "DENY_SKILL_MISSING"
    if not capability_available:
        return "DENY_CAPABILITY_MISSING"
    if not authority_granted:
        return "DENY_AUTHORITY_MISSING"
    return "ELIGIBLE_FOR_COMMAND_GATEWAY"
