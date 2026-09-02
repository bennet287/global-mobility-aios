# V1.3-B.1 Minimal Governance Kernel — Canonical Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Implementation commit:** `d351ad85f5c3464178b56dd9da6ac5c83090a27a`  
**Disposition:** **COMPLETE / PASS / SEALED AS B.1 FOUNDATION**

## Purpose

This record closes the first V1.3-B slice after canonical Windows-checkout acceptance.

B.1 introduced the typed, deterministic Governance Kernel foundation while deliberately reusing the existing organization command and Activity infrastructure rather than creating a second command framework.

## Canonical acceptance evidence

Focused Governance Kernel suite:

```text
pytest apps/api/tests/test_organization_governance_kernel.py -q
19 passed, 1 warning in 0.16s
```

Repository policy:

```text
scripts/check_repo_policy.py --root .
Repository policy check passed.
```

Full API regression:

```text
pytest apps/api/tests -q
905 passed, 5 skipped, 1 warning in 325.63s (0:05:25)
```

Database migration integrity:

```text
Database migration check passed.
database_url=sqlite:///./gmai.db
migration_heads=0076_organization_position_active_identity
registered_tables=118
physical_schema=ok
database_revision=0076_organization_position_active_identity
```

Preserved local database schema parity:

```text
Local DB schema check passed.
database_url=sqlite:///D:/global-mobility-aios/gmai.db
registered_tables=118
actual_tables=118
physical_tables=119
infrastructure_tables=["alembic_version"]
```

Git integrity:

```text
git diff --check
# no output

git status -sb
## roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

## Accepted B.1 contracts

The accepted foundation includes:

- actor/tenant-bound `CapabilityAuthority`;
- capability/action/scope checks;
- A0–A5 autonomy routing;
- R0–R5 constitutional risk-floor enforcement;
- typed `MaterialAction` envelope;
- expected-version/precondition decisions;
- idempotency replay/conflict decisions;
- deterministic policy dispositions;
- Board-reserved action protection;
- trace identity;
- OrganizationActivity-compatible governance projection.

Government submission remains R5 and Board-reserved even when capability autonomy is A5.

## Warning disposition

The single warning is the pre-existing Starlette/httpx TestClient deprecation warning. It is not introduced by the Governance Kernel and remains a separate dependency-maintenance concern.

## Non-claims

B.1 acceptance does not claim:

- a production domain mutation has yet crossed the kernel;
- a new MaterialAction persistence table exists;
- Decision Readiness exists;
- independent verification exists;
- Organizational Immune System exists;
- full Transparency / Decision Lineage exists;
- GitHub CI PASS exists.

Those boundaries belong to later V1.3 slices.

## Next slice

V1.3-B.2 should prove the kernel against one real, reversible, low-risk existing organization command:

```text
Actor
→ MaterialAction
→ deterministic gateway
→ expected-version + idempotency
→ existing domain mutation
→ existing audit + semantic Activity
→ governance Activity / trace
→ one atomic commit
```

The selected first action is `work_item.assignment` (R1 / REVERSIBLE).
