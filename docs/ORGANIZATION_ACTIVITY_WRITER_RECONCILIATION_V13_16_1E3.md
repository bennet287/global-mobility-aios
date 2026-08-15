# Phase 13.16.1E3 Legacy Writer Reconciliation Audit

## Status

**13.16.1E3A — WRITER INVENTORY / COVERAGE-EPOCH DESIGN: COMPLETE.**

**13.16.1E3B — LEGACY WORKITEM MATERIAL-WRITER ADAPTERS: COMPLETE / PASS.**

**13.16.1E3C — LEGACY EXECUTIVEDECISION / COUPLED ADAPTERS: COMPLETE / PASS.**

E3A writer-inventory baseline reviewed: `8bfbd40a1b4e460757b99d943a139cfd2ef83316`.

E3B implementation baseline: `9e97f0f0e3a1f3c9cbf66a05286e67096195ab64`.
E3B accepted commit: `fac48397a712ddb184fb7fac44f95b71f2860a52`.

E3A was a repository-backed design/reconciliation slice only. E3B is the bounded runtime
adapter slice described below; it does not change the database schema, Contribution
authority, historical coverage truth, or Observatory activation. E3A itself changed no runtime
Python, routers, tests, Activity rows, Austria v4 state, or PostgreSQL data.
`activity_history_established` remains `false`.

## 1. Purpose

E2 added caller-owned Activity staging and semantic adapters to the modern 13.16.1 command
services. E3 closes the remaining truth gap: older Phase 13 organization-governance code
still creates or mutates the same `OrganizationalWorkItem` and `ExecutiveDecision` rows
without the E2 semantic Activity adapters.

The goal is not to turn every state write into Activity. E3 must distinguish material
organizational history from execution leases, retries, reminders, evidence refreshes, and
other intermediate/telemetry state. Only the material writer surface is adapted. Explicit
exclusions remain non-authoritative and must never be used as Contribution volume or
productivity evidence.

## 2. Repository-wide writer boundary

A repository-wide search of application Python at the E3A baseline found the durable
WorkItem/Decision types in the canonical E2 services plus these remaining legacy writer
surfaces:

- `app/routers/organization_governance.py`
- `app/services/organization_governance.py`
- `app/tasks/organization_tasks.py`

`app/tasks/organization_tasks.py` delegates material WorkItem/Decision state changes back
to `organization_governance.py`; its only direct `ExecutiveDecision` write is
`reminded_at`, which is reminder bookkeeping and is excluded from semantic Activity.

The older governance router still constructs WorkItems and Decisions directly in
`create_work_item(...)`. The automation bridge constructs them in
`route_automation_event(...)` and deliberately leaves commit ownership with the enclosing
automation-event transaction.

## 3. Writer inventory and disposition

