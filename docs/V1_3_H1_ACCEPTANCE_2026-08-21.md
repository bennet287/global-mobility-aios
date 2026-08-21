# Global Mobility AIOS — V1.3 H.1 Acceptance Record

**Acceptance date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Acceptance candidate:** `0b19d61a417de2d372e101d4e132a6a0a6c2a84f`  
**GitHub Actions run:** `32463849415`  
**H.1 status:** ACCEPTED / SEALED  
**Production Proof Gate:** ACCEPTED / GREEN  
**H.2 status:** BLOCKED pending required-check enforcement verification

## 1. Acceptance decision

V1.3 H.1 is accepted and sealed.

The acceptance is based on converged proof across:

- one shared canonical eligibility-lineage contract used by G.3, G.4 and H.1;
- adversarial durable-lineage corruption regression;
- full deterministic constrained backend regression;
- fresh PostgreSQL 16 migration, physical-schema and governed H.1 proof;
- frontend dependency-security repair and reproducible install;
- frontend design, request/auth, TypeScript, production-build and compiled-auth proof;
- repository policy, release consistency, dependency-constraint and diff-hygiene proof;
- a complete GitHub-hosted Linux Production Proof workflow with all four jobs green.

This acceptance does not weaken the permanent safety rule:

> **Agents may be wrong while thinking; AIOS may not be wrong silently when committing truth.**

The H.1 Immune System remains restrictive only. It may block, open circuits and require recovery authority; it does not grant authority, autonomy or permission.

## 2. Canonical lineage contract

Canonical eligibility lineage is owned by:

```text
apps/api/app/services/organization_eligibility_lineage.py
```

G.3 replay, G.4 replay and H.1 preflight delegate to the shared domain contract rather than reconstructing overlapping durable-lineage invariants independently.

The canonical aggregate identity remains:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

The validator proves tenant, aggregate, revision/lifecycle, supersession, pathway, independent-verification, verification-floor, governance, semantic activity, source identity, fingerprints and causal ancestry appropriate to the caller.

## 3. Deterministic backend proof

The exact constrained Python runtime was successfully installed and integrity-checked on CPython 3.13.12.

Key direct candidates included:

```text
fastapi=0.115.0
starlette=0.38.6
pydantic=2.8.0
sqlmodel=0.0.22
alembic=1.13.0
PyYAML=6.0.3
clamd=1.0.2
psycopg=3.2.2
psycopg-binary=3.2.2
pytest=8.3.0
```

Dependency proof:

```text
Python dependency constraints: PASS (25 direct dependencies)
pip check: PASS — No broken requirements found
```

Full constrained backend result:

```text
1105 passed
7 skipped
1 warning
0 failed
536.28s
```

The remaining warning is the known Pydantic 2.8 protected-namespace warning for `model_metadata_json`. It is visible, non-silent and non-blocking because it did not affect application import, route registration, persistence or any passing backend contract.

## 4. Fresh PostgreSQL 16 proof

A fresh empty PostgreSQL 16 database was migrated through the complete Alembic sequence ending at:

```text
0077_canonical_eligibility_assessment_revision
```

Fresh physical-schema proof:

```text
migration_heads=0077_canonical_eligibility_assessment_revision
registered_tables=119
physical_schema=ok
database_revision=0077_canonical_eligibility_assessment_revision
```

The governed eligibility/H.1 suite then ran on the same fresh PostgreSQL database:

```text
57 passed
1 warning
0 failed
973.50s
```

The earlier PostgreSQL identifier-length defect was corrected with explicit bounded index names; the fresh migration proved that repair.

## 5. Canonical evidence-receipt portability proof

The production-proof correction exposed two text evidence receipts whose SHA-256 values reflected Windows checkout bytes rather than canonical Git blob bytes.

A complete Git-blob audit checked 20 receipt-bearing evidence packs and found exactly two stale receipts:

```text
v10_22_2_africa_tranche_1A_ready_9.json
canonical SHA-256 = e7527b1ea84fca60c0afde49d5b6f0c48a22e6d9207305cd2c1fcecebc970db4

v10_22_3_botswana_supplemental_source.json
canonical SHA-256 = 546343546f7112e8d6b2c59abda1f7a06563ae3a14e7da4863d884098d0c31a2
```

Only the stale receipt files were corrected. The evidence JSON was not changed and SHA validation was not weakened.

The subsequent GitHub-hosted Linux backend lane passed, closing the cross-platform receipt-integrity defect.

## 6. Frontend security and production proof

The old frontend baseline (`next 15.2.4`, `react 19.0.0`, `react-dom 19.0.0`) was not accepted because current audit evidence contained high/critical vulnerabilities.

