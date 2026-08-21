# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.18+ — production-proof discipline extended into H.2
**Date:** 2026-08-21
**Active development branch:** `roadmap/global-mobility-aios-v12`
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR
**Active organization architecture:** `HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md` + `GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`
**Munder donor baseline:** `v0.4.4` — strategic donor / controlled adoption programme
**Last accepted V1.3 checkpoint:** V1.3-H.2.2 — COMPLETE / PASS / SEALED on technical candidate `c5c2a68ac3a9caf2551204d61862b6ad0b6281eb`
**Latest accepted Production Proof:** GitHub Actions run `32473526874` — 4/4 jobs PASS
**Required-check enforcement:** CONFIGURED / OWNER-CONFIRMED — active `Production proof enforcement` ruleset on `main`
**H.2:** IN PROGRESS — H.2.1 and H.2.2 SEALED; next bounded H.2 increment NOT STARTED
**Code migration head:** `0077_canonical_eligibility_assessment_revision`

<!-- CURRENT_MIGRATION_HEAD: 0077_canonical_eligibility_assessment_revision -->

> **V11 preserves the checkpoint. V12 proves and implements the direction.**

> **Governance before unrestricted execution. Transparency before increased autonomy. Production proof before additional safety architecture.**

---

## 1. What Global Mobility AIOS is

Global Mobility AIOS is being built as a **governed, transparent, self-improving, high-autonomy AI-operated professional Global Mobility organization**.

It is not merely an immigration chatbot, visa questionnaire, generic AI assistant, CRM with AI, document uploader, workflow engine, disconnected multi-agent demo, generic SaaS/admin surface, browser agent or human approval queue.

Target identity:

> **Persistent AI employees research, reason, collaborate, remember, use tools, manage work, prepare professional outputs, make authorized decisions, execute bounded real-world operations and learn from outcomes while the Human Owner / Board retains supreme strategic and reserved authority.**

Operating principles:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Board by exception. Transparency by default.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

> **Architectural sophistication must be matched by automated production proof.**

Canonical architecture records:

- `docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`
- `docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

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
| V1.3-H.2 overall | IN PROGRESS | H.2 proceeds only as separately proven bounded increments; no broader health policy is pre-authorized |
| V12 Production Proof Gate | ACCEPTED / GREEN | Repository, backend SQLite, frontend and PostgreSQL lanes are continuously executable; latest accepted H.2.2 run `32473526874` |
| Required GitHub check enforcement | CONFIGURED / OWNER-CONFIRMED | Active `Production proof enforcement` ruleset protects `main` and requires all four Production Proof checks |
| V1.3-I Earned Autonomy | NOT STARTED | Follows accepted H-stage safety/measurement foundations |

The accepted V1.3 baseline is now **H.2.2**. Detailed evidence is preserved in `docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md`.

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

## 5. Latest accepted quality evidence — V1.3-H.2.2

Historical accepted results are not represented as rerun unless actually rerun.

H.1 and H.2.1 remain sealed by their own acceptance records. H.2.2 adds the following accepted proof:

```text
H.2.2 local focused H-stage regression      48 passed / 1 skipped / 1 warning / 0 failed
GitHub backend regression                   1118 passed / 8 skipped / 1 warning / 0 failed
Fresh PostgreSQL 16 Alembic                 PASS — 0001 → 0077
Registered SQLModel tables                  119
Fresh PostgreSQL physical schema            PASS
GitHub PostgreSQL governed suite            71 passed / 1 warning / 0 failed
H.2.2 producer attribution                  PASS
H.2.2 verifier attribution + causation      PASS
H.2.2 deterministic replay                  PASS
H.2.2 torn-pair fail-closed                  PASS
H.2.2 paired-write rollback atomicity       PASS
H.2.2 trusted runtime identity drift reject PASS
Repeated runtime warnings remain observe    PASS — no circuit open
Frontend npm ci                             PASS
Frontend high-severity audit                PASS
Frontend design foundation                  PASS
Frontend request/auth                       PASS
Frontend TypeScript                         PASS
Frontend Next.js 16.3.1 build               PASS
Frontend compiled auth                      PASS
Repository policy                           PASS
Release consistency                         PASS — 0077
Python dependency constraints               PASS — 25 direct dependencies
Diff hygiene                                PASS — git diff --check HEAD^
GitHub Production Proof run 32473526874     4/4 jobs PASS
Accepted technical candidate                c5c2a68ac3a9caf2551204d61862b6ad0b6281eb
```

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

Canonical acceptance records include `docs/V1_3_*_ACCEPTANCE_2026-08-20.md` for D.1 through G.5, `docs/V1_3_H1_ACCEPTANCE_2026-08-21.md` for H.1, `docs/V1_3_H2_1_ACCEPTANCE_2026-08-21.md` for H.2.1 and `docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md` for H.2.2.

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

Latest accepted H.2.2 GitHub-hosted run:

```text
candidate = c5c2a68ac3a9caf2551204d61862b6ad0b6281eb
run       = 32473526874

Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

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

Latest accepted H.2.2 backend result:

```text
1118 passed / 8 skipped / 1 warning / 0 failed
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

The focused lane covers G.3/G.4/G.5/H.1 and accepted H.2 eligibility safety contracts. H.2.2 adds both its normal runtime-health attribution tests and adversarial atomicity/identity-drift tests to this lane.

Latest accepted PostgreSQL evidence from H.2.2:

```text
Alembic 0001 → 0077              PASS
registered tables                 119
physical schema                   PASS
governed eligibility suite        71 passed / 1 warning / 0 failed
```

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

The accepted schema currently has 119 registered SQLModel tables and one controlled Alembic head:

```text
0077_canonical_eligibility_assessment_revision
```

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

H.2.2 intentionally introduces no new table or migration.

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

### 14.2 Frontend API decomposition

Split domain clients behind one common request/auth/error primitive. Do not create duplicate fetch/auth frameworks.

### 14.3 CSS decomposition

Move design tokens, primitives, layouts and feature styles incrementally. Preserve visual behavior through build/tests and future browser golden journeys.

### 14.4 Governance-service decomposition

Extract only semantic seams with stable contracts and tests. Do not split by arbitrary line-count quotas.

Permanent rule:

> **Improve regression detection before increasing refactor surface area.**

---

## 15. H.1, H.2.1 and H.2.2 acceptance gates — satisfied

H.1 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H1_ACCEPTANCE_2026-08-21.md`.

H.2.1 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H2_1_ACCEPTANCE_2026-08-21.md`.

H.2.2 is **COMPLETE / PASS / SEALED** under `docs/V1_3_H2_2_ACCEPTANCE_2026-08-21.md`.

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

Accepted H.2.2 technical candidate:

```text
c5c2a68ac3a9caf2551204d61862b6ad0b6281eb
```

Accepted H.2.2 GitHub run:

```text
32473526874
```

---

## 16. Immediate execution order

The current H-stage sequence is:

```text
1. H.1 canonical lineage + circuit foundation             COMPLETE / SEALED
2. Production Proof + required-check enforcement          COMPLETE
3. H.2.1 verifier-disagreement recurrence guard           COMPLETE / SEALED
4. H.2.2 runtime-health attribution foundation            COMPLETE / SEALED
5. next bounded H.2 failure model / restriction scope     NOT STARTED
6. define scope/time/blast-radius contract before coding  REQUIRED
7. later H.2 health/anomaly controls                      NOT PRE-AUTHORIZED
8. Earned Autonomy                                        NOT STARTED
```

Browser golden-journey proof and incremental semantic decomposition remain parallel proof/maintainability priorities and do not pre-accept any future H.2 behavior.

---

## 17. V1.3-H.2 — in progress as bounded increments

H.2 is not a single generic anomaly platform. Each increment must have a concrete failure model, a bounded scope and its own proof.

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

### 17.3 Next H.2 increment — not started

The next increment must be selected from evidence, not from symmetry with H.2.1 or the existence of H.2.2 attribution data.

Before code, its design must state:

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

Each H.2 increment must preserve the H.1 rule that the Immune System is restrictive only and must receive its own bounded implementation and proof before acceptance.

---

## 18. V1.3-I — Earned Autonomy

Earned Autonomy remains a later stage after the Immune System has accepted measurement and restriction semantics.

Target principle:

```text
promotion requires measured evidence
downgrade may be faster than promotion
scope is capability-specific
agents cannot self-promote
Board ceilings remain supreme
```

The Immune System may reduce autonomy; it does not grant authority.

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

H.2.2 improves the future Incident drill-down by making runtime-health warnings attributable to a trusted execution role/runtime identity without changing control authority.

---

## 21. Operational proof still to add after this gate

The V12 Production Proof Gate is the minimum continuous proof boundary, not the endpoint of operational maturity.

Still required later:

- Playwright/browser golden journey;
- controlled failure/recovery drills;
- backup/restore proof;
- observability SLOs and alert routing;
- load/concurrency benchmarks beyond the focused canonical eligibility contract;
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
- H.2 completion;
- a selected or implemented H.2.3 policy;
- provider/runtime health scoring or provider-wide quarantine;
- rolling-window runtime anomaly policy;
- automatic Immune System recovery;
- earned-autonomy implementation;
- full Organizational Immune System implementation;
- production-scale operational readiness.

These are intentionally explicit so implementation, documentation and acceptance state remain consistent.

---

## 23. Current canonical records

Accepted architecture / history:

- `docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`
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
- `docs/V12_18_PENDING_CHANGELOG.md` (historical filename; content closed as the V12.18 acceptance changelog)

Repository enforcement state:

- active `Production proof enforcement` ruleset targets `main`;
- pull request integration is required;
- branches must be up to date before merging;
- all four V12 Production Proof checks are required;
- deletions and force pushes are restricted;
- bypass list is empty;
- configuration is owner-confirmed from GitHub Settings.

The accepted baseline is H.2.2. No H.2.3 policy has been selected or pre-authorized.

---

## 24. Current roadmap statement

Global Mobility AIOS is not changing direction away from high-autonomy architecture.

The delivery correction succeeded in converting architectural safety claims into continuously executable and repository-enforced proof. H.2 now extends that discipline one bounded failure model at a time.

> **The next risk is no longer lack of architectural ideas. It is maintaining the discipline that architectural sophistication remains continuously proven and repository-enforced.**

The governing sequence is now:

```text
G.5 accepted baseline
→ H.1 canonical lineage + circuit foundation — SEALED
→ Production Proof + required GitHub checks — SEALED
→ H.2.1 verifier-disagreement recurrence — SEALED
→ H.2.2 trusted runtime-health attribution — SEALED
→ next bounded H.2 failure model — NOT STARTED / NOT PRE-AUTHORIZED
→ Earned Autonomy
→ broader Organization Fabric / operational scale
```
