from __future__ import annotations

from app.core.config import settings


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


def validate_production_settings() -> None:
    """Fail fast before serving requests when production security is incomplete.

    Development keeps convenient local defaults. Production never relies on them:
    authentication must be enabled, unsigned role headers must be disabled, and
    credentials/signing material must be explicitly hardened. Document-storage
    enforcement is repeated in the storage service so a direct storage client also
    fails closed outside application startup.
    """
    if not settings.is_production():
        return

    failures: list[str] = []

    if not settings.auth_enabled:
        failures.append("AUTH_ENABLED must remain true in production")
    if settings.auth_allow_header_role:
        failures.append("AUTH_ALLOW_HEADER_ROLE must be false in production")

    jwt_secret = settings.jwt_secret.strip()
    if jwt_secret in DEFAULT_INSECURE_SECRETS:
        failures.append("JWT_SECRET must be set to a non-default production secret")
    elif len(jwt_secret) < 32:
        failures.append("JWT_SECRET must be at least 32 characters in production")

    admin_password = settings.auth_admin_password.strip()
    if admin_password in DEFAULT_INSECURE_PASSWORDS:
        failures.append("AUTH_ADMIN_PASSWORD must be set to a non-default production password")
    elif len(admin_password) < 12:
        failures.append("AUTH_ADMIN_PASSWORD must be at least 12 characters in production")

    if failures:
        raise RuntimeError(
            "Production startup blocked due to insecure authentication configuration: "
            + "; ".join(failures)
        )
