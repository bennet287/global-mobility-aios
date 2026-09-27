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
    "JWT_SECRET_REF": "jwt_secret_ref",
    "AUTOMATION_WEBHOOK_SECRET_REF": "automation_webhook_secret_ref",
    "MINIO_ACCESS_KEY_REF": "minio_access_key_ref",
    "MINIO_SECRET_KEY_REF": "minio_secret_key_ref",
    "DOCUMENT_ACCESS_TOKEN_SECRET_REF": "document_access_token_secret_ref",
}


def validate_production_settings() -> None:
    """Fail fast before serving requests when production security is incomplete.

    Development keeps convenient local defaults. Production never relies on them:
    authentication must be enabled, unsigned role headers must be disabled, and
    migrated runtime credentials must be supplied through governed secret references.
    Document-storage enforcement is repeated in the storage service so a direct
    storage client also fails closed outside application startup.
    """
    if not settings.is_production():
        return

    failures: list[str] = []

    if not settings.auth_enabled:
        failures.append("AUTH_ENABLED must remain true in production")
    if settings.auth_allow_header_role:
        failures.append("AUTH_ALLOW_HEADER_ROLE must be false in production")

    for env_name, field_name in PRODUCTION_RUNTIME_SECRET_REFS.items():
        reference = getattr(settings, field_name, "")
        if not isinstance(reference, str) or not reference.strip():
            failures.append(f"{env_name} must be configured in production")

    try:
        jwt_secret = settings.jwt_secret.strip()
    except SecretResolutionError:
        failures.append("JWT_SECRET_REF must resolve to an available production secret")
    else:
        if jwt_secret in DEFAULT_INSECURE_SECRETS:
            failures.append("JWT secret must resolve to a non-default production secret")
        elif len(jwt_secret) < 32:
            failures.append("JWT secret must be at least 32 characters in production")

    try:
        webhook_secret = settings.automation_webhook_secret.strip()
    except SecretResolutionError:
        failures.append("AUTOMATION_WEBHOOK_SECRET_REF must resolve to an available production secret")
    else:
        if not webhook_secret or webhook_secret.lower().startswith("change-this"):
            failures.append("Automation webhook secret must resolve to a non-default production secret")
        elif len(webhook_secret) < 32:
            failures.append("Automation webhook secret must be at least 32 characters in production")

    admin_password = settings.auth_admin_password.strip()
    if admin_password in DEFAULT_INSECURE_PASSWORDS:
        failures.append("AUTH_ADMIN_PASSWORD must be set to a non-default production password")
    elif len(admin_password) < 12:
        failures.append("AUTH_ADMIN_PASSWORD must be at least 12 characters in production")

    if failures:
        raise RuntimeError(
            "Production startup blocked due to insecure runtime configuration: "
            + "; ".join(failures)
        )
