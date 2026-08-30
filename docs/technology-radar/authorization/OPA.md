# Open Policy Agent — AIOS Authorization Research

**State:** ASSESS / R2
**Reviewed pin:** `open-policy-agent/opa@8e733384254aa0211f0464852f2881f83d700bf1`
**License:** Apache-2.0
**Primary source:** `https://www.openpolicyagent.org/docs`

## Fit

OPA deliberately separates policy decision from enforcement. The natural AIOS shape is Command Gateway as policy enforcement point and OPA as an optional policy decision provider for contextual action/risk rules.

```text
typed CommandRequest + canonical facts
→ versioned policy/data bundle
→ OPA evaluation
→ allow/deny + reason data
→ Command Gateway final decision
```

## Risks

- flexible Rego/data input can create opaque or overly broad policy;
- relationship-heavy organization grants need careful data modeling;
- policy bundle and canonical authority versions can drift;
- evaluation output must be constrained to a typed contract;
- debugging, partial evaluation and bundle lifecycle add operational complexity.

## Required R3 tests

Prove the five-action fixture, risk/context rules, tenant isolation, deny precedence, unknown input rejection, stale policy/data denial, bundle rollback, deterministic receipt hashing, unavailable-provider fail closed and explainable reason codes.

## Decision

Proceed only to the same isolated lab as OpenFGA. Do not introduce OPA in addition to another engine unless a measured hybrid need survives the comparison.
