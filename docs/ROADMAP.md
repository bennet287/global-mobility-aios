# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.20 — I.1 capability-specific autonomy truth foundation implemented; acceptance pending
**Date:** 2026-08-21
**Active development branch:** `roadmap/global-mobility-aios-v12`
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR
**Active organization architecture:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` + `HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`
**Active Technology Radar:** `TECHNOLOGY_RADAR_V1_3_1.md`
**Context compression:** LLMLingua-2 — SELECTED PRIMARY PILOT behind AIOS-owned `ContextCompressionPort`; not production adopted
**Plasma donor programme:** Wiki 1.2.0 + Fractal 1.1.0 — PILOT APPROVED; PR #7 remains DRAFT / SOURCE IMPORT INCOMPLETE
**Munder donor baseline:** `v0.4.4` — strategic donor / controlled adoption programme
**Last accepted V1.3 checkpoint:** V1.3-H.2.4 — COMPLETE / PASS / SEALED on technical candidate `e7584b90fc967e828960ae0730a35d8646fba74f`
**Latest accepted Production Proof:** GitHub Actions run `32505228943` — 4/4 jobs PASS
**Required-check enforcement:** CONFIGURED / OWNER-CONFIRMED — active `Production proof enforcement` ruleset on `main`
**H.2:** BOUNDED FOUNDATION CLOSED — accepted measurement + restrict-only safety foundation is sufficient for I.1; full future Immune System is not claimed complete
**V1.3-I.1:** IMPLEMENTED / ACCEPTANCE PENDING — canonical capability/context autonomy profile + deterministic evidence lineage + Board transparency foundation; no automatic promotion/downgrade
**Code migration head:** `0078_capability_autonomy_profile_foundation`

<!-- CURRENT_MIGRATION_HEAD: 0078_capability_autonomy_profile_foundation -->

> **V11 preserves the checkpoint. V12 proves and implements the direction.**

> **Governance before unrestricted execution. Transparency before increased autonomy. Production proof before additional safety architecture.**

---

## 1. What Global Mobility AIOS is

Global Mobility AIOS is being built as a **governed, evidence-grounded, transparent and cost-intelligent high-autonomy digital organization for global mobility**.

It is not merely an immigration chatbot, visa questionnaire, generic AI assistant, CRM with AI, document uploader, workflow engine, disconnected multi-agent demo, generic SaaS/admin surface, browser agent or human approval queue.

Target identity:

> **Global Mobility AIOS coordinates persistent AI employees to perform global-mobility work through dynamic Missions, purpose-scoped context, earned capability-specific autonomy, risk-tiered verification, governed execution and Human Owner / Board sovereignty.**

Operating principles:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Board by exception. Transparency by default.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

> **Architectural sophistication must be matched by automated production proof.**

> **Quality first. Cost intelligence second. Premium compute only where it produces measurable additional value.**

> **No new major framework by default; prove a measured architectural gap first.**

Canonical architecture records:

- `docs/GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` — active canonical refinement
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md` — constitutional high-autonomy source
- `docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md` — historical predecessor
- `docs/TECHNOLOGY_RADAR_V1_3_1.md` — active technology/adoption direction
- `docs/V1_3_H2_FOUNDATION_CLOSURE_AND_I1_ENTRY_2026-08-21.md` — H→I stage decision
- `docs/V1_3_I1_CAPABILITY_AUTONOMY_PROFILE_FOUNDATION_2026-08-21.md` — active I.1 implementation contract
- `docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`
- `docs/PLASMA_AIOS_ADOPTION_V1.md`

---

## 2. Complete mobility lifecycle target

```text
Goal
→ profile / circumstances / constraints / consent
→ mobility strategy
→ country and pathway discovery
→ eligibility and alternatives
→ Evidence requirements and collection
→ official rules and regulatory intelligence
→ risk / cost / timeline / dependencies
→ documents and consistency
→ professional / regulated review where required
→ application preparation
→ Decision Readiness / verification
→ Human / Board authority where required
→ submission / appointment / external action
→ authority response
→ remediation / follow-up / appeal where applicable
→ relocation / post-arrival obligations
→ renewal / status change / family progression
→ long-term residence
→ citizenship / business / investment / long-term mobility strategy
```

The lifecycle must support changed goals, employers and jurisdictions; rejected applications; expired Evidence; superseded rules; family dependencies; long-lived case history; reassessment; and future mobility strategy.

---

## 3. Repository truth and accepted checkpoints

The roadmap distinguishes three states:

```text
IMPLEMENTED            code/docs exist
ACCEPTANCE PENDING     implementation has not yet satisfied its required proof gate
COMPLETE / PASS / SEALED
                       accepted evidence exists and repository truth is reconciled
```

Implementation is never treated as acceptance automatically.

Current V1.3 state:

