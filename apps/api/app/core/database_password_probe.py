"""Read-only production probe for PostgreSQL role-password rotation."""

from __future__ import annotations

import json
import secrets

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database_url import configured_database_url


class DatabasePasswordProbeError(RuntimeError):
    pass


def _is_password_rejection(error: DBAPIError, role: str) -> bool:
    state = getattr(error.orig, "sqlstate", None)
    if state == "28P01":
        return True
    if state is not None:
        return False
    # libpq/psycopg may omit SQLSTATE during connection startup. Match only
    # the server's specific rejection for this same role; never print it.
    return f'password authentication failed for user "{role}"' in str(error.orig)


def _connect_and_identify(url):
    engine = create_engine(url, connect_args={"connect_timeout": 5}, poolclass=NullPool)
    try:
        with engine.connect() as connection:
            return connection.execute(
                text("SELECT current_user, current_database(), inet_client_addr() IS NOT NULL")
            ).one()
    finally:
        engine.dispose()


def probe_database_password() -> dict[str, str | bool]:
    """Require a real TCP login and rejection of an incorrect password.

    The negative attempt detects a server configured with trust authentication,
    where a successful connection would not prove the staged password works.
    """
    if not settings.is_production():
        raise DatabasePasswordProbeError("Production environment is required")
    stage = "configuration"
    try:
        url = make_url(configured_database_url())
        stage = "configured connection"
        role, database, tcp = _connect_and_identify(url)
        if role != url.username or database != url.database or not tcp:
            raise DatabasePasswordProbeError("PostgreSQL connection identity did not match configuration")

        incorrect = secrets.token_urlsafe(32)
        stage = "incorrect-password rejection"
        try:
            _connect_and_identify(url.set(password=incorrect))
        except DBAPIError as exc:
            if not _is_password_rejection(exc, role):
                raise DatabasePasswordProbeError("Incorrect-password rejection was not established") from None
        else:
            raise DatabasePasswordProbeError("PostgreSQL accepted an incorrect password")
        return {"authenticated": True, "incorrect_password_rejected": True, "role": role, "database": database}
    except DatabasePasswordProbeError:
        raise
    except Exception:
        # DBAPI errors may embed a URL or credential. Never emit the raw exception.
        raise DatabasePasswordProbeError(f"PostgreSQL password probe failed at {stage}") from None


def main() -> int:
    try:
        print(json.dumps(probe_database_password(), sort_keys=True))
        return 0
    except DatabasePasswordProbeError:
        print("PostgreSQL password probe failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
