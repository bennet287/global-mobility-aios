# V12.20 Acceptance Changelog — V1.3-I.1 Capability Autonomy Truth Foundation

**Date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** ACCEPTED / COMPLETE / PASS / SEALED  
**Accepted technical candidate:** `581df5d99b65f0a7a49ace228ee707b881d508fa`  
**Accepted Production Proof:** GitHub Actions run `32529241957`  
**Acceptance record:** `docs/V1_3_I1_CAPABILITY_AUTONOMY_PROFILE_ACCEPTANCE_2026-08-21.md`

This file retains its historical `PENDING_CHANGELOG` filename for continuity, but the I.1 delivery recorded here is now closed and accepted. The full code/runtime proof applies to the exact technical candidate above; later acceptance-documentation commits reconcile repository truth without pretending the full code suite reran on those docs-only SHAs.

## Implementation lineage

```text
746978b2c44956ee97d2eb52612285e6f855b860  docs: define I.1 autonomy profile foundation
ca14bce1649871df42cc25b20ee3b5ff26b2fcdd  feat: add I.1 capability autonomy truth foundation
4a533117c729df94f09f4f6d641505e44443a412  test: wire I.1 migration and PostgreSQL contracts
b34822d7a6af169f4be0410e179aa2be197513f0  docs: mark I.1 implementation acceptance pending
97315a58b311384ac095a983c406f5e02966ced3  docs: record I.1 implementation pending proof
395ec3548a3d3749baba4aff4f543445cac0e669  fix: verify autonomy profile fingerprints on read
1e5f7755a6afd7d01e5783c4b9c75cf2179f45ff  test: cover autonomy profile fingerprint drift
584a590550213df2106605f56c04249c555dc4a5  fix: order autonomy profile persistence before evidence
1114df38bbd8765c11d2f1bfdcfd2fbca65f065d  fix: reconcile Africa evidence pack receipt
d4516bbc4f9b2b579b2a799a7c5473fd21b59b3c  test: advance organization migration boundary to I.1
00d4443fb62ad3640930c124938c04cc478bbbae  fix: normalize evidence pack receipt hashing
8d2956802ab0960ce53e444c3a8a27dd554b921b  test: cover cross-platform evidence receipt hashing
88d9b8b42421b3fdd6b67192790d573df08c61e2  fix: restore canonical evidence pack receipt hash
68205518ff0751d8e34f0afa8e53924fd4ce9141  ci: prove exact PR head in production gate
27d77884f1c2e29e8153600d57c38266efd68f61  fix: make governed work preconditions monotonic
da4e9a9f333f4397ed4a78a46aac505aa53530ee  test: freeze governed work stale-version clock
581df5d99b65f0a7a49ace228ee707b881d508fa  docs: record governed work stale-version repair
607f9a746ca1d8486052d1ed081edafc0289d14a  docs: seal V1.3 I.1 autonomy profile foundation
```

## Canonical implementation

I.1 introduces two bounded companion models through the existing shared SQLModel registry:

```text
CapabilityAutonomyProfile
CapabilityAutonomyEvidence
```

The linear Alembic head advances from:

```text
0077_canonical_eligibility_assessment_revision
```

to:

```text
0078_capability_autonomy_profile_foundation
```

The profile truth is scoped by tenant, persistent `OrganizationPosition`, capability and context. It records explicit A0–A5 autonomy, an independent Board ceiling, authority requirement, R0–R5 risk ceiling, evidence-policy version, immutable supersession lineage, Board governance Activity identity, idempotency key and deterministic record fingerprint.

The evidence companion links a profile revision to canonical `OrganizationActivity` rows and captures the source Activity fingerprint observed when the Board decision was committed.

## Governance boundary

The canonical writer is HTTP-independent and requires:

```text
authenticated internal human
+ admin role
+ persistent Board position
+ active target OrganizationPosition
+ requested autonomy <= explicit Board ceiling
+ same-tenant canonical Activity evidence
```

The command stages the Board governance Activity, autonomy profile, evidence links and audit mutations in one transaction.

There is deliberately no I.1 `POST`, `PUT`, `PATCH` or `DELETE` autonomy route. Agents cannot invoke the canonical writer, and request JSON cannot self-select or promote autonomy.

Capability, authority, autonomy and risk remain separate. I.1 records autonomy truth; it does not mint `CapabilityAuthority`, replace the Command Gateway or weaken legal/professional/Board review floors.

## Append-only / replay / concurrency contract

