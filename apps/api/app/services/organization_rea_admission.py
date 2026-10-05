"""Board-reviewed local-build and challenge-bound worker observations.

This is an internal pre-admission predicate. A reviewed deployment key authenticates
statement possession only: no owned REA transport, actual isolation/provider behavior,
upstream provenance or execution entitlement is established here.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import sqlite3
from uuid import UUID, uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.exc import OperationalError
from sqlmodel import select

from app.models.domain import AuditLog, ExecutiveDecision, OrganizationalWorkItem, OrganizationExecutionAttempt, now_utc
from app.schemas_organization_rea_admission import ReaProviderProposal, ReaProviderScope, ReaWorkerObservation
from app.services.audit_log import record_audit
from app.services.organization_command import InvalidTransition, AuthorityDenied, canonical_fingerprint, canonical_json, snapshot
from app.services.organization_decision import create_executive_decision
from app.services.organization_rea_catalog import REA_LOCAL_CATALOG_SHA256, REA_SOURCE_COMMIT, compare_rea_tools_observation, MAX_JSON_BYTES, ReaCatalogInvalid
from app.services import organization_rea_artifacts as artifact

SOURCE = "organization_rea_provider_v1"
KIND = "rea_provider_review_v1"
PROPOSE = "organization.rea.provider.propose"
CHALLENGE = "organization.rea.worker.challenge"
CONSUME = "organization.rea.worker.observation"


@dataclass(frozen=True)
class ReaDeploymentTrust:
    """Deployment-owned input, never HTTP or worker observation data.

    Independently configured worker key/policy are administrator trust anchors,
    not proof of current key custody or enforcement on the remote worker.
    """
    build_root: Path
    build_relative: str
    worker_id: str
    worker_public_key: bytes
    isolation_policy_sha256: str
    custody_root: Path


def _contract(row):
    values = artifact._json(row.conditions_json, limit=artifact.MAX_CONTRACT_BYTES)
    if type(values) is not list or len(values) != 1 or type(values[0]) is not dict or set(values[0]) != {"kind", "scope", "link", "artifact_decision_id", "artifact_contract_sha256", "catalog_sha256", "source_commit"}:
        raise InvalidTransition("decision lacks typed provider review")
    contract = values[0]
    if contract["kind"] != KIND or contract["catalog_sha256"] != REA_LOCAL_CATALOG_SHA256 or contract["source_commit"] != REA_SOURCE_COMMIT:
        raise InvalidTransition("provider review catalog/source differs")
    try:
        scope = ReaProviderScope.model_validate(contract["scope"])
    except (ValidationError, TypeError, ValueError) as exc:
        raise InvalidTransition("invalid provider review scope") from exc
    if contract["scope"] != scope.model_dump(mode="json") or row.source_object_type != KIND or row.source_object_id != scope.build_sha256 or row.source_object_version != canonical_fingerprint(contract):
        raise InvalidTransition("provider review source/scope differs")
    return contract, scope


def _witness(session, row, *, approved):
    contract, scope = _contract(row)
    if row.decision_type != "board_reserved" or row.authority_level != "L4" or row.decision_owner_position != "board" or row.work_item_id is None or row.accepted_action_output_id is not None:
        raise InvalidTransition("provider review owner/linkage differs")
    creation = artifact._audits(session, row, "organization.decision.create")
    proposals = artifact._audits(session, row, PROPOSE, SOURCE)
    if len(creation) != 1 or len(proposals) != 1:
        raise InvalidTransition("provider review lacks guarded proposal lineage")
    created = artifact._json(creation[0].after_state_json)
    if type(created) is not dict:
        raise InvalidTransition("provider creation snapshot is invalid")
    for key in ("created_at", "expires_at", "due_at"):
        if created.get(key):
            try:
                created[key] = artifact._utc(datetime.fromisoformat(created[key])).isoformat()
            except (TypeError, ValueError) as exc:
                raise InvalidTransition("provider snapshot datetime invalid") from exc
    expected = {"contract_sha256": canonical_fingerprint(contract), "record_fingerprint": row.record_fingerprint,
                "tenant_key": row.tenant_key, "work_item_id": str(row.work_item_id), "human_proposal": True}
    if artifact._json(proposals[0].after_state_json) != expected or proposals[0].actor != creation[0].actor or artifact._utc(proposals[0].created_at) < artifact._utc(creation[0].created_at) or canonical_fingerprint(artifact._invariant(row)) != canonical_fingerprint({key: created.get(key) for key in artifact._invariant(row)}):
        raise InvalidTransition("provider proposal snapshot differs")
    if approved:
        approvals = artifact._audits(session, row, "organization.decision.approved")
        if row.status != "approved" or len(approvals) != 1 or row.decided_at is None:
            raise InvalidTransition("provider review is not canonically approved")
        before, after = artifact._json(approvals[0].before_state_json), artifact._json(approvals[0].after_state_json)
        if type(before) is not dict or type(after) is not dict or before.get("status") != "pending_board" or after.get("status") != "approved" or approvals[0].actor != row.decided_by or artifact._utc(proposals[0].created_at) > artifact._utc(approvals[0].created_at):
            raise InvalidTransition("provider approval lineage differs")
        for key, value in snapshot(row).items():
            if key in {"reminded_at", "coordination_token", "coordination_claimed_at"}:
                continue
            if key in {"updated_at", "decided_at", "created_at", "expires_at"} and value is not None and after.get(key) is not None:
                try:
                    matches = artifact._utc(datetime.fromisoformat(value)) == artifact._utc(datetime.fromisoformat(after[key]))
                except (TypeError, ValueError) as exc:
                    raise InvalidTransition("provider approval datetime invalid") from exc
            else:
                matches = after.get(key) == value
            if not matches:
                raise InvalidTransition("provider approval snapshot differs")
        if artifact._utc(row.decided_at) >= scope.expires_at:
            raise InvalidTransition("provider approval was expired")
    return contract, scope


def propose_rea_provider_review(session, context, payload: ReaProviderProposal):
    artifact._board(context)
    payload = ReaProviderProposal.model_validate(payload.model_dump())
    now = artifact._utc(now_utc())
    if not now < payload.scope.expires_at <= now + timedelta(days=30):
        raise InvalidTransition("provider expiry must be future within 30 days")
    # Follow provider -> artifact -> work -> position lock order, including
    # retries and replacement proposals which can reference existing provider rows.
    existing = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.tenant_key == context.tenant_key,
        ExecutiveDecision.decision_key == payload.decision_key)).first()
    provider_ids = {existing.id} if existing is not None else set()
    if payload.supersedes_decision_id:
        provider_ids.add(payload.supersedes_decision_id)
    if provider_ids:
        session.exec(select(ExecutiveDecision).where(ExecutiveDecision.tenant_key == context.tenant_key,
            ExecutiveDecision.id.in_(provider_ids)).order_by(ExecutiveDecision.id)
            .execution_options(populate_existing=True).with_for_update()).all()
    predecessor = None
    if payload.supersedes_decision_id:
        predecessor = artifact._decision(session, context.tenant_key, payload.supersedes_decision_id)
        _witness(session, predecessor, approved=True)
    authorized = artifact.resolve_rea_artifact_authorization(session, context, decision_id=payload.artifact_decision_id)
    if payload.scope.expires_at > authorized.expires_at:
        raise InvalidTransition("provider review cannot outlive artifact authorization")
    _, link = artifact._work_link(session, context.tenant_key, authorized.work_item_id)
    contract = {"kind": KIND, "scope": payload.scope.model_dump(mode="json"), "link": link,
                "artifact_decision_id": str(payload.artifact_decision_id), "artifact_contract_sha256": authorized.contract_sha256,
                "catalog_sha256": REA_LOCAL_CATALOG_SHA256, "source_commit": REA_SOURCE_COMMIT}
    # Bound the escaped serialized contract too: generic creation/approval audits
    # embed conditions_json as a JSON string and escape it a second time.
    if len(canonical_json([contract]).encode()) > artifact.MAX_CONTRACT_BYTES or len(json.dumps([contract], ensure_ascii=True).encode()) > artifact.MAX_CONTRACT_BYTES:
        raise InvalidTransition("provider review exceeds aggregate persisted JSON bounds")
    if predecessor is not None:
        if predecessor.work_item_id != authorized.work_item_id:
            raise InvalidTransition("provider replacement must retain WorkItem")
    row = create_executive_decision(session, context, decision_key=payload.decision_key, decision_type="board_reserved", authority_level="L4",
        requested_by_position=context.position_key, decision_owner_position="board", title="REA build and worker trust review",
        question="Review build bytes, deployment key and explicit full-catalog provider/effect dispositions",
        recommendation="Review pre-admission trust only; execution and transport remain disabled", conditions=[contract],
        work_item_id=authorized.work_item_id, source_object_type=KIND, source_object_id=payload.scope.build_sha256,
        source_object_version=canonical_fingerprint(contract), supersedes_decision_id=payload.supersedes_decision_id,
        expires_at=payload.scope.expires_at)
    row = artifact._decision(session, context.tenant_key, row.id)
    proposals = artifact._audits(session, row, PROPOSE, SOURCE)
    expected = {"contract_sha256": canonical_fingerprint(contract), "record_fingerprint": row.record_fingerprint,
                "tenant_key": row.tenant_key, "work_item_id": str(row.work_item_id), "human_proposal": True}
    if proposals:
        if len(proposals) != 1 or artifact._json(proposals[0].after_state_json) != expected:
            raise InvalidTransition("provider proposal witness conflict")
        return row
    creation = artifact._audits(session, row, "organization.decision.create")
    if row.status != "pending_board" or artifact._audits(session, row, "organization.decision.approved") or len(creation) != 1 or creation[0].actor != context.actor_id:
        raise AuthorityDenied("only matching creator may complete pending typed provider review")
    try:
        record_audit(session, action=PROPOSE, entity_type="executive_decision", entity_id=row.id,
                     after_state=expected, actor=context.actor_id, source=SOURCE)
        session.commit()
    except Exception:
        session.rollback()
        # Generic creation commits independently; missing witness remains fail closed.
        raise
    return row


def resolve_rea_provider_review(session, context, *, decision_id, trust: ReaDeploymentTrust):
    row = artifact._decision(session, context.tenant_key, decision_id)
    contract, scope = _witness(session, row, approved=True)
    if artifact._utc(now_utc()) >= scope.expires_at or row.expires_at is None or artifact._utc(row.expires_at) != scope.expires_at:
        raise InvalidTransition("provider review expired")
    if session.exec(select(ExecutiveDecision).where(ExecutiveDecision.supersedes_decision_id == row.id)).first():
        raise InvalidTransition("provider review has successor lineage")
    authorized = artifact.resolve_rea_artifact_authorization(session, context, decision_id=UUID(contract["artifact_decision_id"]))
    _, link = artifact._work_link(session, context.tenant_key, row.work_item_id)
    if authorized.work_item_id != row.work_item_id or authorized.contract_sha256 != contract["artifact_contract_sha256"] or link != contract["link"]:
        raise InvalidTransition("provider artifact/work linkage changed")
    if type(trust) is not ReaDeploymentTrust or type(trust.worker_public_key) is not bytes or len(trust.worker_public_key) != 32 or trust.worker_id != scope.worker_id or trust.worker_public_key.hex() != scope.worker_public_key_hex or trust.isolation_policy_sha256 != scope.isolation_policy_sha256:
        raise AuthorityDenied("independent deployment worker trust anchor differs")
    fd = None
    try:
        fd = artifact._source_file(trust.build_root, trust.build_relative)
        if os.fstat(fd).st_mode & 0o222 or artifact._bytes(fd, scope.build_bytes) != scope.build_sha256:
            raise InvalidTransition("reviewed build bytes/mode differ")
    except OSError as exc:
        raise InvalidTransition("build path unavailable or unsafe") from exc
    finally:
        if fd is not None:
            os.close(fd)
    return row, contract, scope, authorized


def _attempt(session, context, work_id, attempt_id):
    work, _ = artifact._work_link(session, context.tenant_key, work_id)
    attempt = session.exec(select(OrganizationExecutionAttempt).where(OrganizationExecutionAttempt.id == attempt_id,
        OrganizationExecutionAttempt.work_item_id == work.id).execution_options(populate_existing=True).with_for_update()).first()
    if attempt is None or work.status != "running" or attempt.status != "running" or attempt.completed_at is not None or not work.execution_token or attempt.execution_token != work.execution_token or attempt.attempt_number != work.execution_attempts or work.execution_started_at is None or not artifact._utc(work.execution_started_at) <= artifact._utc(attempt.started_at) <= artifact._utc(now_utc()):
        raise InvalidTransition("worker observation requires fresh running canonical attempt")
    audits = session.exec(select(AuditLog).where(AuditLog.entity_type == "organizational_work_item", AuditLog.entity_id == str(work.id), AuditLog.action == "organization_work_execution_started", AuditLog.source == "ai_organization_v13.0")).all()
    matching = []
    for audit in audits:
        data = artifact._json(audit.after_state_json)
        if type(data) is not dict:
            raise InvalidTransition("canonical start audit must be an object")
        if data.get("execution_token") == attempt.execution_token and type(data.get("attempt")) is int and data["attempt"] == attempt.attempt_number:
            matching.append(audit)
    running = session.exec(select(OrganizationExecutionAttempt).where(OrganizationExecutionAttempt.work_item_id == work.id,
        OrganizationExecutionAttempt.status == "running").execution_options(populate_existing=True)).all()
    if len(running) != 1 or running[0].id != attempt.id:
        raise InvalidTransition("canonical running attempt is ambiguous")
    if len(matching) != 1 or matching[0].actor != attempt.actor or artifact._utc(matching[0].created_at) < artifact._utc(attempt.started_at):
        raise InvalidTransition("attempt lacks canonical start audit")
    return work, attempt


def _barrier(session, context, work_id, attempt_id):
    work, attempt = _attempt(session, context, work_id, attempt_id)
    result = session.exec(update(OrganizationalWorkItem).where(OrganizationalWorkItem.id == work.id,
        OrganizationalWorkItem.tenant_key == context.tenant_key, OrganizationalWorkItem.status == "running",
        OrganizationalWorkItem.execution_token == attempt.execution_token,
        OrganizationalWorkItem.execution_attempts == attempt.attempt_number,
        OrganizationalWorkItem.cancel_requested_at.is_(None), OrganizationalWorkItem.cancelled_at.is_(None))
        .values(updated_at=OrganizationalWorkItem.updated_at).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        raise InvalidTransition("canonical attempt changed before observation lock")
    # A real conditional write serializes SQLite writers too; FOR UPDATE alone does not.
    return _attempt(session, context, work_id, attempt_id)


def _logs(session, challenge_id, action):
    return session.exec(select(AuditLog).where(AuditLog.entity_type == "rea_worker_challenge", AuditLog.entity_id == str(challenge_id),
        AuditLog.action == action, AuditLog.source == SOURCE).execution_options(populate_existing=True)).all()


def issue_rea_worker_challenge(session, context, *, decision_id, attempt_id, receipt_id, trust: ReaDeploymentTrust):
    """Internal trusted worker operation; no transport connection is made."""
    try:
        row, _, _, _ = resolve_rea_provider_review(session, context, decision_id=decision_id, trust=trust)
        _barrier(session, context, row.work_item_id, attempt_id)
        row, contract, scope, authorized = resolve_rea_provider_review(session, context, decision_id=decision_id, trust=trust)
        artifact.revalidate_rea_artifact_custody(session, context, receipt_id=receipt_id, decision_id=authorized.decision_id, custody_root=trust.custody_root)
        work, attempt = _attempt(session, context, row.work_item_id, attempt_id)
        now = artifact._utc(now_utc())
        challenge = {"kind": "rea_worker_challenge_v1", "challenge_id": str(uuid4()), "nonce": secrets.token_hex(32),
            "session_id": str(uuid4()), "tenant_key": context.tenant_key, "decision_id": str(row.id),
            "contract_sha256": canonical_fingerprint(contract), "scope": scope.model_dump(mode="json"), "work_link": contract["link"],
            "work_item_id": str(work.id), "attempt_id": str(attempt.id), "attempt_number": attempt.attempt_number,
            "execution_token_sha256": hashlib.sha256(attempt.execution_token.encode()).hexdigest(),
            "artifact_decision_id": str(authorized.decision_id), "artifact_contract_sha256": authorized.contract_sha256,
            "artifact_sha256": authorized.artifact_sha256, "custody_receipt_id": str(receipt_id),
            "catalog_sha256": REA_LOCAL_CATALOG_SHA256, "issued_at": now.isoformat(),
            "expires_at": min(now+timedelta(minutes=5), scope.expires_at, authorized.expires_at).isoformat(),
            "transport_owned": False, "execution_authorized": False}
        record_audit(session, action=CHALLENGE, entity_type="rea_worker_challenge", entity_id=challenge["challenge_id"],
            after_state=challenge, actor=context.actor_id, source=SOURCE)
        session.commit()
        return challenge
    except OperationalError as exc:
        session.rollback()
        if getattr(exc.orig,"sqlstate",None) not in {"40001","40P01","55P03"} and (getattr(exc.orig,"sqlite_errorcode",0) & 0xff) not in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
            raise
        raise InvalidTransition("worker challenge database serialization failed") from exc
    except Exception:
        session.rollback()
        raise


def parse_rea_worker_observation(raw: bytes) -> ReaWorkerObservation:
    """Transport-independent bounded raw decoder; no decoded JSON ambiguity."""
    try:
        if type(raw) is not bytes or len(raw) > artifact.MAX_AUDIT_BYTES:
            raise InvalidTransition("worker statement exceeds byte bounds")
        return ReaWorkerObservation.model_validate(artifact._json(raw.decode("utf-8")))
    except (UnicodeError, ValidationError, TypeError) as exc:
        raise InvalidTransition("invalid bounded worker statement JSON") from exc


def consume_rea_worker_observation(session, context, *, challenge_id: UUID, observation: ReaWorkerObservation, tools_observation: bytes, trust: ReaDeploymentTrust):
    """Authenticate one reviewed-key statement; never enable or establish live transport."""
    try:
        if type(challenge_id) is not UUID or type(tools_observation) is not bytes or len(tools_observation) > MAX_JSON_BYTES:
            raise InvalidTransition("invalid bounded worker observation")
        observation = ReaWorkerObservation.model_validate(artifact._json(canonical_json(observation.model_dump()), limit=artifact.MAX_AUDIT_BYTES))
        logs = _logs(session, challenge_id, CHALLENGE)
        if len(logs) != 1:
            raise InvalidTransition("worker challenge unavailable or ambiguous")
        original = artifact._json(logs[0].after_state_json)
        expected_keys = {"kind", "challenge_id", "nonce", "session_id", "tenant_key", "decision_id", "contract_sha256", "scope", "work_link", "work_item_id", "attempt_id", "attempt_number", "execution_token_sha256", "artifact_decision_id", "artifact_contract_sha256", "artifact_sha256", "custody_receipt_id", "catalog_sha256", "issued_at", "expires_at", "transport_owned", "execution_authorized"}
        if type(original) is not dict or set(original) != expected_keys or original.get("kind") != "rea_worker_challenge_v1" or type(original.get("attempt_number")) is not int or canonical_json(original) != canonical_json(observation.challenge) or original.get("challenge_id") != str(challenge_id) or original.get("tenant_key") != context.tenant_key:
            raise InvalidTransition("worker challenge binding differs")
        try:
            decision_id, work_id, attempt_id = (UUID(original[k]) for k in ("decision_id", "work_item_id", "attempt_id"))
        except (ValueError, TypeError, KeyError) as exc:
            raise InvalidTransition("worker challenge identity invalid") from exc
        resolve_rea_provider_review(session, context, decision_id=decision_id, trust=trust)
        _barrier(session, context, work_id, attempt_id)
        if len(_logs(session, challenge_id, CHALLENGE)) != 1 or _logs(session, challenge_id, CONSUME):
            raise InvalidTransition("worker challenge consumed or ambiguous")
        if artifact._json(_logs(session, challenge_id, CHALLENGE)[0].after_state_json) != original:
            raise InvalidTransition("worker challenge changed during validation")
        row, contract, scope, authorized = resolve_rea_provider_review(session, context, decision_id=decision_id, trust=trust)
        work, attempt = _attempt(session, context, work_id, attempt_id)
        current = {"decision_id": str(row.id), "contract_sha256": canonical_fingerprint(contract), "scope": scope.model_dump(mode="json"),
            "work_link": contract["link"], "work_item_id": str(row.work_item_id), "attempt_id": str(attempt.id),
            "attempt_number": attempt.attempt_number, "execution_token_sha256": hashlib.sha256(attempt.execution_token.encode()).hexdigest(),
            "artifact_decision_id": str(authorized.decision_id), "artifact_contract_sha256": authorized.contract_sha256,
            "artifact_sha256": authorized.artifact_sha256, "catalog_sha256": REA_LOCAL_CATALOG_SHA256,
            "transport_owned": False, "execution_authorized": False}
        if any(canonical_json(original.get(k)) != canonical_json(v) for k,v in current.items()):
            raise InvalidTransition("worker challenge canonical state changed")
        now = artifact._utc(now_utc())
        try:
            issued, expires = (datetime.fromisoformat(original[k]) for k in ("issued_at", "expires_at"))
            if issued.tzinfo is None or expires.tzinfo is None or not artifact._utc(attempt.started_at) <= issued <= artifact._utc(logs[0].created_at) or not issued <= now < expires <= min(issued+timedelta(minutes=5), scope.expires_at, authorized.expires_at):
                raise ValueError("challenge expiry")
            for key in ("challenge_id", "session_id", "decision_id", "work_item_id", "attempt_id", "artifact_decision_id", "custody_receipt_id"):
                if type(original[key]) is not str or str(UUID(original[key])) != original[key]:
                    raise ValueError("noncanonical challenge UUID")
            receipt_id = UUID(original["custody_receipt_id"])
            if type(original["nonce"]) is not str or re.fullmatch(r"[0-9a-f]{64}", original["nonce"]) is None:
                raise ValueError("nonce")
        except (ValueError, TypeError, KeyError) as exc:
            raise InvalidTransition("worker challenge expiry/nonce/session invalid") from exc
        artifact.revalidate_rea_artifact_custody(session, context, receipt_id=receipt_id, decision_id=authorized.decision_id, custody_root=trust.custody_root)
        digest = hashlib.sha256(tools_observation).hexdigest()
        if digest != observation.tools_observation_sha256 or not compare_rea_tools_observation(tools_observation).advertised_contract_matches:
            raise InvalidTransition("worker observed catalog differs")
        reported = {k: getattr(scope,k) for k in ("worker_id", "build_sha256", "package_name", "package_version", "server_name", "server_version", "protocol_version", "platform", "isolation_policy_sha256")}
        reported.update(session_id=original["session_id"], provider_matrix_sha256=canonical_fingerprint(scope.model_dump(mode="json")["tools"]))
        if observation.reported.model_dump(mode="json") != reported:
            raise InvalidTransition("signed worker reported identity differs from review/challenge")
        signed = {"challenge": original, "reported": reported, "tools_observation_sha256": digest}
        try:
            Ed25519PublicKey.from_public_bytes(trust.worker_public_key).verify(bytes.fromhex(observation.signature_hex), canonical_json(signed).encode())
        except (ValueError, InvalidSignature) as exc:
            raise AuthorityDenied("worker signature does not match independent reviewed key") from exc
        _attempt(session, context, work_id, attempt_id)
        result = {"challenge_id": str(challenge_id), "session_id": original["session_id"], "tenant_key": context.tenant_key,
            "work_item_id": str(work.id), "attempt_id": str(attempt.id), "decision_id": str(row.id),
            "statement_sha256": canonical_fingerprint(signed), "tools_observation_sha256": digest,
            "reviewed_build_bytes_verified": True, "worker_signature_verified": True, "live_transport_owned": False,
            "isolation_verified": False, "provider_ready": False, "execution_authorized": False,
            "blockers": ["publisher_source_build_provenance_unproven", "installed_runtime_byte_binding_unproven", "owned_live_transport_unproven", "actual_worker_isolation_unproven", "provider_behavior_effects_unproven", "per_call_entitlement_and_resources_unadmitted"]}
        # Custody/catalog/signature verification can outlive the earlier check.
        # Recheck at witness creation and immediately before its durable commit.
        def require_fresh_expiry():
            final_now = artifact._utc(now_utc())
            if not issued <= final_now < min(expires, scope.expires_at, authorized.expires_at):
                raise InvalidTransition("worker observation expired before consumption")
        require_fresh_expiry()
        record_audit(session, action=CONSUME, entity_type="rea_worker_challenge", entity_id=challenge_id,
            after_state=result, actor=context.actor_id, source=SOURCE)
        require_fresh_expiry()
        session.commit()
        return result
    except OperationalError as exc:
        session.rollback()
        if getattr(exc.orig,"sqlstate",None) not in {"40001","40P01","55P03"} and (getattr(exc.orig,"sqlite_errorcode",0) & 0xff) not in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
            raise
        raise InvalidTransition("worker observation database serialization failed") from exc
    except (ValidationError, ReaCatalogInvalid) as exc:
        session.rollback()
        raise InvalidTransition("invalid bounded worker observation") from exc
    except Exception:
        session.rollback()
        raise