| Writer / path | Durable mutation | Existing transaction boundary | E3 disposition | Semantic Activity requirement |
|---|---|---|---|---|
| `routers.organization_governance.create_work_item` | direct WorkItem create; optional Decision create | router-owned commit | **ADAPT**; retain route compatibility for now | Work created; Decision created when present |
| `organization_governance.route_automation_event` | direct WorkItem create; optional Decision create | caller-owned automation transaction | **ADAPT IN PLACE**; must not add a commit | Work created; Decision created when present |
| `_requeue_position_holds` / `_requeue_executive_contract_holds` | `held -> queued` WorkItem side effects | enclosing `ensure_foundation_positions` / resume/control transaction | **ADAPT** | Work status requeued |
| `ensure_foundation_positions` callers, including Board snapshot/bootstrap/list-position paths | may trigger the requeue helpers while registering/repairing positions | caller/router commit | **ADAPT SIDE EFFECT**, do not call read-time requeue “telemetry” | Activity only when a WorkItem actually changes |
| `resume_position` | WorkItems held for unavailable/suspended position can return to `queued` | service-owned commit | **ADAPT** | Work status requeued |
| `set_global_control(active)` | eligible held WorkItems can return to `queued` | service-owned commit | **ADAPT** | Work status requeued |
| `set_work_deadline` | WorkItem `due_at` | service-owned commit | **ADAPT** | versioned Work deadline-set Activity |
| `set_decision_deadline` | Decision `due_at` | service-owned commit | **ADAPT** | versioned Decision deadline-set Activity |
| `escalate_work_item` | Work assignment/escalation; possible Decision owner/status change | one service-owned commit | **ADAPT AS COUPLED UNIT** | Work assignment/escalation plus Decision escalation/owner event when changed |
| `mark_work_emergency` | multi-step Work hold/escalation/pending-board; Decision create/update | intentionally multiple replay-safe commits | **ADAPT EACH MATERIAL COMMIT**, do not collapse transactions | Work emergency/hold/assignment/pending-board; Decision create/escalation as applicable |
| `_claim_work_execution` | Work `queued/retry_wait -> running`, attempt/token/lease fields | service-owned claim commit | **EXCLUDE** | execution-claim/attempt telemetry; no curated Activity per retry claim |
| `_mark_execution_failed` while attempts remain | Work `running -> retry_wait`, retry/error fields | service-owned commit | **EXCLUDE RETRY STATE** | retry/attempt telemetry only |
| `_mark_execution_failed` when attempts exhausted | Work terminal `failed` | service-owned commit | **ADAPT TERMINAL BRANCH** | Work failed Activity |
| `_mark_execution_cancelled` | Work terminal `cancelled` | service-owned commit | **ADAPT** | Work cancelled Activity |
| `_hold_work_without_claim` | Work material `held` state with governance reason | service-owned commit | **ADAPT** | Work held Activity |
| `execute_work_item` global-pause branch | Work becomes `held`; currently commits without a matching source AuditLog | service-owned commit | **ADAPT + CLOSE AUDIT GAP** | Work held Activity and source audit in same commit |
| `_execute_claimed_work_item` intermediate delegation/action-output commits | delegation/output/agent progress | multiple execution commits | **EXCLUDE** | raw/intermediate execution evidence; no Activity per delegation/tool/retry |
| `_execute_claimed_work_item` final Work disposition | Work `held`, `completed`, `pending_ceo`, or `pending_board` | final service-owned commit | **ADAPT FINAL DISPOSITION** | one Work material status Activity |
| `_execute_claimed_work_item` Decision evidence refresh | `evidence_json` / `updated_at` only | same final commit | **EXCLUDE AS EVIDENCE REFRESH** | not a Decision outcome/authority transition |
| `cancel_work_item` | cancellation request; immediate terminal cancellation when not running | service-owned commit | **ADAPT** | cancellation-requested Activity; terminal cancelled Activity when same commit closes work |
| `retry_work_item` | explicit admin retry authorization to `queued` | service-owned commit | **ADAPT CONTROL ACTION** | retry-requested Activity; do not infer success |
| `amend_technology_evidence` | Work evidence context; may release `held -> queued` | service-owned commit | **ADAPT MATERIAL READINESS CHANGE** | evidence-amended Activity; Work requeue Activity when state changes |
| `board_override_decision` | terminal Decision outcome and linked Work outcome | one service-owned commit | **ADAPT AS COUPLED UNIT** | Decision outcome + linked Work status Activity |
| `_hold_ceo_decision` | `coordinating_ceo -> pending_ceo` because coordination is held | service-owned commit | **ADAPT** | Decision held Activity |
| `_promote_decision_to_board` | Decision `pending_board`/owner change plus Work `pending_board` | service commit, then Board packet side effect | **ADAPT PRE-PACKET COMMIT** | Decision escalation + Work status Activity |
| `_claim_ceo_decision` lease claim/recovery | `pending_ceo <-> coordinating_ceo` plus lease token/timestamp | lease-management commits | **EXCLUDE LEASE TELEMETRY** | no curated Activity for claim, stale recovery, or token renewal |
| `_release_ceo_claim_after_error` | coordination lease release to `pending_ceo` | error-recovery commit | **EXCLUDE LEASE TELEMETRY** | no curated Activity |
| `_coordinate_claimed_ceo_decision` | recommendation/evidence/impact enrichment only | enclosing coordination flow | **EXCLUDE INTERMEDIATE ANALYSIS** | supporting evidence, not authority outcome |
| `decide_executive_decision` | terminal Decision outcome plus linked Work outcome | one service-owned commit | **ADAPT AS COUPLED UNIT** | Decision outcome + linked Work status Activity |
| `tasks.scan_organization_deadlines` direct Decision `reminded_at` | reminder bookkeeping | task-owned commit | **EXPLICITLY EXCLUDE** | no semantic Activity; reminder is operational bookkeeping |

## 4. Hidden writer behavior that E3 must preserve

### 4.1 Position/bootstrap reads can have WorkItem side effects

`ensure_foundation_positions(...)` is not a pure read helper. Registration or contract
repair can requeue held WorkItems. It is called from bootstrap paths and also from legacy
Board/position snapshot paths that commit after the call. E3 cannot declare history
complete while those side effects remain unadapted.

E3 should not broaden this behavior. If a call produces no WorkItem change it produces no
Work Activity. If it does requeue Work, that material status change must stage Activity in
the same transaction that persists the requeue.

### 4.2 Emergency and runtime execution intentionally use multiple commits

`mark_work_emergency(...)` persists replay-safe escalation hops. `_execute_claimed_work_item(...)`
commits intermediate delegation/output progress. E3 must not “improve atomicity” by wrapping
either workflow in one giant transaction. Instead, each existing **material** commit gets
its matching Activity, while intermediate execution/delegation commits stay excluded.

