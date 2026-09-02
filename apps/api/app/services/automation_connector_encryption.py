from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CredentialEncryptionError(Exception):
    pass


def _fernet_key(secret: str) -> bytes:
    """Derive a 32-byte URL-safe base64-encoded Fernet key from a secret."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    raw_key = settings.automation_encryption_key.strip()
    if not raw_key:
        raw_key = settings.jwt_secret
    if not raw_key:
        raise CredentialEncryptionError("An encryption key is required to store automation credentials")
    try:
        return Fernet(_fernet_key(raw_key))
    except Exception as exc:
        raise CredentialEncryptionError("Invalid automation encryption key") from exc


def encrypt_credentials(credentials: dict[str, Any]) -> str:
    """Encrypt a credentials dict and return a ciphertext string.

    Returns an empty JSON object encrypted when credentials are empty.
    """
    fernet = _get_fernet()
    plaintext = json.dumps(credentials, sort_keys=True, separators=(",", ":"), default=str)
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_credentials(ciphertext: str | None) -> dict[str, Any]:
    """Decrypt a credentials ciphertext string back to a dict.

    Falls back to parsing legacy plaintext JSON if decryption fails.
    """
    if not ciphertext:
        return {}
    fernet = _get_fernet()
    try:
        plaintext = fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Legacy plaintext credentials (created before encryption was enabled).
        plaintext = ciphertext
    try:
        return json.loads(plaintext) if plaintext else {}
    except json.JSONDecodeError as exc:
        raise CredentialEncryptionError("Stored credentials are not valid JSON") from exc
