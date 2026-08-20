# Global Mobility AIOS — V1.3-H.1 Production Proof Gate

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING  
**Accepted baseline remains:** V1.3-G.5  
**H.1 seal:** PAUSED pending proof below  
**H.2:** BLOCKED until this gate is accepted

## 1. Why this gate exists

Global Mobility AIOS has reached a point where governance sophistication is advancing faster than automated production proof.

The corrective principle is:

> **Do not add another architectural safety concept while the current safety invariants are not continuously proven.**

The immediate sequence is therefore:

```text
H.1 seal paused
→ consolidate canonical eligibility-lineage invariant
→ adversarial regression
→ full application regression
→ real PostgreSQL governance contracts
→ frontend build/type/test proof
→ repository/dependency hygiene proof
→ accept H.1
→ only then begin H.2
```

This is not a rollback of the V1.3 architecture. It is a shift in delivery priority from adding concepts to proving the concepts already implemented.

## 2. Canonical eligibility-lineage consolidation

The repository previously reconstructed overlapping durable-lineage invariants independently in:

```text
G.3 canonical-effect replay
G.4 orchestration replay
H.1 immune-system preflight
```

That created invariant-drift risk. In particular, an H.1 lineage check could prove that a row existed and was causally connected without proving that the row represented the expected eligibility Activity kind.

The canonical contract is now owned by:

```text
apps/api/app/services/organization_eligibility_lineage.py
```

Primary entry points:

```text
validate_canonical_eligibility_lineage(...)
canonical_eligibility_lineage_for_governance(...)
validate_canonical_eligibility_aggregate_lineage(...)
```

The validator is intentionally domain-specific. It is not a generic workflow/lineage framework.

It validates, as applicable:

- tenant identity;
- stable eligibility aggregate identity;
- revision version/lifecycle;
- contiguous aggregate revision sequence;
- single latest ACTIVE revision;
- predecessor/supersession identity;
- assessment ↔ revision identity;
- pathway version and stable pathway identity;
- exact independent-verification Activity type;
- exact verification-floor Activity type;
- canonical governance record kind;
- exact semantic eligibility-effect Activity type;
- MATERIAL constitutional lineage classification;
- source object type/id/version identity;
- action, intent, readiness, verification, verification-floor and effect fingerprints;
- expected prior revision fields;
- semantic revision/effect/source identity;
- E.2 → G.1 → G.2 → G.3 → semantic causation.

G.3 replay, G.4 replay and H.1 preflight now consume this shared contract and retain only their caller-specific checks.

Permanent rule:

> **Canonical eligibility lineage has one domain contract. Replay, orchestration and the Immune System may not redefine it independently.**

## 3. Adversarial regression contract

H.1 must not be accepted merely because valid fixtures pass.

Adversarial tests now deliberately corrupt durable committed lineage, including:

```text
verification Activity type
verification-floor Activity type
governance record kind
semantic Activity type
assessment/revision identity
semantic source revision identity
missing semantic lineage
invalid aggregate lifecycle
```

For fresh governed execution after a structural corruption, the required H.1 behavior is:

```text
shared canonical validator detects corruption
→ CRITICAL immune incident
→ aggregate-scoped circuit OPEN
→ producer provider calls = 0
→ verifier provider calls = 0
→ governed execution remains blocked
```

Historical G.3/G.4 replay must also fail closed when the same canonical lineage contract is violated.

## 4. Repository hygiene contract

The accidental tracked file:

```text
apps/api/=5.4
```

was shell/Powershell redirection output rather than product source and has been removed.

Repository policy now rejects suspicious tracked artifact filenames beginning with redirection-like markers such as:

```text
=...
<...
>...
```

The existing content-policy scan coverage remains intact.

## 5. Python dependency reproducibility

`apps/api/requirements.txt` remains the direct dependency declaration surface.

A new explicit direct-dependency constraint baseline exists at:

```text
apps/api/constraints.txt
```

Install contract:

```text
python -m pip install -r apps/api/requirements.txt -c apps/api/constraints.txt
```

The API Docker image uses the same constraint file.

Repository automation checks that every direct requirement has exactly one matching exact-version constraint and that no orphan direct constraints exist.

Current claim boundary:

> **This is a direct-dependency reproducibility baseline, not yet a complete transitive lock.**

A future transitive lock may be introduced after the constrained baseline is proven across supported Python/PostgreSQL environments. H.1 acceptance does not depend on inventing a second package-management system.

## 6. CI production-proof workflow

Workflow:

```text
.github/workflows/v12-production-proof.yml
```

It runs on:

```text
push → main
push → roadmap/**
pull_request
```

The workflow contains four independent proof lanes.

### 6.1 Repository policy and constraints

Proves:

```text
repository policy
release consistency
direct Python dependency constraints
diff whitespace hygiene
```

### 6.2 Backend regression — SQLite

Proves the existing broad hermetic regression surface:

```text
constrained dependency install
Python source compilation
full apps/api/tests pytest suite
migration consistency
local schema contract
```

SQLite remains useful for fast broad regression. It is not treated as sufficient production database proof.

### 6.3 Frontend tests, types and build

Proves the current frontend surface without pretending browser E2E already exists:

```text
npm ci
design-foundation Node tests
request/auth Node tests
TypeScript --noEmit
Next.js production build
compiled-auth Node tests
```

Playwright/browser golden-journey coverage remains a follow-on production-proof requirement before aggressive frontend decomposition.

### 6.4 PostgreSQL governance contracts

Uses a real PostgreSQL 16 service and first upgrades the isolated database through the canonical Alembic head.

The focused suite exercises the governed eligibility vertical and H.1 using the same pytest fixtures against PostgreSQL rather than maintaining a parallel test framework.

It includes cross-session contracts for:

- stale reassessment after another session commits the next canonical revision;
- zero-provider-call stale rejection;
- circuit OPEN visibility across sessions;
- authorized circuit recovery;
- a later critical incident reopening the aggregate;
- replay of an older recovery being unable to override the later OPEN state.

The broader focused PostgreSQL lane also executes existing G.3/G.4/G.5/H.1 idempotency, supersession, rollback and lineage tests.

## 7. Test database contract

Normal tests continue to default to:

```text
SQLite + StaticPool
```

Focused real-database tests set:

```text
GMAI_TEST_DATABASE_URL=postgresql+psycopg://...
```

The shared pytest fixture then runs the same model/test machinery against the explicitly supplied isolated PostgreSQL database.

Migration correctness is checked before the focused test fixture resets its isolated test schema. This keeps two questions separate:

```text
Can Alembic produce the expected PostgreSQL schema?
Can the governed services satisfy their behavioral contracts on PostgreSQL?
```

## 8. CI enforcement versus CI existence

The workflow is now repository code, but a workflow file alone does not make checks branch-protection-required.

H.1 acceptance therefore distinguishes:

```text
CI workflow exists and executes
```

from:

```text
repository rules require those checks before protected-branch integration
```

The second condition must be verified from GitHub repository rules/settings before it is claimed as mandatory enforcement.

## 9. H.1 acceptance gate

H.1 remains **IMPLEMENTED / ACCEPTANCE PENDING** until all of the following are true:

1. canonical eligibility-lineage focused tests pass;
2. H.1 adversarial identity-corruption tests pass;
3. G.3 and G.4 historical replay regression passes through the shared validator;
4. full backend regression passes;
5. migration and local schema checks pass;
6. frontend Node tests pass;
7. TypeScript check passes;
8. production Next.js build passes;
9. PostgreSQL migration upgrade passes;
10. focused PostgreSQL governance contracts pass;
11. repository policy passes with the accidental artifact removed;
12. Python constraint enforcement passes;
13. branch/head and documentation state are synchronized;
14. GitHub-required-check enforcement is either verified or explicitly recorded as a remaining repository-settings action.

No test count or PASS status is recorded here until the command/workflow actually runs.

## 10. H.2 entry condition

H.2 must not start simply because H.1 code exists.

Entry condition:

```text
H.1 canonical lineage repair accepted
+ production-proof gate green
+ repository truth reconciled
→ H.2 may begin
```

Only after that should work proceed into recurrence thresholds, anomaly aggregation, broader blast-radius policy or additional Immune System capabilities.

## 11. Decomposition sequencing

Large-file concentration remains a maintainability risk, but decomposition is intentionally sequenced after proof infrastructure.

Do not simultaneously refactor:

```text
organization_governance.py
domain.py
api.ts
globals.css
```

First extraction priorities after the proof gate are semantic seams, not arbitrary line-count chunks:

- model modules by bounded context while retaining one SQLModel metadata registry and one linear Alembic lineage/head;
- frontend API modules by product/domain behind one common request/auth client;
- CSS tokens/primitives/layout/features incrementally;
- browser golden journey before aggressive frontend restructuring.

Permanent rule:

> **Improve the ability to detect regressions before increasing the surface area of refactoring.**