| Stage | State | Meaning |
|---|---|---|
| V1.3-A Constitutional Contracts | COMPLETE / PASS / SEALED | Constitutional risk, authority, transparency and consequence primitives accepted |
| V1.3-B Minimal Governance Kernel | COMPLETE / PASS / SEALED | Bounded Command Gateway/governance kernel accepted |
| V1.3-C Transparency Foundation | COMPLETE / PASS / SEALED through C.4 | Board-inspectable activity/trace/read contracts accepted |
| V1.3-D Context + persistent employee/runtime | COMPLETE / PASS / SEALED through D.3 | OrganizationPosition, ContextBundle and runtime separation accepted |
| V1.3-E First Governed Mobility Vertical | COMPLETE / PASS / SEALED through E.2 | Governed mobility brief and eligibility intent accepted |
| V1.3-F Decision Readiness | COMPLETE / PASS / SEALED through F.1 | Deterministic readiness routing accepted |
| V1.3-G Independent Verification + canonical eligibility | COMPLETE / PASS / SEALED through G.5 | Blind verification, verification floor, canonical effect, orchestration and reassessment accepted |
| V1.3-H.1 Eligibility Immune Circuit | COMPLETE / PASS / SEALED | Restrictive aggregate circuit, canonical-lineage consolidation and proof accepted |
| V1.3-H.2.1 Eligibility Warning Recurrence Guard | COMPLETE / PASS / SEALED | Third verifier disagreement in one recovery epoch opens the exact aggregate circuit; PostgreSQL concurrency proof accepted |
| V1.3-H.2.2 Eligibility Runtime-Health Attribution | COMPLETE / PASS / SEALED | Trusted producer/verifier runtime identity is durably paired with runtime-health warnings; atomicity and identity-drift adversarial proof accepted; no provider-health policy yet |
| H.2.2 Runtime-Health Classification Refinement | COMPLETE / PASS / SEALED | Separates configuration/binding, provider transport and provider response-contract failures and records provider-egress provenance; measurement-only; Production Proof accepted |
| V1.3-H.2.3 Eligibility Revision-Conflict Attribution | COMPLETE / PASS / SEALED | Genuine lower-than-current G.5 pre-egress stale reassessments are durably attributed; false-positive exclusions and atomic replay/rollback proof accepted; no recurrence policy |
| V1.3-H.2.4 Post-Producer Revision-Race Attribution | COMPLETE / PASS / SEALED | Event-time v1 → v2 race attribution survives legitimate v3 supersession before first persistence; shared canonical aggregate lineage validation and PostgreSQL adversarial proof accepted |
| V1.3-H.2 overall | BOUNDED FOUNDATION CLOSED | Accepted measurement + restrict-only safety foundation is sufficient for I.1; no claim that the full future Immune System is complete |
| V12 Production Proof Gate | ACCEPTED / GREEN | Repository, backend SQLite, frontend and PostgreSQL lanes are continuously executable; latest accepted refinement run `32505228943` |
| Required GitHub check enforcement | CONFIGURED / OWNER-CONFIRMED | Active `Production proof enforcement` ruleset protects `main` and requires all four Production Proof checks |
| V1.3-I.1 Capability-Specific Autonomy Profile + Evidence | IMPLEMENTED / ACCEPTANCE PENDING | Canonical capability/context autonomy truth, append-only supersession, deterministic Activity evidence lineage, Board ceiling enforcement and Board read model are implemented; exact-candidate proof is still required |

The accepted V1.3 baseline remains **H.2.4**, sealed by `docs/V1_3_H2_4_ACCEPTANCE_2026-08-21.md`. The H.2.2 runtime-health classification refinement is also COMPLETE / PASS / SEALED on technical candidate `25b19728e7dc35f3f0450f6ae839fa57fe36c1e4`, Production Proof run `32505228943`; it changes measurement provenance only and does not authorize provider-health policy.

I.1 is now implemented but **not yet accepted**. Until the exact implementation/documentation candidate passes the required SQLite, PostgreSQL, frontend and repository proof gates, no COMPLETE / PASS / SEALED claim is valid.

---

## 4. Historical compatibility contract — protected

The active V12 roadmap preserves historical markers protected by repository regression tests and meaningful to current Evidence provenance.

`v10.22` introduced **multi-batch tranche operations** around the governed jurisdiction Evidence workflow.

Historical database lineage includes:

```text
0032_initial_rule_assertions
```

Protected exact markers:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

No V1.3, canonical eligibility-effect, Immune System, CI or Munder work may erase this provenance contract.

---

## 5. Latest accepted quality evidence — H.2.4 + H.2.2 classification refinement

Historical accepted results are not represented as rerun unless actually rerun.

H.1 through H.2.3 remain sealed by their own acceptance records. H.2.4 adds the following accepted proof:

```text
GitHub backend regression                         1135 passed / 10 skipped / 1 warning / 0 failed
Fresh PostgreSQL 16 Alembic                       PASS — 0001 → 0077
Registered SQLModel tables                        119
Fresh PostgreSQL physical schema                  PASS
GitHub PostgreSQL governed suite                  90 passed / 1 warning / 0 failed
H.2.4 v1 → v2 post-producer race                  PASS
H.2.4 first attribution after v3 supersession     PASS — critic blocker closed
H.2.4 event-time v2 snapshot preserved            PASS
H.2.4 v3 remains sole ACTIVE head                 PASS
Shared canonical aggregate lineage validation     PASS
Existing H.2.4 replay/rollback/torn-pair proofs   PASS
Frontend npm ci                                   PASS
Frontend high-severity audit                      PASS — 0 vulnerabilities
Frontend design foundation                        PASS — 28/28
Frontend request/auth                             PASS — 4/4
Frontend TypeScript                               PASS
Frontend Next.js 16.3.1 build                     PASS
Frontend compiled auth                            PASS
Repository policy                                 PASS
Release consistency                               PASS — 0077
Python dependency constraints                     PASS — 25 direct dependencies
Diff hygiene                                      PASS — git diff --check HEAD^
GitHub Production Proof run 32500438187           4/4 jobs PASS
Accepted technical candidate                      e7584b90fc967e828960ae0730a35d8646fba74f
H.2.2 classification candidate                    25b19728e7dc35f3f0450f6ae839fa57fe36c1e4
H.2.2 classification Production Proof             32505228943 — 4/4 jobs PASS
Classification backend regression                 1138 passed / 10 skipped / 1 warning / 0 failed
Classification PostgreSQL governed suite          93 passed / 1 warning / 0 failed
Configuration/binding provenance                  PASS — provider egress false
Provider transport provenance                     PASS — provider egress true
Provider response-contract provenance             PASS — provider egress true
Legacy H.2.2 replay                               PASS
Classification drift fail-closed                  PASS
```

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

