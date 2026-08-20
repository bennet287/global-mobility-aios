# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.18 — production-proof correction  
**Date:** 2026-08-20  
**Active development branch:** `roadmap/global-mobility-aios-v12`  
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`  
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`  
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Active organization architecture:** `HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md` + `GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`  
**Munder donor baseline:** `v0.4.4` — strategic donor / controlled adoption programme  
**Last accepted V1.3 checkpoint:** V12.17 / V1.3-G.5 — COMPLETE / PASS / SEALED  
**Current implementation candidate:** V1.3-H.1 — Eligibility Immune Circuit Foundation — IMPLEMENTED / ACCEPTANCE PENDING  
**Current proof programme:** H.1 canonical-lineage consolidation + V12 Production Proof Gate — IMPLEMENTED / ACCEPTANCE PENDING  
**H.1 seal:** PAUSED pending real regression / PostgreSQL / frontend / repository proof  
**H.2:** BLOCKED until H.1 and the Production Proof Gate are accepted  
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
| V1.3-H.1 Eligibility Immune Circuit | IMPLEMENTED / ACCEPTANCE PENDING | Restrictive aggregate circuit and signal wiring exist; seal paused |
| V12 Production Proof Gate | IMPLEMENTED / ACCEPTANCE PENDING | CI/real-DB/frontend/dependency proof infrastructure exists; green evidence not yet recorded |
| V1.3-H.2 | BLOCKED | No additional Immune System feature slice until H.1 proof is accepted |
| V1.3-I Earned Autonomy | NOT STARTED | Follows accepted H-stage safety/measurement foundations |

The accepted baseline remains **G.5** until the H.1 proof programme produces actual evidence.

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

## 5. Last accepted quality evidence — V1.3-G.5

Historical accepted results are not represented as rerun unless actually rerun.

The latest accepted V1.3 evidence remains:

```text
G.5 precondition + G.3 baseline          20 passed / 1 warning / 0 failed
G.5 E.2/G.2 integration                 38 passed / 1 warning / 0 failed
G.5 canonical-effect core               28 passed / 1 warning / 0 failed
E.2 → G.5 effect vertical               84 passed / 1 warning / 0 failed
G.4 + G.5 orchestration/API             15 passed / 1 warning / 0 failed
E.2 → G.5 full governed vertical        99 passed / 1 warning / 0 failed
Platform hardening                      8 passed / 1 warning / 0 failed
Repository policy                       PASS
Full API regression                     1075 passed / 5 skipped / 1 warning / 0 failed
Duration                                397.94s
Database migration check                PASS
Migration head                          0077_canonical_eligibility_assessment_revision
Registered tables                       119
Local DB schema                         PASS
Actual tables                           119
Physical tables                         120 incl. alembic_version
git diff --check                        clean
V12 branch                              clean / synchronized
```

Canonical acceptance records are preserved under `docs/V1_3_*_ACCEPTANCE_2026-08-20.md` for D.1 through G.5.

No current H.1 test count, PostgreSQL PASS, frontend PASS or GitHub CI PASS is claimed until those checks actually run.

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

## 8. Current H.1 implementation candidate

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

## 9. H.1 release blocker resolved in implementation — acceptance still pending

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

This repair is **implemented but not yet accepted**.

---

## 10. Adversarial H.1 regression requirement

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

G.3/G.4 replay must fail closed on the same canonical invariant.

---

## 11. Production Proof Gate — required before H.2

Canonical proof record:

```text
docs/V1_3_H1_PRODUCTION_PROOF_GATE.md
```

CI workflow:

```text
.github/workflows/v12-production-proof.yml
```

The gate contains four lanes.

### 11.1 Repository policy / dependency contract

```text
repository policy
release consistency
Python direct-dependency constraints
diff hygiene
```

Repository policy now also rejects shell-redirection-like tracked filenames. The accidental `apps/api/=5.4` artifact has been removed.

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

### 11.3 Frontend proof

```text
npm ci
design-foundation tests
request/auth tests
TypeScript --noEmit
Next.js production build
compiled-auth tests
```

There is not yet a Playwright/browser workflow suite. A browser golden journey is required before aggressive frontend restructuring.

### 11.4 PostgreSQL governance proof

A real PostgreSQL 16 service is migrated through the single Alembic head, physically checked against SQLModel metadata, then used by focused governance tests.

The same pytest fixture switches to PostgreSQL only when:

```text
GMAI_TEST_DATABASE_URL=postgresql+psycopg://...
```

The focused lane covers existing G.3/G.4/G.5/H.1 semantics plus explicit cross-session contracts for stale reassessment and circuit recovery/reopen behavior.

---

## 12. Python dependency reproducibility

Backend direct dependencies remain declared in:

```text
apps/api/requirements.txt
```

Exact direct-dependency constraints now live in:

```text
apps/api/constraints.txt
```

Required constrained install:

```text
python -m pip install -r apps/api/requirements.txt -c apps/api/constraints.txt
```

The API Docker image and V12 Production Proof workflow use the same constraints.

Current claim boundary:

> **This is a direct-dependency reproducibility baseline, not yet a complete transitive lock.**

