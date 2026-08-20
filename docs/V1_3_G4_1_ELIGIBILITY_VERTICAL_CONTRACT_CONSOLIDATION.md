# Global Mobility AIOS — V1.3-G.4.1 Eligibility Vertical Contract Consolidation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

## Purpose

G.4.1 consolidates only the shared contracts that became demonstrably stable while proving and operationalizing the first governed eligibility vertical through E.2 → F.1 → G.1 → G.2 → G.3 → G.4.

This is behavior-preserving vertical hardening. It does not introduce a generic orchestration, intent, effect, review or authority framework.

Permanent rule:

> **Consolidate proven meaning; do not generalize merely because code looks similar.**

## Accepted upstream vertical preserved

G.4.1 must preserve the already-sealed flow exactly:

```text
trusted G.4 organization request / WorkItems
→ E.2 governed eligibility proposal
→ F.1 deterministic Decision Readiness
→ G.1 blind independent verification
→ G.2 verification-floor integration
→ G.3 fresh final Command Gateway authorization
→ canonical EligibilityAssessment + EligibilityAssessmentRevision
→ durable G.4 trace/effect identity
```

No G.4.1 helper gains authority of its own.

## 1. Canonical mobility intent → domain mapping

New public service:

```text
app.services.mobility_domain.mobility_intent_domain(...)
```

It replaces the duplicated E.2 `_intent_domain(...)` and F.1 `_lead_domain(...)` implementations while preserving the accepted first-slice mapping exactly:

```text
study_abroad / study / student        → study
overseas_job / work / job / employment → work
visa / permanent / residency / immigration → visa
anything else                          → general
```

The helper deliberately does **not** reinterpret richer profile goals, pathway matching, or the full product taxonomy. It exists because E.2 and F.1 were already enforcing the same semantic contract.

## 2. System-bound AI employee command context

New public constructor:

```text
app.services.organization_command.system_bound_agent_command_context(...)
```

It centralizes the repeated organizational execution identity used by E.2 and G.1 and reused through G.2/G.3:

```text
actor_id               = OrganizationPosition.position_key
actor_type             = agent
authenticated_user_id  = system
role                    = operator
position_key            = OrganizationPosition.position_key
```

Optional correlation/request identity remains caller supplied.

Permanent interpretation:

```text
system/operator execution boundary
≠ Human operator authority
≠ provider/model identity
≠ CapabilityAuthority grant
```

The persistent `OrganizationPosition` remains the organizational actor. Capability authority continues to be supplied and validated separately by the Governance Kernel.

## 3. Public pathway publication-integrity contract

New public service surface:

```text
app.services.pathway_publication_integrity.pathway_publication_integrity_blockers(...)
```

F.1 no longer imports `_publication_evidence_blockers` directly from `pathway_catalogue.py`.

For this bounded consolidation, the new public surface delegates to the mature catalogue implementation rather than copying or relocating a large publication subsystem. This preserves the exact accepted rules for:

- required official-source Evidence links;
- core-route Evidence shape;
- pathway-specific structured Evidence roles;
- source certification;
- VerifiedRule publication/provenance;
- pathway country/domain compatibility.

The compatibility adapter is the only G.4.1 bridge to the historical private catalogue implementation. Downstream organization services consume the public contract.

A deeper catalogue-internal extraction is deliberately deferred until it can be performed as its own bounded change with catalogue-specific regression evidence.

## 4. Public eligibility action reconstruction contracts

G.2 now exposes eligibility-specific public contracts:

```text
eligibility_command_context(...)
original_eligibility_attempt_payload(...)
rebuild_eligibility_action(...)
```

These replace G.3's private imports of:

```text
_command_context
_original_e2_payload
_rebuild_action
```

The reconstruction contract still derives the exact accepted E.2 `MaterialAction` from canonical state and preserves:

