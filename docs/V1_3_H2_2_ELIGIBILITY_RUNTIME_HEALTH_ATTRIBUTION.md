# Global Mobility AIOS — V1.3 H.2.2 Eligibility Runtime-Health Attribution Foundation

**Stage:** V1.3-H.2.2
**Status:** COMPLETE / PASS / SEALED
**Accepted technical candidate:** `c5c2a68ac3a9caf2551204d61862b6ad0b6281eb`
**Accepted Production Proof:** GitHub Actions run `32473526874` — 4/4 jobs PASS
**Parent accepted baseline:** V1.3-H.2.1 — COMPLETE / PASS / SEALED
**Parent accepted candidate:** `9e63c358b9692529278595201250c4dc8bb1ff47`
**Parent Production Proof:** GitHub Actions run `32469756908`
**Scope:** G.4 `mobility.eligibility` producer/verifier runtime-health failures only

## 1. Purpose

H.2.2 establishes trusted, durable runtime-failure attribution before Global Mobility AIOS attempts provider/runtime health scoring or any wider blast-radius restriction.

The existing H.1 warning kind `runtime_health_failure` correctly records that a governed eligibility runtime failed, but the warning alone does not durably distinguish the trusted execution role and runtime identity that failed. Producer and verifier failures are operationally different, and a shared provider/runtime may affect more than one eligibility aggregate.

Therefore H.2.2 does **not** copy the H.2.1 aggregate recurrence rule onto runtime failures. It first makes the failure identity inspectable and deterministic.

Constitutional boundary:

> The Immune System may restrict or stop execution. It does not grant authority, autonomy or permission.

H.2.2 itself adds observation/provenance only and introduces no new restriction.

## 2. New durable attribution Activity

H.2.2 adds one Activity contract:

```text
organization.immune.eligibility_runtime_health_attributed.v1
```

Schema:

```text
eligibility-runtime-health-attribution.v1
```

For a G.4 runtime failure, the durable pair is:

```text
runtime-health attribution Activity
+ existing runtime_health_failure immune incident
```

Both records use deterministic keys in the existing aggregate immune stream and are committed as one transaction.

No new incident table, schema migration, provider-health table, capability authority or request field is introduced.

## 3. Trusted attribution fields

Attribution is derived only from the trusted server-side `GovernedEligibilityExecutionPlan` and `AgentRuntimeProfile` already validated by G.4.

The Activity records:

```text
execution_role
failure_stage
position_key
runtime_profile_key
runtime_profile_version
runtime_profile_fingerprint
runtime_class
adapter_key
provider_key
model_key
independence_group
```

Execution roles are bounded to:

```text
producer
verifier
```

Stage mapping is deterministic:

```text
producer -> e2_proposal_runtime
verifier -> g1_independent_verification_runtime
```

The HTTP request cannot supply or replace these values.

## 4. Atomicity and replay

The attribution Activity is staged first in:

```text
immune:eligibility:<canonical aggregate>
```

The accepted H.1 incident command then stages the paired `runtime_health_failure` warning and commits the transaction. A persistence failure rolls the pair back.

Replay does not restage a new timestamped attribution. It validates the persisted attribution fingerprint and reuses the durable pair. If exactly one side of the pair exists, H.2.2 fails closed instead of silently backfilling or repairing history.

This preserves a clear distinction between:

```text
historical legacy warning without attribution
new H.2.2 attributed warning pair
```

H.2.2 does not retroactively rewrite pre-H.2.2 history.

## 5. Control semantics remain unchanged

Runtime-health incidents remain:

```text
severity                 = warning
automatic circuit action = none
```

The attribution Activity explicitly records:

```text
control_effect                 = observation_only
authority_effect               = none
provider_health_policy_applied = false
```

Repeated runtime-health failures do **not** open an aggregate circuit in H.2.2 and do not contribute to the H.2.1 verifier-disagreement threshold.

The H.2.1 recurrence policy remains exactly scoped to `verifier_disagreement`.

## 6. Why provider/runtime scoring is deferred

A provider/runtime health policy needs a scope and time model that H.2.2 intentionally does not invent. Evidence still needed before a future control policy includes questions such as:

- whether health is provider-, model-, runtime-profile-, adapter-, position- or tenant-scoped;
- whether failures across aggregates should aggregate;
- how rolling windows and recovery epochs should work;
- how transport outage differs from malformed provider output or binding mismatch;
- what minimum sample size and decay policy avoid false quarantine;
- what blast radius is safe for an automatic restriction.

A generic score without these contracts could either miss a real infrastructure outage or over-quarantine unrelated client work.

## 7. Accepted proof

H.2.2 is accepted on technical candidate:

```text
c5c2a68ac3a9caf2551204d61862b6ad0b6281eb
```

Accepted GitHub-hosted Production Proof:

```text
run = 32473526874
Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

Verified proof evidence:

```text
Local focused H-stage regression             48 passed / 1 skipped / 1 warning / 0 failed
GitHub full backend SQLite regression         1118 passed / 8 skipped / 1 warning / 0 failed
GitHub PostgreSQL governed eligibility suite  71 passed / 1 warning / 0 failed
Fresh PostgreSQL migration chain              PASS — 0001 → 0077
Registered SQLModel tables                    119
PostgreSQL physical schema                    PASS
Repository policy                             PASS
Release consistency                           PASS — 0077
Python direct dependency constraints          PASS — 25 dependencies
Diff hygiene                                  PASS — `git diff --check HEAD^`
Frontend dependency install                   PASS
Frontend high-severity audit                  PASS
Frontend design foundation                    PASS
Frontend request/auth                         PASS
Frontend TypeScript                           PASS
Frontend Next.js production build             PASS
Frontend compiled auth                        PASS
```

The accepted tests prove:

1. producer runtime failure creates the existing warning plus trusted producer attribution;
2. verifier runtime failure creates the existing warning plus trusted verifier attribution;
3. attribution contains the exact trusted OrganizationPosition/runtime profile/provider/model identity;
4. verifier attribution preserves proposal causation and trace correlation;
5. attribution + incident are deterministic and replay-safe;
6. a torn historical pair fails closed rather than being silently repaired;
7. injected paired-write failure rolls back the staged attribution, proving atomicity;
8. replay with drifted trusted runtime identity fails closed rather than mutating the durable pair;
9. repeated runtime-health failures remain observation-only and do not open a circuit;
10. H.2.1 verifier-disagreement recurrence remains unchanged;
11. broad SQLite regression remains green;
12. the H.2.2 normal and adversarial tests run on real PostgreSQL 16;
13. migration/schema, repository policy, dependency constraints and frontend proof remain green through V12 Production Proof.

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

Canonical acceptance record:

```text
docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md
```

## 8. Explicit non-claims

H.2.2 does not claim or implement:

- provider/runtime health scoring;
- rolling-window runtime anomaly thresholds;
- provider-, model- or tenant-wide circuit breaking;
- cross-aggregate incident aggregation;
- automatic quarantine;
- automatic recovery;
- root-cause subtype diagnosis beyond trusted execution role/stage attribution;
- authority or autonomy changes;
- H.2 completion.

A later H.2 increment may use the accepted attribution evidence to define a bounded runtime-health policy, but no such policy is pre-authorized here.
