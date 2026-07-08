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
from app.core.database_url import mask_database_url, normalize_database_url  # noqa: E402
from app.core.db import register_models  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402


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
    if not revisions:
        print("Alembic has no revisions.", file=sys.stderr)
        return 1
    if not table_names:
        print("SQLModel metadata has no registered tables.", file=sys.stderr)
        return 1

    print("Database migration check passed.")
    print(f"database_url={mask_database_url(normalize_database_url(settings.database_url))}")
    print(f"migration_heads={','.join(heads)}")
    print(f"registered_tables={len(table_names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