The first H.2.3 proof run `32479407154` is retained as superseded diagnostic evidence: repository policy, frontend and PostgreSQL passed, while broad SQLite exposed one stale pre-H.2.3 error-message assertion. Commit `17edeca...` aligned only that legacy test expectation; the H.2.3 runtime implementation remained unchanged.

Canonical acceptance records include `docs/V1_3_*_ACCEPTANCE_2026-08-20.md` for D.1 through G.5, `docs/V1_3_H1_ACCEPTANCE_2026-08-21.md` for H.1, `docs/V1_3_H2_1_ACCEPTANCE_2026-08-21.md` for H.2.1, `docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md` for H.2.2, `docs/V1_3_H2_3_ACCEPTANCE_2026-08-21.md` for H.2.3, `docs/V1_3_H2_4_ACCEPTANCE_2026-08-21.md` for H.2.4 and `docs/V1_3_H2_2_RUNTIME_HEALTH_CLASSIFICATION_ACCEPTANCE_2026-08-21.md` for the H.2.2 classification refinement.

Repository-owner Settings evidence confirms that `main` is protected by an active ruleset requiring the four Production Proof checks before integration. The GitHub connector does not expose ruleset configuration directly, so this enforcement claim remains owner-confirmed rather than connector-introspected.

---

## 6. Permanent constitutional execution invariants

```text
Capability ≠ Authority ≠ Autonomy ≠ Risk
CAN DO ≠ MAY DO
Scores route; deterministic gates authorize.
Memory provides continuity. Evidence provides authority.
Conversation does not create authority.
Provider output does not become canonical truth automatically.
Compression output is derived context, not source truth.
Retrieved knowledge is data, not executable authority.
Model capability eligibility is measured, not self-declared.
Child delegation may narrow parent scope, never expand it.
Immune System is restrict-only and never grants authority.
```

Human Owner / Board remains supreme authority.

Autonomy remains capability-specific:

| Level | Meaning |
|---|---|
| A0 | Prohibited |
| A1 | Human executes |
| A2 | AI prepares; approval required |
| A3 | Autonomous with mandatory review |
| A4 | Autonomous with monitoring and valid recovery controls |
| A5 | Fully autonomous bounded operation |

Risk remains consequence-oriented:

| Risk | Typical work | Verification |
|---|---|---|
| R0 | brainstorming / summarization | single agent |
| R1 | routine internal operation | deterministic checks |
| R2 | client-facing preparation / Evidence validation | Evidence validation |
| R3 | eligibility / material recommendation | blind independent verification |
| R4 | certification / regulatory publication | independent verification + fresh source + authority |
| R5 | government submission / critical reserved action | full AI preparation + required Human/Board authority |

---

## 7. Accepted governed eligibility vertical

The accepted R3 eligibility chain is:

```text
trusted G.4 organization request / WorkItems
→ E.2 material proposal / governance attempt
→ F.1 deterministic Decision Readiness
→ G.1 blind independent verification
→ G.2 verification-floor re-evaluation
→ G.3 canonical governance authorization
→ G.3 semantic EligibilityAssessment effect
→ G.4 durable trace/effect identifiers
→ G.5 explicit canonical revision precondition for reassessment
→ append-only supersession lineage
```

Accepted aggregate identity:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

G.5 preserves two separate concurrency contracts:

```text
MaterialAction.expected_version
    = Profile.profile_version

expected_eligibility_revision_version
    = current ACTIVE canonical eligibility revision
```

There is no implicit reassessment and no last-write-wins canonical truth.

Historical replay may resolve already-durable superseded revisions but may not authorize new work from stale state.

The governed HTTP route remains:

```text
POST /api/v1/organization/eligibility/orchestrate
```

Request JSON cannot select tenant authority, OrganizationPosition, provider/model, autonomy, risk, scope or `CapabilityAuthority`.

---

## 8. Accepted H.1 Eligibility Immune Circuit Foundation

Canonical design record:

```text
docs/V1_3_H1_ELIGIBILITY_IMMUNE_CIRCUIT_FOUNDATION.md
```

H.1 is aggregate-scoped and uses existing `OrganizationActivity` durability rather than a new incident table.

Current control types:

```text
organization.immune.eligibility_incident.v1
organization.immune.eligibility_circuit_opened.v1
organization.immune.eligibility_circuit_closed.v1
```

Critical structural classes:

```text
CANONICAL_AGGREGATE_INTEGRITY
DURABLE_LINEAGE_INTEGRITY
```

Warning classes currently include:

```text
RUNTIME_HEALTH_FAILURE
REVISION_CONFLICT
VERIFIER_DISAGREEMENT
REASSESSMENT_ROLLBACK
```

Automatic opening is restrict-only. Recovery requires an authenticated human admin and restores execution attempts only; it grants no authority.

Fresh G.4 execution performs circuit/lineage preflight before provider egress. Exact committed historical replay remains provider-free but must satisfy durable canonical lineage.

---

## 9. H.1 canonical-lineage blocker — resolved and accepted

The H.1 candidate previously duplicated part of the G.3/G.4 durable-lineage invariant.

That was unsafe because a row could remain:

```text
present
+ same tenant
+ causally linked
```

while its semantic identity had changed.

The repository now has one domain-specific canonical eligibility-lineage contract:

```text
apps/api/app/services/organization_eligibility_lineage.py
```

Consumers:

```text
G.3 canonical-effect replay
G.4 orchestration replay
H.1 aggregate preflight
```

The shared validator proves:

- existence;
- tenant;
- stable aggregate identity;
- revision/lifecycle/supersession;
- assessment identity;
- exact G.1/G.2/semantic Activity types;
- canonical governance record kind;
- MATERIAL classification;
- source type/id/version;
- action/readiness/verification/floor/effect fingerprints;
- expected revision identity/version;
- semantic revision/effect identity;
- E.2 → G.1 → G.2 → G.3 → semantic causation.

Aggregate validation additionally requires one contiguous revision chain with exactly one latest ACTIVE revision.

