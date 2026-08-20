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

## 2026-08-20 — V1.3-G.4.1 ELIGIBILITY VERTICAL CONTRACT CONSOLIDATION — COMPLETE / PASS / SEALED

### Status

**The first governed eligibility vertical now has its proven shared semantic seams consolidated without changing the accepted E.2→G.4 behavior or introducing a speculative horizontal framework.**

Accepted implementation head:

```text
65ed83270389d5de88d917c5562077c1fbf9c8de
```

Accepted consolidation:

```text
E.2 + F.1
→ one mobility_intent_domain(...)

E.2 + G.1 + downstream G.2/G.3 execution identity
→ one system_bound_agent_command_context(...)

F.1
→ public pathway_publication_integrity_blockers(...)
→ no direct catalogue-private publication blocker import

G.2 / G.3
→ public eligibility_command_context(...)
→ public original_eligibility_attempt_payload(...)
→ public rebuild_eligibility_action(...)
→ no G.3 private G.2 helper imports
```

Permanent rule:

> **Consolidate proven meaning; do not generalize merely because code looks similar.**

G.4.1 intentionally does not replace `session.expire_all()` and does not force E.2/F.1/G.1 through one generic reference/fingerprint resolver because those consumers still have materially different authority and failure semantics.

### Acceptance test defect verified

The first focused run reported one failure in `test_g4_1_g3_consumes_public_g2_action_contracts`.

The implementation was verified correct. The test asserted that the substring `_command_context` was absent from the G.3 source, which falsely matched the intended public symbol `eligibility_command_context`.

The repair changed only the anti-regression test to inspect exact module symbols. This was a test defect, not a production defect.

### Accepted evidence

