from __future__ import annotations

import base64
from datetime import timedelta, timezone
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlmodel import Session, func, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationActorType,
    OrganizationDecisionType,
    OrganizationalWorkItem,
)
from app.models.production_deployment_acceptance import (
    ProductionDeploymentAcceptanceCheckReceipt,
)
from app.schemas_phase22_external_network_verifier import (
    Phase22ExternalNetworkManifest,
    Phase22ExternalNetworkManifestEnvelope,
)
from app.services.organization_command import OrganizationCommandContext
from app.services.phase22_external_network_verifier import (
    EXTERNAL_NETWORK_VERIFIER_CONTRACT_KEY,
    EXTERNAL_NETWORK_VERIFIER_CONTRACT_VERSION,
    EXTERNAL_NETWORK_VERIFIER_REPOSITORY,
    EXTERNAL_NETWORK_VERIFIER_WORKFLOW_PATH,
    ExternalNetworkVerifierEvidenceError,
    external_network_manifest_bytes,
    external_verifier_public_key_fingerprint,
    verify_external_network_manifest,
)
from app.services.production_deployment_acceptance import (
    networking_contract_fingerprint,
    prepare_deployment_acceptance_run,
)


RELEASE_SHA = "a" * 40
ROLLBACK_SHA = "b" * 40
RELEASE_CONFIG_FP = "c" * 64
ROLLBACK_CONFIG_FP = "d" * 64
ENVIRONMENT_FP = "e" * 64
EXPECTED_IPV4 = "8.8.8.8"
WEB_HOST = "app.globalmobility.example.eu"
API_HOST = "api.globalmobility.example.eu"


def _context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="pytest-board",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="pytest-board",
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )


def _work_and_decision(session: Session):
    suffix = str(uuid4())
    work = OrganizationalWorkItem(
        idempotency_key=f"phase22-verifier-work-{suffix}",
        tenant_key="default",
        work_type="production_deployment_acceptance",
        objective_key=f"phase22-verifier-{suffix}",
        phase_key="22",
        title="Verify off-host network evidence",
        objective="Prepare an exact canary deployment run for signed external network evidence.",
        department="Technology",
        authority_level="L4",
        assigned_position_key="board",
        risk_level="high",
        source_object_type="release_request",
        source_object_id=f"release-request-{suffix}",
        source_object_version=RELEASE_SHA,
        created_by="pytest",
    )
    session.add(work)
    session.commit()
    session.refresh(work)

    decision = ExecutiveDecision(
        decision_key=f"phase22-verifier-decision-{suffix}",
        tenant_key="default",
        decision_type=OrganizationDecisionType.board_reserved,
        work_item_id=work.id,
        source_object_type=work.source_object_type,
        source_object_id=work.source_object_id,
        source_object_version=work.source_object_version,
        authority_level="L4",
        requested_by_position="cto",
        decision_owner_position="board",
        title="Admit bounded canary preparation",
        question="May this exact deployment acceptance run be prepared?",
        recommendation="Prepare identity and verifier trust root only.",
        status="approved",
        decided_by="pytest-board",
        decision_reason="Pytest governed deployment preparation.",
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)
    return work, decision


def _keypair():
    private_key = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_key, public_bytes, external_verifier_public_key_fingerprint(public_bytes)


def _prepare(session: Session, *, verifier_fingerprint: str):
    context = _context()
    work, decision = _work_and_decision(session)
    contract = {
        "web_hostname": WEB_HOST,
        "api_hostname": API_HOST,
        "expected_public_ipv4": EXPECTED_IPV4,
        "allowed_public_tcp_ports": [80, 443],
        "external_verifier_public_key_fingerprint": verifier_fingerprint,
    }
    run = prepare_deployment_acceptance_run(
        session,
        context,
        deployment_run_key=f"phase22-external-verifier-{uuid4()}",
        environment_key="canary-single-vps",
        target_environment_fingerprint=ENVIRONMENT_FP,
        release_commit_sha=RELEASE_SHA,
        release_configuration_fingerprint=RELEASE_CONFIG_FP,
        rollback_release_commit_sha=ROLLBACK_SHA,
        rollback_configuration_fingerprint=ROLLBACK_CONFIG_FP,
        networking_contract=contract,
        work_item_id=work.id,
        admission_decision_id=decision.id,
        reason="Prepare exact run for signed off-host networking evidence.",
    )
    return context, run, contract


