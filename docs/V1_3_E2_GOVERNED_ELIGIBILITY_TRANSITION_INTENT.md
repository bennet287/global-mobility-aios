# V1.3-E.2 — Governed Eligibility Transition Intent → Command Gateway

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

## Purpose

E.2 proves the missing half of the first real Global Mobility AIOS execution loop:

```text
persistent AI employee
→ governed case/pathway ContextBundle
→ runtime binding
→ typed EligibilityTransitionIntent
→ deterministic domain validation
→ MaterialAction(eligibility.transition)
→ Command Gateway
→ REVIEW_REQUIRED / BLOCK
→ durable Board-inspectable attempt
```

E.2 deliberately does **not** mutate eligibility state.

The goal is to prove that a model-generated material recommendation remains a proposal until AIOS independently interprets, validates and governs it.

Permanent rule:

> **The runtime proposes. AIOS validates. The Command Gateway authorizes or refuses organizational action.**

## Why E.2 does not auto-execute

`MaterialActionType.ELIGIBILITY_TRANSITION` is constitutionally material with an R3 floor.

R3 means a material recommendation / eligibility decision that requires independent verification.

The generic B.1 kernel knows the R3 floor but does not itself know whether an independent verifier has actually been satisfied. Until V1.3-F/G provide Decision Readiness and independent verification, E.2 explicitly supplies:

```text
PolicyDisposition.HUMAN_REQUIRED
```

for A1-A5 authorities.

Therefore even an A5 position cannot auto-execute the eligibility transition in E.2.

A0 remains an unconditional prohibition. E.2 deliberately lets A0 reach the kernel with ordinary policy disposition so the existing:

```text
AUTONOMY_PROHIBITED
```

BLOCK semantics are preserved rather than accidentally converting a prohibited action into a review queue.

## Persistent employee identity

E.2 binds organization identity as:

```text
OrganizationPosition.position_key
        ↓
OrganizationCommandContext.actor_id
        ↓
CapabilityAuthority.actor_id
```

Provider/model/runtime identity is never used as the organizational actor.

Therefore:

```text
position = employee / authority subject
runtime  = technical cognition implementation
```

## Case/profile context binding

E.2 extends the existing ContextBundle reference semantics without adding a second case-context abstraction.

When a WorkItem carries `lead_id` and/or `profile_id`, the Context Broker now versions those canonical references with deterministic record fingerprints:

```text
lead reference
    id      = Lead.id
    version = canonical Lead fingerprint

profile reference
    id      = Profile.id
    version = canonical Profile fingerprint
```

`Profile.profile_version` remains the separate domain precondition used for the eligibility material action.

This means:

- Lead changes alter `context_hash`;
- profile lifecycle/content changes alter `context_hash`;
- a new current Profile invalidates an old bound profile;
- runtime binding becomes stale when the actual case state changes.

E.2 re-resolves the ContextBundle again **after** runtime latency before constructing the MaterialAction. A case change during the model call therefore fails closed before a material gateway attempt is created.

## Minimum case state

The E.2 pilot requires:

- one bound Lead;
- one bound current active immutable Profile;
- Profile belongs to Lead;
- Profile consent status is `granted`;
- target country is known;
- mobility goal/intent is known;
- case target country matches the governed pathway;
- case intent domain matches the governed pathway;
- ContextBundle has no unresolved authority unknowns or contradictions;
- governed pathway Evidence is present;
- governed VerifiedRules are present;
- active CountryPolicy was resolved by D.3.

If these prerequisites are not met, E.2 does not call the runtime for a material eligibility proposal.

## Data minimization for the case-scoped runtime payload

E.2 deliberately excludes direct contact/identity fields such as:

- full name;
- email;
- phone.

Only bounded professional/mobility facts needed for the pilot are placed in the runtime payload, such as:

- nationality;
- current/target country;
- mobility goal;
- occupation;
- years of experience;
- job-offer status;
- qualification-recognition state;
- language level;
- profile readiness/completeness.

This is data minimization, **not** a completed sensitivity/egress policy.

For that reason E.2 requires an explicitly supplied `LLMProvider` adapter and does **not** automatically call `LLMProviderFactory` for case-scoped processing. Default external provider selection remains blocked until provider-egress/sensitivity policy is explicitly governed.

## Typed intent

The runtime can emit only:

```text
EligibilityTransitionIntent
├── work_item_id             AIOS-bound
├── lead_id                  AIOS-bound
├── profile_id               AIOS-bound
├── profile_version          AIOS-bound
├── pathway_version_id       AIOS-bound
├── proposed_state           model proposal
├── evidence_basis           model-selected subset of governed Evidence
├── rule_basis               model-selected subset of governed VerifiedRules
├── rationale                model proposal
└── confidence               informational only
```

The runtime output JSON itself contains only:

```text
proposed_state
evidence_basis
rule_basis
rationale
confidence
```

Provider/model identity is **not** accepted from model output. It comes from the D.2 runtime binding and actual provider response.

Allowed proposed states in E.2 are intentionally narrow:

- `potentially_eligible`
- `potentially_ineligible`
- `needs_documents`
- `insufficient_information`

These are proposal states, not canonical eligibility truth.

## Confidence is not authority

`confidence` must be between 0 and 1 but is informational only.

It is not included as a deterministic authorization gate and cannot relax:

- R3;
- Evidence requirements;
- VerifiedRule requirements;
- authority;
- scope;
- expected-version checks;
- policy review;
- A0 prohibition.