A transitive lock may be added after this baseline is proven on the supported environments.

---

## 13. Migration/data-model doctrine

The accepted schema currently has 119 registered SQLModel tables and one controlled Alembic head:

```text
0077_canonical_eligibility_assessment_revision
```

The concentration of models in `domain.py` is a maintainability risk, but the migration doctrine remains:

> **Split model modules by bounded context; retain one SQLModel metadata registry and one controlled linear Alembic lineage/head.**

Do not create independent migration heads merely to mirror code-module boundaries.

The production-proof migration checker now validates:

```text
exactly one Alembic head
physical schema matches registered SQLModel tables/columns
alembic_version equals the declared head
```

for SQLite and PostgreSQL when those databases are supplied.

---

## 14. Complexity/decomposition programme — sequenced, not simultaneous

Large-module concentration is accepted as a maintainability risk. It is not a reason to begin four broad refactors before the proof system is reliable.

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

## 15. H.1 acceptance gate

H.1 remains **ACCEPTANCE PENDING** until all required proof is real:

1. shared canonical-lineage focused tests pass;
2. adversarial Activity-identity corruption tests pass;
3. fresh structural corruption produces CRITICAL circuit OPEN before provider calls;
4. G.3/G.4 historical replay fails closed on corrupted lineage;
5. full backend regression passes;
6. Alembic + physical schema checks pass;
7. frontend Node tests pass;
8. TypeScript check passes;
9. Next.js production build passes;
10. PostgreSQL migration upgrade passes;
11. PostgreSQL migration/schema contract passes;
12. focused PostgreSQL governance contracts pass;
13. cross-session stale reassessment contract passes;
14. cross-session circuit recovery/reopen contract passes;
15. repository policy passes;
16. dependency constraint enforcement passes;
17. branch/head/docs are synchronized;
18. required-check enforcement in GitHub repository settings is either verified or explicitly recorded as a remaining settings action.

No H.1 acceptance document is created before this gate is satisfied.

---

## 16. Immediate execution order

This ordering is authoritative for the next work:

```text
1. H.1 seal paused
2. canonical eligibility-lineage consolidation
3. adversarial regression
4. full H.1 / governed-vertical acceptance
5. Production Proof Gate green on SQLite + frontend + PostgreSQL
6. reconcile ROADMAP / CHANGELOG / acceptance record
7. verify required GitHub check enforcement
8. only then begin H.2
```

Steps 2–3 and the CI implementation for step 5 are currently implemented. They remain acceptance-pending until executed successfully.

---

## 17. V1.3-H.2 — blocked future scope

H.2 must not begin until section 15 is green.

Potential bounded H.2 work includes only evidence-driven extensions such as:

- recurrence thresholds;
- rolling-window anomaly policy;
- incident aggregation;
- root-cause classification;
- provider/runtime health scoring;
- broader but still scope-limited blast-radius controls;
- automatic escalation routing where constitutionally valid.

Do not begin with a generic anomaly platform.

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

---

## 21. Operational proof still to add after this gate

The V12 Production Proof Gate is the minimum continuous proof boundary, not the endpoint of operational maturity.

Still required later:

- Playwright/browser golden journey;
- controlled failure/recovery drills;
- backup/restore proof;
- observability SLOs and alert routing;
- load/concurrency benchmarks beyond the focused canonical eligibility contract;
- security/dependency scanning policy;
- production deployment rehearsal;
- provider outage/degradation drills;
- database restore and migration rollback/forward-recovery evidence;
- long-lived cost/latency/quality telemetry.

These should be added based on production risk, not to maximize tooling count.

---

## 22. Current non-claims

The repository does **not** currently claim:

- H.1 PASS or SEALED;
- green results for the newly added V12 Production Proof workflow;
- mandatory branch-protection enforcement of the new checks;
- complete PostgreSQL coverage of every backend test;
- a complete transitive Python lock;
- Playwright/browser E2E coverage;
- completed god-module decomposition;
- H.2 implementation;
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

Current acceptance-pending work:

- `docs/V1_3_H1_ELIGIBILITY_IMMUNE_CIRCUIT_FOUNDATION.md`
- `docs/V1_3_H1_PRODUCTION_PROOF_GATE.md`
- `.github/workflows/v12-production-proof.yml`

The accepted changelog remains anchored at G.5 until the current proof gate produces real acceptance evidence. Pending implementation history is preserved by Git commits and the H.1 proof records above; it must not be misrepresented as accepted delivery.

---

## 24. Current roadmap statement

Global Mobility AIOS is not changing direction away from high-autonomy architecture.

The delivery correction is:

> **The next risk is no longer lack of architectural ideas. It is the gap between architectural sophistication and continuously enforced production proof.**

Therefore the project now prioritizes invariant consolidation, adversarial regression, mandatory-quality workflow execution, real PostgreSQL proof, dependency/repository hygiene and operational evidence before adding another Immune System feature slice.

The governing sequence is:

```text
G.5 accepted baseline
→ H.1 candidate
→ canonical lineage repair
→ adversarial proof
→ Production Proof Gate
→ H.1 acceptance/seal
→ H.2
→ Earned Autonomy
→ broader Organization Fabric / operational scale
```