This repair is **ACCEPTED / SEALED** as part of V1.3-H.1.

---

## 10. Adversarial H.1 regression — accepted

The acceptance surface intentionally corrupts committed lineage rather than testing only valid fixtures.

Corruptions include:

```text
verification Activity type
verification-floor Activity type
governance record kind
semantic Activity type
assessment/revision identity
semantic source revision identity
missing semantic lineage
invalid revision lifecycle
```

Required fresh-execution behavior:

```text
canonical validator rejects corruption
→ CRITICAL incident
→ exact aggregate circuit OPEN
→ producer calls = 0
→ verifier calls = 0
```

G.3/G.4 replay fails closed on the same canonical invariant.

---

## 11. Production Proof Gate — accepted / continuously reused

Canonical H.1 proof records:

```text
docs/V1_3_H1_PRODUCTION_PROOF_GATE.md
docs/V1_3_H1_ACCEPTANCE_2026-08-21.md
```

CI workflow:

```text
.github/workflows/v12-production-proof.yml
```

Original accepted H.1 GitHub-hosted run:

```text
candidate = 0b19d61a417de2d372e101d4e132a6a0a6c2a84f
run       = 32463849415
```

Accepted H.2.1 GitHub-hosted run:

```text
candidate = 9e63c358b9692529278595201250c4dc8bb1ff47
run       = 32469756908
```

Accepted H.2.2 GitHub-hosted run:

```text
candidate = c5c2a68ac3a9caf2551204d61862b6ad0b6281eb
run       = 32473526874
```

Latest accepted H.2.3 GitHub-hosted run:

```text
candidate = 17edeca46af2b9cc7e0a6111ec2b3270f4bb1283
run       = 32480405051

Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

H.2.4 is accepted and sealed on technical candidate `e7584b90fc967e828960ae0730a35d8646fba74f`; run `32500438187` passed all four lanes.

### 11.1 Repository policy / dependency contract

```text
repository policy
release consistency
Python direct-dependency constraints
diff hygiene
```

Repository policy rejects shell-redirection-like tracked filenames. The accidental `apps/api/=5.4` artifact has been removed.

A canonical Git-blob audit also corrected exactly two stale evidence receipts without changing the evidence JSON or weakening SHA validation; the GitHub-hosted Linux backend lane subsequently passed.

Candidate-local proof should use `git diff --check HEAD^` when validating committed diff hygiene; plain `git diff --check` only inspects uncommitted working-tree changes and is insufficient for this gate.

### 11.2 Full backend regression — SQLite

```text
constrained Python dependency install
compileall
Alembic upgrade on isolated SQLite
full apps/api/tests pytest regression
migration head + physical schema verification
local schema contract
```

SQLite remains the broad fast regression environment. It is not sufficient production-database proof by itself.

Latest accepted H.2.3 backend result:

```text
1127 passed / 8 skipped / 1 warning / 0 failed
```

### 11.3 Frontend proof

Accepted frontend baseline:

```text
next=16.3.1
react=19.0.8
react-dom=19.0.8
```

Accepted proof:

```text
npm ci
npm audit --audit-level=high → 0 vulnerabilities
design-foundation tests → PASS
request/auth tests → PASS
TypeScript --noEmit → PASS
Next.js production build → PASS
compiled-auth tests → PASS
```

The GitHub frontend lane uses Node 24 so the CI runtime matches the proven request/auth test contract.

There is not yet a Playwright/browser workflow suite. A browser golden journey is required before aggressive frontend restructuring.

### 11.4 PostgreSQL governance proof

A real PostgreSQL 16 service is migrated through the single Alembic head, physically checked against SQLModel metadata, then used by focused governance tests.

The same pytest fixture switches to PostgreSQL only when:

```text
GMAI_TEST_DATABASE_URL=postgresql+psycopg://...
```

The focused lane covers G.3/G.4/G.5/H.1 and accepted H.2 eligibility safety contracts. Accepted H.2.4 additionally includes `test_organization_eligibility_revision_runtime_race.py` and its adversarial companion, including the real cross-session post-producer race and pre-persistence v3 supersession contracts.

I.1 extends the already-executed `test_organization_eligibility_postgres_contract.py` with real PostgreSQL competing-profile and stale-supersession proofs so the existing Production Proof lane exercises the new autonomy concurrency contract without introducing a second PostgreSQL test framework.

Latest **accepted** PostgreSQL evidence remains H.2.4:

```text
Alembic 0001 → 0077              PASS
registered tables                 119
physical schema                   PASS
governed eligibility suite        90 passed / 1 warning / 0 failed
```

The I.1 migration/runtime proof for `0078` is acceptance-pending and is not represented above as already passed.

---

## 12. Python dependency reproducibility

Backend direct dependencies remain declared in:

```text
apps/api/requirements.txt
```

Exact direct-dependency constraints live in:

```text
apps/api/constraints.txt
```

Required constrained install:

```text
python -m pip install -r apps/api/requirements.txt -c apps/api/constraints.txt
```

The API Docker image and V12 Production Proof workflow use the same constraints.

Current claim boundary:

> **This is a direct-dependency reproducibility baseline, not a complete transitive lock.**

The accepted constrained candidate passed installation, `pip check`, application import and the complete backend regression.

---

## 13. Migration/data-model doctrine

The current implementation declares one controlled Alembic head:

```text
0078_capability_autonomy_profile_foundation
```

I.1 adds exactly two bounded companion tables to the single SQLModel registry:

```text
capability_autonomy_profiles
capability_autonomy_evidence
```

The prior accepted H.2.4 checkpoint had 119 registered SQLModel tables at migration 0077. The current I.1 branch therefore declares 121 registered domain tables before the infrastructure `alembic_version` table; that updated physical-schema claim remains acceptance-pending until Production Proof verifies the exact candidate.

The concentration of models in `domain.py` is a maintainability risk, but the migration doctrine remains:

> **Split model modules by bounded context; retain one SQLModel metadata registry and one controlled linear Alembic lineage/head.**

Do not create independent migration heads merely to mirror code-module boundaries.

The production-proof migration checker validates:

```text
exactly one Alembic head
physical schema matches registered SQLModel tables/columns
alembic_version equals the declared head
```

for SQLite and PostgreSQL when those databases are supplied.

H.2.4 intentionally introduced no new table or migration. I.1 introduces the two companion tables through linear migration `0078` and registers them through the existing model registry.

---

## 14. Complexity/decomposition programme — sequenced, not simultaneous

Large-module concentration is accepted as a maintainability risk. It is not a reason to begin four broad refactors at once.

Known concentration areas include:

```text
organization_governance.py
domain.py
apps/web/lib/api.ts
apps/web/app/globals.css
```

Sequence after the Production Proof Gate:

### 14.1 Backend model decomposition

Extract bounded-context model modules while preserving:

```text
one SQLModel metadata registry
one canonical table identity per model
one linear Alembic lineage/head
no migration-history rewrite
```

I.1 follows this doctrine by adding `app/models/autonomy_profile.py` as a companion model module while registering it in the existing shared SQLModel metadata surface.

### 14.2 Frontend API decomposition

Split domain clients behind one common request/auth/error primitive. Do not create duplicate fetch/auth frameworks.

### 14.3 CSS decomposition

Move design tokens, primitives, layouts and feature styles incrementally. Preserve visual behavior through build/tests and future browser golden journeys.

### 14.4 Governance-service decomposition

Extract only semantic seams with stable contracts and tests. Do not split by arbitrary line-count quotas.

Permanent rule:

> **Improve regression detection before increasing refactor surface area.**

---

## 15. H.1 through H.2.4 acceptance gates — satisfied

H.1 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H1_ACCEPTANCE_2026-08-21.md`.