A confidence of `1.0` still routes a valid A5 eligibility proposal to `REVIEW_REQUIRED` in E.2.

## Domain integrity before MaterialAction

Before constructing `MaterialAction(ELIGIBILITY_TRANSITION)`, E.2 validates:

- current case/profile binding;
- granted consent;
- current ContextBundle freshness;
- target-country/pathway compatibility;
- domain/pathway compatibility;
- governed Evidence availability;
- governed VerifiedRule availability;
- model Evidence citations are a subset of `ContextBundle.evidence_refs`;
- model rule citations are a subset of `ContextBundle.verified_rule_refs`;
- runtime provider/model matches D.2 binding;
- case/context did not change during runtime execution.

Forged, stale or out-of-authority Evidence/rule references therefore fail before the material gateway action exists.

Authority/scope/risk/autonomy authorization remains owned by the Command Gateway rather than being reimplemented in the vertical.

## MaterialAction construction

AIOS, not the model, constructs:

```text
MaterialAction(
    action_type = eligibility.transition,
    capability = mobility.eligibility,
    subject_type = lead_eligibility,
    subject_id = Lead.id,
    expected_version = Profile.profile_version,
    scope_key = <country>:<domain>,
    evidence_refs = validated Evidence + rule basis,
    consequence_class = APPEND_ONLY_CORRECTION,
    ...
)
```

The model cannot choose:

- action type;
- capability;
- actor identity;
- subject identity;
- expected version;
- scope;
- risk tier;
- consequence class;
- policy disposition;
- autonomy;
- provider/model audit identity.

## Durable attempt transparency

For `REVIEW_REQUIRED` and `BLOCK`, E.2 persists one trace-scoped governance Activity:

```text
governance:attempt:<trace_id>
```

The payload records, among other fields:

- action fingerprint;
- trace ID;
- context hash;
- runtime-binding hash;
- intent fingerprint;
- Lead/Profile/Pathway identities;
- proposed state;
- informational confidence;
- Evidence basis;
- rule basis;
- explicit unsatisfied R3 independent-verification floor.

The Activity is linked to the WorkItem, so existing C.4/C.1 transparency readers can inspect it through both trace and WorkItem history.

This is the first vertical proof that a model can propose a material organizational action and AIOS can durably refuse to execute it while retaining Board-visible lineage.

## No eligibility mutation

E.2 does not create or mutate:

- `EligibilityAssessment`;
- Lead eligibility state;
- application state;
- client-facing recommendation;
- external communication;
- external action.

`mutated` is always false for this slice.

The future authorized eligibility effect remains downstream of Decision Readiness and genuine independent verification.

## No generic intent bus

E.2 intentionally adds the domain-specific service:

```text
governed_eligibility_transition_intent(...)
```

It does not create:

```text
governed_intent(action_type=...)
UniversalIntentDispatcher
IntentBus
```

The second real Command Gateway consumer should remain vertical until multiple proven consumers reveal a stable common abstraction.

## Tests

`apps/api/tests/test_organization_eligibility_transition_intent.py` covers the E.2 contract, including:

1. runtime → typed intent → R3 gateway → `REVIEW_REQUIRED`;
2. no EligibilityAssessment mutation;
3. Board-inspectable trace and WorkItem transparency;
4. Lead/Profile fingerprinting in ContextBundle;
5. direct contact identity excluded from runtime payload;
6. arbitrary WorkItem working context cannot self-promote into model authority;
7. forged Evidence basis fails before gateway Activity;
8. forged VerifiedRule basis fails before gateway Activity;
9. wrong-country/stale governed rule fails before runtime;
10. missing governed Evidence/policy context blocks material proposal;
11. granted consent is required before case facts reach runtime;
12. authority-actor mismatch becomes a durable Command Gateway BLOCK while actor identity remains OrganizationPosition;
13. case change during runtime invalidates the proposal before gateway attempt;
14. unsupported runtime / provider-model drift fails closed;
15. confidence cannot relax the R3 review floor;
16. A0 remains `AUTONOMY_PROHIBITED`;
17. Lead state changes alter ContextBundle hash.

Parameterization means the exact pytest collected count is authoritative and should be recorded from the canonical local run rather than inferred from this list.

## Migration posture

E.2 introduces no database migration.

Existing `OrganizationActivity`, WorkItem, Lead/Profile, pathway authority and governance contracts are reused.

## Non-claims

E.2 does not claim:

- E.1 acceptance unless separately evidenced;
- eligibility decision execution;
- independent verification completion;
- Decision Readiness completion;
- generic intent dispatch;
- AgentRun / Flight Recorder completion;
- external provider-egress authorization for case data;
- Munder adoption;
- client-facing eligibility recommendation;
- GitHub CI PASS.

## Acceptance gate

Canonical acceptance should include:

- E.1 focused tests if E.1 has not yet been sealed;
- E.2 focused tests;
- D.1-D.3 context/runtime authority tests;
- B/C governance/transparency chain;
- protected v10.22 roadmap regression if roadmap changes;
- repository policy;
- full API regression;
- migration/schema checks;
- `git diff --check`;
- clean synchronized V12 branch.

If E.1 and E.2 both pass, seal them separately with their actual evidence. The next architecture step should then be V1.3-F Decision Readiness feeding V1.3-G independent verification before any eligibility mutation is authorized.
