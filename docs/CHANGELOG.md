# Global Mobility AIOS — V12 Active Changelog

This changelog records meaningful delivery on:

```text
roadmap/global-mobility-aios-v12
```

Repository lineage:

```text
V12 fork origin
  dd2f2cd6e9e47179b1fd744ba3f56daf7c787449

Frozen V11 reference branch final documentation head
  ac130deaafa7aa44068e9459facbda2b4df327d6
```

> **V11 preserves the reference product checkpoint. V12 is the active implementation line.**

Exact historical diffs remain available through Git history, the frozen V11 branch and archived changelogs.

---

## 2026-08-20 — V1.3-E FIRST GOVERNED MOBILITY VERTICAL — E.1 + E.2 COMPLETE / PASS / SEALED

### Status

**The first governed Global Mobility AIOS vertical is accepted through E.2. A persistent AI employee can now receive governed mobility truth, execute through a bound runtime, emit a typed material eligibility proposal, and have AIOS independently validate and route that proposal through the Command Gateway without allowing the model to mutate eligibility truth.**

Accepted chain:

```text
OrganizationPosition
→ ContextBundle
→ EmployeeRuntimeBinding
→ E.1 governed mobility pathway brief
→ E.2 typed EligibilityTransitionIntent
→ deterministic domain validation
→ MaterialAction(eligibility.transition)
→ Command Gateway
→ REVIEW_REQUIRED / BLOCK
→ durable Board-inspectable attempt
→ NO eligibility mutation
```

### E.1 acceptance

E.1 is now:

```text
COMPLETE / PASS / SEALED
```

Accepted evidence:

```text
Repository policy             PASS
Full API regression           969 passed / 5 skipped / 1 warning / 0 failed
Database migration check      PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS
Actual tables                 118
Physical tables               119 incl. alembic_version
git diff --check              clean
```

Canonical records:

```text
docs/V1_3_E1_GOVERNED_MOBILITY_PATHWAY_BRIEF.md
docs/V1_3_E1_ACCEPTANCE_2026-08-20.md
```

E.1 remains read-only. It proves governed pathway Evidence/rules/policy can reach a bound hosted runtime without arbitrary WorkItem working context promoting itself into authority.

### E.2 acceptance

E.2 is now:

```text
COMPLETE / PASS / SEALED
```

Accepted evidence:

```text
Repository policy             PASS
Full API regression           984 passed / 5 skipped / 1 warning / 0 failed
Duration                      355.85s
Database migration check      PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS
Actual tables                 118
Physical tables               119 incl. alembic_version
git diff --check              clean
V12 branch                    clean / synchronized
```

Canonical records:

```text
docs/V1_3_E2_GOVERNED_ELIGIBILITY_TRANSITION_INTENT.md
docs/V1_3_E2_ACCEPTANCE_2026-08-20.md
```

E.2 proves:

- `OrganizationPosition.position_key` is the organizational actor identity;
- provider/model/runtime identity is not authority;
- case/profile records participate in ContextBundle freshness;
- the runtime emits only a narrow typed proposal;
- AIOS constructs `MaterialAction(eligibility.transition)` itself;
- forged/stale Evidence or VerifiedRule citations fail closed;
- confidence is informational only;
- A0 remains prohibited;
- A1–A5 remain unable to execute the R3 eligibility transition while independent verification is unsatisfied;
- REVIEW_REQUIRED/BLOCK attempts are durable and Board-inspectable;
- no `EligibilityAssessment`, Lead eligibility truth, application state, client-facing recommendation or external action is mutated.

The case-scoped pilot deliberately requires an explicitly supplied provider adapter and does not claim a completed provider-egress/sensitivity policy.

### Roadmap effect

The active roadmap advances from **V12.10 to V12.11**.

```text
V1.3-A  COMPLETE / PASS / SEALED
V1.3-B  COMPLETE / PASS / SEALED
V1.3-C  COMPLETE / PASS / SEALED through C.4
V1.3-D  COMPLETE / PASS / SEALED through D.3
V1.3-E  COMPLETE / PASS / SEALED through E.2
V1.3-F  Decision Readiness — NEXT / NOT YET IMPLEMENTED
```

Decision Readiness remains routing/quality infrastructure rather than authorization:

> **Scores route; deterministic gates authorize.**

No canonical eligibility mutation is authorized until Decision Readiness and genuinely independent verification are implemented and accepted.

Known non-blocking warning remains the existing Starlette/httpx deprecation warning. No dependency change is implied.

No GitHub CI PASS is claimed without attached status/check evidence.

---

## 2026-08-20 — MUNDER DIFFLIN v0.4.4 FROZEN DONOR SOURCE — VENDORED INTO AIOS

### Status

**The exact Munder Difflin `v0.4.4` donor baseline is now available inside the Global Mobility AIOS repository for direct AI-assistant and developer inspection. This is a reference/provenance import only and does not claim runtime adoption of Munder subsystems.**

Vendored location:

```text
vendor/munder-difflin/v0.4.4/
```