H.2.1 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H2_1_ACCEPTANCE_2026-08-21.md`.

H.2.2 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md`.

H.2.3 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H2_3_ACCEPTANCE_2026-08-21.md`.

H.2.4 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H2_4_ACCEPTANCE_2026-08-21.md`.

H.2.1 acceptance proves:

1. first and second verifier disagreements remain warning-only;
2. the third disagreement opens the exact aggregate circuit;
3. warning + OPEN transition are atomic;
4. incident replay cannot duplicate OPEN;
5. human-admin recovery starts a new recurrence epoch;
6. unrelated warning kinds do not contribute to the disagreement threshold;
7. fresh execution after recurrence OPEN is blocked before provider egress;
8. PostgreSQL serializes concurrent threshold crossing to exactly one OPEN.

H.2.2 acceptance additionally proves:

1. producer and verifier runtime-health failures receive trusted server-side attribution;
2. runtime position/profile/provider/model identity is durable and fingerprinted;
3. verifier attribution preserves proposal causation and trace correlation;
4. attribution + warning replay is deterministic;
5. a torn pair fails closed;
6. injected failure between attribution staging and warning persistence rolls the pair back atomically;
7. replay with changed trusted runtime identity fails closed;
8. repeated runtime-health warnings remain observation-only and do not open an aggregate circuit;
9. H.2.1 recurrence semantics remain unchanged;
10. broad backend, frontend, migration/schema, PostgreSQL and repository proof are green.

H.2.3 acceptance additionally proves:

1. only lower-than-current pre-egress revision expectations become the H.2.3 conflict subtype;
2. stale reassessment is rejected before producer or verifier provider egress;
3. expected and observed canonical revision identity is durable and reconciled;
4. missing, future and no-current expectations are excluded from H.2.3 incident attribution;
5. post-provider races remain generic stale state rather than being misclassified;
6. attribution + warning is atomic and replay-deterministic;
7. torn pairs and changed conflict snapshots fail closed;
8. repeated revision-conflict warnings remain observation-only and do not open a circuit;
9. full SQLite, fresh PostgreSQL, frontend and repository proof are green.

H.2.4 acceptance additionally proves:

1. a valid reassessment may advance during producer runtime without stale output becoming canonical;
2. producer egress is recorded while verifier egress remains false;
3. the event-time observed revision remains durable even if superseded before first attribution persistence;
4. a legitimate v3 may supersede event-time v2 before first persistence without losing the v1 → v2 explanation;
5. the current ACTIVE head and event-time revision must belong to the same contiguous canonical aggregate lineage;
6. replay, torn-pair, snapshot-drift and runtime-identity protections remain fail-closed;
7. full SQLite, fresh PostgreSQL, frontend and repository proof are green.

Accepted H.2.4 technical candidate:

```text
e7584b90fc967e828960ae0730a35d8646fba74f
```

Accepted H.2.4 GitHub run:

```text
32500438187
```

The H.2.2 runtime-health classification refinement is **COMPLETE / PASS / SEALED** on technical candidate `25b19728e7dc35f3f0450f6ae839fa57fe36c1e4`, Production Proof run `32505228943`.

---

## 16. Immediate execution order

The current H→I stage sequence is:

```text
1. H.1 canonical lineage + circuit foundation             COMPLETE / SEALED
2. Production Proof + required-check enforcement          COMPLETE
3. H.2.1 verifier-disagreement recurrence guard           COMPLETE / SEALED
4. H.2.2 runtime-health attribution foundation            COMPLETE / SEALED
5. H.2.3 revision-conflict attribution foundation         COMPLETE / SEALED
6. H.2.4 post-producer revision-race attribution          COMPLETE / SEALED
7. H.2.2 runtime-health classification refinement         COMPLETE / SEALED
8. H.2 bounded safety/measurement foundation              CLOSED
9. V1.3-I.1 autonomy profile + evidence foundation        IMPLEMENTED / ACCEPTANCE PENDING
10. Exact-candidate V12 Production Proof                   REQUIRED BEFORE I.1 ACCEPTANCE
```

