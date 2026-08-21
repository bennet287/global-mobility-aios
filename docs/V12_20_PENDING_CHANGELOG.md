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
- PostgreSQL stale cross-session supersession rejection.

These tests are present but are **not represented as passed** in this pending record until they actually run on the exact candidate.

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
