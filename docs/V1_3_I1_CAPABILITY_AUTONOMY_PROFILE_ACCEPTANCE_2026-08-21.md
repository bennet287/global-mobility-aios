# Global Mobility AIOS — V1.3 I.1 Acceptance Record — 2026-08-21

**Stage:** V1.3-I.1 — Capability-Specific Autonomy Profile + Evidence Foundation  
**Status:** ACCEPTED / COMPLETE / PASS / SEALED  
**Accepted technical candidate:** `581df5d99b65f0a7a49ace228ee707b881d508fa`  
**Accepted Production Proof:** GitHub Actions run `32529241957`  
**Parent accepted checkpoint:** V1.3-H.2.4 — `e7584b90fc967e828960ae0730a35d8646fba74f`  
**Parent Production Proof:** run `32500438187`  
**Accepted migration head:** `0078_capability_autonomy_profile_foundation`

## 1. Acceptance decision

V1.3-I.1 is accepted and sealed on technical candidate `581df5d99b65f0a7a49ace228ee707b881d508fa`.

I.1 establishes canonical, capability-specific and context-specific autonomy truth without collapsing capability, authority, autonomy and risk into one concept.

Permanent doctrine remains:

```text
Capability ≠ Authority ≠ Autonomy ≠ Risk
Memory ≠ Truth
Human Owner / Board remains supreme authority
Agents cannot self-promote
Scores and confidence do not create permission
```

The accepted foundation provides durable autonomy truth and Board inspection. It does not create automatic earned-autonomy promotion or downgrade policy.

## 2. Accepted canonical truth model

I.1 adds two bounded companion models to the shared SQLModel registry:

```text
CapabilityAutonomyProfile
CapabilityAutonomyEvidence
```

Canonical scope is:

```text
tenant
+ persistent OrganizationPosition
+ capability
+ context scope
+ evidence-policy version
```

Each accepted profile revision records:

- explicit A0–A5 autonomy;
- an explicit Board ceiling;
- authority requirement separately from autonomy;
- R0–R5 risk ceiling separately from autonomy;
- evidence-policy version;
- append-only profile sequence and supersession lineage;
- Board governance Activity identity;
- idempotency identity;
- deterministic semantic fingerprint.

Evidence rows bind one profile revision to canonical `OrganizationActivity` evidence by immutable Activity identity plus the captured Activity fingerprint observed at the Board decision.

## 3. Accepted governance boundary

The canonical writer is HTTP-independent and requires an authenticated internal human admin occupying the persistent Board position.

Accepted establishment preconditions include:

```text
active target OrganizationPosition
valid A0–A5 autonomy
valid R0–R5 risk ceiling
requested autonomy <= explicit Board ceiling
same-tenant canonical Activity evidence
exact semantic fingerprint/idempotency contract
expected profile sequence for existing chains
```

The Board governance Activity, profile revision, evidence rows and audit mutations remain one atomic transaction.

There is deliberately no autonomy `POST`, `PUT`, `PATCH` or `DELETE` HTTP route. An agent cannot invoke the canonical writer, and request JSON cannot mint or self-select autonomy.

## 4. Append-only, replay and concurrency acceptance

Acceptance proves the canonical profile chain is append-only and fail-closed.

Accepted protections include:

```text
unique scope + profile_sequence
unique tenant + supersedes_profile_id
unique tenant + idempotency_key
PostgreSQL current-profile row locking where available
expected_profile_sequence optimistic precondition
exact semantic record fingerprint
exact evidence record fingerprint
```

Exact idempotent replay reuses already-durable canonical truth. Divergent reuse of one idempotency key fails closed.

Real PostgreSQL proof exercises both:

- competing first-profile writers, where only one canonical initial profile wins;
- stale cross-session supersession, where the stale writer is rejected and the valid chain remains contiguous.

The PostgreSQL-only persistence-order defect found during pre-acceptance proof was repaired before the accepted candidate by explicitly flushing the parent `CapabilityAutonomyProfile` before queuing companion evidence rows. Parent, child evidence, governance Activity and audits still commit or roll back as one transaction.

## 5. Board / Cockpit transparency acceptance