Browser golden-journey proof and incremental semantic decomposition remain parallel proof/maintainability priorities and do not pre-accept I.1 or any future autonomy policy.

---

## 17. V1.3-H.2 — bounded safety/measurement foundation closed

H.2 is closed as the accepted bounded safety/measurement foundation required to enter I.1. This does not claim the complete future Organizational Immune System is implemented. The accepted H.2 increments remain individually sealed by their own evidence and may not be broadened implicitly.

### 17.1 H.2.1 — accepted verifier-disagreement recurrence

Canonical records:

```text
docs/V1_3_H2_1_ELIGIBILITY_WARNING_RECURRENCE_GUARD.md
docs/V1_3_H2_1_ACCEPTANCE_2026-08-21.md
```

Accepted policy:

```text
incident kind  = verifier_disagreement
threshold      = 3
scope          = exact tenant + canonical eligibility aggregate
recovery epoch = stream start or latest authorized circuit close
```

The individual incident remains WARNING; the repeated pattern causes a restrict-only OPEN.

### 17.2 H.2.2 — accepted runtime-health attribution foundation

Canonical records:

```text
docs/V1_3_H2_2_ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION.md
docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md
```

H.2.2 makes G.4 runtime failure provenance durable:

```text
execution role
failure stage
OrganizationPosition
runtime profile identity/version/fingerprint
runtime class / adapter
provider / model
independence group
```

The values come only from the trusted server-side execution plan. They are paired atomically with the existing `runtime_health_failure` warning.

Accepted control semantics remain intentionally non-restrictive:

```text
runtime-health warning         observation-only
runtime recurrence threshold   none
provider-health score          none
cross-aggregate quarantine     none
automatic recovery             none
```

H.2.2 deliberately does **not** add a runtime recurrence threshold, provider-health score, cross-aggregate quarantine or automatic recovery. Those require a separately justified scope/time/blast-radius policy.

### 17.2A H.2.2 runtime-health classification refinement — accepted

Canonical refinement records:

```text
docs/V1_3_H2_2_RUNTIME_HEALTH_CLASSIFICATION_REFINEMENT_2026-08-21.md
docs/V1_3_H2_2_RUNTIME_HEALTH_CLASSIFICATION_ACCEPTANCE_2026-08-21.md
```

The refinement adds measurement provenance only:

```text
configuration_or_binding_failure      provider_egress_occurred=false
provider_transport_failure            provider_egress_occurred=true
provider_response_contract_failure    provider_egress_occurred=true
```

It does not create a provider-health score, recurrence threshold, quarantine, automatic failover, authority change or autonomy change. Already-durable H.2.2 v1 records are not rewritten.

This refinement is **COMPLETE / PASS / SEALED** on technical candidate `25b19728e7dc35f3f0450f6ae839fa57fe36c1e4`, proven by GitHub Actions run `32505228943` across all four V12 Production Proof lanes.

### 17.3 H.2.3 — accepted pre-egress revision-conflict attribution foundation

Canonical records:

```text
docs/V1_3_H2_3_REVISION_CONFLICT_ATTRIBUTION_FOUNDATION.md
docs/V1_3_H2_3_ACCEPTANCE_2026-08-21.md
```

Accepted classification:

```text
aggregate has exactly one ACTIVE revision
caller expectation >= 1
caller expectation < current ACTIVE revision
conflict detected before producer provider egress
```

Accepted durable pair:

```text
organization.immune.eligibility_revision_conflict_attributed.v1
+
organization.immune.eligibility_incident.v1
  kind = revision_conflict
  severity = warning
```

The attribution records the expected revision and observed current revision identity/version with `provider_egress_occurred=false`.

Accepted control semantics remain observation-only:

```text
revision-conflict warning       observation-only
revision recurrence threshold   none
circuit action                  none
automatic retry/rebase          none
authority/autonomy effect       none
```

Missing expectations, future expectations, nonexistent-current expectations, aggregate corruption and post-provider revision races are deliberately excluded from this incident class.

### 17.4 H.2.4 — accepted post-producer revision-race attribution

Canonical records:

```text
docs/V1_3_H2_4_POST_PRODUCER_REVISION_RACE_ATTRIBUTION.md
docs/V1_3_H2_4_ACCEPTANCE_2026-08-21.md
```

Accepted classification:

```text
exact current reassessment revision accepted before producer egress
producer provider returns successfully
same canonical aggregate advances during producer runtime
post-producer E.2 revalidation captures the event-time advancement
verifier egress = false
canonical effect from stale attempt = false
```

Accepted durable pair:

```text
organization.immune.eligibility_revision_runtime_race_attributed.v1
+
organization.immune.eligibility_incident.v1
  kind = revision_conflict
  severity = warning
```

The attribution records the resolved and event-time observed canonical revision identities plus trusted producer position/runtime/provider/model identity.

The repaired persistence contract also accepts a legitimate newer v3 that supersedes observed v2 before the first attribution write, but only when the shared canonical aggregate lineage validator proves the current head, observed revision and resolved revision belong to one contiguous lineage.

Accepted control semantics remain intentionally non-restrictive:

```text
post-producer race warning       observation-only
revision recurrence threshold    none
circuit action                   none
automatic retry/rebase           none
reuse stale producer output      prohibited by fail-closed path
authority/autonomy effect        none
```

Concurrent first-time creation, H.2.3 pre-egress conflicts, runtime failure, verifier-stage races, G.2/G.3 races and transaction rollback remain explicitly excluded.

H.2.4 is **COMPLETE / PASS / SEALED** on technical candidate `e7584b90fc967e828960ae0730a35d8646fba74f`, Production Proof run `32500438187`.

### 17.5 Future H.2 reopening — not selected / not pre-authorized

