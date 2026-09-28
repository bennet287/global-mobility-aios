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
    try:
        url = make_url(configured_database_url())
        role, database, tcp = _connect_and_identify(url)
        if role != url.username or database != url.database or not tcp:
            raise DatabasePasswordProbeError("PostgreSQL connection identity did not match configuration")

        incorrect = secrets.token_urlsafe(32)
        try:
            _connect_and_identify(url.set(password=incorrect))
        except DBAPIError as exc:
            if getattr(exc.orig, "sqlstate", None) != "28P01":
                raise DatabasePasswordProbeError("Incorrect-password rejection was not established") from None
        else:
            raise DatabasePasswordProbeError("PostgreSQL accepted an incorrect password")
        return {"authenticated": True, "incorrect_password_rejected": True, "role": role, "database": database}
    except DatabasePasswordProbeError:
        raise
    except Exception:
        # DBAPI errors may embed a URL or credential. Never emit the raw exception.
        raise DatabasePasswordProbeError("PostgreSQL password authentication could not be verified") from None


def main() -> int:
    try:
        print(json.dumps(probe_database_password(), sort_keys=True))
        return 0
    except DatabasePasswordProbeError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