```text
G.4.1 focused contract tests   7 passed / 1 warning / 0 failed
Pathway catalogue regression   2 passed / 1 warning / 0 failed
E.2 → G.4.1 vertical           88 passed / 1 warning / 0 failed
Repository policy              PASS
Full API regression            1057 passed / 5 skipped / 1 warning / 0 failed
Full API duration              400.30s
Database migration check       PASS
Migration head                 0077_canonical_eligibility_assessment_revision
Registered tables              119
Local DB schema                PASS
Actual tables                  119
Physical tables                120 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

Canonical records:

```text
docs/V1_3_G4_1_ELIGIBILITY_VERTICAL_CONTRACT_CONSOLIDATION.md
docs/V1_3_G4_1_ACCEPTANCE_2026-08-20.md
```

### Roadmap effect

The active roadmap advances from **V12.15 to V12.16**.

```text
V1.3-A     COMPLETE / PASS / SEALED
V1.3-B     COMPLETE / PASS / SEALED
V1.3-C     COMPLETE / PASS / SEALED through C.4
V1.3-D     COMPLETE / PASS / SEALED through D.3
V1.3-E     COMPLETE / PASS / SEALED through E.2
V1.3-F     COMPLETE / PASS / SEALED through F.1
V1.3-G     COMPLETE / PASS / SEALED through G.4.1
V1.3-G.4   Governed Eligibility Orchestration — COMPLETE / PASS / SEALED
V1.3-G.4.1 Eligibility Vertical Contract Consolidation — COMPLETE / PASS / SEALED
V1.3-G.5   Eligibility Reassessment / Supersession — NEXT
```

G.5 must introduce an explicit expected canonical eligibility revision precondition before any v2+ revision effect is allowed. Prior canonical eligibility truth remains append-only; reassessment must repeat readiness, blind independent verification, verification-floor integration and fresh final Command Gateway authorization.

Known non-blocking warning remains the existing Starlette/httpx deprecation warning. No dependency change is implied.

No GitHub CI PASS is claimed because no attached status checks were present on the accepted implementation head.

---

## 2026-08-20 — V1.3-G.4 GOVERNED ELIGIBILITY ORCHESTRATION — COMPLETE / PASS / SEALED

### Status

**The accepted E.2→G.3 governed eligibility vertical is now operationally reachable through one bounded organization orchestration boundary without creating a second governance path or a generic workflow/effect framework.**

Accepted chain:

```text
trusted organization request / WorkItems
→ trusted server-side execution plan
→ E.2 governed eligibility proposal
→ F.1 deterministic Decision Readiness
→ G.1 blind independent verification
→ G.2 verification-floor integration
→ G.3 fresh final authorization + canonical effect
→ durable trace/effect identifiers
```

Permanent boundary:

```text
human initiator ≠ material-action actor
request JSON ≠ runtime/provider/authority policy
route exists ≠ external provider egress automatically authorized
orchestration ≠ new governance path
```

### Governed API boundary

New accepted route:

```text
POST /api/v1/organization/eligibility/orchestrate
```

Request surface is limited to:

```text
proposal_work_item_id
verification_work_item_id
idempotency_key
```

The request cannot select tenant, actor, producer/verifier OrganizationPosition, runtime profile, provider, model, autonomy, risk, scope, allowed action types or `CapabilityAuthority`.

These remain trusted server-side execution-plan inputs.

The default execution-plan dependency intentionally fails closed with HTTP 503 until a governed provider-egress/runtime/authority policy is configured. The legacy global `LLMProviderFactory` switch is not treated as permission to send case-scoped personal data externally.

Authenticated `admin` / `operator` users may initiate the route, but the producer `OrganizationPosition` remains the material-action actor. Reviewer mutation access is denied by the existing global auth middleware before execution-plan/provider resolution.

### Accepted orchestration states

```text
PROPOSAL_BLOCKED
NOT_READY
HUMAN_INPUT_REQUIRED
VERIFICATION_DISAGREES
VERIFICATION_INSUFFICIENT_BASIS
AWAITING_AUTHORITY
CANONICAL_EFFECT_COMMITTED
```

G.4 preserves lower-layer semantics. G.1 disagreement/insufficient basis never reaches effect integration; A1/A2 remain review-required after the verification floor and create no canonical effect; only G.3 fresh final `AUTO_EXECUTE` may commit canonical eligibility truth.

### Post-commit replay

Exact retries after G.3 has already committed validate the durable governance/revision/assessment/verification/floor/semantic lineage and return:

```text
state = CANONICAL_EFFECT_COMMITTED
gateway_outcome = IDEMPOTENT_REPLAY
replayed = true
```

Neither producer nor verifier model is called again.

Torn or conflicting durable lineage fails closed.

### Accepted evidence

```text
G.4 focused orchestration/API  10 passed / 1 warning / 0 failed
G.4 + OpenAPI boundary         11 passed / 1 warning / 0 failed
E.2 → G.4 vertical             81 passed / 1 warning / 0 failed
Repository policy              PASS
Full API regression            1050 passed / 5 skipped / 1 warning / 0 failed
Full API duration              488.05s
Database migration check       PASS
Migration head                 0077_canonical_eligibility_assessment_revision
Registered tables              119
Local DB schema                PASS
Actual tables                  119
Physical tables                120 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

Canonical records:

```text
docs/V1_3_G4_GOVERNED_ELIGIBILITY_ORCHESTRATION.md
docs/V1_3_G4_ACCEPTANCE_2026-08-20.md
```

### Acceptance boundary repairs

Two stale test expectations were corrected without changing G.4 production behavior:

1. the reviewer-denial test now asserts the canonical global auth-middleware 403 structure rather than an unreachable route-local generic 403 body;
2. the platform hardening router inventory advanced from 65 to 66 and now explicitly requires the `organization-governed-eligibility` feature.

### Roadmap effect

The active roadmap advances from **V12.14 to V12.15**.

```text
V1.3-A     COMPLETE / PASS / SEALED
V1.3-B     COMPLETE / PASS / SEALED
V1.3-C     COMPLETE / PASS / SEALED through C.4
V1.3-D     COMPLETE / PASS / SEALED through D.3
V1.3-E     COMPLETE / PASS / SEALED through E.2
V1.3-F     COMPLETE / PASS / SEALED through F.1
V1.3-G     COMPLETE / PASS / SEALED through G.4
V1.3-G.4   Governed Eligibility Orchestration — COMPLETE / PASS / SEALED
V1.3-G.4.1 Eligibility Vertical Contract Consolidation — NEXT
```

G.4.1 is deliberately separate so the project does not falsely claim that every critic-verified helper consolidation was already completed inside the orchestration slice.

