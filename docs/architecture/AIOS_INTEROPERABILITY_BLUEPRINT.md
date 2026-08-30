# AIOS MCP / A2A Interoperability Blueprint

**Status:** V1.3.6 TRANCHE 1 ARCHITECTURE / NOT IMPLEMENTED

## Protocol roles

```text
MCP = governed access to external tools/data/prompt-like resources
A2A = governed interaction with independent external agent systems
```

Neither protocol owns AIOS identity, skills, capability, authority, autonomy, Evidence, WorkItems, ActionOutputs, Activity or Board sovereignty.

## Gateway topology

```text
                   AIOS canonical control plane
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
 Skill Registry       Authority Engine       Command Gateway
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
       McpGatewayPort                  A2AGatewayPort
              │                               │
    reviewed MCP servers             reviewed external agents
              │                               │
        tools/resources                  tasks/artifacts
```

## Common gateway request

Both ports consume an AIOS-owned envelope:

```text
tenant / authenticated principal / position version
WorkItem + command + purpose
capability / skill versions
authority decision receipt
risk / materiality / human-approval receipt
target registration + exact operation/schema version
data classification + outbound field allowlist
credential reference
idempotency key + command fingerprint
timeout / budget / retry / circuit policy
```

The gateway rejects missing, stale, mismatched or expired inputs.

## Provider registration

```text
ExternalProviderRegistration
  provider_type = MCP_SERVER | A2A_AGENT
  stable provider identity
  exact endpoint/interface/spec versions
  TLS/trust/signature policy
  credential reference
  capability catalog/card hash
  allowed tenants/purposes/data classes
  schema and operation allowlists
  effect/risk floor
  rate/budget/time limits
  review/effective/expiry/revocation state
```

Registration is canonical AIOS configuration. The external catalog/card remains attributed provider data.

## Execution receipt

```text
InteroperabilityExecutionReceipt
  request/correlation/idempotency identifiers
  target registration + version/hash
  protocol + operation + schema hash
  authority/human-approval receipt references
  normalized request hash
  provider task/call identifier
  status / typed error / retry classification
  response/artifact hashes and data classification
  timestamps / latency / cost where established
  external-effect and reconciliation state
```

The receipt can support AgentRun/ActionOutput lineage. It does not itself prove business correctness or become canonical Activity.

## State mapping

```text
MCP call state    = technical provider execution state
A2A task state    = external collaboration state
AIOS WorkItem     = canonical organizational work state
AIOS ActionOutput = accepted typed output
AIOS Activity     = canonical organization event when material
```

Provider success cannot complete a WorkItem until result validation, evidence/provenance checks and reconciliation succeed.

## Failure policy

- authentication, trust, authorization or schema failure: deny before provider call;
- target unavailable: typed `UNAVAILABLE`, no permissive fallback for material action;
- uncertain external effect: block replay and enter reconciliation;
- timeout before confirmed no-effect: treat as ambiguous, not automatically retryable;
- duplicate response/task: idempotently return the canonical receipt;
- catalog/card drift: quarantine target until reviewed;
- invalid/malicious output: retain technical receipt, reject canonical materialization;
- cross-tenant mismatch: deny and raise a security event.

## R3 lab boundary

Use disposable local servers, synthetic Austria fixtures and credentials with no production scope. The lab must prove malicious discovery, schema drift, revocation, replay, timeout/ambiguous effect, tenant isolation, data minimization and provider-output rejection. It must not contact real clients, government systems or production case stores.

## Adoption gate

No gateway implementation enters production without a concrete provider/use case, threat model, approved registration model, secrets integration, tenant/data-egress review, exact protocol version, conformance/security tests, kill switch, recovery/reconciliation runbook and acceptance record.
