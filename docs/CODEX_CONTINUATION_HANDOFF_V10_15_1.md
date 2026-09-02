# Codex Continuation Handoff v10.15.1

## Hotfix

Migration `0030_global_coverage_evidence_batches` used two explicit index names longer than PostgreSQL's 63-character identifier limit. SQLite accepted them, while PostgreSQL rejected the migration before the API could start.

The migration now wraps convention-generated index names with `op.f(...)`, allowing SQLAlchemy to apply deterministic PostgreSQL-safe truncation while preserving metadata parity.

## Safety

PostgreSQL transactional DDL means the failed `0030` attempt does not leave a partially applied migration. Apply this hotfix, rebuild the API migration image, and run `alembic upgrade head`. The expected final head remains `0030_global_coverage_evidence_batches`.

## Regression coverage

An offline PostgreSQL `alembic upgrade head --sql` compilation test now catches overlong identifiers without requiring a live PostgreSQL server. `docs/ROADMAP.md` was updated in this patch.