### 4.3 Automation routing already has the correct caller-owned boundary

`route_automation_event(...)` intentionally does not commit. The enclosing automation
capture transaction owns the event, routed WorkItem, optional Decision/Risk, and audit.
E3 must use `stage_activity(...)` there and preserve that outer transaction ownership.

## 5. Activity-vs-telemetry classification

The following are explicitly **not** coverage gaps and must remain outside curated
semantic Activity:

- execution claim tokens and claim/release leases;
- per-attempt `running` claims and `retry_wait` bookkeeping;
- delegation state, `OrganizationExecutionAttempt`, action-output writes, AgentRun/tool
  progress, retry counters, and provider telemetry;
- CEO coordination token claim/recovery/release;
- Decision evidence/recommendation refresh that does not change authority state;
- deadline reminder timestamps (`reminded_at`).

Terminal failure, terminal cancellation, a governance hold, explicit retry authorization,
assignment/escalation, deadline change, evidence-driven release from hold, and final
Decision/Work dispositions remain material and therefore require Activity.

## 6. Coverage truth finding: writer closure alone is insufficient

E3A found a second correctness boundary in the E1 Observatory contract. The current
response exposes only:

- `activity_history_basis = partial_activity_coverage`; and
- `activity_history_established = false`.

There is no durable Activity coverage-start marker. Even after every legacy writer is
adapted, rows created before E3 will legitimately have no semantic Activity because E2/E3
forbid historical reconstruction from `updated_at`, AuditLog, attempts, or mutable current
state. Therefore E3 must **not** flip `activity_history_established` to `true` merely
because source code is fully adapted.

The accepted E3 closure design is an explicit immutable coverage epoch using the existing
Activity ledger rather than fabricating a backfill:

- append one idempotent operational Activity such as
  `organization.activity_coverage.established.v1` in a dedicated tenant stream only after
  all material writer adapters and cross-database acceptance pass;
- treat its `occurred_at` as the authoritative semantic-history coverage start;
- expose that timestamp in Observatory coverage metadata;
- historical metrics may be called authoritative only for periods beginning on or after
  that coverage start;
- pre-epoch Activity may remain visible as historical evidence but is labelled partial and
  must not be used to claim complete period throughput/cycle time;
- no pre-epoch WorkItem/Decision row is synthesized or backfilled.

The activation must be explicit, idempotent, admin/internal-human governed, and must not
create a Contribution.

## 7. E3 implementation sequence

To keep the regression surface bounded, E3 is split into four internal sub-slices:

1. **E3A — writer inventory + coverage-epoch design: COMPLETE.** This document and roadmap
   reconciliation only; no runtime changes.
2. **E3B — legacy WorkItem material-writer adapters: COMPLETE / PASS.** Cover direct
   creation/routing, requeue/control/deadline/escalation/emergency Work-side changes,
   governance holds, terminal execution/cancellation/failure, explicit retry, evidence
   amendment/release, and linked Work outcome staging. Runtime claim/retry telemetry stays
   excluded.
3. **E3C — legacy ExecutiveDecision material-writer adapters: COMPLETE / PASS.** Cover
   direct creation, deadlines, escalation/ownership, CEO hold/Board promotion, Board/CEO
   terminal outcomes, and coupled transaction regression. Lease/reminder/evidence-only
   writes stay excluded.
4. **E3D — explicit coverage epoch + Observatory coverage activation: UNLOCKED / NOT STARTED.**
   Add the coverage-start contract, cross-database reconciliation tests, and only then
   allow `activity_history_established = true` from the epoch forward.

Phase 13.16.2 remains locked through E3D and the remaining 13.16.1 exit gates. No dashboard may present historical
throughput, cycle time, resolved-blocker period throughput, or last-material-transition
ageing as authoritative until E3D is accepted.

### E3B implementation disposition

The bounded E3B implementation now stages semantic WorkItem Activity for the legacy
material-writer surface while preserving each writer's existing transaction ownership:

- direct legacy API creation and caller-owned automation routing stage Work-created
  Activity without adding a new commit;
- position/bootstrap repair, position resume, and global-control resume stage `held ->
  queued` Work Activity only when Work actually changes;
- deadlines, assignment/escalation, emergency marking/escalation, governance holds,
  terminal execution dispositions, terminal failure/cancellation, explicit retry
  authorization, and Technology evidence amendment/release have versioned Work Activity;
- Board/CEO terminal decision paths stage only their linked Work outcome in E3B; Decision
  Activity was reserved for E3C and is now accepted;
- the global-pause execution hold now closes its previously identified source-AuditLog gap
  in the same commit as the Work mutation and Activity;
- execution claims, `retry_wait`, delegation/action-output progress, coordination leases,
  reminder timestamps, and Decision evidence-only refresh remain excluded telemetry;
