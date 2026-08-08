from __future__ import annotations

import os

from app.core.config import settings


DEFAULT_INSECURE_SECRETS = {
    "change-this-in-production",
    "",
}
DEFAULT_INSECURE_PASSWORDS = {
    "admin",
    "",
}


def _is_production() -> bool:
    return settings.app_env.lower() in {"production", "prod"}


def validate_production_settings() -> None:
    """Fail fast on insecure production configuration.

    Misconfiguration should prevent the application from booting in production
    rather than falling back to defaults that bypass authentication or expose
    sensitive data.
    """
    if not _is_production():
        return

    errors: list[str] = []

    if settings.auth_allow_header_role:
        errors.append(
            "auth_allow_header_role must be disabled in production. "
            "Header-role authentication is for local development and tests only."
        )

    if settings.jwt_secret in DEFAULT_INSECURE_SECRETS:
        errors.append(
            "jwt_secret is unset or uses a default value in production. "
            "Set a strong, unique JWT secret."
        )

    if settings.auth_admin_password in DEFAULT_INSECURE_PASSWORDS:
        errors.append(
            "auth_admin_password is unset or uses a default value in production. "
            "Set a strong, unique admin password."
        )

    if settings.document_storage_backend == "local":
        if not settings.document_storage_allow_local_in_production:
            errors.append(
                "document_storage_backend is 'local' in production. "
                "Use object storage (e.g., minio) or explicitly allow local "
                "storage only for a specific transitional deployment."
            )

    if settings.document_storage_backend == "minio" and not settings.minio_server_side_encryption:
        errors.append(
            "minio_server_side_encryption is disabled in production. "
            "Enable server-side encryption for stored documents."
        )

    if errors:
        message = "Production startup blocked due to insecure configuration:\n" + "\n".join(
            f"- {error}" for error in errors
        )
        raise RuntimeError(message)


def require_env_secret(name: str) -> str:
    """Return an environment variable value or fail fast in production."""
    value = os.environ.get(name, "").strip()
    if not value and _is_production():
        raise RuntimeError(f"Missing required production environment variable: {name}")
    return value