G.4.1 targets only proven shared seams: canonical mobility intent→domain mapping, system-bound-agent command context, public pathway publication integrity, public eligibility action reconstruction/original-payload helpers, and shared reference/fingerprint helpers where real consumers prove identical semantics.

`session.expire_all()` remains conservative until a dependency-aware freshness resolver can cover every hash-bearing ContextBundle input safely.

G.5 reassessment/supersession follows G.4.1 and requires an explicit canonical eligibility revision precondition.

Known non-blocking warning remains the existing Starlette/httpx deprecation warning. No dependency change is implied.

No GitHub CI PASS is claimed because no attached status checks were present on the accepted implementation head.

---

## 2026-08-20 — V1.3-G.3 FIRST CANONICAL ELIGIBILITY EFFECT — COMPLETE / PASS / SEALED

### Status

**The first governed eligibility vertical is now accepted end to end through canonical organizational truth. AIOS can take a persistent employee's governed eligibility proposal, deterministically establish Decision Readiness, run a blind independent verifier, satisfy the R3 verification floor, obtain fresh final Command Gateway authorization and atomically commit a canonical eligibility assessment with durable version/lineage semantics.**

Accepted chain:

```text
E.2 governed eligibility proposal
→ F.1 deterministic Decision Readiness
→ G.1 blind independent AGREES verification
→ G.2 verification-floor integration
→ fresh final Command Gateway authorization
→ governance:<original E.2 idempotency key>
→ EligibilityAssessment
→ EligibilityAssessmentRevision v1
→ semantic MATERIAL eligibility Activity
```

Permanent boundary:

```text
model proposal ≠ canonical truth
independent verification ≠ authorization
Gateway authorization ≠ external/client publication
canonical eligibility truth ≠ application mutation / government action
```

### Canonical aggregate and migration

G.3 adds one companion canonical model/table:

```text
EligibilityAssessmentRevision
eligibility_assessment_revisions
```

Migration:

```text
0077_canonical_eligibility_assessment_revision
```

Accepted aggregate identity:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

Accepted first-slice version semantics:

```text
version = 1
lifecycle_status = active
supersedes_revision_id = null
```

Legacy `EligibilityAssessment` rows are not silently promoted. Only an assessment linked through `EligibilityAssessmentRevision` is a V1.3 governed canonical eligibility effect.

A second active canonical revision is intentionally refused until reassessment/supersession carries an explicit canonical eligibility revision precondition.

### Atomic authorization + effect

G.3 revalidates the accepted E.2/F.1/G.1/G.2 chain and reconstructs the exact original `MaterialAction` and original E.2 idempotency key.

Only a fresh final:

```text
GatewayOutcome.AUTO_EXECUTE
```

may enter the canonical transaction.

A0/A1/A2 therefore cannot commit. A3 persists `post_review_required=true`; A4/A5 remain subject to the same Gateway authority/scope/risk/version/policy gates.

Fresh G.3 stages:

```text
canonical governance authorization Activity
+ EligibilityAssessment
+ EligibilityAssessmentRevision
+ semantic eligibility Activity
```

and commits once. A synthetic mid-transaction failure must roll the whole G.3 unit back.

### Canonical idempotency / replay

G.3 is the first eligibility slice that consumes:

```text
governance:<original E.2 idempotency key>
```

Exact retries return the durable canonical effect as `IDEMPOTENT_REPLAY` without duplicate assessment/revision/semantic Activity.

Replay validates the persisted assessment/revision/effect and the E.2 action, E.2 intent, F.1 readiness, G.1 verification, G.2 floor and G.3 effect fingerprints. Torn or inconsistent state fails closed rather than being silently repaired.

### Governed score semantics

The compatibility `EligibilityAssessment.overall_score` is written as `0.0` because the accepted governed contract has **no canonical numerical eligibility score**. That value must not be presented by future governed read/API/UI surfaces as a calculated zero eligibility score.

### Accepted evidence

