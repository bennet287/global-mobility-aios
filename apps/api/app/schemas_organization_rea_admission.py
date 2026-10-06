"""Reviewed trust inputs and signed observations; none confer execution permission."""
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator, model_serializer, model_validator
from app.schemas_organization_rea_artifacts import Key, Text, ReaArtifactScope

Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReaCiSourceRelationEvidence(StrictModel):
    witness_sha256: Digest
    reviewed_verifier_sha256: Digest
    approved_base_sha: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{40}$")] | None = None


class ReaCompilerLaneEvidence(StrictModel):
    manifest_sha256: Digest
    bundle_sha256: Digest
    workflow_sha256: Digest


class ReaCompilerOutputsEvidence(StrictModel):
    a: ReaCompilerLaneEvidence
    b: ReaCompilerLaneEvidence


class ReaCiAttestationEvidence(StrictModel):
    """Exact human-approved attesting execution; compiler causality is separate."""
    compiler_outputs: ReaCompilerOutputsEvidence | None = None
    source_relation: ReaCiSourceRelationEvidence | None = None
    bundle_sha256: Digest
    ci_source_sha: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{40}$")]
    ci_workflow_sha: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{40}$")]
    source_ref: Annotated[StrictStr, Field(max_length=256)]
    trigger: Literal["pull_request", "workflow_dispatch"]

    @model_serializer(mode="wrap")
    def preserve_historical_shape(self, handler):
        value = handler(self)
        for key in ("source_relation", "compiler_outputs"):
            if key not in self.model_fields_set:
                value.pop(key, None)
        return value

    @model_validator(mode="after")
    def compiler_requires_source_relation(self):
        if self.compiler_outputs is not None and self.source_relation is None:
            raise ValueError("compiler outputs require reviewed source relation")
        return self

    @field_validator("source_ref")
    @classmethod
    def exact_ref(cls, value, info):
        import re
        if not (re.fullmatch(r"refs/pull/[1-9][0-9]*/merge", value) or
                (re.fullmatch(r"refs/heads/[A-Za-z0-9_.\-/]+", value) and ".." not in value)):
            raise ValueError("exact supported CI ref required")
        return value


class ReaCompilationEvidence(StrictModel):
    """Board-reviewed correlation pins; file location stays deployment-owned."""

    ci_attestation: ReaCiAttestationEvidence | None = None
    report_sha256: Digest
    candidate_sha: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{40}$")]
    repository: Literal["bennet287/global-mobility-aios"]
    run_id: Annotated[StrictStr, Field(pattern=r"^[1-9][0-9]{0,19}$")]
    run_attempt: Annotated[StrictStr, Field(pattern=r"^[1-9][0-9]{0,5}$")]
    workflow_sha256: Digest
    helper_sha256: Digest
    review_reference: Text

    @model_serializer(mode="wrap")
    def preserve_historical_shape(self, handler):
        value = handler(self)
        if "ci_attestation" not in self.model_fields_set:
            value.pop("ci_attestation", None)
        return value

    @field_validator("review_reference")
    @classmethod
    def meaningful(cls, value):
        return ReaArtifactScope.meaningful(value)


class ReaToolAdmission(StrictModel):
    tool_id: Key
    disposition: Literal["candidate", "blocked"]
    provider: Key
    provider_version: Key
    effects: Annotated[list[Key], Field(max_length=16)]
    review_reference: Text

    @field_validator("effects", mode="before")
    @classmethod
    def unique_effects(cls, value):
        if type(value) is not list or any(type(v) is not str or not v.strip() or "\x00" in v for v in value) or len(set(value)) != len(value):
            raise ValueError("effects must be explicit unique meaningful strings")
        return sorted(value)

    @field_validator("tool_id", "provider", "provider_version", "review_reference")
    @classmethod
    def meaningful(cls, value):
        return ReaArtifactScope.meaningful(value)


class ReaProviderScope(StrictModel):
    package_name: Literal["rea-agents"] = "rea-agents"
    package_version: Literal["3.2.1"] = "3.2.1"
    build_sha256: Digest
    build_bytes: Annotated[StrictInt, Field(ge=1, le=256*1024*1024)]
    build_review_reference: Text
    publisher_review_reference: Text
    compilation_evidence: ReaCompilationEvidence | None = None
    worker_id: Key
    worker_public_key_hex: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    isolation_policy_sha256: Digest
    isolation_review_reference: Text
    platform: Key
    server_name: Literal["rea"]
    server_version: Literal["3.2.1"]
    protocol_version: Key
    tools: Annotated[list[ReaToolAdmission], Field(min_length=122, max_length=122)]
    expires_at: datetime

    @field_validator("tools", mode="before")
    @classmethod
    def explicit_list(cls, value):
        if type(value) is not list:
            raise ValueError("tools must be an explicit list")
        return value

    @field_validator("tools")
    @classmethod
    def complete(cls, value):
        from app.services.organization_rea_catalog import discover_rea_tools
        ids = [v.tool_id for v in value]
        if len(set(ids)) != 122 or set(ids) != {v.tool_id for v in discover_rea_tools()}:
            raise ValueError("all 122 exact tools require independent explicit disposition")
        from app.services.organization_rea_catalog import get_rea_tool, EFFECT_FIELDS
        hazards = EFFECT_FIELDS - {"idempotent"}
        for entry in value:
            declared = {k for k,v in get_rea_tool(entry.tool_id).contract()["effects"].items() if k in hazards and v is True}
            supplied = set(entry.effects)
            if not supplied <= hazards | {"no_declared_hazards"} or not declared <= supplied or not supplied or ("no_declared_hazards" in supplied and len(supplied) != 1):
                raise ValueError("reviewed effects must explicitly include all source-declared hazards")
            if declared and "no_declared_hazards" in supplied:
                raise ValueError("declared hazards cannot be represented as none")
        return sorted(value, key=lambda v:v.tool_id)

    @field_validator("expires_at", mode="before")
    @classmethod
    def explicit_time(cls, value):
        return ReaArtifactScope.datetime_type(value)

    @field_validator("expires_at")
    @classmethod
    def aware(cls, value):
        return ReaArtifactScope.aware(value)

    @field_validator("build_review_reference", "publisher_review_reference", "worker_id", "isolation_review_reference", "platform", "server_name", "server_version", "protocol_version")
    @classmethod
    def meaningful(cls, value):
        return ReaArtifactScope.meaningful(value)


class ReaProviderProposal(StrictModel):
    decision_key: Key
    artifact_decision_id: UUID
    scope: ReaProviderScope
    supersedes_decision_id: UUID | None = None

    @field_validator("decision_key")
    @classmethod
    def meaningful(cls, value):
        return ReaArtifactScope.meaningful(value)


class ReaReportedIdentity(StrictModel):
    worker_id: Key
    build_sha256: Digest
    package_name: Literal["rea-agents"]
    package_version: Literal["3.2.1"]
    server_name: Literal["rea"]
    server_version: Literal["3.2.1"]
    protocol_version: Key
    platform: Key
    session_id: UUID
    isolation_policy_sha256: Digest
    provider_matrix_sha256: Digest

    @field_validator("worker_id", "server_name", "server_version", "protocol_version", "platform")
    @classmethod
    def meaningful(cls, value):
        return ReaArtifactScope.meaningful(value)


class ReaWorkerObservation(StrictModel):
    # Exact challenge object is signed, with advertised catalog bytes separately committed.
    challenge: dict
    reported: ReaReportedIdentity
    tools_observation_sha256: Digest
    signature_hex: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{128}$")]
