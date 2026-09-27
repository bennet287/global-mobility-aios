from __future__ import annotations

from app.core.config import settings
from app.core.secrets import SecretResolutionError


DEFAULT_INSECURE_SECRETS = {
    "",
    "change-this-in-production",
    "change-this-to-a-long-random-secret",
}
DEFAULT_INSECURE_PASSWORDS = {
    "",
    "admin",
    "change-this",
    "change-this-admin-password",
}


PRODUCTION_RUNTIME_SECRET_REFS = {
    "JWT_SECRET_REF": ("jwt_secret_ref", "jwt_secret"),
    "AUTOMATION_WEBHOOK_SECRET_REF": (
        "automation_webhook_secret_ref",
        "automation_webhook_secret",
    ),
    "MINIO_ACCESS_KEY_REF": ("minio_access_key_ref", "minio_access_key"),
    "MINIO_SECRET_KEY_REF": ("minio_secret_key_ref", "minio_secret_key"),
    "DOCUMENT_ACCESS_TOKEN_SECRET_REF": (
        "document_access_token_secret_ref",
        "document_access_token_secret",
    ),
}


def _runtime_secret_failures() -> list[str]:
    """Validate production runtime refs through the canonical Settings resolver.

    Accessing each governed value field intentionally delegates to Settings.__getattribute__,
    which resolves the configured reference through SecretsPort on every access. This keeps
    one runtime-secret implementation and proves the same path consumers use at runtime.
    """
    failures: list[str] = []
    resolved_runtime_secrets: dict[str, str] = {}

    for env_name, (reference_field, value_field) in PRODUCTION_RUNTIME_SECRET_REFS.items():
        reference = getattr(settings, reference_field, "")
        if not isinstance(reference, str) or not reference.strip():
            failures.append(f"{env_name} must be configured in production")
            continue
        try:
            resolved_runtime_secrets[value_field] = getattr(settings, value_field).strip()
        except SecretResolutionError:
            failures.append(f"{env_name} must resolve to an available production secret")

    jwt_secret = resolved_runtime_secrets.get("jwt_secret", "")
    if jwt_secret and jwt_secret in DEFAULT_INSECURE_SECRETS:
        failures.append("JWT secret must resolve to a non-default production secret")
    elif jwt_secret and len(jwt_secret) < 32:
        failures.append("JWT secret must be at least 32 characters in production")

    webhook_secret = resolved_runtime_secrets.get("automation_webhook_secret", "")
    if webhook_secret and webhook_secret.lower().startswith("change-this"):
        failures.append("Automation webhook secret must resolve to a non-default production secret")
    elif webhook_secret and len(webhook_secret) < 32:
        failures.append("Automation webhook secret must be at least 32 characters in production")

    return failures


def _raise_production_failures(failures: list[str]) -> None:
    if failures:
        raise RuntimeError(
            "Production startup blocked due to insecure runtime configuration: "
            + "; ".join(failures)
        )


def validate_production_settings() -> None:
    """Fail fast before the production API serves requests."""
    if not settings.is_production():
        return

    failures = _runtime_secret_failures()

    if not settings.auth_enabled:
        failures.append("AUTH_ENABLED must remain true in production")
    if settings.auth_allow_header_role:
        failures.append("AUTH_ALLOW_HEADER_ROLE must be false in production")

    admin_password = settings.auth_admin_password.strip()
    if admin_password in DEFAULT_INSECURE_PASSWORDS:
        failures.append("AUTH_ADMIN_PASSWORD must be set to a non-default production password")
    elif len(admin_password) < 12:
        failures.append("AUTH_ADMIN_PASSWORD must be at least 12 characters in production")

    _raise_production_failures(failures)


def validate_production_worker_settings() -> None:
    """Fail closed before a production worker accepts tasks.

    Workers share the runtime secret and document-storage gates but intentionally do not
    receive API-only bootstrap login credentials such as AUTH_ADMIN_PASSWORD.
    """
    if not settings.is_production():
        return

    _raise_production_failures(_runtime_secret_failures())

    from app.services.document_storage import validate_document_storage_configuration

    validate_document_storage_configuration()
