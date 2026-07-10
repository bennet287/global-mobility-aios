from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.db import register_models  # noqa: E402
from scripts.check_local_db_schema import check_local_db_schema  # noqa: E402


def test_local_db_schema_check_passes_for_current_metadata() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    register_models()
    SQLModel.metadata.create_all(engine)

    result = check_local_db_schema(engine)

    assert result["status"] == "ok"
    assert result["missing_tables"] == {}
    assert result["missing_columns"] == {}


def test_local_db_schema_check_reports_stale_document_columns(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'old-demo.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE documents (
                    id CHAR(32) PRIMARY KEY,
                    lead_id CHAR(32),
                    document_type VARCHAR NOT NULL,
                    filename VARCHAR NOT NULL,
                    storage_key VARCHAR,
                    status VARCHAR NOT NULL,
                    extracted_metadata_json VARCHAR,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

    result = check_local_db_schema(engine)

    assert result["status"] == "schema_drift"
    assert "documents" in result["missing_columns"]
    assert "storage_provider" in result["missing_columns"]["documents"]
    assert "file_hash" in result["missing_columns"]["documents"]
    assert result["suggested_local_demo_fix"]