```text
Migration-boundary repairs     2 passed / 1 warning / 0 failed
G.3 focused                    15 passed / 1 warning / 0 failed
Repository policy              PASS
Protected v10.22 regression    1 passed / 1 warning / 0 failed
Full API regression            1040 passed / 5 skipped / 1 warning / 0 failed
Full API duration              505.33s
Database migration check       PASS
Migration head                 0077_canonical_eligibility_assessment_revision
Registered tables              119
Local DB schema                PASS
Actual tables                  119
Physical tables                120 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

Canonical records:

```text
docs/V1_3_G3_CANONICAL_ELIGIBILITY_EFFECT.md
docs/V1_3_G3_ACCEPTANCE_2026-08-20.md
```

The migration initially exposed two stale repository tests that hard-coded 0076 as the migration head/ceiling. Those tests were corrected without changing G.3 production code, then the full suite passed at 1040.

### Roadmap effect

The active roadmap advances from **V12.13 to V12.14**.

```text
V1.3-A   COMPLETE / PASS / SEALED
V1.3-B   COMPLETE / PASS / SEALED
V1.3-C   COMPLETE / PASS / SEALED through C.4
V1.3-D   COMPLETE / PASS / SEALED through D.3
V1.3-E   COMPLETE / PASS / SEALED through E.2
V1.3-F   COMPLETE / PASS / SEALED through F.1
V1.3-G   COMPLETE / PASS / SEALED through G.3
V1.3-G.4 Governed Eligibility Orchestration + Vertical Consolidation — NEXT
```

G.4 will operationalize the accepted v1 vertical through a trusted orchestration boundary and consolidate only the now-proven shared eligibility seams needed to do so. It must not route through the legacy immediate-persistence `/api/v1/eligibility/evaluate` path and must not become a generic workflow/effect framework.

Reassessment/supersession follows only after canonical v1 is operationally reachable and will require an explicit expected canonical eligibility revision version.

Known non-blocking warning remains the existing Starlette/httpx deprecation warning. No dependency change is implied.

No GitHub CI PASS is claimed without attached status/check evidence.

---

## 2026-08-20 — V1.3-G.1 + G.2 INDEPENDENT VERIFICATION AND R3 FLOOR INTEGRATION — COMPLETE / PASS / SEALED

### Status

**The first governed R3 eligibility chain is now accepted through independent verification and verification-floor integration. AIOS can take a governed eligibility proposal, deterministically establish Decision Readiness, run a genuinely independent blind verifier, and then re-evaluate the exact original material action through the unchanged Command Gateway without letting either model or verifier own organizational authority.**

Accepted chain:

```text
E.2 governed eligibility proposal
→ F.1 deterministic Decision Readiness
→ G.1 blind independent verifier
→ AGREES / DISAGREES / INSUFFICIENT_BASIS
→ G.2 exact lineage/freshness validation
→ reconstruct exact E.2 MaterialAction
→ satisfy only the R3 independent-verification floor
→ existing Command Gateway re-evaluates
→ no canonical eligibility effect yet
```

Permanent boundary:

```text
independent verification ≠ authorization
verification floor satisfied ≠ canonical effect committed
AUTO_EXECUTE at G.2 ≠ eligibility mutation already happened
```

### G.1 accepted capability

G.1 requires meaningful first-slice R3 independence:

```text
verifier OrganizationPosition != proposer OrganizationPosition
verifier WorkItem              != proposer WorkItem
verifier independence_group    != proposer independence_group
verifier provider              != proposer provider
verifier pinned model          != proposer pinned model
```

The verifier receives the governed case/pathway Evidence and VerifiedRules but not the proposer conclusion, rationale or confidence. AIOS compares conclusions only after the verifier returns.

G.1 creates durable Board-inspectable MATERIAL lineage and no eligibility mutation.

Accepted G.1 evidence:

```text
G.1 focused                    15 passed / 1 warning / 0 failed
E.2 + F.1 + G.1               42 passed / 1 warning / 0 failed
D.1–D.3 + E.1–E.2 + F.1–G.1  81 passed / 1 warning / 0 failed
Protected v10.22 regression    1 passed / 1 warning / 0 failed
Repository policy              PASS
Full API regression            1011 passed / 5 skipped / 1 warning / 0 failed
Full API duration              472.92s
Database migration check       PASS
Migration head                 0076_organization_position_active_identity
Registered tables              118
Local DB schema                PASS
Actual tables                  118
Physical tables                119 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