The existing Board-only transparency facade exposes:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}?context_scope=...
```

The accepted read model validates before returning history:

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

The Cockpit receives current profile, revision history and evidence lineage without raw Activity payload JSON and without gaining a write path.

## 6. Cross-platform proof hardening accepted with the candidate

Pre-acceptance full regression exposed that a canonical JSON evidence receipt was being verified against raw checkout bytes, producing LF/CRLF-dependent hashes across Linux and Windows.

The accepted candidate includes the bounded repair:

- canonical JSON receipt hashing normalizes CRLF/CR to LF;
- regression coverage proves LF and CRLF representations validate against the same canonical receipt;
- the tracked receipt is restored to the canonical normalized hash;
- evidence JSON content is unchanged.

The V12 Production Proof workflow also now checks out the exact pull-request head SHA rather than GitHub's synthetic merge commit, so every acceptance lane proves the exact technical candidate.

## 7. Governed WorkItem precondition repair included before acceptance

The final Python 3.12 local regression before acceptance exposed one cross-platform/timing-sensitive optimistic-concurrency defect in the existing governed WorkItem assignment path.

`updated_at` supplied the WorkItem precondition token, but a successful assignment previously used `updated_at = now_utc()` without guaranteeing strict advancement. If the effective clock/storage resolution returned the same timestamp, a second command carrying the old version could incorrectly appear current.

The accepted candidate repairs that invariant by making every real assignment timestamp strictly monotonic: wall-clock time is used when greater than the prior value, otherwise the prior UTC timestamp advances by one microsecond.

A deterministic frozen-clock regression now proves:

```text
first authorized assignment advances the precondition token
new idempotency key + old precondition => BLOCK / STALE_VERSION
stale command does not mutate the WorkItem
```

Focused Python 3.12 local proof on the accepted candidate completed with:

```text
11 passed / 1 warning / 0 failed
repository policy                 PASS
release consistency               PASS — 0078
```

The subsequent local `git diff` command printed usage because the PowerShell command form was invalid. That shell invocation is not used as acceptance evidence. Exact-head GitHub Production Proof independently executed and passed its canonical diff-hygiene step.

## 8. Accepted Production Proof

### 8.1 Exact accepted run

```text
run                                      32529241957
head                                     581df5d99b65f0a7a49ace228ee707b881d508fa
workflow conclusion                      completed / success
Repository policy and constraints        PASS
Backend regression (SQLite)              PASS
Frontend tests, types and build          PASS
PostgreSQL governance contracts          PASS
```

All four jobs explicitly checked out the exact accepted technical candidate.

### 8.2 Full backend SQLite evidence

GitHub Actions used Python 3.12 and completed:

```text
1143 passed
12 skipped
1 warning
0 failed
```

The same job additionally proves:

```text
constrained dependency install            PASS
pip check                                 PASS
Python compileall                         PASS
Alembic SQLite 0001 -> 0078               PASS
migration head                            0078_capability_autonomy_profile_foundation
registered SQLModel tables                121
physical schema                           PASS
local schema contract                     PASS
```

### 8.3 PostgreSQL 16 evidence

Fresh PostgreSQL 16 proof completed with:

```text
Alembic 0001 -> 0078                      PASS
migration head                            0078_capability_autonomy_profile_foundation
registered SQLModel tables                121
physical schema                           PASS
governed eligibility/autonomy suite       95 passed / 1 warning / 0 failed
I.1 competing initial-profile writers     PASS
I.1 stale cross-session supersession      PASS
```

The duplicate-key message visible in the PostgreSQL service log is expected loser-side database enforcement exercised by the concurrency contract; the governed PostgreSQL pytest lane completed successfully.

### 8.4 Frontend and repository proof

```text
Node 24                                   PASS
npm ci                                    PASS
high-severity dependency audit            PASS — 0 vulnerabilities
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

## 9. Accepted capability boundary

I.1 is sealed as a **truth foundation**, not as the full Earned Autonomy system.

This acceptance does not claim:

- automatic autonomy promotion;
- automatic dynamic downgrade;
- a Dynamic Autonomy Manager;
- agent self-grading or self-promotion as permission;
- provider/model-specific autonomy grants;
- confidence or score as permission;
- a single organization-wide autonomy score;
- replacement of the Command Gateway;
- weakening of legal, professional, Human or Board review floors;
- full future Organizational Immune System completion;
- completion of the wider Earned Autonomy stage.

Future I-stage policy must remain capability-specific, evidence-backed, bounded by Board ceilings and independently proven before acceptance.

## 10. Seal

The accepted V1.3 technical baseline advances from H.2.4 plus the sealed H.2.2 runtime-health classification refinement to **V1.3-I.1 Capability-Specific Autonomy Profile + Evidence Foundation**.

The next I-stage increment may build on this truth surface, but must not infer that the existence of a profile automatically authorizes promotion, execution or wider authority.