The accepted implementation preserves prior profile rows unchanged and derives current/superseded lifecycle from the append-only chain.

Concurrency and replay protections include:

```text
expected_profile_sequence on an existing chain
PostgreSQL current-profile row lock where available
unique scope + profile_sequence
unique tenant + supersedes_profile_id
unique tenant + idempotency_key
exact semantic record fingerprint
exact evidence record fingerprint
```

Exact idempotent replay returns existing canonical truth. Divergent reuse of the same idempotency key fails closed.

Competing first-profile creation and stale cross-session supersession are exercised by real-PostgreSQL contract tests inside the existing `test_organization_eligibility_postgres_contract.py`, which is already part of the Production Proof PostgreSQL lane. No second PostgreSQL test framework or workflow is introduced.

### PostgreSQL persistence-order diagnostic and repair

The first focused PostgreSQL proof on candidate `331ac66e7c2319c5a05edd603dd55550938d31aa` successfully migrated a fresh PostgreSQL 16 database through `0078` and verified 121 registered tables with a matching physical schema, but both I.1 concurrency tests failed before their intended concurrency assertions.

The failure was a real PostgreSQL-only persistence-order defect: `CapabilityAutonomyEvidence` could be flushed before its parent `CapabilityAutonomyProfile`, causing `fk_cap_autonomy_evidence_profile_tenant` to reject the child row. The initial-profile race therefore produced two rejected writers, and the stale-supersession test could not establish its seed profile.

Commit `584a590550213df2106605f56c04249c555dc4a5` repairs only that ordering boundary. The command explicitly flushes the parent profile before queuing evidence rows. The Board decision Activity, parent profile, evidence rows and audit records still belong to the same caller-owned transaction; any later failure rolls the complete unit back. No schema, authority, autonomy or concurrency semantics changed.

The focused repair verification on candidate `fe0ca59242b22c1ad11478fa5f4a4f92ecf8b9af` then passed repository policy, release consistency, diff hygiene, Python compilation, all focused SQLite I.1 contracts and both real-PostgreSQL autonomy concurrency contracts.

## Full Production Proof diagnostics before acceptance

A full local proof on `fe0ca59242b22c1ad11478fa5f4a4f92ecf8b9af` exposed two repository-truth issues:

```text
1140 passed
12 skipped
2 failed
```

The failures were:

1. a platform-dependent raw-byte SHA receipt for `v10_22_2_africa_tranche_1A_ready_9.json`;
2. a stale architecture test that still forbade migration numbers beyond `0077`.

The migration-boundary test was advanced to require `0078`. The receipt path was hardened so canonical JSON hashing normalizes CRLF/CR to LF, and regression coverage proves LF and CRLF checkout representations validate against one canonical receipt. The evidence-pack JSON itself was not changed.

The first Python 3.12 exact-candidate local rerun on `02decd17fa52652c99dffdfccc90db74a3192b9d` also exposed that the ignored developer `.env` enabled the coverage-tranche assistant. Repository defaults and `.env.example` remained disabled, so subsequent local proof explicitly forced `COVERAGE_TRANCHE_ASSISTANT_ENABLED=false` to match the clean workflow environment.

GitHub Actions run `32525735708` then provided independent evidence that frontend and PostgreSQL were green while exposing the cross-platform evidence receipt and synthetic-merge diff-hygiene issues. Those gate issues were repaired before final acceptance.

### Exact-head CI hardening

The PR-triggered workflow previously checked GitHub's synthetic merge commit. Its `git diff --check HEAD^` therefore compared the entire long-lived V12 branch delta against `main` and surfaced unrelated historical whitespace instead of the acceptance candidate.

Commit `68205518ff0751d8e34f0afa8e53924fd4ce9141` makes every V12 Production Proof job check out `${{ github.event.pull_request.head.sha || github.sha }}`. Repository-policy checkout retains depth 2 so last-commit diff hygiene remains available.

### Governed WorkItem precondition monotonicity diagnostic

The final Python 3.12 Windows SQLite regression before acceptance reached one remaining failure after 1,142 tests passed and 12 were skipped. `test_stale_material_attempt_is_persisted_and_does_not_change_work` showed that a second command using the old WorkItem precondition could still receive `AUTO_EXECUTE` if the first assignment failed to advance the timestamp-derived token.

The governance kernel's stale-version comparison was correct. The defect was at the WorkItem mutation boundary: `_stage_assignment` assigned `updated_at = now_utc()` without guaranteeing strict advancement.

