# Global Mobility AIOS — V1.3-H.1 Production Proof Gate

**Date:** 2026-08-20  
**Accepted:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** ACCEPTED / GREEN  
**Acceptance candidate:** `0b19d61a417de2d372e101d4e132a6a0a6c2a84f`  
**GitHub Actions run:** `32463849415`  
**H.1 seal:** ACCEPTED / SEALED  
**H.2:** BLOCKED pending required-check enforcement verification

## 1. Why this gate exists

Global Mobility AIOS has reached a point where governance sophistication is advancing faster than automated production proof.

The corrective principle is:

> **Do not add another architectural safety concept while the current safety invariants are not continuously proven.**

The immediate sequence was therefore:

```text
H.1 seal paused
→ consolidate canonical eligibility-lineage invariant
→ adversarial regression
→ full application regression
→ real PostgreSQL governance contracts
→ frontend build/type/test proof
→ repository/dependency hygiene proof
→ accept H.1
→ verify required-check enforcement
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

H.1 was not accepted merely because valid fixtures passed.

Adversarial tests deliberately corrupt durable committed lineage, including:

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

Historical G.3/G.4 replay also fails closed when the same canonical lineage contract is violated.

## 4. Repository hygiene contract

The accidental tracked file:

```text
apps/api/=5.4
```

was shell/Powershell redirection output rather than product source and has been removed.

Repository policy rejects suspicious tracked artifact filenames beginning with redirection-like markers such as:

```text
=...
<...
>...
```

The existing content-policy scan coverage remains intact.

Cross-platform production proof additionally exposed two stale SHA-256 receipt files whose values reflected Windows checkout bytes rather than canonical Git blob bytes. A complete audit checked 20 receipt-bearing evidence packs, found exactly two stale receipts, and corrected only those receipt files. The evidence JSON was unchanged and SHA validation was not weakened.

## 5. Python dependency reproducibility

`apps/api/requirements.txt` remains the direct dependency declaration surface.

An explicit direct-dependency constraint baseline exists at:

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

> **This is a direct-dependency reproducibility baseline, not a complete transitive lock.**

The accepted deterministic backend candidate passed constraint validation, constrained installation, `pip check`, application import and the full backend suite.

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

The accepted frontend lane uses Node 24 and proves:

```text
npm ci
npm audit --audit-level=high
design-foundation Node tests
request/auth Node tests
TypeScript --noEmit
Next.js production build
compiled-auth Node tests
```

The accepted frontend dependency baseline is:

```text
next=16.3.1
react=19.0.8
react-dom=19.0.8
```

The final audit reports zero vulnerabilities.

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

The workflow exists and has executed successfully, but a workflow file alone does not make checks branch-protection-required.

H.1 acceptance distinguishes:

```text
CI workflow exists and executes successfully
```

from:

```text
repository rules require those checks before protected-branch integration
```

The first condition is proven. The second condition has not been verified from GitHub repository rules/settings and is explicitly retained as a remaining repository-settings action.

No claim is made that branch protection or a ruleset currently requires these checks.

## 9. H.1 acceptance gate — SATISFIED

H.1 was accepted on 2026-08-21 after the following conditions were proven:

1. canonical eligibility-lineage focused tests — PASS;
2. H.1 adversarial identity-corruption tests — PASS;
3. G.3 and G.4 historical replay regression through the shared validator — PASS;
4. full backend regression — PASS;
5. migration and local schema checks — PASS;
6. frontend Node tests — PASS;
7. TypeScript check — PASS;
8. production Next.js build — PASS;
9. PostgreSQL migration upgrade — PASS;
10. focused PostgreSQL governance contracts — PASS;
11. repository policy with the accidental artifact removed — PASS;
12. Python constraint enforcement — PASS;
13. acceptance candidate and evidence record synchronization — PASS;
14. required-check enforcement — explicitly recorded as the remaining repository-settings action, as permitted by this gate.

Accepted deterministic backend evidence includes:

```text
1105 passed
7 skipped
1 warning
0 failed
```

Accepted fresh PostgreSQL 16 evidence includes:

```text
Alembic 0001 → 0077              PASS
registered tables                 119
physical schema                   PASS
governed eligibility/H.1 suite    57 passed / 1 warning / 0 failed
```

Accepted local frontend evidence includes:

```text
npm ci                            PASS
npm audit --audit-level=high      PASS — 0 vulnerabilities
design foundation                 28/28 PASS
request/auth                      4/4 PASS
TypeScript                        PASS
Next.js production build          PASS
compiled auth                     PASS
```

Final GitHub-hosted acceptance run:

```text
candidate = 0b19d61a417de2d372e101d4e132a6a0a6c2a84f
run       = 32463849415

Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

Detailed acceptance evidence is preserved in:

```text
docs/V1_3_H1_ACCEPTANCE_2026-08-21.md
```

## 10. H.2 entry condition

H.1 is now accepted and the Production Proof Gate is green, but the roadmap retains one stricter repository-governance prerequisite before H.2 begins:

```text
verify required GitHub check enforcement
```

Current transition state:

```text
H.1 canonical lineage repair        ACCEPTED / SEALED
Production Proof Gate               ACCEPTED / GREEN
Required-check enforcement          NOT VERIFIED
H.2                                 BLOCKED
```

Only after required-check enforcement is verified should work proceed into H.2 production transition guardrails, recurrence thresholds, anomaly aggregation, broader blast-radius policy or additional Immune System capabilities.

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