The bounded H.2 foundation is closed. No additional control is selected merely because telemetry exists. A future H-stage reopening requires a newly measured failure model and must again define:

```text
failure model
measurement scope
time/window or recovery epoch
minimum evidence/sample contract
restriction blast radius
false-positive containment
human/automatic recovery boundary
interaction with existing aggregate circuit
authority/autonomy non-effect
```

Potential later H.2 work may include:

- rolling-window anomaly policy;
- incident aggregation;
- bounded root-cause classification;
- provider/runtime health scoring;
- broader but still scope-limited blast-radius controls;
- automatic escalation routing where constitutionally valid.

Do not build a generic anomaly platform.

Any future H-stage increment must preserve the H.1 rule that the Immune System is restrictive only and must receive its own bounded implementation and proof before acceptance.

---

## 18. V1.3-I — Earned Autonomy

**I.1 FOUNDATION IS IMPLEMENTED; ACCEPTANCE IS PENDING.**

Canonical implementation contract:

```text
docs/V1_3_I1_CAPABILITY_AUTONOMY_PROFILE_FOUNDATION_2026-08-21.md
```

The I.1 foundation now creates canonical append-only autonomy truth at the exact scope:

```text
tenant
+ persistent OrganizationPosition
+ capability
+ context scope
+ evidence-policy version
```

Implemented canonical records:

```text
CapabilityAutonomyProfile
CapabilityAutonomyEvidence
```

Implemented invariants:

```text
A0–A5 autonomy is explicit and capability/context-specific
Board ceiling is explicit and enforced
Authority requirement is stored separately from autonomy
Risk ceiling is stored separately from autonomy
profile revisions are append-only
supersession is explicit and cannot fork one predecessor into two children
evidence lineage points to canonical OrganizationActivity IDs + captured fingerprints
exact idempotent replay reuses canonical truth
divergent idempotency reuse fails closed
existing-profile updates require expected_profile_sequence
PostgreSQL uses current-profile row locking plus database uniqueness constraints
agents cannot invoke the canonical profile writer
only authenticated internal Human Board/admin context may establish the profile
HTTP exposes read-only Board transparency; no autonomy POST/PUT/PATCH/DELETE route exists
```

