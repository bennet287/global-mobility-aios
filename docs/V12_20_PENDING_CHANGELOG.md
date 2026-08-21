# V12.20 Pending Changelog — V1.3-I.1 Capability Autonomy Truth Foundation

**Date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING

This record captures the I.1 implementation state without claiming COMPLETE / PASS / SEALED before the exact candidate passes V12 Production Proof.

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
```

The final acceptance candidate is intentionally not named yet because this pending record itself advances the branch head and must be included in the exact-candidate proof.

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

The profile truth is scoped by tenant, persistent OrganizationPosition, capability and context. It records explicit A0–A5 autonomy, an independent Board ceiling, authority requirement, R0–R5 risk ceiling, evidence-policy version, immutable supersession lineage, Board governance Activity identity, idempotency key and deterministic record fingerprint.

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

The command stages the Board governance Activity, autonomy profile and evidence links in one transaction.

There is deliberately no I.1 POST/PUT/PATCH/DELETE autonomy route. Agents cannot invoke the canonical writer, and request JSON cannot self-select or promote autonomy.

Capability, authority, autonomy and risk remain separate. I.1 records autonomy truth; it does not mint `CapabilityAuthority`, replace the Command Gateway or weaken legal/professional/Board review floors.

## Append-only / replay / concurrency contract

The implementation preserves prior profile rows unchanged and derives current/superseded lifecycle from the append-only chain.

Concurrency and replay protections include:

```text
expected_profile_sequence on an existing chain
PostgreSQL current-profile row lock where available
unique scope + profile_sequence
unique tenant + supersedes_profile_id
unique tenant + idempotency_key
exact semantic record fingerprint
```

Exact idempotent replay returns the existing canonical profile. Divergent reuse of the same idempotency key fails closed.

Competing first-profile creation and stale cross-session supersession are exercised by real-PostgreSQL contract tests inside the existing `test_organization_eligibility_postgres_contract.py`, which is already part of the Production Proof PostgreSQL lane. No second PostgreSQL test framework or workflow is introduced.

### PostgreSQL persistence-order diagnostic and repair

The first focused PostgreSQL proof on candidate `331ac66e7c2319c5a05edd603dd55550938d31aa` successfully migrated a fresh PostgreSQL 16 database through `0078` and verified 121 registered tables with a matching physical schema, but both I.1 concurrency tests failed before their intended concurrency assertions.

The failure was a real PostgreSQL-only persistence-order defect: `CapabilityAutonomyEvidence` could be flushed before its parent `CapabilityAutonomyProfile`, causing `fk_cap_autonomy_evidence_profile_tenant` to reject the child row. The initial-profile race therefore produced two rejected writers, and the stale-supersession test could not establish its seed profile.

Commit `584a590550213df2106605f56c04249c555dc4a5` repairs only that ordering boundary. The command now explicitly flushes the parent profile before queuing evidence rows. The Board decision Activity, parent profile, evidence rows and audit records still belong to the same caller-owned transaction; any later failure rolls the complete unit back. No schema, migration, authority, autonomy or concurrency semantics changed.

The focused repair verification on candidate `fe0ca59242b22c1ad11478fa5f4a4f92ecf8b9af` then passed repository policy, release consistency, diff hygiene, Python compilation, all four focused SQLite I.1 contracts, and both real-PostgreSQL autonomy concurrency contracts.

## Full Production Proof diagnostic

The next full local Production Proof attempt confirmed candidate `fe0ca59242b22c1ad11478fa5f4a4f92ecf8b9af` and passed repository policy, release consistency, Python dependency constraints and diff hygiene.

The local virtual environment was Python 3.13.12, while the canonical GitHub Production Proof workflow provisions Python 3.12. That environment mismatch is not treated as an application defect and cannot by itself provide exact CI-runtime parity.

The full SQLite backend regression completed with:

```text
1140 passed
12 skipped
2 failed
```

Both failures were repository-truth drift outside the I.1 command implementation:

1. `test_coverage_evidence_packs.py` detected that the tracked receipt for `v10_22_2_africa_tranche_1A_ready_9.json` still declared SHA-256 `e7527b1e...`, while the Windows checkout calculated `59e16db2...` from raw bytes. Commit `1114df38bbd8765c11d2f1bfdcfd2fbca65f065d` temporarily reconciled the receipt to that Windows byte representation.
2. `test_organization_records_api.py` still encoded the pre-I.1 architecture ceiling by asserting that no numbered migration may exceed `0077`. Commit `d4516bbc4f9b2b579b2a799a7c5473fd21b59b3c` now explicitly requires `0078_capability_autonomy_profile_foundation.py` and forbids migrations beyond `0078`.

The same run independently passed the SQLite migration consistency and local physical-schema contracts at migration head `0078`, with 121 registered/application tables and the expected Alembic infrastructure table.

Frontend Production Proof steps completed successfully on Node 24, including dependency installation/audit, design-foundation tests, request/auth tests, TypeScript, production build and compiled-auth verification. The PostgreSQL governance lane had started on a fresh healthy PostgreSQL 16 instance when the captured output ended; no result from that local full governed PostgreSQL suite is claimed from that transcript.

### Cross-platform receipt and exact-candidate CI hardening

The first Python 3.12 exact-candidate local rerun on `02decd17fa52652c99dffdfccc90db74a3192b9d` passed repository policy and constraints but stopped in the SQLite lane with two local feature-flag assertions because the ignored developer `.env` enabled the coverage-tranche assistant. Repository defaults and `.env.example` remain disabled; subsequent local proof must explicitly force `COVERAGE_TRANCHE_ASSISTANT_ENABLED=false` to match the clean workflow environment.

GitHub Actions run `32525735708` on the same PR state provided independent clean-environment evidence:

```text
Frontend tests, types and build: PASS
PostgreSQL governance contracts: PASS
Backend regression (SQLite): FAIL — evidence receipt only
Repository policy and constraints: FAIL — PR synthetic-merge diff hygiene only
```

The GitHub Linux checkout calculated canonical LF bytes for `v10_22_2_africa_tranche_1A_ready_9.json` as SHA-256 `e7527b1e...`, while the existing Windows working tree calculated `59e16db2...` from CRLF bytes. Raw-byte hashing of a tracked JSON text file was therefore platform-dependent. Commit `00d4443fb62ad3640930c124938c04cc478bbbae` now normalizes JSON CRLF/CR line endings to LF before receipt hashing. Commit `8d2956802ab0960ce53e444c3a8a27dd554b921b` adds a regression contract proving LF and CRLF representations validate against the same receipt. Commit `88d9b8b42421b3fdd6b67192790d573df08c61e2` restores the receipt to the canonical normalized hash `e7527b1e...`; the evidence-pack content remains unchanged.

The PR-triggered workflow previously checked GitHub's synthetic merge commit. Its `git diff --check HEAD^` therefore compared the entire long-lived V12 branch delta against `main` and surfaced unrelated historical whitespace instead of the exact acceptance candidate. Commit `68205518ff0751d8e34f0afa8e53924fd4ce9141` makes every V12 Production Proof job check out `${{ github.event.pull_request.head.sha || github.sha }}` so pull-request and push runs prove the exact candidate head. Repository-policy checkout still uses depth 2 so last-commit diff hygiene remains available.

These gate hardenings do not change I.1 authority, autonomy, schema or runtime semantics. Because they advance the branch head, I.1 remains ACCEPTANCE PENDING until the post-hardening exact candidate is green.

## Board / Cockpit transparency

The existing Board-only transparency facade now includes:

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

The profile fingerprint is recomputed from persisted tenant/scope/autonomy/ceiling/authority/risk/policy/governance/idempotency/evidence semantics on every Board read. This closes the gap where a direct database mutation that remained under the Board ceiling could otherwise have escaped the simpler ceiling-only integrity check.

The API returns the current profile plus revision/evidence history without exposing raw Activity payload JSON.

## Test surface added / changed

The repository now contains contract coverage for:

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
- cross-platform LF/CRLF stability for canonical JSON evidence-pack receipts.

These tests are present but are **not represented as globally accepted** in this pending record until the exact post-fix candidate passes the required Production Proof gates.

## Explicit non-claims

This implementation does not claim:

- I.1 COMPLETE / PASS / SEALED before exact-candidate proof;
- automatic autonomy promotion;
- automatic dynamic downgrade;
- a Dynamic Autonomy Manager;
- agent self-grading or self-promotion as permission;
- provider/model-specific autonomy grants;
- a single organization-wide autonomy score;
- confidence or score as permission;
- replacement of the Command Gateway;
- weakening of human/professional/legal/Board review floors;
- completion of the wider Earned Autonomy stage.

The accepted V1.3 baseline remains H.2.4 plus the sealed H.2.2 runtime-health classification refinement until exact-candidate Production Proof is green and I.1 acceptance is explicitly recorded.
