"""Board-reviewed artifact scope and internal custody, without executable authority.

Trusted command contexts and AuditLog storage are canonical boundaries. Hashes/modes
are integrity controls, not signatures, target rights verification, or a sandbox.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import stat
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlmodel import Session, select

from app.models.domain import AuditLog, ExecutiveDecision, OrganizationPosition, OrganizationalWorkItem, now_utc
from app.schemas_organization_rea_artifacts import ReaArtifactProposal, ReaArtifactScope, ReaArtifactAuthorizationRead
from app.services.organization_command import (
    AuthorityDenied, InvalidTransition, OrganizationCommandContext, canonical_fingerprint,
    canonical_json, require_human, snapshot, tenant_record,
)
from app.services.organization_decision import create_executive_decision
from app.services.audit_log import record_audit
from app.services.organization_rea_catalog import REA_LOCAL_CATALOG_SHA256, REA_SOURCE_COMMIT

SOURCE = "organization_rea_artifact_v1"
KIND = "rea_artifact_authorization_v1"
MAX_CONTRACT_BYTES = 128_000
MAX_AUDIT_BYTES = 512_000


def _utc(value: datetime) -> datetime:
    # SQLite drops timezone information on canonical persisted UTC datetimes.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _json(raw: str, *, limit: int = MAX_AUDIT_BYTES):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    def bad(_):
        raise ValueError("nonfinite constant")
    try:
        if not isinstance(raw, str) or len(raw.encode()) > limit:
            raise ValueError("JSON size")
        result = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
        stack = [(result, 0)]
        count = 0
        while stack:
            value, depth = stack.pop()
            count += 1
            if count > 10_000 or depth > 32 or isinstance(value, float) and not math.isfinite(value):
                raise ValueError("JSON structure/number bounds")
            if isinstance(value, dict):
                stack.extend((child, depth + 1) for child in value.values())
            elif isinstance(value, list):
                stack.extend((child, depth + 1) for child in value)
        return result
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InvalidTransition("invalid bounded artifact contract/audit") from exc


def _board(context):
    require_human(context, admin=True)
    if context.position_key not in {"board", "owner"}:
        raise AuthorityDenied("Board/owner is required for artifact review")


def _work_link(session, tenant, work_id):
    work = session.exec(select(OrganizationalWorkItem).where(
        OrganizationalWorkItem.id == work_id, OrganizationalWorkItem.tenant_key == tenant
    ).execution_options(populate_existing=True).with_for_update()).first()
    if work is None:
        tenant_record(session, OrganizationalWorkItem, work_id, tenant, label="work item")
    if work.status not in {"queued", "assigned", "in_progress", "running", "awaiting_human", "blocked"} or work.cancel_requested_at or work.cancelled_at:
        raise InvalidTransition("artifact work is not current")
    position = session.exec(select(OrganizationPosition).where(
        OrganizationPosition.position_key == work.assigned_position_key, OrganizationPosition.status == "active"
    ).execution_options(populate_existing=True).with_for_update()).first()
    if position is None or position.suspended_at is not None:
        raise InvalidTransition("artifact position is unavailable or suspended")
    # Assignment history distinguishes reassign-away-and-back from the reviewed assignment.
    assignments = session.exec(select(AuditLog).where(
        AuditLog.entity_type == "organizational_work_item", AuditLog.entity_id == str(work.id),
        AuditLog.action == "organization.work.assign"
    ).order_by(AuditLog.created_at, AuditLog.id)).all()
    fields = ("id", "tenant_key", "idempotency_fingerprint", "work_type", "objective_key", "phase_key", "parent_work_item_id",
              "lead_id", "profile_id", "application_id", "corporate_account_id", "corporate_mobility_case_id",
              "source_object_type", "source_object_id", "source_object_version", "title", "objective", "department",
              "authority_level", "risk_level", "context_json", "assigned_position_key")
    data = snapshot(work)
    link = {"work_scope_sha256": canonical_fingerprint({key: data[key] for key in fields}),
            "assignment_sha256": canonical_fingerprint([str(item.id) for item in assignments]),
            "position_id": str(position.id), "position_version": position.version,
            "position_contract_sha256": hashlib.sha256(position.contract_json.encode()).hexdigest()}
    return work, link


def _audits(session, decision, action, source="organization_command_v13.16.1b"):
    return session.exec(select(AuditLog).where(AuditLog.entity_type == "executive_decision",
        AuditLog.entity_id == str(decision.id), AuditLog.action == action, AuditLog.source == source)).all()


def _invariant(row):
    data = snapshot(row)
    # Only outcome-owned and coordination/reminder fields may change after proposal.
    mutable = {"status", "decided_by", "decision_reason", "effect_summary", "decided_at", "updated_at",
               "coordination_token", "coordination_claimed_at", "reminded_at"}
    result = {key: value for key, value in data.items() if key not in mutable}
    for key in ("created_at", "expires_at", "due_at"):
        if result.get(key):
            result[key] = _utc(datetime.fromisoformat(result[key])).isoformat()
    return result


def _contract(row):
    values = _json(row.conditions_json, limit=MAX_CONTRACT_BYTES)
    expected = {"kind", "operation", "scope", "link", "catalog_sha256", "source_commit"}
    if type(values) is not list or len(values) != 1 or type(values[0]) is not dict or set(values[0]) != expected:
        raise InvalidTransition("decision lacks one typed artifact contract")
    contract = values[0]
    if contract["kind"] != KIND or type(contract["operation"]) is not str or contract["operation"] not in {"authorize", "revoke"} or contract["catalog_sha256"] != REA_LOCAL_CATALOG_SHA256 or contract["source_commit"] != REA_SOURCE_COMMIT:
        raise InvalidTransition("artifact contract identity differs")
    try:
        scope = ReaArtifactScope.model_validate(contract["scope"])
    except (ValidationError, TypeError) as exc:
        raise InvalidTransition("invalid artifact scope") from exc
    if type(contract["link"]) is not dict:
        raise InvalidTransition("invalid artifact work linkage shape")
    if contract["scope"] != scope.model_dump(mode="json"):
        raise InvalidTransition("artifact contract is not canonical")
    if row.source_object_type != KIND or row.source_object_id != scope.artifact_sha256 or row.source_object_version != canonical_fingerprint(contract):
        raise InvalidTransition("artifact contract source digest differs")
    return contract, scope


def _witness(session, row, *, approved):
    contract, scope = _contract(row)
    if row.authority_level != "L4" or row.decision_type != "board_reserved" or row.decision_owner_position != "board" or row.work_item_id is None:
        raise InvalidTransition("artifact decision owner/linkage differs")
    creation = _audits(session, row, "organization.decision.create")
    proposal = _audits(session, row, "organization.rea.artifact.propose", SOURCE)
    if len(creation) != 1 or len(proposal) != 1:
        raise InvalidTransition("artifact decision lacks canonical proposal audit")
    created = _json(creation[0].after_state_json)
    if type(created) is not dict:
        raise InvalidTransition("artifact creation audit must be an object")
    for key in ("created_at", "expires_at", "due_at"):
        if created.get(key):
            try:
                created[key] = _utc(datetime.fromisoformat(created[key])).isoformat()
            except (TypeError, ValueError) as exc:
                raise InvalidTransition("invalid artifact creation audit datetime") from exc
    if proposal[0].actor != creation[0].actor or _utc(proposal[0].created_at) < _utc(creation[0].created_at):
        raise InvalidTransition("artifact proposal actor/order differs")
    if canonical_fingerprint(_invariant(row)) != canonical_fingerprint({key: created.get(key) for key in _invariant(row)}):
        raise InvalidTransition("artifact decision changed after proposal")
    witnessed = _json(proposal[0].after_state_json)
    if witnessed != {"contract_sha256": canonical_fingerprint(contract), "record_fingerprint": row.record_fingerprint,
                     "tenant_key": row.tenant_key, "work_item_id": str(row.work_item_id), "human_proposal": True}:
        raise InvalidTransition("artifact proposal witness differs")
    if approved:
        approvals = _audits(session, row, "organization.decision.approved")
        if row.status != "approved" or row.decided_at is None or len(approvals) != 1:
            raise InvalidTransition("artifact decision is not canonically approved")
        before, after = _json(approvals[0].before_state_json), _json(approvals[0].after_state_json)
        if type(before) is not dict or type(after) is not dict:
            raise InvalidTransition("artifact approval audit must contain objects")
        if _utc(proposal[0].created_at) > _utc(approvals[0].created_at):
            raise InvalidTransition("artifact proposal witness must precede approval")
        if before.get("status") != "pending_board" or after.get("status") != "approved" or approvals[0].actor != row.decided_by:
            raise InvalidTransition("artifact approval lineage differs")
        current = snapshot(row)
        # Datetime serialization round-trips SQLite UTC with and without timezone.
        for key in current:
            if key in {"updated_at", "decided_at", "created_at", "expires_at"}:
                if after.get(key) is None or current[key] is None:
                    if after.get(key) != current[key]:
                        raise InvalidTransition("artifact approval snapshot differs")
                else:
                    try:
                        matches = _utc(datetime.fromisoformat(after[key])) == _utc(datetime.fromisoformat(current[key]))
                    except (TypeError, ValueError) as exc:
                        raise InvalidTransition("invalid artifact approval audit datetime") from exc
                    if not matches:
                        raise InvalidTransition("artifact approval snapshot differs")
            elif key not in {"reminded_at", "coordination_token", "coordination_claimed_at"} and after.get(key) != current[key]:
                raise InvalidTransition("artifact approval snapshot differs")
        if _utc(row.decided_at) >= scope.expires_at:
            raise InvalidTransition("artifact approval occurred after expiry")
    return contract, scope


def propose_rea_artifact(session: Session, context: OrganizationCommandContext, payload: ReaArtifactProposal) -> ExecutiveDecision:
    _board(context)
    payload = ReaArtifactProposal.model_validate(payload.model_dump())
    now = _utc(now_utc())
    if not now < payload.scope.expires_at <= now + timedelta(days=30):
        raise InvalidTransition("artifact expiry must be future and within 30 days")
    work, link = _work_link(session, context.tenant_key, payload.work_item_id)
    contract = {"kind": KIND, "operation": "authorize", "scope": payload.scope.model_dump(mode="json"),
                "link": link, "catalog_sha256": REA_LOCAL_CATALOG_SHA256, "source_commit": REA_SOURCE_COMMIT}
    if payload.supersedes_decision_id:
        predecessor = _decision(session, context.tenant_key, payload.supersedes_decision_id)
        _witness(session, predecessor, approved=True)
        if predecessor.work_item_id != work.id:
            raise InvalidTransition("replacement must retain artifact WorkItem")
    return _propose(session, context, payload.decision_key, work.id, contract, payload.supersedes_decision_id)


def _propose(session, context, key, work_id, contract, predecessor, reason=None):
    row = create_executive_decision(session, context, decision_key=key, decision_type="board_reserved", authority_level="L4",
        requested_by_position=context.position_key, decision_owner_position="board", title="REA artifact review",
        question="Review authorized artifact purpose, exact tool scope and custody prerequisites",
        evidence=[{"rea_revocation_reason": reason}] if reason else [],
        recommendation="Review artifact scope; this decision does not enable REA execution", conditions=[contract],
        work_item_id=work_id, source_object_type=KIND, source_object_id=contract["scope"]["artifact_sha256"],
        source_object_version=canonical_fingerprint(contract), supersedes_decision_id=predecessor,
        expires_at=datetime.fromisoformat(contract["scope"]["expires_at"]))
    row = _decision(session, context.tenant_key, row.id)
    existing = _audits(session, row, "organization.rea.artifact.propose", SOURCE)
    witness = {"contract_sha256": canonical_fingerprint(contract), "record_fingerprint": row.record_fingerprint,
               "tenant_key": context.tenant_key, "work_item_id": str(work_id), "human_proposal": True}
    if existing:
        if len(existing) != 1 or _json(existing[0].after_state_json) != witness:
            raise InvalidTransition("artifact proposal witness conflict")
        return row
    if row.status != "pending_board" or _audits(session, row, "organization.decision.approved"):
        raise InvalidTransition("cannot attach artifact proposal witness after settlement")
    creation = _audits(session, row, "organization.decision.create")
    if len(creation) != 1 or creation[0].actor != context.actor_id:
        raise AuthorityDenied("only the matching authenticated creator may complete pending proposal")
    try:
        record_audit(session, action="organization.rea.artifact.propose", entity_type="executive_decision", entity_id=row.id,
            after_state=witness, actor=context.actor_id, source=SOURCE)
        session.commit()
    except Exception:
        session.rollback()
        # Generic decision creation owns its transaction; this incomplete pending
        # proposal is deliberately unusable without the committed typed witness.
        raise
    return row


def _decision(session, tenant, decision_id):
    row = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.id == decision_id,
        ExecutiveDecision.tenant_key == tenant).execution_options(populate_existing=True).with_for_update()).first()
    if row is None:
        tenant_record(session, ExecutiveDecision, decision_id, tenant, label="artifact decision")
    return row


def propose_rea_artifact_revocation(session, context, *, decision_id, decision_key, reason):
    _board(context)
    from app.schemas_organization_rea_artifacts import ReaArtifactRevocation
    request = ReaArtifactRevocation(decision_key=decision_key, reason=reason)
    row = _decision(session, context.tenant_key, decision_id)
    contract, _ = _witness(session, row, approved=True)
    if contract["operation"] != "authorize":
        raise InvalidTransition("only artifact authorization may be revoked")
    # A revocation never becomes an authorization and remains invalidating after its expiry.
    contract = dict(contract, operation="revoke")
    return _propose(session, context, request.decision_key, row.work_item_id, contract, row.id, request.reason)


def resolve_rea_artifact_authorization(session, context, *, decision_id) -> ReaArtifactAuthorizationRead:
    row = _decision(session, context.tenant_key, decision_id)
    contract, scope = _witness(session, row, approved=True)
    if contract["operation"] != "authorize" or _utc(now_utc()) >= scope.expires_at or row.expires_at is None or _utc(row.expires_at) != scope.expires_at:
        raise InvalidTransition("artifact authorization revoked or expired")
    _, link = _work_link(session, context.tenant_key, row.work_item_id)
    if contract["link"] != link:
        raise InvalidTransition("artifact work scope or assignment changed")
    successors = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.supersedes_decision_id == row.id)
        .execution_options(populate_existing=True)).all()
    if successors:
        # Proposed/failed/unknown edges also block this predecessor: they are a
        # lineage conflict, not a claimed human revocation. Expiration never revives it.
        raise InvalidTransition("artifact decision has superseding/revoking lineage")
    return ReaArtifactAuthorizationRead(decision_id=row.id, work_item_id=row.work_item_id,
        contract_sha256=canonical_fingerprint(contract), artifact_sha256=scope.artifact_sha256,
        artifact_bytes=scope.artifact_bytes, exact_tools=scope.exact_tools, expires_at=scope.expires_at)


def _directory(path: Path) -> int:
    """Open every absolute component without following symlinks, including roots."""
    if not isinstance(path, Path) or not path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        raise InvalidTransition("custody roots must be explicit absolute paths")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except Exception:
        os.close(fd)
        raise


def _source_file(root: Path, relative: str) -> int:
    if type(relative) is not str or not relative or relative.startswith("/") or "\x00" in relative or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise InvalidTransition("invalid relative custody source")
    fd = _directory(root)
    try:
        parts = relative.split("/")
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        # NONBLOCK avoids blocking on FIFO/device files before the regular-file check.
        result = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        if not stat.S_ISREG(os.fstat(result).st_mode):
            os.close(result)
            raise InvalidTransition("custody source must be a regular file")
        return result
    finally:
        os.close(fd)


def _bytes(fd: int, expected_size: int, output_fd: int | None = None) -> str:
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode) or before.st_size != expected_size:
        raise InvalidTransition("artifact size/type differs from review")
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = os.read(fd, min(1024 * 1024, expected_size + 1 - size))
        if not chunk:
            break
        size += len(chunk)
        if size > expected_size:
            raise InvalidTransition("artifact exceeded reviewed size")
        digest.update(chunk)
        if output_fd is not None:
            pending = memoryview(chunk)
            while pending:
                written = os.write(output_fd, pending)
                if written <= 0:
                    raise InvalidTransition("staged artifact write failed")
                pending = pending[written:]
    after = os.fstat(fd)
    if size != expected_size or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise InvalidTransition("artifact changed during custody read")
    return digest.hexdigest()


def stage_rea_artifact_custody(session, context, *, decision_id, source_root: Path, source_relative: str, custody_root: Path) -> UUID:
    """Internal worker entry point. Roots are trusted deployment inputs, never HTTP input.

    Successful files outlive this transaction and require explicit lifecycle cleanup.
    Errors remove the investigation directory; cleanup errors propagate rather than
    claiming rollback removed a file. This function does not dispatch a REA tool.
    """
    authorization = resolve_rea_artifact_authorization(session, context, decision_id=decision_id)
    receipt = uuid4()
    root_fd = directory_fd = source_fd = output_fd = None
    created = False
    try:
        root_fd = _directory(custody_root)
        root_stat = os.fstat(root_fd)
        if stat.S_IMODE(root_stat.st_mode) != 0o700:
            raise InvalidTransition("custody root must have restrictive 0700 mode")
        source_fd = _source_file(source_root, source_relative)
        os.mkdir(str(receipt), mode=0o700, dir_fd=root_fd)
        created = True
        directory_fd = os.open(str(receipt), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
        os.fchmod(directory_fd, 0o700)
        output_fd = os.open("artifact", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd)
        digest = _bytes(source_fd, authorization.artifact_bytes, output_fd)
        if digest != authorization.artifact_sha256:
            raise InvalidTransition("artifact hash differs from review")
        os.fchmod(output_fd, 0o400)
        os.fsync(output_fd)
        os.close(output_fd)
        output_fd = None
        os.fsync(directory_fd)
        os.fsync(root_fd)
        # Verify the named copy, directory and trusted root still refer to what was
        # opened; fd-relative writes alone would not detect a concurrent rename.
        check_root = _directory(custody_root)
        try:
            actual_root = os.fstat(check_root)
            named_dir = os.stat(str(receipt), dir_fd=check_root, follow_symlinks=False)
            opened_dir = os.fstat(directory_fd)
            if (actual_root.st_dev, actual_root.st_ino) != (root_stat.st_dev, root_stat.st_ino) or (named_dir.st_dev, named_dir.st_ino) != (opened_dir.st_dev, opened_dir.st_ino):
                raise InvalidTransition("custody root/directory changed during staging")
            check_file = os.open("artifact", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
            try:
                if stat.S_IMODE(os.fstat(check_file).st_mode) != 0o400 or _bytes(check_file, authorization.artifact_bytes) != digest:
                    raise InvalidTransition("staged copy changed before custody audit")
            finally:
                os.close(check_file)
        finally:
            os.close(check_root)
        # Re-read the complete canonical boundary before persisting custody witness.
        current = resolve_rea_artifact_authorization(session, context, decision_id=decision_id)
        if current != authorization:
            raise InvalidTransition("artifact authorization changed during custody")
        witness = {"tenant_key": context.tenant_key, "decision_id": str(decision_id), "work_item_id": str(current.work_item_id),
            "contract_sha256": current.contract_sha256, "artifact_sha256": digest, "artifact_bytes": current.artifact_bytes,
            "receipt_id": str(receipt), "root_device": root_stat.st_dev, "root_inode": root_stat.st_ino,
            "execution_authorized": False}
        record_audit(session, action="organization.rea.artifact.custody", entity_type="rea_artifact_custody", entity_id=receipt,
            after_state=witness, actor=context.actor_id, source=SOURCE)
        session.commit()
        return receipt
    except Exception:
        session.rollback()
        if output_fd is not None:
            os.close(output_fd)
            output_fd = None
        if created:
            if directory_fd is not None:
                try:
                    os.unlink("artifact", dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
            os.rmdir(str(receipt), dir_fd=root_fd)
        raise
    finally:
        for fd in (output_fd, source_fd, directory_fd, root_fd):
            if fd is not None:
                os.close(fd)


def revalidate_rea_artifact_custody(session, context, *, receipt_id: UUID, decision_id: UUID, custody_root: Path) -> ReaArtifactAuthorizationRead:
    """Receipt IDs select committed witnesses, not caller-created path/authority handles."""
    if type(receipt_id) is not UUID:
        raise InvalidTransition("custody receipt must be an ID")
    current = resolve_rea_artifact_authorization(session, context, decision_id=decision_id)
    rows = session.exec(select(AuditLog).where(AuditLog.entity_type == "rea_artifact_custody", AuditLog.entity_id == str(receipt_id),
        AuditLog.action == "organization.rea.artifact.custody", AuditLog.source == SOURCE)).all()
    if len(rows) != 1:
        raise InvalidTransition("custody witness unavailable or ambiguous")
    witness = _json(rows[0].after_state_json)
    root_fd = fd = None
    try:
        root_fd = _directory(custody_root)
        root_stat = os.fstat(root_fd)
        expected = {"tenant_key": context.tenant_key, "decision_id": str(decision_id), "work_item_id": str(current.work_item_id),
            "contract_sha256": current.contract_sha256, "artifact_sha256": current.artifact_sha256, "artifact_bytes": current.artifact_bytes,
            "receipt_id": str(receipt_id), "root_device": root_stat.st_dev, "root_inode": root_stat.st_ino,
            "execution_authorized": False}
        if witness != expected or stat.S_IMODE(root_stat.st_mode) != 0o700:
            raise InvalidTransition("custody witness does not match canonical authorization/root")
        directory_fd = os.open(str(receipt_id), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
        try:
            if stat.S_IMODE(os.fstat(directory_fd).st_mode) != 0o700:
                raise InvalidTransition("custody directory mode changed")
            fd = os.open("artifact", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        finally:
            os.close(directory_fd)
        if stat.S_IMODE(os.fstat(fd).st_mode) != 0o400 or _bytes(fd, current.artifact_bytes) != current.artifact_sha256:
            raise InvalidTransition("staged artifact differs from custody witness")
        return current
    except OSError as exc:
        raise InvalidTransition("custody path is unavailable or unsafe") from exc
    finally:
        for handle in (fd, root_fd):
            if handle is not None:
                os.close(handle)