Canonical records:

```text
docs/V1_3_G1_BLIND_INDEPENDENT_ELIGIBILITY_VERIFICATION.md
docs/V1_3_G1_ACCEPTANCE_2026-08-20.md
```

### G.2 accepted capability

G.2 does not change the generic Governance Kernel. It accepts only a durable G.1 `AGREES` result, recomputes readiness/freshness, verifies the exact E.2→G.1 lineage, reconstructs the exact E.2 `MaterialAction`, and changes only the domain policy input from the temporary `HUMAN_REQUIRED` verification floor to `ALLOW`.

The unchanged Gateway therefore retains the final decision:

```text
A0      → BLOCK / AUTONOMY_PROHIBITED
A1/A2   → REVIEW_REQUIRED / AUTONOMY_REVIEW_REQUIRED
A3      → AUTO_EXECUTE / AUTHORIZED + post_review_required=true
A4/A5   → AUTO_EXECUTE / AUTHORIZED
```

Authority, scope, risk, expected version, policy and Board-reserved checks remain Gateway-owned.

G.2 persists only:

```text
governance:verification-floor:<verification_floor_fingerprint>
```

and deliberately leaves the original canonical slot:

```text
governance:<original E.2 idempotency key>
```

unused for the future transaction that actually commits eligibility truth.

The accepted suite proves exact G.2 reruns reuse the same floor Activity without consuming that future canonical idempotency slot.

Accepted G.2 evidence:

```text
G.2 focused                    14 passed / 1 warning / 0 failed
G.1 + G.2                     29 passed / 1 warning / 0 failed
E.2 + F.1 + G.1 + G.2         56 passed / 1 warning / 0 failed
D.1–D.3 + E.1–E.2 + F.1–G.2  95 passed / 1 warning / 0 failed
Repository policy              PASS
Full API regression            1025 passed / 5 skipped / 1 warning / 0 failed
Full API duration              536.84s
Database migration check       PASS
Migration head                 0076_organization_position_active_identity
Registered tables              118
Local DB schema                PASS
Actual tables                  118
Physical tables                119 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

Canonical records:

```text
docs/V1_3_G2_ELIGIBILITY_VERIFICATION_FLOOR.md
docs/V1_3_G2_ACCEPTANCE_2026-08-20.md
```

### No canonical mutation

G.1/G.2 create no:

- canonical `EligibilityAssessment` effect;
- Lead eligibility-state mutation;
- application mutation;
- client-facing recommendation;
- external communication;
- government submission.

G.2 may return `eligible_for_effect_integration = true` only after a fresh Gateway `AUTO_EXECUTE`, but still returns:

```text
canonical_effect_committed = false
mutated                    = false
```

### Verified critic hardening disposition

Post-G.2 review identified real but non-blocking hardening seams:

- duplicated mobility intent→domain mapping should become one mobility-domain contract;
- repeated system-bound-agent `OrganizationCommandContext` construction should be centralized and documented;
- F.1's private pathway publication-blocker dependency is now mature enough for a public integrity contract;
- canonical reference/fingerprint helpers should be extracted only where semantics are actually identical;
- `session.expire_all()` is conservative but must not be replaced with incomplete targeted expiry that misses hash-bearing Evidence/policy/runtime dependencies;
- service decomposition should follow proven semantic seams rather than arbitrary file-size thresholds.

One reviewer criticism was already obsolete: the exact G.2 rerun / future canonical idempotency-slot test already exists and is part of the accepted G.2 suite.

The existing legacy `/api/v1/eligibility/evaluate` endpoint is not treated as the new governed orchestration boundary because it persists through the older eligibility engine/controlled-agent path.

### Roadmap effect

The active roadmap advances from **V12.12 to V12.13**.

```text
V1.3-A   COMPLETE / PASS / SEALED
V1.3-B   COMPLETE / PASS / SEALED
V1.3-C   COMPLETE / PASS / SEALED through C.4
V1.3-D   COMPLETE / PASS / SEALED through D.3
V1.3-E   COMPLETE / PASS / SEALED through E.2
V1.3-F   COMPLETE / PASS / SEALED through F.1
V1.3-G   COMPLETE / PASS / SEALED through G.2
V1.3-G.3 First Canonical Eligibility Effect — NEXT / NOT YET IMPLEMENTED
```

G.3 must define explicit `EligibilityAssessment` identity/version/supersession semantics before any effect is committed. It must perform fresh final Gateway evaluation and commit canonical governance authorization + EligibilityAssessment + semantic effect Activity atomically, with exact idempotent replay and no automatic client/external action.

HTTP/worker exposure follows the canonical effect contract rather than preceding it.

Known non-blocking warning remains the existing Starlette/httpx deprecation warning. No dependency change is implied.

No GitHub CI PASS is claimed without attached status/check evidence.

---

## 2026-08-20 — V1.3-F.1 ELIGIBILITY DECISION READINESS — COMPLETE / PASS / SEALED

### Status

**The first deterministic Decision Readiness slice is accepted. AIOS can now take an already-governed E.2 R3 eligibility proposal, prove that its durable governance attempt and canonical context remain intact, and deterministically decide whether the proposal is ready for genuinely independent verification, not ready, or requires human input.**

Accepted chain:

```text
E.2 REVIEW_REQUIRED eligibility proposal
→ durable E.2 attempt integrity
→ fresh ContextBundle
→ current Lead / Profile / pathway state
→ deterministic F.1 gates
→ READY_FOR_INDEPENDENT_VERIFICATION
   or NOT_READY
   or HUMAN_INPUT_REQUIRED