An intermediate Next 15.5.21 candidate still produced high-severity findings through `nanoid`, `postcss` and `sharp`, so the security gate remained closed.

The bounded accepted frontend dependency candidate is:

```text
next=16.3.1
react=19.0.8
react-dom=19.0.8
postcss=8.5.23
sharp=0.35.3
nanoid=3.3.18
```

Local production proof on Node 24.18.0 / npm 11.16.0 established:

```text
npm ci                         PASS
npm audit --audit-level=high   PASS — 0 vulnerabilities
design foundation              PASS — 28/28
request/auth                   PASS — 4/4
TypeScript                     PASS
Next.js production build       PASS
compiled auth                  PASS
git diff --check               PASS
```

Next 16 generated TypeScript/route-type configuration was accepted, and the removed `next lint` command was not retained as a knowingly invalid package script.

## 7. GitHub-hosted Production Proof — final green run

Workflow:

```text
.github/workflows/v12-production-proof.yml
```

Final acceptance candidate:

```text
0b19d61a417de2d372e101d4e132a6a0a6c2a84f
```

GitHub Actions run:

```text
32463849415
```

All four independent jobs completed with `success`:

```text
Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

The frontend job passed every required step:

```text
checkout                            PASS
Node 24 setup                       PASS
npm ci                              PASS
high-severity dependency audit      PASS
design-foundation tests             PASS
request/auth tests                  PASS
TypeScript --noEmit                 PASS
Next.js production build            PASS
compiled auth                       PASS
```

The final Node 24 workflow correction was required because the previous GitHub run explicitly installed Node 20.20.2 while `test:request-auth` uses `--experimental-strip-types`. That previous run had already proven `npm ci`, zero-vulnerability audit and all 28 design tests before failing at the runtime-incompatible Node flag. The final run aligns CI with the proven frontend runtime and closes that mismatch.

## 8. Production-proof defects retained as evidence

The proof process intentionally did not hide failed candidates. It exposed and corrected, among other things:

- PostgreSQL persisted-governance representation mismatch (`AUTO_EXECUTE`);
- PostgreSQL-invalid adversarial fixture construction;
- stale replay assertion wording;
- PostgreSQL 63-byte index-name violation in migration `0077`;
- invalid extras syntax in constraints;
- wheel/build incompatibilities for PyYAML, clamd and psycopg candidates;
- invalid body-bearing FastAPI HTTP 204 route contract;
- expanded repository-policy false positive against declared reference-only vendor content;
- stale Windows-vs-Git evidence SHA receipts;
- vulnerable Next/React frontend baseline;
- GitHub shallow-checkout `HEAD^` diff-hygiene defect;
- Node 20 versus Node 24 frontend proof-runtime mismatch.

Acceptance is therefore based on corrected production behavior and reproducible proof, not on suppressing failures.

## 9. Acceptance checklist disposition

The H.1 Production Proof Gate is satisfied as follows:

1. canonical eligibility-lineage focused tests — PASS;
2. H.1 adversarial identity-corruption tests — PASS;
3. G.3/G.4 historical replay through shared validator — PASS;
4. full backend regression — PASS;
5. migration/local schema checks — PASS;
6. frontend Node tests — PASS;
7. TypeScript check — PASS;
8. production Next.js build — PASS;
9. fresh PostgreSQL migration upgrade — PASS;
10. focused PostgreSQL governance contracts — PASS;
11. repository policy — PASS;
12. Python constraint enforcement — PASS;
13. acceptance candidate and evidence record synchronized — PASS;
14. required-check enforcement — **explicitly recorded as the remaining repository-settings action**.

Item 14 follows the gate's own acceptance rule: enforcement may be verified before H.1 acceptance or explicitly recorded as a remaining repository-settings action. No claim is made that GitHub branch protection or rulesets currently require the checks.

## 10. Repository-settings action and H.2 boundary

The available GitHub connector evidence does not expose repository branch-protection/ruleset configuration sufficiently to prove required-check enforcement.

Therefore the current truth is:

```text
Production Proof workflow exists             YES
Production Proof workflow executes           YES
Final four-lane candidate is green            YES
Required-check enforcement in repo settings   NOT VERIFIED
```

The roadmap's stricter H.2 sequencing is preserved:

```text
H.1 ACCEPTED / SEALED
+ Production Proof ACCEPTED / GREEN
+ verify required GitHub check enforcement
→ only then begin H.2 production transition guardrails
```

Accordingly:

```text
H.1 = ACCEPTED / SEALED
Production Proof Gate = ACCEPTED / GREEN
H.2 = BLOCKED pending required-check enforcement verification
```

No H.2 implementation is authorized by this acceptance record alone.
