from __future__ import annotations

from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import AuditLog, AutomationConnectorConfig
from app.services.automation_connector_encryption import (
    CredentialEncryptionError,
    decrypt_credentials_with_current_key,
)
from app.services import connector_key_rotation
from app.services.connector_key_rotation import rotate_connector_rows


pytestmark = pytest.mark.usefixtures("automation_encryption_key")
OLD = "old-connector-secret-for-rotation"
NEW = "new-connector-secret-for-rotation"


def _account(client) -> str:
    account = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Rotation Test", "primary_country": "Austria"},
    )
    assert account.status_code == 201, account.text
    return account.json()["id"]


def _connector(client, monkeypatch, key: str, channel: str, account_id: str) -> UUID:
    monkeypatch.setattr(settings, "automation_encryption_key", key)
    response = client.post(
        "/api/v1/automation/connectors",
        json={
            "corporate_account_id": account_id,
            "channel": channel,
            "provider_type": "console",
            "credentials": {"secret": f"{channel}-credential"},
        },
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


def test_rotation_is_read_only_until_apply_then_active_only(client, db_session: Session, monkeypatch):
    account_id = _account(client)
    old_id = _connector(client, monkeypatch, OLD, "email", account_id)
    new_id = _connector(client, monkeypatch, NEW, "crm", account_id)
    old_token = db_session.get(AutomationConnectorConfig, old_id).credentials_json

    counts = rotate_connector_rows(
        db_session, active_key=NEW, previous_key=OLD, mode="check", lock_table=False
    )
    assert counts == {"total": 2, "already_active": 1, "previous": 1}
    assert db_session.get(AutomationConnectorConfig, old_id).credentials_json == old_token
    with pytest.raises(CredentialEncryptionError, match="active key"):
        rotate_connector_rows(db_session, active_key=NEW, mode="verify", lock_table=False)

    assert rotate_connector_rows(
        db_session, active_key=NEW, previous_key=OLD, mode="apply", lock_table=False
    ) == counts
    assert rotate_connector_rows(
        db_session, active_key=NEW, mode="verify", lock_table=False
    ) == {"total": 2, "already_active": 2, "previous": 0}
    monkeypatch.setattr(settings, "automation_encryption_key", NEW)
    for row_id in (old_id, new_id):
        row = db_session.get(AutomationConnectorConfig, row_id)
        db_session.refresh(row)
        assert decrypt_credentials_with_current_key(row.credentials_json)["secret"]
    audits = list(db_session.exec(select(AuditLog).where(
        AuditLog.action == "automation_connector_credentials_reencrypted"
    )))
    assert [audit.entity_id for audit in audits] == [str(old_id)]
    assert "credential" not in (audits[0].before_state_json or "")


def test_unreadable_row_aborts_whole_rotation(client, db_session: Session, monkeypatch):
    account_id = _account(client)
    good_id = _connector(client, monkeypatch, OLD, "email", account_id)
    bad_id = _connector(client, monkeypatch, OLD, "crm", account_id)
    good_token = db_session.get(AutomationConnectorConfig, good_id).credentials_json
    bad = db_session.get(AutomationConnectorConfig, bad_id)
    bad.credentials_json = "unreadable-token"
    db_session.add(bad)
    db_session.commit()

    with pytest.raises(CredentialEncryptionError, match="unreadable"):
        rotate_connector_rows(
            db_session, active_key=NEW, previous_key=OLD, mode="apply", lock_table=False
        )
    db_session.expire_all()
    assert db_session.get(AutomationConnectorConfig, good_id).credentials_json == good_token
    assert not list(db_session.exec(select(AuditLog).where(
        AuditLog.action == "automation_connector_credentials_reencrypted"
    )))


def test_write_failure_rolls_back_prior_row_change(client, db_session: Session, monkeypatch):
    account_id = _account(client)
    old_id = _connector(client, monkeypatch, OLD, "email", account_id)
    old_token = db_session.get(AutomationConnectorConfig, old_id).credentials_json

    def fail_audit(*args, **kwargs):
        raise RuntimeError("simulated audit write failure")

    monkeypatch.setattr(connector_key_rotation, "record_audit", fail_audit)
    with pytest.raises(RuntimeError, match="audit write failure"):
        rotate_connector_rows(
            db_session, active_key=NEW, previous_key=OLD, mode="apply", lock_table=False
        )
    db_session.expire_all()
    assert db_session.get(AutomationConnectorConfig, old_id).credentials_json == old_token