Current Board read surface:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}?context_scope=...
```

The read model validates contiguous profile supersession, decision-Activity identity, evidence ordering and evidence fingerprint integrity before returning the current profile plus revision history. Raw Activity payload JSON is not exposed.

This foundation does **not** yet implement a Dynamic Autonomy Manager. It does not automatically promote or downgrade agents. It does not grant authority from scores, provider/model identity, confidence or self-evaluation.

Target principle for later I-stage policy remains:

```text
promotion requires measured evidence
downgrade may be faster than promotion
scope is capability-specific
agents cannot self-promote
Board ceilings remain supreme
```

The Immune System may reduce autonomy; it does not grant authority.

I.1 acceptance requires the exact candidate to pass the V12 Production Proof repository, SQLite, frontend and real PostgreSQL lanes. Until that proof is green and recorded, this section remains **IMPLEMENTED / ACCEPTANCE PENDING**.

---

## 19. Organization Fabric and Munder adoption

The future Organization Fabric includes:

- persistent employee/runtime binding;
- organizational communication;
- Missions/WorkItems;
- Dynamic Mission Squads;
- presence/heartbeats;
- Mission Rooms;
- Skills/Capability Registry;
- memory mechanics;
- Event Nervous System;
- scheduling/triggers/webhooks;
- runtime telemetry.

Munder v0.4.4 remains a controlled donor. AIOS retains exclusive ownership of organizational semantics, authority, Evidence, risk, Decision Readiness, Command Gateway decisions and canonical state.

High-value donor areas remain runtime/provider abstraction, messaging, Skills, task coordination, circuit-breaking mechanics, triggers, memory, telemetry, token/cost tracking and live-scene concepts.

Hard rejects remain:

```text
SQLite/file state as canonical production authority
GOD-style unlimited implicit authority
direct material mutation bypassing AIOS governance
provider-owned organizational semantics
retro pixel-office UI as final product design
```

---

## 20. Transparency / Cockpit direction

Board Transparency remains a cross-cutting architectural invariant rather than a later dashboard feature.

Target drill-down:

```text
Organization
→ Department
→ Mission
→ Case
→ WorkItem
→ Squad
→ Agent
→ Conversation
→ Decision
→ Tool Action
→ Evidence / Rule
→ Canonical Effect
→ Incident / Recovery
→ Outcome
```

Board visibility does not imply Board interruption.

The top-level Human Owner / Board experience remains the **Global Mobility AIOS Cockpit**; Board Room is a module inside that control surface.

H.2.2 improves the future Incident drill-down by making runtime-health warnings attributable to a trusted execution role/runtime identity. Its accepted classification refinement additionally distinguishes configuration/binding failures from provider transport and response-contract failures without creating a provider-health policy. H.2.3 makes pre-egress stale reassessment contention inspectable as an exact expected-versus-current canonical revision snapshot. Accepted H.2.4 extends that explainability to stale producer work when the canonical revision advances during producer latency, without changing control authority.

I.1 extends the existing Board-only transparency facade with a canonical capability-autonomy history view. The Cockpit can inspect which profile is current, which revision it superseded, its Board ceiling, independent authority/risk bounds, evidence-policy version and exact canonical Activity evidence lineage without receiving raw payload JSON or gaining a new autonomy write path.

---

## 21. Operational proof still to add after this gate

The V12 Production Proof Gate is the minimum continuous proof boundary, not the endpoint of operational maturity.

Still required later:

- Playwright/browser golden journey;
- controlled failure/recovery drills;
- backup/restore proof;
- observability SLOs and alert routing;
- load/concurrency benchmarks beyond the focused canonical eligibility/autonomy contracts;
- security/dependency scanning policy beyond the accepted npm high-severity gate;
- production deployment rehearsal;
- provider outage/degradation drills;
- database restore and migration rollback/forward-recovery evidence;
- long-lived cost/latency/quality telemetry.

These should be added based on production risk, not to maximize tooling count.

---

## 22. Current non-claims

The repository does **not** currently claim:

- connector-introspected proof of the GitHub ruleset configuration; the enforcement record is owner-confirmed from repository Settings;
- complete PostgreSQL coverage of every backend test;
- a complete transitive Python lock;
- Playwright/browser E2E coverage;
- completed god-module decomposition;
- complete future Organizational Immune System implementation beyond the closed H.2 bounded foundation;
- revision-conflict recurrence thresholds or circuit opening from revision conflicts;
- automatic retry/rebase or reuse of stale H.2.4 producer output;
- verifier-stage or G.2/G.3 revision-race attribution;
- reassessment rollback policy;
- provider/runtime health scoring or provider-wide quarantine;
- rolling-window runtime anomaly policy;
- automatic Immune System recovery;
- accepted I.1 autonomy-profile implementation before exact-candidate proof is green;
- automatic earned-autonomy promotion or dynamic downgrade;
- a Dynamic Autonomy Manager;
- agent self-promotion or self-grading as permission;
- provider/model-specific autonomy grants;
- a single organization-wide autonomy score;
- full Organizational Immune System implementation;
- production-scale operational readiness.

These are intentionally explicit so implementation, documentation and acceptance state remain consistent.

---

## 23. Current canonical records

Accepted architecture / history:

- `docs/GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`
- `docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md` (historical predecessor)
- `docs/TECHNOLOGY_RADAR_V1_3_1.md`
- `docs/V1_3_H2_FOUNDATION_CLOSURE_AND_I1_ENTRY_2026-08-21.md`
- `docs/PLASMA_AIOS_ADOPTION_V1.md`
- `docs/CHANGELOG.md`
- `docs/V1_3_G5_ELIGIBILITY_REASSESSMENT_SUPERSESSION.md`
- `docs/V1_3_G5_ACCEPTANCE_2026-08-20.md`
- `docs/V1_3_H1_ELIGIBILITY_IMMUNE_CIRCUIT_FOUNDATION.md`
- `docs/V1_3_H1_PRODUCTION_PROOF_GATE.md`
- `docs/V1_3_H1_ACCEPTANCE_2026-08-21.md`
- `docs/V1_3_H2_1_ELIGIBILITY_WARNING_RECURRENCE_GUARD.md`
- `docs/V1_3_H2_1_ACCEPTANCE_2026-08-21.md`
- `docs/V1_3_H2_2_ELIGIBILITY_RUNTIME_HEALTH_ATTRIBUTION.md`
- `docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md`
- `docs/V1_3_H2_3_REVISION_CONFLICT_ATTRIBUTION_FOUNDATION.md`
- `docs/V1_3_H2_3_ACCEPTANCE_2026-08-21.md`
- `docs/V1_3_H2_4_POST_PRODUCER_REVISION_RACE_ATTRIBUTION.md`
- `docs/V1_3_H2_4_ACCEPTANCE_2026-08-21.md`
- `docs/V12_18_PENDING_CHANGELOG.md` (historical filename; content closed as the V12.18 acceptance changelog)

Accepted H.2.2 classification-refinement records:

- `docs/V1_3_H2_2_RUNTIME_HEALTH_CLASSIFICATION_REFINEMENT_2026-08-21.md`
- `docs/V1_3_H2_2_RUNTIME_HEALTH_CLASSIFICATION_ACCEPTANCE_2026-08-21.md`

Active I.1 implementation record:

- `docs/V1_3_I1_CAPABILITY_AUTONOMY_PROFILE_FOUNDATION_2026-08-21.md` — IMPLEMENTED / ACCEPTANCE PENDING

Repository enforcement state:

- active `Production proof enforcement` ruleset targets `main`;
- pull request integration is required;
- branches must be up to date before merging;
- all four V12 Production Proof checks are required;
- deletions and force pushes are restricted;
- bypass list is empty;
- configuration is owner-confirmed from GitHub Settings.

The accepted technical baseline remains H.2.4 plus the sealed H.2.2 runtime-health classification refinement. The H.2 bounded safety/measurement foundation is CLOSED. V1.3-I.1 is IMPLEMENTED / ACCEPTANCE PENDING, and no automatic promotion/downgrade policy or future H-stage policy is selected or pre-authorized.

---

## 24. Current roadmap statement

Global Mobility AIOS is not changing direction away from high-autonomy architecture.

The delivery correction succeeded in converting architectural safety claims into continuously executable and repository-enforced proof. That bounded H-stage foundation is closed. The first I-stage implementation now adds canonical capability-specific autonomy truth, append-only evidence-backed profile history and Board inspection without introducing automatic promotion or a second governance framework.

> **The next risk is no longer lack of architectural ideas. It is maintaining the discipline that architectural sophistication remains continuously proven and repository-enforced.**

The governing sequence is now:

```text
G.5 accepted baseline
→ H.1 canonical lineage + circuit foundation — SEALED
→ Production Proof + required GitHub checks — SEALED
→ H.2.1 verifier-disagreement recurrence — SEALED
→ H.2.2 trusted runtime-health attribution — SEALED
→ H.2.3 pre-egress revision-conflict attribution — SEALED
→ H.2.4 post-producer revision-race attribution — SEALED
→ H.2.2 runtime-health classification refinement — SEALED
→ H.2 bounded safety/measurement foundation — CLOSED
→ I.1 capability-specific autonomy profile/evidence — IMPLEMENTED / ACCEPTANCE PENDING
→ exact-candidate Production Proof — REQUIRED
→ later Earned Autonomy promotion/downgrade policy — NOT STARTED
→ broader Organization Fabric / operational scale
```