```

Permanent boundary:

```text
READY_FOR_INDEPENDENT_VERIFICATION
≠ eligibility truth
≠ independent verification complete
≠ Command Gateway authorization
≠ canonical mutation
```

### Accepted evidence

```text
Repository policy             PASS
Full API regression           996 passed / 5 skipped / 1 warning / 0 failed
Duration                      359.39s
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
docs/V1_3_F1_ELIGIBILITY_DECISION_READINESS.md
docs/V1_3_F1_ACCEPTANCE_2026-08-20.md
```

### Accepted readiness contract

F.1 evaluates five deterministic gates:

```text
proposal_state_actionable
governed_authority_complete
required_case_facts_present
pathway_publication_integrity
material_fact_preconditions
```

The existing `binding_job_offer_in_austria_required` pathway criterion is the first explicit material-fact precondition admitted into F.1. Known unsatisfied facts produce `NOT_READY`; unresolved required human facts produce `HUMAN_INPUT_REQUIRED`.

The readiness score is descriptive only. Model confidence and generic Profile completeness/readiness cannot authorize or veto a material recommendation by themselves.

F.1 additionally proves the durable E.2 attempt itself contains the expected `eligibility.transition`, `REVIEW_REQUIRED`, `POLICY_REVIEW_REQUIRED`, R3 and exact actor/action/intent/context/runtime fingerprints. A BLOCKed proposal cannot be reclassified by forging an in-memory GatewayEvaluation.

### Read-only safety posture

F.1 performs no LLM call and creates no AgentRun, OrganizationActivity, EligibilityAssessment, eligibility-state mutation, application-state mutation, client-facing recommendation or external action.

Accepted result properties remain:

```text
independent_verification_required = true
authorization_effect              = false
canonical_commit_allowed          = false
```

### Roadmap effect

The active roadmap advances from **V12.11 to V12.12**.

```text
V1.3-A  COMPLETE / PASS / SEALED
V1.3-B  COMPLETE / PASS / SEALED
V1.3-C  COMPLETE / PASS / SEALED through C.4
V1.3-D  COMPLETE / PASS / SEALED through D.3
V1.3-E  COMPLETE / PASS / SEALED through E.2
V1.3-F  COMPLETE / PASS / SEALED through F.1
V1.3-G  Independent Verification — NEXT / NOT YET IMPLEMENTED
```

G.1 must consume only F.1-ready proposals and prove meaningful verifier independence rather than merely rerunning the same model/provider/context and rubber-stamping the proposer.

No canonical eligibility mutation is authorized by F.1. The existing R3 verification floor remains unsatisfied until an independent-verification contract is implemented and accepted.

Known non-blocking warning remains the existing Starlette/httpx deprecation warning. No dependency change is implied.

No GitHub CI PASS is claimed without attached status/check evidence.

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