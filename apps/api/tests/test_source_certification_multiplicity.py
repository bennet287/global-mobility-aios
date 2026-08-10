from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, create_engine

from app.models.domain import (
    JurisdictionSourceCertification,
    now_utc,
)
from app.services.jurisdiction_registry import (
    _source_certification_lineage_filters,
)


def _row(
    *,
    jurisdiction_id,
    source_id,
    scope,
    version,
):
    now = now_utc()

    return {
        "id": uuid4(),
        "jurisdiction_id": jurisdiction_id,
        "registry_entry_id": uuid4(),
        "regulatory_authority_id": uuid4(),
        "official_source_id": source_id,
        "certification_version": version,
        "certification_scope": scope,
        "coverage_domains_json": '["visa"]',
        "evidence_notes": "Test evidence.",
        "status": "pending_review",
        "proposed_by": "test-proposer",
        "reviewed_by": None,
        "reviewed_at": None,
        "review_notes": None,
        "supersedes_certification_id": None,
        "created_at": now,
        "updated_at": now,
    }


def _engine():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


def test_supplemental_lineage_includes_source_identity():
    filters = _source_certification_lineage_filters(
        jurisdiction_id=uuid4(),
        certification_scope="supplemental_visa",
        official_source_id=uuid4(),
    )

    assert len(filters) == 3
    assert "official_source_id" in str(filters[2])


def test_primary_lineage_remains_jurisdiction_scoped():
    filters = _source_certification_lineage_filters(
        jurisdiction_id=uuid4(),
        certification_scope="primary_immigration",
        official_source_id=uuid4(),
    )

    assert len(filters) == 2


def test_two_supplemental_sources_may_each_start_at_v1():
    engine = _engine()

    jurisdiction_id = uuid4()

    rows = [
        _row(
            jurisdiction_id=jurisdiction_id,
            source_id=uuid4(),
            scope="supplemental_visa",
            version=1,
        ),
        _row(
            jurisdiction_id=jurisdiction_id,
            source_id=uuid4(),
            scope="supplemental_visa",
            version=1,
        ),
    ]

    with engine.begin() as connection:
        connection.execute(
            JurisdictionSourceCertification.__table__.insert(),
            rows,
        )


def test_same_supplemental_source_cannot_duplicate_version():
    engine = _engine()

    jurisdiction_id = uuid4()
    source_id = uuid4()

    rows = [
        _row(
            jurisdiction_id=jurisdiction_id,
            source_id=source_id,
            scope="supplemental_visa",
            version=1,
        ),
        _row(
            jurisdiction_id=jurisdiction_id,
            source_id=source_id,
            scope="supplemental_visa",
            version=1,
        ),
    ]

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                JurisdictionSourceCertification.__table__.insert(),
                rows,
            )


def test_primary_v1_remains_unique_across_sources():
    engine = _engine()

    jurisdiction_id = uuid4()

    rows = [
        _row(
            jurisdiction_id=jurisdiction_id,
            source_id=uuid4(),
            scope="primary_immigration",
            version=1,
        ),
        _row(
            jurisdiction_id=jurisdiction_id,
            source_id=uuid4(),
            scope="primary_immigration",
            version=1,
        ),
    ]

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                JurisdictionSourceCertification.__table__.insert(),
                rows,
            )


def test_proposal_and_review_share_lineage_primitive():
    root = Path(__file__).resolve().parents[3]

    service = (
        root
        / "apps"
        / "api"
        / "app"
        / "services"
        / "jurisdiction_registry.py"
    ).read_text(encoding="utf-8")

    # Definition + proposal path + review path.
    assert service.count(
        "_source_certification_lineage_filters("
    ) >= 3

    assert "superseded.official_source_id" in service
    assert (
        "!= certification.official_source_id"
        in service
    )


def test_0069_migration_preserves_primary_and_supplemental_invariants():
    root = Path(__file__).resolve().parents[3]

    migration = (
        root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0069_source_certification_multiplicity.py"
    ).read_text(encoding="utf-8")

    assert (
        'down_revision = "0068_external_validation_framework"'
        in migration
    )

    assert "uq_jsc_primary_scope_version" in migration
    assert (
        "uq_jsc_supplemental_source_scope_version"
        in migration
    )
    assert "uq_jsc_scope_version" in migration
    assert "official_source_id" in migration