def _manifest(run, contract, *, complete_offset_minutes: int = 2):
    prepared = run.created_at
    if prepared.tzinfo is None:
        prepared = prepared.replace(tzinfo=timezone.utc)
    start = prepared + timedelta(minutes=1)
    complete = prepared + timedelta(minutes=complete_offset_minutes)
    return Phase22ExternalNetworkManifest(
        contract_key=EXTERNAL_NETWORK_VERIFIER_CONTRACT_KEY,
        contract_version=EXTERNAL_NETWORK_VERIFIER_CONTRACT_VERSION,
        deployment_run_id=run.id,
        networking_contract_fingerprint=networking_contract_fingerprint(contract),
        web_hostname=WEB_HOST,
        api_hostname=API_HOST,
        expected_public_ipv4=EXPECTED_IPV4,
        allowed_public_tcp_ports=[80, 443],
        observed_started_at=start,
        observed_completed_at=complete,
        provenance={
            "repository": EXTERNAL_NETWORK_VERIFIER_REPOSITORY,
            "workflow_path": EXTERNAL_NETWORK_VERIFIER_WORKFLOW_PATH,
            "verifier_ref": "refs/heads/main",
            "verifier_commit_sha": "9" * 40,
            "github_actions_run_id": 123456,
            "github_actions_run_attempt": 1,
        },
        dns_observations=[
            {"hostname": WEB_HOST, "ipv4_answers": [EXPECTED_IPV4], "ipv6_answers": []},
            {"hostname": API_HOST, "ipv4_answers": [EXPECTED_IPV4], "ipv6_answers": []},
        ],
        tcp_observation={
            "target_ipv4": EXPECTED_IPV4,
            "first_port": 1,
            "last_port": 65535,
            "scan_complete": True,
            "open_tcp_ports": [80, 443],
        },
        http_redirect_observations=[
            {
                "hostname": WEB_HOST,
                "target_ipv4": EXPECTED_IPV4,
                "status_code": 308,
                "location": f"https://{WEB_HOST}/",
            },
            {
                "hostname": API_HOST,
                "target_ipv4": EXPECTED_IPV4,
                "status_code": 308,
                "location": f"https://{API_HOST}/",
            },
        ],
        tls_https_observations=[
            {
                "hostname": WEB_HOST,
                "target_ipv4": EXPECTED_IPV4,
                "path": "/",
                "https_status_code": 200,
                "certificate_sha256": "1" * 64,
                "certificate_not_before": start - timedelta(days=1),
                "certificate_not_after": start + timedelta(days=30),
                "hostname_valid": True,
                "chain_valid": True,
            },
            {
                "hostname": API_HOST,
                "target_ipv4": EXPECTED_IPV4,
                "path": "/health",
                "https_status_code": 200,
                "certificate_sha256": "2" * 64,
                "certificate_not_before": start - timedelta(days=1),
                "certificate_not_after": start + timedelta(days=30),
                "hostname_valid": True,
                "chain_valid": True,
            },
        ],
    )


def _envelope(manifest, private_key, public_bytes):
    signature = private_key.sign(external_network_manifest_bytes(manifest))
    return Phase22ExternalNetworkManifestEnvelope(
        manifest=manifest,
        public_key_b64=base64.b64encode(public_bytes).decode("ascii"),
        signature_b64=base64.b64encode(signature).decode("ascii"),
    )


def _count_receipts(session: Session) -> int:
    return session.exec(
        select(func.count()).select_from(ProductionDeploymentAcceptanceCheckReceipt)
    ).one()


def _verify_now(manifest):
    return manifest.observed_completed_at + timedelta(minutes=1)


def test_signed_external_network_manifest_verifies_without_writing_receipt(
    db_session: Session,
) -> None:
    private_key, public_bytes, fingerprint = _keypair()
    context, run, contract = _prepare(db_session, verifier_fingerprint=fingerprint)
    manifest = _manifest(run, contract)
    before = _count_receipts(db_session)

    result = verify_external_network_manifest(
        db_session,
        context,
        deployment_run_id=run.id,
        envelope=_envelope(manifest, private_key, public_bytes),
        verified_at=_verify_now(manifest),
    )

    assert result.signature_verified is True
    assert result.freshness_verified is True
    assert result.network_contract_satisfied is True
    assert result.blockers == ()
    assert result.receipt_written is False
    assert result.rollback_verified is False
    assert result.authority_conclusion == "none_granted"
    assert result.production_ready is False
    assert result.promotion_authorized is False
    assert _count_receipts(db_session) == before