Provenance:

```text
upstream repository  chaitanyagiri/munder-difflin
upstream tag         v0.4.4
upstream commit      4b6f8b71ef904a1df908c03430934d1ecda9a744
uploaded ZIP SHA256  8c7a152873f72a2ddbb2f508a02bfe49903c8feb1ba59d1aaec30befa4b6e82a
```

The snapshot preserves source, tests, runtime resources/Skills, tools/scripts/prototypes, package/configuration material and the primary upstream architecture/specification documents. `SOURCE_MANIFEST.txt` and `AIOS_VENDOR_METADATA.md` are included for inspection and provenance.

The donor snapshot remains **read-only reference material**. AIOS production implementation must continue through explicit DIRECT REUSE / PORT / ADAPT / REIMPLEMENT / REJECT decisions and AIOS-owned modules behind the Context Broker, authority/autonomy contracts, Evidence model, Canonicalization, Command Gateway, Transparency Layer and Organizational Immune System.

### Licensing boundary

Munder's upstream `LICENSE` states that the bundled LimeZu pixel-art assets are not covered by the MIT source-code license and that the free-version visual assets are non-commercial. Those art assets are intentionally excluded from the AIOS vendor snapshot; the relevant attribution notice is retained where available.

This also matches the accepted product direction: Munder's pixel-office presentation is not the AIOS target. The Living Organization will use a completely redesigned premium modern 2D/2.5D cartoon-character system.

Heavy documentation media, generated website output, release binaries, caches, logs and generated build output are also intentionally excluded.

Canonical records:

```text
docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md
docs/MUNDER_DIFFLIN_VENDOR_SNAPSHOT_V0_4_4.md
vendor/munder-difflin/v0.4.4/AIOS_VENDOR_METADATA.md
vendor/munder-difflin/v0.4.4/SOURCE_MANIFEST.txt
```

No migration, database mutation, production dependency, authority expansion, runtime behavior or acceptance-state change is claimed by this import.

---

## 2026-08-20 — FINAL COMBINED AIOS + MUNDER DIFFLIN ARCHITECTURE — DOCUMENTATION CHECKPOINT

### Status

**The Global Mobility AIOS V1.3 architecture has been consolidated with the selected compatible capabilities from Munder Difflin v0.4.4. This is an architecture/documentation checkpoint only; it does not claim runtime implementation or PASS for the newly described Munder-derived subsystems.**

New canonical documents:

```text
docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md
docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md
```

Updated canonical surfaces:

```text
README.md
docs/ROADMAP.md
docs/CHANGELOG.md
```

### Final architecture decision

Munder Difflin v0.4.4 is now treated as a **frozen strategic donor / controlled adoption programme** rather than merely an informal architecture reference.

The governing rule is:

> **Global Mobility AIOS remains the product, domain model, constitutional authority, canonical truth system and governing architecture. Munder supplies implementation mechanics where compatible.**

AIOS retains exclusive ownership of Human Owner / Board supremacy, organizational meaning, OrganizationPosition identity, Mission/WorkItem semantics, Evidence and SourceSnapshots, VerifiedRules and domain meaning, authority/delegation/autonomy, risk and Decision Readiness, Command Gateway decisions, canonical state, Board Transparency/Decision Lineage and Global Mobility business truth.

### Explicitly preserved V1.3 primitives

The combined architecture preserves Human Owner / Board supreme authority, Board by exception, cross-cutting Transparency, Decision Lineage, persistent AI employees, Memory ≠ Truth, Context Broker / ContextBundle, Capability ≠ Authority ≠ Autonomy ≠ Risk, capability-specific A0–A5 autonomy, risk-tiered verification, independent verification, typed MaterialAction, Canonicalization/Command Gateway, concurrency/idempotency, Organizational Immune System, Evidence trust ladder and provider/framework independence.

### New explicitly adopted combined-architecture features

The final combined architecture adds or makes explicit AIOS Organization Fabric, Agent Runtime Fabric, Organizational Communication Fabric, Dynamic Mission Squads, Mission Rooms, presence/heartbeats, agent relationships, Skills runtime, Event Nervous System, Professional Peer Review Network, Flight Recorder, Replay, Shadow Employees, AI Economics, Organization/Decision Graph, Living Organization, specialized Engineering Workspace and future voice/realtime concepts.

### Munder donor mapping

High-value Munder donor areas include messaging/routing, provider/runtime abstraction, PTY/CLI execution, Skills, task coordination, circuit breaking, triggers/schedules/heartbeats, webhooks, memory mechanics, transcripts/telemetry, token/cost signals, graph/live-scene mechanics, worktrees/IDE and voice/realtime concepts.

Hard architectural rejects remain:

```text
SQLite/file state as canonical authority
GOD-style unlimited implicit authority
direct agent mutation of authoritative state
provider-owned organizational semantics
retro pixel-office presentation as final AIOS UI
```

### Living Organization decision

