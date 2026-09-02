from __future__ import annotations

import hmac
import hashlib
import json
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import httpx

from email.message import EmailMessage

from sqlmodel import Session, select

from app.models.domain import AutomationConnectorConfig, AutomationDelivery, AutomationEvent, CorporateAccount
from app.schemas_automation import ConnectorConfigCreate
from app.services.audit_log import record_audit, to_audit_dict
from app.services.external_action_gates import assert_delivery_dispatch_authorized
from app.services.automation_connector_encryption import (
    CredentialEncryptionError,
    decrypt_credentials,
    encrypt_credentials,
)


MAX_DELIVERY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (60, 300, 900)
AUTOMATION_CONNECTOR_CHANNELS = {"email", "messaging", "calendar", "crm", "webhook"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _mask_credentials(value: Any) -> Any:
    """Return a credentials-shaped structure with every scalar value redacted."""
    if isinstance(value, dict):
        return {key: _mask_credentials(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_mask_credentials(item) for item in value]
    return "***"


class AdapterSendError(Exception):
    pass


class AutomationProviderAdapter(ABC):
    @abstractmethod
    def send(self, delivery: AutomationDelivery, config: AutomationConnectorConfig) -> str:
        """Send the delivery and return a provider message identifier."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self, config: AutomationConnectorConfig) -> str:
        """Verify the provider is reachable and the config is usable.

        Returns a short status string or raises AdapterSendError on failure.
        """
        raise NotImplementedError


class ConsoleAdapter(AutomationProviderAdapter):
    """Local/test adapter that writes to stdout and returns a stable message id."""

    def send(self, delivery: AutomationDelivery, config: AutomationConnectorConfig) -> str:
        payload = _load(delivery.payload_json, {})
        print(
            f"[automation:console:{delivery.channel}] to={delivery.destination} "
            f"subject={delivery.subject} body={payload.get('body', '')[:200]}"
        )
        return f"console-{uuid4().hex[:12]}"

    def health_check(self, config: AutomationConnectorConfig) -> str:
        return "healthy"


class SmtpAdapter(AutomationProviderAdapter):
    """SMTP email adapter. Credentials must contain host, port, username, password."""

    def _credentials(self, config: AutomationConnectorConfig) -> dict[str, Any]:
        return decrypt_credentials(config.credentials_json)

    def send(self, delivery: AutomationDelivery, config: AutomationConnectorConfig) -> str:
        credentials = self._credentials(config)
        host = credentials.get("host", "")
        port = int(credentials.get("port", 587))
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        if not host or not username or password is None:
            raise AdapterSendError("SMTP credentials must include host, username, and password")

        payload = _load(delivery.payload_json, {})
        body = payload.get("body", "")
        msg = EmailMessage()
        msg["Subject"] = delivery.subject or "Automation delivery"
        msg["From"] = config.from_address or username
        msg["To"] = delivery.destination or ""
        msg.set_content(body)

        try:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.starttls()
                server.login(username, password)
                result = server.send_message(msg)
        except Exception as exc:
            raise AdapterSendError(f"SMTP send failed: {exc}") from exc

        return f"smtp-{result.get('to', 'unknown')}"

    def health_check(self, config: AutomationConnectorConfig) -> str:
        credentials = self._credentials(config)
        host = credentials.get("host", "")
        port = int(credentials.get("port", 587))
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        if not host or not username or password is None:
            raise AdapterSendError("SMTP credentials must include host, username, and password")

        try:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.starttls()
                server.login(username, password)
        except Exception as exc:
            raise AdapterSendError(f"SMTP health check failed: {exc}") from exc
        return "healthy"


class WebhookAdapter(AutomationProviderAdapter):
    """Generic webhook adapter. Credentials must contain url; secret is optional for HMAC signing."""

    def _credentials(self, config: AutomationConnectorConfig) -> dict[str, Any]:
        return decrypt_credentials(config.credentials_json)

    def _headers(self, credentials: dict[str, Any], body_bytes: bytes) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "gmai-automation/1.0",
        }
        secret = credentials.get("secret")
        if secret:
            signature = hmac.new(
                secret.encode("utf-8"), body_bytes, hashlib.sha256
            ).hexdigest()
            headers["X-GMAI-Signature"] = signature
        return headers

    def send(self, delivery: AutomationDelivery, config: AutomationConnectorConfig) -> str:
        credentials = self._credentials(config)
        url = credentials.get("url", "").strip()
        if not url:
            raise AdapterSendError("Webhook credentials must include url")

        body = delivery.payload_json.encode("utf-8")
        try:
            response = httpx.post(
                url,
                content=body,
                headers=self._headers(credentials, body),
                timeout=30,
                follow_redirects=False,
            )
            response.raise_for_status()
        except Exception as exc:
            raise AdapterSendError(f"Webhook POST failed: {exc}") from exc

        return f"webhook-{uuid4().hex[:12]}"

    def health_check(self, config: AutomationConnectorConfig) -> str:
        credentials = self._credentials(config)
        url = credentials.get("url", "").strip()
        if not url:
            raise AdapterSendError("Webhook credentials must include url")

        try:
            response = httpx.get(url, timeout=10, follow_redirects=False)
            response.raise_for_status()
        except Exception as exc:
            raise AdapterSendError(f"Webhook health check failed: {exc}") from exc
        return "healthy"


_ADAPTERS: dict[str, type[AutomationProviderAdapter]] = {
    "console": ConsoleAdapter,
    "smtp": SmtpAdapter,
    "webhook": WebhookAdapter,
}


def get_adapter(provider_type: str) -> AutomationProviderAdapter:
    adapter_cls = _ADAPTERS.get(provider_type.lower())
    if adapter_cls is None:
        raise AdapterSendError(f"Unknown provider type: {provider_type}")
    return adapter_cls()


def _config_read(config: AutomationConnectorConfig) -> dict[str, Any]:
    return {
        **to_audit_dict(config),
        "credentials": _mask_credentials(decrypt_credentials(config.credentials_json)),
    }


def connector_config_create(
    session: Session,
    payload: ConnectorConfigCreate,
    *,
    actor: str,
) -> AutomationConnectorConfig:
    account = session.get(CorporateAccount, payload.corporate_account_id)
    if account is None:
        raise ValueError("Corporate account not found")
    if account.account_status != "active":
        raise ValueError("Connector configs require an active corporate account")
    if payload.channel not in AUTOMATION_CONNECTOR_CHANNELS:
        raise ValueError(f"Unsupported connector channel: {payload.channel}")
    if payload.provider_type not in _ADAPTERS:
        raise ValueError(f"Unsupported provider type: {payload.provider_type}")

    existing = session.exec(
        select(AutomationConnectorConfig).where(
            AutomationConnectorConfig.corporate_account_id == account.id,
            AutomationConnectorConfig.channel == payload.channel,
            AutomationConnectorConfig.status == "active",
        )
    ).first()
    if existing is not None:
        raise ValueError(f"An active connector config already exists for {payload.channel}")

    now = _now()
    config = AutomationConnectorConfig(
        corporate_account_id=account.id,
        channel=payload.channel,
        provider_type=payload.provider_type,
        credentials_json=encrypt_credentials(payload.credentials),
        from_address=payload.from_address.strip() if payload.from_address else None,
        sender_label=payload.sender_label.strip() if payload.sender_label else None,
        status="active",
        created_by=actor,
        updated_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(config)
    session.flush()
    record_audit(
        session,
        action="automation_connector_config_created",
        entity_type="automation_connector_config",
        entity_id=config.id,
        after_state=_config_read(config),
        actor=actor,
        source="automation_v12_4",
    )
    session.commit()
    session.refresh(config)
    return config


def connector_config_update_status(
    session: Session,
    config: AutomationConnectorConfig,
    *,
    status: str,
    reason: str,
    actor: str,
) -> AutomationConnectorConfig:
    if status not in {"active", "paused"}:
        raise ValueError("Connector config status must be active or paused")
    before = _config_read(config)
    now = _now()
    config.status = status
    config.updated_by = actor
    config.updated_at = now
    session.add(config)
    record_audit(
        session,
        action=f"automation_connector_config_{status}",
        entity_type="automation_connector_config",
        entity_id=config.id,
        before_state=before,
        after_state=_config_read(config),
        reason=reason.strip(),
        actor=actor,
        source="automation_v12_4",
    )
    session.commit()
    session.refresh(config)
    return config


def find_connector_for_account_channel(
    session: Session,
    corporate_account_id: UUID,
    channel: str,
) -> AutomationConnectorConfig | None:
    return session.exec(
        select(AutomationConnectorConfig).where(
            AutomationConnectorConfig.corporate_account_id == corporate_account_id,
            AutomationConnectorConfig.channel == channel,
            AutomationConnectorConfig.status == "active",
        )
    ).first()


def find_connector_for_delivery(
    session: Session,
    delivery: AutomationDelivery,
) -> AutomationConnectorConfig | None:
    if delivery.connector_config_id is not None:
        config = session.get(AutomationConnectorConfig, delivery.connector_config_id)
        if config is not None and config.status == "active":
            return config

    event = session.get(AutomationEvent, delivery.automation_event_id)
    if event is None:
        return None
    return session.exec(
        select(AutomationConnectorConfig).where(
            AutomationConnectorConfig.corporate_account_id == event.corporate_account_id,
            AutomationConnectorConfig.channel == delivery.channel,
            AutomationConnectorConfig.status == "active",
        )
    ).first()


def _backoff_delay(attempt_count: int) -> int:
    index = max(0, min(attempt_count, len(RETRY_BACKOFF_SECONDS) - 1))
    return RETRY_BACKOFF_SECONDS[index]


STALE_DISPATCHING_MINUTES = 5


def reset_stale_dispatching_deliveries(
    session: Session,
    *,
    max_age_minutes: int = STALE_DISPATCHING_MINUTES,
    actor: str = "automation-worker",
) -> int:
    """Reset deliveries stuck in dispatching back to ready/retry and audit."""
    cutoff = _now() - timedelta(minutes=max_age_minutes)
    statement = (
        select(AutomationDelivery)
        .where(AutomationDelivery.status == "dispatching")
        .where(AutomationDelivery.updated_at <= cutoff)
    )
    reset_count = 0
    for delivery in session.exec(statement).all():
        before = to_audit_dict(delivery)
        delivery.status = "retry" if delivery.attempt_count < MAX_DELIVERY_ATTEMPTS else "failed"
        delivery.last_error = "Dispatch lock expired; recovered by worker"
        delivery.next_attempt_at = None if delivery.status == "failed" else _now()
        delivery.updated_at = _now()
        session.add(delivery)
        record_audit(
            session,
            action="automation_delivery_dispatch_lock_recovered",
            entity_type="automation_delivery",
            entity_id=delivery.id,
            before_state=before,
            after_state=to_audit_dict(delivery),
            actor=actor,
            source="automation_v12_4",
        )
        reset_count += 1
    if reset_count:
        session.commit()
    return reset_count


def attempt_delivery_dispatch(
    session: Session,
    delivery: AutomationDelivery,
    *,
    actor: str,
    max_attempts: int = MAX_DELIVERY_ATTEMPTS,
) -> AutomationDelivery:
    if delivery.status not in {"ready", "retry", "dispatching"}:
        raise ValueError("Only ready, retry, or dispatching deliveries can be dispatched")

    assert_delivery_dispatch_authorized(session, delivery)

    config = find_connector_for_delivery(session, delivery)
    if config is None:
        delivery.attempt_count += 1
        delivery.last_error = "No active connector config for channel"
        delivery.status = "failed" if delivery.attempt_count >= max_attempts else "retry"
        if delivery.status == "retry":
            delivery.next_attempt_at = _now() + timedelta(seconds=_backoff_delay(delivery.attempt_count))
        else:
            delivery.next_attempt_at = None
        delivery.updated_at = _now()
        session.add(delivery)
        session.commit()
        session.refresh(delivery)
        return delivery

    before = to_audit_dict(delivery)
    try:
        adapter = get_adapter(config.provider_type)
        provider_message_id = adapter.send(delivery, config)
        now = _now()
        delivery.status = "dispatched"
        delivery.dispatched_by = actor
        delivery.dispatched_at = now
        delivery.provider_message_id = provider_message_id.strip()
        delivery.attempt_count += 1
        delivery.last_error = None
        delivery.next_attempt_at = None
        delivery.updated_at = now
        session.add(delivery)
        record_audit(
            session,
            action="automation_delivery_dispatched",
            entity_type="automation_delivery",
            entity_id=delivery.id,
            before_state=before,
            after_state=to_audit_dict(delivery),
            actor=actor,
            source="automation_v12_4",
        )
        session.commit()
        session.refresh(delivery)
        return delivery
    except AdapterSendError as exc:
        now = _now()
        delivery.attempt_count += 1
        delivery.last_error = str(exc)
        if delivery.attempt_count >= max_attempts:
            delivery.status = "failed"
            delivery.next_attempt_at = None
        else:
            delivery.status = "retry"
            delivery.next_attempt_at = now + timedelta(seconds=_backoff_delay(delivery.attempt_count))
        delivery.updated_at = now
        session.add(delivery)
        record_audit(
            session,
            action="automation_delivery_attempt_failed",
            entity_type="automation_delivery",
            entity_id=delivery.id,
            before_state=before,
            after_state=to_audit_dict(delivery),
            reason=str(exc),
            actor=actor,
            source="automation_v12_4",
        )
        session.commit()
        session.refresh(delivery)
        return delivery


def check_connector_health(
    session: Session,
    config: AutomationConnectorConfig,
    *,
    actor: str,
) -> dict[str, Any]:
    """Run a provider health check and audit the result."""
    adapter = get_adapter(config.provider_type)
    try:
        status = adapter.health_check(config)
    except AdapterSendError as exc:
        record_audit(
            session,
            action="automation_connector_health_check_failed",
            entity_type="automation_connector_config",
            entity_id=config.id,
            reason=str(exc),
            actor=actor,
            source="automation_v12_4",
        )
        session.commit()
        raise

    record_audit(
        session,
        action="automation_connector_health_check_succeeded",
        entity_type="automation_connector_config",
        entity_id=config.id,
        after_state={"status": status, "provider_type": config.provider_type},
        actor=actor,
        source="automation_v12_4",
    )
    session.commit()
    return {"status": status, "provider_type": config.provider_type}


def reconcile_automation_deliveries(
    session: Session,
    *,
    max_age_hours: int = 24,
    actor: str = "reconciliation-worker",
) -> dict[str, int]:
    """Mark long-dispatched console deliveries as reconciled and audit the action.

    Reconciliation is currently a local best-effort confirmation for console
    deliveries. Real provider reconciliation will be added per-adapter as
    integrations mature.
    """
    cutoff = _now() - timedelta(hours=max_age_hours)
    statement = (
        select(AutomationDelivery)
        .where(AutomationDelivery.status == "dispatched")
        .where(AutomationDelivery.dispatched_at <= cutoff)
        .where(AutomationDelivery.reconciled.is_(False))
        .where(AutomationDelivery.provider_message_id.like("console-%"))
        .order_by(AutomationDelivery.dispatched_at)
    )
    deliveries = list(session.exec(statement).all())
    reconciled_count = 0
    for delivery in deliveries:
        before = to_audit_dict(delivery)
        delivery.reconciled = True
        delivery.reconciled_at = _now()
        delivery.updated_at = _now()
        session.add(delivery)
        record_audit(
            session,
            action="automation_delivery_reconciled",
            entity_type="automation_delivery",
            entity_id=delivery.id,
            before_state=before,
            after_state=to_audit_dict(delivery),
            actor=actor,
            source="automation_v12_4",
        )
        reconciled_count += 1
    session.commit()
    return {"reconciled": reconciled_count}