def test_external_network_manifest_rejects_wrong_pinned_key(
    db_session: Session,
) -> None:
    _private_key, _public_bytes, pinned_fingerprint = _keypair()
    context, run, contract = _prepare(db_session, verifier_fingerprint=pinned_fingerprint)
    manifest = _manifest(run, contract)
    other_private, other_public, _ = _keypair()

    with pytest.raises(ExternalNetworkVerifierEvidenceError, match="trust root"):
        verify_external_network_manifest(
            db_session,
            context,
            deployment_run_id=run.id,
            envelope=_envelope(manifest, other_private, other_public),
            verified_at=_verify_now(manifest),
        )


def test_external_network_manifest_rejects_signature_tamper(
    db_session: Session,
) -> None:
    private_key, public_bytes, fingerprint = _keypair()
    context, run, contract = _prepare(db_session, verifier_fingerprint=fingerprint)
    original = _manifest(run, contract)
    envelope = _envelope(original, private_key, public_bytes)
    tampered = original.model_copy(deep=True)
    tampered.tcp_observation.open_tcp_ports = [22, 80, 443]
    envelope.manifest = tampered

    with pytest.raises(ExternalNetworkVerifierEvidenceError, match="signature"):
        verify_external_network_manifest(
            db_session,
            context,
            deployment_run_id=run.id,
            envelope=envelope,
            verified_at=_verify_now(tampered),
        )


def test_external_network_manifest_rejects_stale_or_wrong_run_identity(
    db_session: Session,
) -> None:
    private_key, public_bytes, fingerprint = _keypair()
    context, run, contract = _prepare(db_session, verifier_fingerprint=fingerprint)
    manifest = _manifest(run, contract)
    envelope = _envelope(manifest, private_key, public_bytes)

    with pytest.raises(ExternalNetworkVerifierEvidenceError, match="stale"):
        verify_external_network_manifest(
            db_session,
            context,
            deployment_run_id=run.id,
            envelope=envelope,
            verified_at=manifest.observed_completed_at + timedelta(hours=3),
        )

    wrong = manifest.model_copy(deep=True)
    wrong.deployment_run_id = uuid4()
    wrong_envelope = _envelope(wrong, private_key, public_bytes)
    with pytest.raises(ExternalNetworkVerifierEvidenceError, match="different deployment run"):
        verify_external_network_manifest(
            db_session,
            context,
            deployment_run_id=run.id,
            envelope=wrong_envelope,
            verified_at=_verify_now(wrong),
        )


def test_authentic_signed_network_failure_is_valid_failure_evidence(
    db_session: Session,
) -> None:
    private_key, public_bytes, fingerprint = _keypair()
    context, run, contract = _prepare(db_session, verifier_fingerprint=fingerprint)
    manifest = _manifest(run, contract)
    manifest.tcp_observation.open_tcp_ports = [22, 80, 443]
    manifest.dns_observations[0].ipv6_answers = ["2001:4860:4860::8888"]
    before = _count_receipts(db_session)

    result = verify_external_network_manifest(
        db_session,
        context,
        deployment_run_id=run.id,
        envelope=_envelope(manifest, private_key, public_bytes),
        verified_at=_verify_now(manifest),
    )

    assert result.signature_verified is True
    assert result.network_contract_satisfied is False
    assert "tcp:open_port_set_mismatch" in result.blockers
    assert f"dns:{WEB_HOST}:unexpected_ipv6_answers" in result.blockers
    assert _count_receipts(db_session) == before


def test_external_network_manifest_rejects_networking_fingerprint_mismatch(
    db_session: Session,
) -> None:
    private_key, public_bytes, fingerprint = _keypair()
    context, run, contract = _prepare(db_session, verifier_fingerprint=fingerprint)
    manifest = _manifest(run, contract)
    manifest.networking_contract_fingerprint = "0" * 64

    with pytest.raises(ExternalNetworkVerifierEvidenceError, match="networking fingerprint"):
        verify_external_network_manifest(
            db_session,
            context,
            deployment_run_id=run.id,
            envelope=_envelope(manifest, private_key, public_bytes),
            verified_at=_verify_now(manifest),
        )
