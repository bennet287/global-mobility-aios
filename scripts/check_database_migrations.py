from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from alembic.config import Config  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database_url import is_sqlite_url, mask_database_url, normalize_database_url  # noqa: E402
from app.core.db import register_models  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from check_local_db_schema import check_local_db_schema  # noqa: E402


def main() -> int:
    register_models()

    alembic_ini = ROOT / "alembic.ini"
    if not alembic_ini.exists():
        print(f"Missing Alembic config: {alembic_ini}", file=sys.stderr)
        return 1

    config = Config(str(alembic_ini))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    revisions = list(script.walk_revisions())
    table_names = sorted(SQLModel.metadata.tables.keys())

    if not heads:
        print("Alembic has no migration head.", file=sys.stderr)
        return 1
    if len(heads) != 1:
        print(f"Alembic must have exactly one controlled head; found {heads}.", file=sys.stderr)
        return 1
    if not revisions:
        print("Alembic has no revisions.", file=sys.stderr)
        return 1
    if not table_names:
        print("SQLModel metadata has no registered tables.", file=sys.stderr)
        return 1

    database_url = normalize_database_url(settings.database_url)
    connect_args = {"check_same_thread": False} if is_sqlite_url(database_url) else {}
    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
    try:
        schema_result = check_local_db_schema(engine)
        if schema_result["status"] != "ok":
            print("Database migration check found physical schema drift.", file=sys.stderr)
            print(f"database_url={mask_database_url(database_url)}", file=sys.stderr)
            print(f"missing_tables={schema_result['missing_tables']}", file=sys.stderr)
            print(f"missing_columns={schema_result['missing_columns']}", file=sys.stderr)
            print(f"extra_tables={schema_result['extra_tables']}", file=sys.stderr)
            return 1

        inspector = inspect(engine)
        if "alembic_version" not in inspector.get_table_names():
            print("Database migration check found no Alembic version table.", file=sys.stderr)
            return 1
        with engine.connect() as connection:
            database_revisions = [
                str(row[0])
                for row in connection.execute(text("SELECT version_num FROM alembic_version"))
            ]
        if database_revisions != heads:
            print("Database migration check found database revision mismatch.", file=sys.stderr)
            print(
                f"database_revision={','.join(database_revisions) if database_revisions else '<empty>'}",
                file=sys.stderr,
            )
            print(f"migration_heads={','.join(heads)}", file=sys.stderr)
            return 1

        print("Database migration check passed.")
        print(f"database_url={mask_database_url(database_url)}")
        print(f"migration_heads={','.join(heads)}")
        print(f"registered_tables={len(table_names)}")
        print("physical_schema=ok")
        print(f"database_revision={database_revisions[0]}")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