Commit `27d77884f1c2e29e8153600d57c38266efd68f61` makes successful assignment timestamps monotonic: wall-clock time is used when later than the previous value; otherwise the canonical timestamp advances by one microsecond.

Commit `da4e9a9f333f4397ed4a78a46aac505aa53530ee` freezes the service clock at the original timestamp and proves the invariant deterministically.

Focused Python 3.12 verification on accepted candidate `581df5d99b65f0a7a49ace228ee707b881d508fa` completed with:

```text
11 passed / 1 warning / 0 failed
repository policy                 PASS
release consistency               PASS — 0078
```

The local shell subsequently printed Git diff usage because the PowerShell diff command form was invalid. That command is not used as acceptance evidence. Exact-head GitHub Production Proof independently passed the canonical diff-hygiene step.

## Accepted Production Proof

The exact technical candidate `581df5d99b65f0a7a49ace228ee707b881d508fa` passed GitHub Actions run `32529241957` across all four required lanes:

```text
Repository policy and constraints        PASS
Backend regression (SQLite)              PASS
Frontend tests, types and build          PASS
PostgreSQL governance contracts          PASS
```

All four jobs explicitly checked out the exact candidate SHA.

Accepted backend evidence:

```text
Python                                    3.12
full SQLite regression                    1143 passed / 12 skipped / 1 warning / 0 failed
Alembic SQLite                            0001 -> 0078 PASS
migration head                            0078_capability_autonomy_profile_foundation
registered SQLModel tables                121
physical schema                           PASS
local schema contract                     PASS
```

Accepted PostgreSQL evidence:

```text
PostgreSQL                                16
Alembic PostgreSQL                        0001 -> 0078 PASS
migration head                            0078_capability_autonomy_profile_foundation
registered SQLModel tables                121
physical schema                           PASS
governed eligibility/autonomy suite       95 passed / 1 warning / 0 failed
competing initial-profile writers         PASS
stale cross-session supersession          PASS
```

Accepted frontend/repository evidence:

```text
Node                                      24
npm install/audit                         PASS — 0 vulnerabilities
design foundation                         PASS — 28/28
request/auth                              PASS — 4/4
TypeScript                                PASS
Next.js 16.3.1 production build           PASS
compiled auth                             PASS
repository policy                         PASS
release consistency                       PASS — 0078
Python dependency constraints             PASS
diff hygiene                              PASS
```

The known Pydantic `model_metadata_json` protected-namespace warning remains visible and non-blocking.

## Board / Cockpit transparency

The existing Board-only transparency facade includes:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}?context_scope=...
```

The read model validates:

```text
contiguous profile sequence
exact profile supersession chain
exact decision-Activity supersession chain
autonomy <= Board ceiling
valid autonomy/risk tiers
fixed Human Board governance source
decision Activity type/source/version identity
deterministic evidence ordering
source Activity fingerprint continuity
evidence record fingerprint integrity
profile semantic record fingerprint integrity
```

The API returns the current profile plus revision/evidence history without exposing raw Activity payload JSON.

## Accepted test surface

Acceptance now includes contract coverage for:

- Human Board-only establishment;
- agent self-promotion refusal;
- Board ceiling enforcement;
- exact idempotent replay;
- divergent idempotency conflict;
- append-only v1→v2 supersession;
- deterministic evidence lineage;
- fail-closed evidence Activity fingerprint drift;
- fail-closed profile semantic fingerprint drift even when the mutated value remains otherwise valid;
- Board-only read API;
- absence of an autonomy write API;
- migration head `0078`;
- PostgreSQL competing initial-profile creation;
- PostgreSQL stale cross-session supersession rejection;
- cross-platform LF/CRLF stability for canonical JSON evidence-pack receipts;
- deterministic monotonic WorkItem precondition advancement under a frozen clock.

## Explicit non-claims

I.1 acceptance does not claim:

- automatic autonomy promotion;
- automatic dynamic downgrade;
- a Dynamic Autonomy Manager;
- agent self-grading or self-promotion as permission;
- provider/model-specific autonomy grants;
- a single organization-wide autonomy score;
- confidence or score as permission;
- replacement of the Command Gateway;
- weakening of human/professional/legal/Board review floors;
- completion of the wider Earned Autonomy stage;
- completion of the future Organizational Immune System.

The accepted V1.3 technical baseline is now I.1, with H.2.4 and the H.2.2 runtime-health classification refinement preserved as sealed parent checkpoints.