- action type `eligibility.transition`;
- capability `mobility.eligibility`;
- Lead eligibility subject identity;
- immutable Profile-version precondition;
- original idempotency key;
- proposed state/profile/pathway/context/runtime/intent fingerprints;
- country/domain scope;
- Evidence + VerifiedRule references;
- rationale;
- append-only-correction consequence semantics;
- original trace identity and request timestamp.

G.2 and G.3 continue to require the reconstructed action fingerprint to equal the accepted E.2 action fingerprint.

## 5. Deliberately deferred reference/fingerprint abstraction

G.4.1 does **not** create one generic reference/freshness resolver across E.2, F.1 and G.1.

Although those modules all dereference governed records, their contracts are not currently identical:

- E.2 validates proposal-time ContextBundle records and raises E.2-specific integrity errors;
- F.1 validates an already-accepted proposal against current canonical state and has Decision-Readiness-specific failure semantics;
- G.1 validates verifier-specific case/authority identity and independence constraints.

Forcing those into one generic resolver now would collapse distinct error/authority semantics merely to reduce code. Shared extraction remains eligible only after another real consumer proves identical meaning.

## 6. Freshness posture remains conservative

G.4.1 intentionally leaves:

```text
session.expire_all()
```

in E.2 and G.1 after runtime latency.

The accepted ContextBundle hash may depend on Lead/Profile, pathway/version, Evidence, VerifiedRules, SourceSnapshots, CountryPolicy, employee/runtime state and related authority inputs. A narrower expiry mechanism must not be introduced until a dependency-aware resolver can prove complete coverage of every hash-bearing input.

Therefore:

```text
blunt but complete freshness
> elegant but incomplete freshness
```

for the current material R3 vertical.

## 7. Anti-regression contract tests

New focused file:

```text
apps/api/tests/test_organization_eligibility_contract_consolidation.py
```

It verifies that:

1. the shared mobility-domain mapping preserves accepted E.2/F.1 semantics;
2. the shared system-bound-agent context keeps `OrganizationPosition.position_key` as actor;
3. F.1 no longer imports the catalogue-private publication blocker directly;
4. E.2 no longer carries duplicate mobility-domain or command-context implementations;
5. G.1 uses the shared system-bound-agent context;
6. G.3 no longer imports G.2 private action helpers;
7. G.2 exposes the named public eligibility reconstruction contracts.

Existing E.2/F.1/G.1/G.2/G.3/G.4 tests remain the behavioral source of truth for fingerprints, Gateway outcomes, lineage, replay, canonical effects and the HTTP boundary.

## Migration posture

G.4.1 adds no database model or migration.

Canonical migration truth remains:

```text
0077_canonical_eligibility_assessment_revision
registered tables 119
actual tables     119
physical tables   120 including alembic_version
```

## Deliberate non-claims

G.4.1 does not claim:

- provider-egress/sensitivity policy completion;
- replacement of `session.expire_all()`;
- generic canonical-reference resolver completion;
- generic canonical-effect framework;
- generic intent bus;
- generic peer-review network;
- eligibility reassessment/version-2 support;
- client-facing publication;
- external action authorization;
- Organization Fabric / Mission Room implementation;
- any migration or schema change.

## Acceptance gate

Canonical acceptance requires at minimum:

- focused G.4.1 contract tests;
- relevant pathway publication/catalogue tests;
- E.2 → G.4 governed vertical regression including G.4.1 tests;
- repository policy PASS;
- full API regression;
- migration/schema checks confirming no database change;
- `git diff --check` clean;
- clean synchronized V12 branch.

ROADMAP and CHANGELOG remain at the accepted V12.15 checkpoint until those results are observed.

No GitHub CI PASS may be claimed without attached check evidence.

## Direction after acceptance

If G.4.1 is accepted without behavior drift, the next bounded stage remains:

```text
V1.3-G.5 — Eligibility Reassessment / Supersession
```

G.5 must introduce an explicit expected canonical eligibility-revision precondition before creating revision v2+ semantics. It must not mutate prior canonical revision truth in place.
