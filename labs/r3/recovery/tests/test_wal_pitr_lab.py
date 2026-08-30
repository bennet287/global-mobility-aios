from __future__ import annotations

from labs.r3.recovery.wal_pitr_lab import POSTGRES_IMAGE


def test_native_pitr_uses_pinned_postgres_major() -> None:
    assert POSTGRES_IMAGE == "postgres:16-alpine"
