"""Bounded, transactional maintenance for automation connector key rotation."""

from __future__ import annotations

import argparse
import hmac
import json

from cryptography.fernet import InvalidToken
from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.core.database_url import configured_database_url
from app.models.domain import AutomationConnectorConfig
from app.services.audit_log import record_audit
from app.services.automation_connector_encryption import (
    CredentialEncryptionError,
    _current_master_key,
    _decode_payload,
    _fernet,
    _previous_master_key,
)


def rotate_connector_rows(
    session: Session,
    *,
    active_key: str,
    previous_key: str = "",
    mode: str,
    lock_table: bool = True,
) -> dict[str, int]:
    """Inspect or migrate all rows in one transaction; never print credential data.

    The production caller uses a PostgreSQL table lock, so no connector write can
    enter between the scan and commit. The caller must stop API/worker activity
    and take a verified backup before applying a rotation.
    """
    if mode not in {"check", "apply", "verify"}:
        raise ValueError("Invalid connector rotation mode")
    if not active_key or (mode != "verify" and not previous_key):
        raise CredentialEncryptionError("The required connector rotation key is missing")
    if previous_key and hmac.compare_digest(active_key, previous_key):
        raise CredentialEncryptionError("Active and previous connector keys must differ")

    active = _fernet(active_key)
    previous = _fernet(previous_key) if mode != "verify" else None
    try:
        if lock_table:
            session.exec(text("LOCK TABLE automation_connector_configs IN ACCESS EXCLUSIVE MODE"))
        rows = list(session.exec(select(AutomationConnectorConfig).order_by(AutomationConnectorConfig.id)))
        counts = {"total": len(rows), "already_active": 0, "previous": 0}
        changes: list[tuple[AutomationConnectorConfig, bytes]] = []
        for row in rows:
            token = row.credentials_json.encode("utf-8")
            try:
                plaintext = active.decrypt(token)
                _decode_payload(plaintext.decode("utf-8"))
                counts["already_active"] += 1
                continue
            except (InvalidToken, UnicodeDecodeError):
                pass
            if previous is None:
                raise CredentialEncryptionError("A connector credential is not readable with the active key")
            try:
                plaintext = previous.decrypt(token)
                _decode_payload(plaintext.decode("utf-8"))
            except (InvalidToken, UnicodeDecodeError) as exc:
                raise CredentialEncryptionError("A connector credential is unreadable with both rotation keys") from exc
            counts["previous"] += 1
            changes.append((row, plaintext))

        if mode == "apply":
            for row, plaintext in changes:
                row.credentials_json = active.encrypt(plaintext).decode("utf-8")
                session.add(row)
                record_audit(
                    session,
                    action="automation_connector_credentials_reencrypted",
                    entity_type="automation_connector_config",
                    entity_id=row.id,
                    reason="active encryption key rotation",
                    actor="operator:connector-key-rotation",
                    source="connector_key_rotation_v1",
                )
            session.flush()
            for row in rows:
                plaintext = active.decrypt(row.credentials_json.encode("utf-8"))
                _decode_payload(plaintext.decode("utf-8"))
            session.commit()
        else:
            session.rollback()
        return counts
    except Exception:
        session.rollback()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect, migrate or verify stored connector credentials")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="Read-only count under both keys")
    modes.add_argument("--apply", action="store_true", help="Atomically re-encrypt prior-key rows")
    modes.add_argument("--verify", action="store_true", help="Require all rows readable with active key alone")
    args = parser.parse_args()
    mode = "apply" if args.apply else "verify" if args.verify else "check"
    engine = None
    try:
        if not settings.is_production():
            raise RuntimeError("Connector rotation requires APP_ENV=production")
        if not settings.automation_encryption_key_ref or (
            mode != "verify" and not settings.automation_encryption_previous_key_ref
        ):
            raise RuntimeError("Connector rotation requires file-backed active and applicable previous keys")
        active_key = _current_master_key()
        previous_key = _previous_master_key() if mode != "verify" else ""
        engine = create_engine(configured_database_url(), pool_pre_ping=True)
        if engine.dialect.name != "postgresql":
            raise RuntimeError("Connector rotation requires production PostgreSQL")
        with Session(engine) as session:
            counts = rotate_connector_rows(
                session, active_key=active_key, previous_key=previous_key, mode=mode
            )
        print(json.dumps({"mode": mode, **counts}, sort_keys=True))
        return 0
    except Exception:
        # Database and crypto exceptions may include connection strings or payloads.
        print("Connector rotation failed; no credentials were printed. Inspect restricted operator logs.")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