The Munder 2D-office idea is retained only as a conceptual/runtime donor. AIOS will pursue a **premium modern 2D/2.5D Living Organization with modern cartoon AI employees** whose animation is tied to genuine organizational state. No fabricated busywork should be generated merely to make the interface look alive.

### Historical implementation truth at this checkpoint

At the time this architecture checkpoint was written, C.4 was still recorded as acceptance pending. Later changelog entries supersede that status. Changelog entries remain historical rather than being rewritten to pretend later evidence existed earlier.

---

## 2026-08-20 — V1.3-C.4 BOARD/COCKPIT TRANSPARENCY READ CONTRACT — IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

This historical entry records the state when C.4 was first implemented. C.4 was subsequently accepted and sealed; see `docs/V1_3_C4_ACCEPTANCE_2026-08-20.md` and the current ROADMAP for canonical status.

Product-facing API:

```text
GET /api/v1/organization/transparency/traces/{trace_id}
GET /api/v1/organization/transparency/work-items/{work_item_id}
```

Current access remains limited to the trusted Board mapping. Tenant isolation, safe bounded projections and fail-closed malformed-data behavior are preserved.

---

## 2026-08-20 — V1.3-C.3 EXPLICIT GOVERNANCE → EFFECT CAUSATION — COMPLETE / PASS / SEALED

C.3 sealed explicit authorization-to-effect lineage for the first governed WorkItem mutation path. Canonical acceptance was reported all green by the Human Owner from the prescribed Windows V12 sequence. Exact final pytest counts were not restated and are not invented.

The last separately evidenced full API baseline before C.3 remains C.2's `922 passed / 5 skipped / 1 warning / 0 failed` and is not relabeled as a C.3 result.

See `docs/V1_3_C3_ACCEPTANCE_2026-08-20.md`.

---

## 2026-08-20 — V1.3-C.2 NON-EXECUTING MATERIAL ATTEMPT TRANSPARENCY — COMPLETE / PASS / SEALED

C.2 sealed durable Board-inspectable transparency for blocked/review-routed material governance attempts even when no domain mutation occurs.

Accepted full API evidence:

```text
922 passed / 5 skipped / 1 warning / 0 failed
```

See `docs/V1_3_C2_NON_EXECUTING_ATTEMPT_TRANSPARENCY.md` and `docs/V1_3_C2_ACCEPTANCE_2026-08-20.md`.

---

## 2026-08-20 — V1.3-C.1 TRANSPARENCY TRACE FOUNDATION — COMPLETE / PASS / SEALED

C.1 established the tenant-scoped durable transparency projection over `OrganizationActivity`.

Accepted evidence:

```text
Focused B.1+B.2+C.1          31 passed / 1 warning / 0 failed
Full API regression           917 passed / 5 skipped / 1 warning / 0 failed
```

See `docs/V1_3_C1_TRANSPARENCY_TRACE_FOUNDATION.md` and `docs/V1_3_C1_ACCEPTANCE_2026-08-20.md`.

---

## 2026-08-20 — V1.3-B.2 GOVERNED WORKITEM ASSIGNMENT — COMPLETE / PASS / SEALED

B.2 sealed the first real material domain mutation executed through the V1.3 Governance Kernel.

Accepted evidence:

```text
Focused B.1 + B.2             25 passed / 1 warning / 0 failed
Full API regression           911 passed / 5 skipped / 1 warning / 0 failed
```

---

## 2026-08-20 — V1.3-B.1 MINIMAL GOVERNANCE KERNEL — COMPLETE / PASS / SEALED AS FOUNDATION

B.1 accepted deterministic capability authority, A0–A5 routing, R0–R5 risk floors, typed MaterialAction, expected-version handling, idempotency, Board-reserved protection, trace identity and OrganizationActivity-compatible governance projection.

Accepted full API regression:

```text
905 passed / 5 skipped / 1 warning / 0 failed
```

---

## 2026-08-20 — V1.3-A CONSTITUTIONAL CONTRACTS — COMPLETE / PASS / SEALED

Accepted full API regression:

```text
886 passed / 5 skipped / 1 warning / 0 failed
```

Historical compatibility markers permanently preserved:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

---

## 2026-08-19 — V12 ROADMAP / README ALIGNMENT

V12 documentation was separated from the frozen V11 reference after the branch split and aligned to the V1.3 direction.

---

## 2026-08-19 — V12 DEVELOPMENT BRANCH OPENED

V12 forked from:

```text
roadmap/global-mobility-aios-v11
@ dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

The frozen V11 branch remains the reference/recovery checkpoint.

---

## History before V12

Use Git history and the frozen V11 branch for exact pre-V12 state.

Existing archives include:

- `docs/archive/CHANGELOG_THROUGH_C192E7D_2026-08-19.md`;
- `docs/archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md`;
- `docs/archive/ROADMAP_V11_5_HIGH_AUTONOMY_DIRECTION_2026-08-19.md` on the final V11 reference branch.

Git history remains the immutable source for exact historical diffs and commit lineage.