- `activity_history_established` remains `false`, no historical backfill exists, and no
  Contribution authority is created by Activity.

Focused E3B regression coverage covers semantic ordering, hidden requeue behavior,
emergency replay, terminal-vs-retry classification, cancellation, evidence release,
coupled Work outcomes, and Activity-stage rollback. E3B acceptance is complete: the focused
suite passed **10 tests with 1 expected PostgreSQL-only skip**, the surrounding organization
regression passed **143 tests with 2 expected skips**, the complete API suite passed
**780 tests with 3 expected PostgreSQL-only skips**, and the isolated PostgreSQL transaction
contracts passed **3/3** at Alembic `0074_durable_contribution_activity_model`.
`organization_activity_streams` and `organization_activities` were both zero before and after
that PostgreSQL acceptance run. Repository policy, release consistency, migration consistency,
and `git diff --check` also passed. E3C is now COMPLETE / PASS after focused, full-suite, repository, migration, and isolated-PostgreSQL acceptance.

### E3C implementation disposition

The bounded E3C implementation stages semantic ExecutiveDecision Activity inside each
existing legacy material-writer transaction:

- direct API Work creation and caller-owned automation routing now stage Decision-created
  Activity whenever the authority boundary creates a Decision; automation routing still does
  not commit;
- Decision deadlines stage a versioned deadline Activity only when the governed instant
  actually changes; same-instant timezone representation replay does not duplicate Activity;
- Work escalation and emergency reconciliation stage Decision escalation Activity only when
  Decision owner, pending authority state, or authority level materially changes;
- `_hold_ceo_decision(...)` stages a semantic hold after a real coordination claim is returned
  to pending review, while claim/recovery/release lease transitions remain excluded;
- `_promote_decision_to_board(...)` stages Decision escalation plus the linked Work
  `pending_board` Activity before the existing pre-packet commit; this closes the coupled
  Work-side omission discovered during E3C tracing;
- Board override and normal Board/CEO outcomes stage Decision outcome plus linked Work status
  in the same existing commit; `approved`, `rejected`, and legacy `returned` outcomes remain
  descriptive governance facts and do not create Contributions automatically;
- Decision evidence/recommendation refresh and reminder timestamps remain excluded; and
- `activity_history_established` remains `false`, with no historical reconstruction or
  Contribution feedback loop.

Focused E3C regression coverage adds eight tests spanning Decision create/deadline/replay,
terminal coupled outcomes, emergency replay, material CEO hold, coupled Board promotion,
caller-owned automation rollback, Activity-stage rollback, and one PostgreSQL-only
Decision transaction/no-residue contract. Acceptance is complete; E3D is now UNLOCKED / NOT STARTED.

E3C acceptance evidence: focused E3C **7 passed / 1 expected PostgreSQL-only skip**; combined organization/E3B/E3C regression **160 passed / 4 expected skips**; complete API **787 passed / 4 expected PostgreSQL-only skips**; isolated PostgreSQL Activity transaction contracts **4/4 passed**. `organization_activity_streams = 0` and `organization_activities = 0` both before and after that PostgreSQL run, Alembic remained `0074_durable_contribution_activity_model`, and repository policy, release consistency, migration consistency, and `git diff --check` all passed. `activity_history_established` remains `false`; the isolated PostgreSQL container was returned to stopped state, and E3D is the next unlocked slice.

## 8. Acceptance invariants for later E3 slices

Every adapted material writer must prove:

1. source/domain row mutation and existing source `AuditLog` are in the same transaction
   as semantic Activity + Activity audit;
2. failure during Activity staging rolls back that material source commit;
3. replay/idempotent no-op paths append no duplicate Activity;
4. actor attribution is explicit, but department/position ownership comes from the
   governed WorkItem/Decision rather than blindly from the caller;
5. legacy default-tenant behavior is preserved without widening public tenant authority;
6. execution leases, retries, reminders, AgentRun/tool volume, and AuditLog counts do not
   become Activity or Contribution authority;
7. no Activity creates a Contribution;
8. SQLite and isolated PostgreSQL 0074 transaction tests pass;
9. the preserved authoritative PostgreSQL `gmai` database remains untouched at 0073;
10. `activity_history_established` remains false until the explicit E3D epoch exists.

## 9. E3A disposition

The legacy writer surface is mapped, E3B WorkItem reconciliation is accepted, and E3C
Decision/coupled adapters are now COMPLETE / PASS. E3C also closes the
one coupled Work-side Board-promotion omission discovered during its writer trace. E3D is now
UNLOCKED / NOT STARTED after the focused/full/isolated-PostgreSQL E3C gates passed.

E3A itself is documentation/design only and requires no API/full-suite rerun. Repository
policy, release consistency, migration consistency, and `git diff --check` are the only
acceptance gates for this sub-slice. E3 overall remains **IN PROGRESS**.
