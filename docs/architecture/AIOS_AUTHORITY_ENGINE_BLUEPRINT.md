# AIOS Authority Engine Blueprint

**Status:** V1.3.6 TRANCHE 1 ARCHITECTURE / NOT IMPLEMENTED
**Candidate direction:** AIOS-owned authority semantics with optional replaceable decision provider

## Ownership

AIOS remains canonical for identity mapping, OrganizationPosition, capability, authority grants, autonomy, risk, Evidence requirements, reserved powers and Command Gateway outcomes.

An external engine may compute a decision from a versioned projection. It may not become the source of organizational meaning or mutate authority by itself.

## Evaluation flow

```text
CommandRequest
→ authenticate actor/service
→ resolve tenant + persistent position
→ resolve technical capability
→ load canonical authority/autonomy/risk/evidence facts
→ build immutable AuthorityEvaluationInput
→ AuthorityEnginePort
→ typed decision receipt
→ Command Gateway applies retained-power/materiality rules
→ canonical outcome/audit lineage
```

The Command Gateway may make the final result more restrictive than the provider response. It may never expand a provider denial into permission.

## Input contract

```text
tenant_id
principal_type / principal_id / identity_version
position_key / position_version
command_type / action / resource_type / resource_id
capability_key / tool_key
authority_policy_id / version
autonomy_profile_id / version
risk_class / materiality
evidence_preconditions + satisfaction refs
purpose / jurisdiction / case scope
requested_at / evaluation_deadline
idempotency_key / command_fingerprint
```

Unknown or missing required fields deny evaluation.

## Decision receipt

```text
decision = ALLOW | DENY | REQUIRE_HUMAN_REVIEW | UNAVAILABLE
reason_codes[]
provider_kind / provider_version
policy/data/projection versions
input_hash / decision_hash
evaluated_at / expires_at
```

`UNAVAILABLE`, stale projection, version mismatch or timeout fails closed for material actions. The receipt is technical/governance evidence, not Evidence/VerifiedRule.

## Provider boundary

```text
NativeAuthorityEvaluator
OpenFGAAdapter candidate
OPAAdapter candidate
CedarAdapter challenger
SpiceDBAdapter challenger
```

Only one primary external decision provider should be active for a given authority concern unless a documented hybrid model proves necessary. Dual-engine disagreement must deny and surface an incident; it must not select the more permissive answer.

## Reference fixture

For `employee:austria_regulatory_agent`:

```text
read approved official source        ALLOW
calculate points                     ALLOW
write internal finding               ALLOW
send legal conclusion to client      DENY / retained human authority
submit RWR application               DENY / no external-action authority
```

Tests must add another tenant, a revoked assignment, stale policy projection, duplicate command and engine outage.

## Adoption gate

No engine may advance beyond R3 without a threat model, exact decision schema, canonical-data synchronization design, failure/recovery semantics, latency budget, tenant/revocation/replay proof, operational ownership and explicit build-vs-integrate ADR.
