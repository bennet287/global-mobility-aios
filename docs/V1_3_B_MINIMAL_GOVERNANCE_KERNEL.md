# V1.3-B.1 — Minimal Governance Kernel Foundation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Phase:** V1.3-B — Minimal Governance Kernel  
**Slice:** B.1 — deterministic governance evaluation foundation  
**Status:** **IMPLEMENTED / ISOLATED FOCUSED TEST PASS / CANONICAL REPOSITORY ACCEPTANCE PENDING**

## Purpose

V1.3-B converts the constitutional vocabulary accepted in V1.3-A into deterministic runtime governance behavior for material organizational actions.

The first slice deliberately avoids creating another command framework. The existing repository already provides important primitives:

- `OrganizationCommandContext` for tenant/actor/authenticated-role identity;
- canonical JSON and SHA-256 fingerprints;
- existing idempotency helpers;
- tenant-isolated command utilities;
- audited mutation staging/commit primitives;
- durable `OrganizationActivity` streams and append/stage functions.

B.1 therefore introduces a thin governance layer over those existing contracts rather than duplicating them.

## Added runtime contract

`apps/api/app/services/organization_governance_kernel.py`

The module introduces:

### Capability authority

`CapabilityAuthority` binds authority to:

```text
tenant
actor
capability
allowed material action types
maximum risk tier
autonomy level
optional scopes
```

This preserves the V1.3 rule:

```text
Capability != Authority != Autonomy != Risk
CAN DO != MAY DO
```

### MaterialAction envelope

The B.1 `MaterialAction` includes:

```text
action_type
capability
subject_type / subject_id
idempotency_key
expected_version
proposed_change
scope_key
evidence_refs
rationale
risk_tier
consequence_class
trace_id
requested_at
```

Only constitutionally material action types may enter this gateway contract. Non-material cognition remains outside the material mutation path.

Risk cannot be lowered below the V1.3-A constitutional Materiality Registry floor.

### Deterministic gateway evaluation

`evaluate_material_action(...)` performs bounded deterministic checks for:

1. tenant/actor authority identity;
2. capability and action-type authority;
3. optional scope authority;
4. risk ceiling;
5. expected-version/precondition consistency;
6. idempotency replay/conflict;
7. deterministic policy disposition;
8. Board-reserved authority;
9. autonomy routing.

Outcomes are typed:

```text
AUTO_EXECUTE
BLOCK
REVIEW_REQUIRED
IDEMPOTENT_REPLAY
```

Reasons are also explicit and machine-readable, including:

```text
AUTHORIZED
OUTSIDE_AUTHORITY
SCOPE_DENIED
RISK_EXCEEDS_AUTHORITY
EXPECTED_VERSION_REQUIRED
STALE_VERSION
IDEMPOTENT_REPLAY
IDEMPOTENCY_CONFLICT
POLICY_DENIED
POLICY_REVIEW_REQUIRED
AUTONOMY_PROHIBITED
AUTONOMY_REVIEW_REQUIRED
BOARD_RESERVED
```

### Reserved authority cannot be hidden by autonomy

The Board-reserved check occurs before ordinary A1/A2/A3/A4/A5 routing.

Therefore a government submission remains:

```text
R5
Board reserved
REVIEW_REQUIRED
reason = BOARD_RESERVED
```

even when an actor is configured at A5.

### A0–A5 routing used by B.1

```text
A0 → BLOCK
A1 → REVIEW_REQUIRED
A2 → REVIEW_REQUIRED
A3 → AUTO_EXECUTE + mandatory post-review marker
A4 → AUTO_EXECUTE
A5 → AUTO_EXECUTE
```

This applies only after authority, scope, risk, version, idempotency, policy and reserved-authority checks pass.

### Traceable Activity projection

`organization_activity_projection(...)` converts a governance evaluation into a stable projection that can be fed into the repository's existing `OrganizationActivity` append/stage path.

The first B.1 slice intentionally maps the physical legacy activity class to `operational` while preserving the new constitutional `MATERIAL` or `AUTHORITY` class in the activity payload. This avoids a schema migration or destructive enum rewrite before V1.3-C formalizes the Transparency Foundation.

The projection includes:

- stable governance activity/stream keys;
- trace ID as correlation key;
- action fingerprint;
- capability/action;
- decision outcome/reason;
- effective risk tier;
- constitutional activity class;
- consequence class;
- review reason;
- idempotency key.

## Focused tests

`apps/api/tests/test_organization_governance_kernel.py`

The isolated pre-publish validation suite contains 19 tests covering:

- authorized low-risk auto execution;
- actor/tenant authority mismatch;
- action-type authority;
- scope authority;
- risk ceiling;
- constitutional risk floors;
- expected-version requirement;
- stale-version rejection;
- exact idempotent replay;
- idempotency conflict;
- policy denial;
- policy-required human review;
- A0 prohibition;
- A2 review routing;
- A3 post-review semantics;
- A5 cannot bypass Board reservation;
- trace-correlated Activity projection;
- non-material action rejection;
- Board-reserved reason precedence over A2 routing.

Isolated validation result before repository publication:

```text
19 passed in 0.05s
```

This is useful implementation evidence but is **not** a substitute for canonical repository acceptance from the real V12 checkout.

## No database migration in B.1

B.1 is intentionally schema-neutral.

It does not add or alter tables, columns, database enums, migrations or the existing `OrganizationActivity` physical schema.

Expected migration head remains:

```text
0076_organization_position_active_identity
```

## Important non-claims

B.1 does **not** yet:

- execute a real production domain mutation through the new gateway;
- persist `MaterialAction` as a new database table;
- introduce a generalized policy engine;
- replace existing route authorization;
- replace existing organization command services;
- implement Decision Readiness;
- implement independent verification;
- implement contradiction detection;
- implement the Organizational Immune System;
- implement earned-autonomy promotion/demotion;
- implement the full Transparency/Decision Lineage layer;
- authorize government submission automatically;
- change existing 118-table schema;
- claim full API regression or GitHub CI PASS for B.1.

## Canonical B.1 acceptance target

After pulling the implementation commit into the canonical V12 checkout, acceptance should verify at minimum:

```text
pytest apps/api/tests/test_organization_governance_kernel.py -q
scripts/check_repo_policy.py --root .
git diff --check
git status -sb
```

A broader API regression should then be run before B.1 is marked PASS because the module imports existing organization command/runtime primitives and forms the foundation for subsequent production wiring.

## Next B slice after B.1 acceptance

B.2 should integrate one existing, reversible, low-risk organization action through the kernel end-to-end:

```text
Actor
→ MaterialAction
→ deterministic authority/policy evaluation
→ expected version / idempotency
→ existing domain command
→ canonical OrganizationActivity
→ trace correlation
```

The first production integration should be deliberately small and reversible. The objective is to prove the governance boundary against a real existing workflow, not to migrate every organizational command at once.
