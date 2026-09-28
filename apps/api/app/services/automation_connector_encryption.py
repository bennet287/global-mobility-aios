from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.secrets import SecretResolutionError


class CredentialEncryptionError(Exception):
    pass


def _fernet_key(secret: str) -> bytes:
    """Derive a 32-byte URL-safe base64-encoded Fernet key from a secret."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _resolved_master_key(*, value_field: str, label: str, required: bool) -> str:
    try:
        raw_key = getattr(settings, value_field)
    except SecretResolutionError as exc:
        raise CredentialEncryptionError(f"{label} could not be resolved") from exc
    if not isinstance(raw_key, str) or not raw_key.strip():
        if required:
            raise CredentialEncryptionError(f"{label} is required to store automation credentials")
        return ""
    return raw_key


def _current_master_key() -> str:
    return _resolved_master_key(
        value_field="automation_encryption_key",
        label="AUTOMATION_ENCRYPTION_KEY",
        required=True,
    )


def _previous_master_key() -> str:
    return _resolved_master_key(
        value_field="automation_encryption_previous_key",
        label="AUTOMATION_ENCRYPTION_PREVIOUS_KEY",
        required=False,
    )


def _fernet(secret: str) -> Fernet:
    try:
        return Fernet(_fernet_key(secret))
    except Exception as exc:  # pragma: no cover - hashlib/base64 output is deterministic
        raise CredentialEncryptionError("Invalid automation encryption key") from exc


def _decode_payload(plaintext: str) -> dict[str, Any]:
    try:
        value = json.loads(plaintext) if plaintext else {}
    except json.JSONDecodeError as exc:
        raise CredentialEncryptionError("Stored credentials are not valid JSON") from exc
    if not isinstance(value, dict):
        raise CredentialEncryptionError("Stored credentials must decode to a JSON object")
    return value


def _decrypt_with_fernet(ciphertext: str, fernet: Fernet) -> dict[str, Any]:
    plaintext = fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    return _decode_payload(plaintext)


def encrypt_credentials(credentials: dict[str, Any]) -> str:
    """Encrypt connector credentials with the active automation encryption key only."""
    plaintext = json.dumps(credentials, sort_keys=True, separators=(",", ":"), default=str)
    return _fernet(_current_master_key()).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_credentials_with_current_key(ciphertext: str | None) -> dict[str, Any]:
    """Decrypt using only the active key, for post-rotation verification."""
    if not ciphertext:
        return {}
    try:
        return _decrypt_with_fernet(ciphertext, _fernet(_current_master_key()))
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise CredentialEncryptionError(
            "Stored connector credentials cannot be decrypted with the active key"
        ) from exc


def decrypt_credentials(ciphertext: str | None) -> dict[str, Any]:
    """Decrypt credentials with active key, then a temporary previous rotation key.

    New writes always use the active key. The previous key exists only to bridge a
    controlled rotation while stored connector ciphertext is explicitly re-encrypted.
    Legacy plaintext JSON remains readable outside production for development/backward
    compatibility; production never accepts plaintext connector credentials.
    """
    if not ciphertext:
        return {}

    current_key = _current_master_key()
    try:
        return _decrypt_with_fernet(ciphertext, _fernet(current_key))
    except (InvalidToken, UnicodeDecodeError):
        pass

    previous_key = _previous_master_key()
    if previous_key:
        if hmac.compare_digest(current_key, previous_key):
            raise CredentialEncryptionError(
                "AUTOMATION_ENCRYPTION_PREVIOUS_KEY must differ from the active key"
            )
        try:
            return _decrypt_with_fernet(ciphertext, _fernet(previous_key))
        except (InvalidToken, UnicodeDecodeError):
            pass

    if not settings.is_production():
        # Backward compatibility for pre-encryption local/test records only.
        try:
            return _decode_payload(ciphertext)
        except CredentialEncryptionError:
            pass

    raise CredentialEncryptionError("Stored connector credentials cannot be decrypted")


def reencrypt_credentials_with_current_key(ciphertext: str | None) -> str:
    """Re-encrypt one stored connector credential payload with the active key."""
    credentials = decrypt_credentials(ciphertext)
    return encrypt_credentials(credentials)
