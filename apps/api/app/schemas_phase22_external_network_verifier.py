from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Phase22ExternalVerifierDnsObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hostname: str = Field(min_length=1, max_length=253)
    ipv4_answers: list[str] = Field(default_factory=list, max_length=16)
    ipv6_answers: list[str] = Field(default_factory=list, max_length=16)
    error_code: str | None = Field(default=None, max_length=200)


class Phase22ExternalVerifierTcpObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_ipv4: str = Field(min_length=7, max_length=15)
    first_port: int = Field(ge=1, le=65535)
    last_port: int = Field(ge=1, le=65535)
    scan_complete: bool
    open_tcp_ports: list[int] = Field(default_factory=list, max_length=65535)
    error_code: str | None = Field(default=None, max_length=200)


class Phase22ExternalVerifierHttpRedirectObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hostname: str = Field(min_length=1, max_length=253)
    target_ipv4: str = Field(min_length=7, max_length=15)
    status_code: int | None = Field(default=None, ge=100, le=599)
    location: str | None = Field(default=None, max_length=2048)
    error_code: str | None = Field(default=None, max_length=200)


class Phase22ExternalVerifierTlsHttpsObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hostname: str = Field(min_length=1, max_length=253)
    target_ipv4: str = Field(min_length=7, max_length=15)
    path: str = Field(min_length=1, max_length=1024)
    https_status_code: int | None = Field(default=None, ge=100, le=599)
    certificate_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    certificate_not_before: datetime | None = None
    certificate_not_after: datetime | None = None
    hostname_valid: bool
    chain_valid: bool
    error_code: str | None = Field(default=None, max_length=200)


class Phase22ExternalVerifierProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository: str = Field(min_length=1, max_length=255)
    workflow_path: str = Field(min_length=1, max_length=255)
    verifier_ref: str = Field(min_length=1, max_length=255)
    verifier_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    github_actions_run_id: int = Field(gt=0)
    github_actions_run_attempt: int = Field(gt=0)


class Phase22ExternalNetworkManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_key: Literal["phase22.external-network-verifier"]
    contract_version: Literal[1]
    deployment_run_id: UUID
    networking_contract_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    web_hostname: str = Field(min_length=1, max_length=253)
    api_hostname: str = Field(min_length=1, max_length=253)
    expected_public_ipv4: str = Field(min_length=7, max_length=15)
    allowed_public_tcp_ports: list[int] = Field(min_length=2, max_length=3)
    observed_started_at: datetime
    observed_completed_at: datetime
    provenance: Phase22ExternalVerifierProvenance
    dns_observations: list[Phase22ExternalVerifierDnsObservation] = Field(min_length=2, max_length=2)
    tcp_observation: Phase22ExternalVerifierTcpObservation
    http_redirect_observations: list[Phase22ExternalVerifierHttpRedirectObservation] = Field(
        min_length=2,
        max_length=2,
    )
    tls_https_observations: list[Phase22ExternalVerifierTlsHttpsObservation] = Field(
        min_length=2,
        max_length=2,
    )


class Phase22ExternalNetworkManifestEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: Phase22ExternalNetworkManifest
    public_key_b64: str = Field(min_length=1, max_length=256)
    signature_b64: str = Field(min_length=1, max_length=256)


class Phase22VerifiedExternalNetworkObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deployment_run_id: UUID
    networking_contract_fingerprint: str
    manifest_sha256: str
    verifier_public_key_fingerprint: str
    verifier_repository: str
    verifier_workflow_path: str
    verifier_ref: str
    verifier_commit_sha: str
    github_actions_run_id: int
    github_actions_run_attempt: int
    observed_started_at: datetime
    observed_completed_at: datetime
    signature_verified: bool = True
    freshness_verified: bool = True
    network_contract_satisfied: bool
    blockers: tuple[str, ...]
    receipt_written: bool = False
    rollback_verified: bool = False
    authority_conclusion: str = "none_granted"
    production_ready: bool = False
    promotion_authorized: bool = False
    limitations: tuple[str, ...] = (
        "This object verifies signed off-host public-network observations only; it is not a Phase 22 gate receipt.",
        "Verifier-ref protection and GitHub Environment secret policy are operational prerequisites and are not proven by this manifest validator.",
        "Restart, rollback, migration/data compatibility and candidate restoration remain target-host/deployment-owner evidence.",
        "A valid signed manifest may truthfully report failed network observations; signature validity does not imply network acceptance.",
    )
