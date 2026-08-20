# Global Mobility AIOS — V1.3-E.1 Governed Mobility Pathway Brief

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** COMPLETE / PASS / SEALED

## Purpose

E.1 is the first bounded end-to-end Global Mobility AIOS vertical built on the sealed governance, transparency, Context Broker and runtime-separation foundations.

It intentionally does **not** introduce another generic agent framework.

The vertical proves this product chain:

```text
Tenant-bound OrganizationalWorkItem
        ↓
Persistent OrganizationPosition employee
        ↓
D.3 governed ContextBundle
        ├── published MobilityPathwayVersion
        ├── MobilityPathwayVersionEvidence
        ├── active/published/effective VerifiedRules
        ├── SourceSnapshot / OfficialSource provenance
        ├── CountryPolicy fingerprint
        └── position-derived tool authority
        ↓
D.2 EmployeeRuntimeBinding
        ↓
bounded hosted LLM runtime
        ↓
strict structured-output validation
        ↓
internal governed mobility pathway brief
        ↓
HUMAN REVIEW REQUIRED
```

This is the first real runtime consumer of D.2 and D.3.

Canonical acceptance: `docs/V1_3_E1_ACCEPTANCE_2026-08-20.md`.

## Why the first vertical is a pathway brief rather than an eligibility decision

Decision Readiness and independent verification are later V1.3 stages. E.1 therefore stops before a material eligibility conclusion or canonical decision.

The output is an internal professional research/preparation artifact only.

Permanent E.1 safety state:

```text
human_review_required        = true
client_facing                = false
canonical_commit_allowed     = false
external_action_authorized   = false
```

The runtime cannot relax these flags.

This ordering lets AIOS prove real model execution over governed mobility truth without pretending that a first-pass model narrative is a verified eligibility determination.

## Runtime boundary

E.1 uses `AgentRuntimeProfile` and `bind_employee_runtime(...)` rather than calling a provider as an ungoverned global utility.

The first proven runtime class is intentionally only:

```text
hosted_api
```

CLI, local, specialized and Munder donor runtimes remain downstream until this vertical proves the execution contract.

When no provider object is explicitly supplied by a caller/test harness, the vertical resolves the bound `provider_key` through the existing `LLMProviderFactory`.

The runtime response must match:

- the bound provider identity; and
- the bound model identity when the runtime profile pins a model.

Provider/model drift therefore fails closed rather than silently changing the execution lineage.

## Governed model input

The runtime receives only an E.1 governed payload assembled by dereferencing the authority already admitted into ContextBundle.

The payload contains bounded forms of:

- employee position identity;
- WorkItem title/objective/risk;
- ContextBundle hash/unknowns/contradictions/policy version;
- canonical pathway identity/version/fingerprint;
- published pathway criteria/documents/costs/processing-time/benefits/risks;
- explicit pathway Evidence bindings;
- official source identity;
- SourceSnapshot content/hash/state;
- VerifiedRule statements/fingerprints/effective state;
- active CountryPolicy content/version.

Arbitrary `OrganizationalWorkItem.context_json` is **not sent to the model** by E.1.

That is intentional. Working context remains useful to other reasoning layers, but it cannot bypass D.3 by smuggling self-declared rules, Evidence, tools, provider selection or invented requirements into the first governed vertical.

## Evidence dereference rule

E.1 does not rediscover authority independently.

It dereferences only IDs already present in the D.3 ContextBundle and verifies their fingerprints again immediately before provider execution.

Therefore:

```text
ContextBundle authority set
        = maximum authority E.1 may send to the runtime
```

If a referenced Evidence binding, rule, SourceSnapshot or policy changed after ContextBundle resolution, E.1 fails closed instead of executing against mixed versions.

## Bounded source content

SourceSnapshot text is included as bounded Evidence context with:

```text
MAX_SOURCE_EXCERPT_CHARS = 6000
```

The payload records whether the excerpt was truncated. This keeps the first vertical aligned with:

> **More relevant truth, not more tokens.**

Later retrieval/tool work may introduce purpose-specific chunking, but E.1 does not build a generic retrieval subsystem.

## Structured output contract

The runtime must return exactly one JSON object containing:

```text
summary
key_requirements[]
material_risks[]
evidence_gaps[]
operator_questions[]
evidence_basis[]
human_review_required
client_facing
canonical_commit_allowed
external_action_authorized
```

No extra keys are accepted.

Every `evidence_basis` item must be one of the citation tokens supplied in the governed payload, such as:

```text
mobility_pathway_version:<uuid>
evidence:<uuid>
verified_rule:<uuid>
source_snapshot:<uuid>
country_policy:<uuid>
```

A model cannot cite an arbitrary rule/source ID outside the ContextBundle authority set.

This does not claim sentence-level factual verification; that belongs to later verification/readiness stages. It does ensure that the runtime cannot expand its declared authority basis beyond the governed context it received.

## Vertical status

E.1 derives vertical status deterministically rather than trusting the model to declare readiness.

```text
ContextBundle unknowns/contradictions absent
    → prepared_for_human_review

ContextBundle unknowns or contradictions present
    → insufficient_governed_context
```

The model cannot override this state.

For example, a pathway with no explicit `MobilityPathwayVersionEvidence` remains visibly incomplete even if the runtime writes a confident narrative.

## Read-only posture

E.1 deliberately creates no:

- `AgentRun`;
- `OrganizationActivity`;
- `EligibilityAssessment`;
- canonical domain mutation;
- external action;
- tool invocation.

This first vertical proves governed execution before durable action/decision lineage is expanded.

## Existing domain engines

The repository already contains `eligibility_engine.py` and `pathway_catalogue.py` with significant deterministic mobility logic.

E.1 intentionally does not blindly wrap `evaluate_lead_eligibility(...)` because that legacy engine currently loads broader active rule state and case/profile facts outside the D.3 ContextBundle authority contract.

The first vertical therefore uses only the single published pathway version and authority set that D.3 admitted.

Later E slices should reconcile reusable deterministic eligibility logic with ContextBundle-scoped inputs rather than allowing a second, broader truth path beside the governed vertical.

## Tests

`apps/api/tests/test_organization_mobility_pathway_brief.py` covers:

1. end-to-end ContextBundle → runtime binding → structured internal brief;
2. governed rule/source content reaches the runtime while arbitrary working-context authority claims do not;
3. runtime citations outside the ContextBundle authority set fail closed;
4. the runtime cannot disable human review or authorize external action;
5. unproven runtime classes are rejected;
6. missing governed Evidence remains visible in deterministic vertical status;
7. runtime provider identity must match the bound profile;
8. the vertical remains read-only and creates no AgentRun or OrganizationActivity.

The service additionally enforces bound model identity when the runtime profile pins a model.

## Accepted evidence

```text
Repository policy             PASS
Full API regression           969 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual / 119 physical incl. alembic_version
git diff --check              clean
```

The acceptance record documents the truthful branch-state nuance from the E.1 run.

## Non-claims

E.1 does not claim:

- eligibility determination;
- legal advice;
- client-facing output;
- Evidence certification;
- Decision Readiness;
- independent verification;
- canonical mutation;
- durable AgentRun/Flight Recorder lineage;
- tool execution;
- CLI/local/Munder runtime adoption;
- automated external action;
- V1.3-E completion by itself;
- GitHub CI PASS.

## Direction after E.1

E.2 is now the accepted downstream vertical proof. The active next stage after E.1 + E.2 is Decision Readiness, followed by genuinely independent verification before any canonical eligibility mutation.