"""Harden source-certification multiplicity.

Revision ID: 0069_source_certification_multiplicity
Revises: 0068_external_validation_framework
"""

from alembic import op
import sqlalchemy as sa


revision = "0069_source_certification_multiplicity"
down_revision = "0068_external_validation_framework"
branch_labels = None
depends_on = None


_TABLE = "jurisdiction_source_certifications"

_OLD_CONSTRAINT = "uq_jsc_scope_version"

_PRIMARY_INDEX = "uq_jsc_primary_scope_version"

_SUPPLEMENTAL_INDEX = (
    "uq_jsc_supplemental_source_scope_version"
)


def upgrade() -> None:
    # The historical constraint treated every certification in the same
    # jurisdiction/domain as one version lineage. That prevents multiple
    # independently certified supplemental sources from coexisting.
    #
    # batch_alter_table keeps the constraint removal portable to SQLite.
    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.drop_constraint(
            _OLD_CONSTRAINT,
            type_="unique",
        )

    # Primary certification remains jurisdiction scoped.
    op.create_index(
        _PRIMARY_INDEX,
        _TABLE,
        [
            "jurisdiction_id",
            "certification_scope",
            "certification_version",
        ],
        unique=True,
        sqlite_where=sa.text(
            "certification_scope = 'primary_immigration'"
        ),
        postgresql_where=sa.text(
            "certification_scope = 'primary_immigration'"
        ),
    )

    # Supplemental certification is independently versioned per source.
    op.create_index(
        _SUPPLEMENTAL_INDEX,
        _TABLE,
        [
            "jurisdiction_id",
            "official_source_id",
            "certification_scope",
            "certification_version",
        ],
        unique=True,
        sqlite_where=sa.text(
            "certification_scope <> 'primary_immigration'"
        ),
        postgresql_where=sa.text(
            "certification_scope <> 'primary_immigration'"
        ),
    )


def downgrade() -> None:
    connection = op.get_bind()

    # Once multiple supplemental sources use the same version number,
    # restoring the historical scope-wide uniqueness would destroy valid
    # lineage semantics. Refuse such a downgrade instead of silently
    # rewriting certification history.
    collision = connection.execute(
        sa.text(
            """
            SELECT
                jurisdiction_id,
                certification_scope,
                certification_version,
                COUNT(*) AS row_count
            FROM jurisdiction_source_certifications
            GROUP BY
                jurisdiction_id,
                certification_scope,
                certification_version
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()

    if collision is not None:
        raise RuntimeError(
            "Cannot downgrade source-certification multiplicity: "
            "multiple source-scoped certifications now share a "
            "jurisdiction/scope/version."
        )

    op.drop_index(
        _SUPPLEMENTAL_INDEX,
        table_name=_TABLE,
    )

    op.drop_index(
        _PRIMARY_INDEX,
        table_name=_TABLE,
    )

    with op.batch_alter_table(_TABLE) as batch_op:
        batch_op.create_unique_constraint(
            _OLD_CONSTRAINT,
            [
                "jurisdiction_id",
                "certification_scope",
                "certification_version",
            ],
        )
