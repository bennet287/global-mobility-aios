# Global Mobility AIOS — V1.3 H.2.2 Runtime-Health Classification Refinement — 2026-08-21

**Stage:** V1.3-H.2.2 follow-up refinement
**Status:** IMPLEMENTED / PRODUCTION PROOF PENDING
**Parent accepted H.2.2 candidate:** `c5c2a68ac3a9caf2551204d61862b6ad0b6281eb`
**Parent accepted H.2.2 Production Proof:** `32473526874`
**Latest accepted V1.3 checkpoint:** V1.3-H.2.4
**Accepted H.2.4 technical candidate:** `e7584b90fc967e828960ae0730a35d8646fba74f`
**Accepted H.2.4 Production Proof:** `32500438187`

## 1. Purpose

This is a bounded measurement/provenance refinement to the already-sealed H.2.2 runtime-health attribution foundation.

It does not introduce H.2.5, provider-health scoring, provider quarantine, a recurrence threshold, automatic failover, automatic recovery, authority, or autonomy.

The verified problem is that the accepted H.2.2 attribution could represent both:

```text
unsupported/configuration/runtime-binding failure before provider egress
and
provider/runtime failure after the provider execution boundary
```

with the same undifferentiated `runtime_health_failure` provenance.

That is harmless while H.2.2 remains observation-only, but unsafe as future measurement input because configuration failures must not silently become evidence of provider outages.

## 2. Classification contract

New H.2.2 attributions explicitly carry:

```text
runtime_failure_classification
provider_egress_occurred
classification_contract
```

Bounded classifications:

```text
configuration_or_binding_failure
provider_transport_failure
provider_response_contract_failure
```

Semantics:

```text
configuration_or_binding_failure
    provider_egress_occurred = false

provider_transport_failure
    provider_egress_occurred = true

provider_response_contract_failure
    provider_egress_occurred = true
```

For this contract, `provider_egress_occurred=true` means the external provider execution boundary was entered. It does not assert that a remote provider successfully processed the request.

## 3. Failure boundaries

Examples classified before provider egress:

```text
unsupported E.2/G.1 runtime class
runtime binding/capability failure
provider configuration failure such as missing API credentials
verifier provider-adapter mismatch before provider invocation
```

Examples classified after the provider boundary:

```text
provider HTTP/request/transport failure
provider adapter returns malformed response envelope
returned provider identity mismatches trusted runtime binding
returned model identity mismatches trusted runtime binding
```

Typed eligibility/verifier business-output validation remains a separate domain-output contract and is not silently converted into provider-health evidence by this refinement.

## 4. Durability and replay

The existing activity type remains:

```text
organization.immune.eligibility_runtime_health_attributed.v1
```

The classification is an additive H.2.2 provenance extension.

Already-durable historical H.2.2 v1 records without the new classification fields remain historical and are not rewritten or backfilled. Their accepted legacy fingerprint remains replayable.

New attributions fingerprint the classification and egress fields. Replay with changed classification therefore fails closed.

A partial classification payload is invalid.

## 5. Control semantics remain unchanged

```text
incident kind                 runtime_health_failure
severity                      warning
control effect                observation_only
automatic circuit action      none
provider health policy        none
provider quarantine           none
automatic failover            none
automatic recovery            none
authority effect              none
autonomy effect               none
```

The Immune System remains restrict-only and this refinement adds no new restriction.

## 6. Acceptance obligations

Before this refinement may be marked accepted:

1. unsupported producer runtime must prove zero provider calls and persist `configuration_or_binding_failure / false`;
2. provider transport failure must persist `provider_transport_failure / true`;
3. provider response identity mismatch must persist `provider_response_contract_failure / true`;
4. verifier runtime-health attribution must retain proposal causation and correlation;
5. changed failure classification on replay must fail closed;
6. existing H.2.2 atomic rollback, torn-pair, identity-drift and observation-only proofs must remain green;
7. broad SQLite backend regression must remain green;
8. fresh PostgreSQL governed eligibility contracts must remain green;
9. frontend proof must remain green;
10. repository policy, dependency, release and diff-hygiene checks must remain green;
11. all four V12 Production Proof jobs must pass on the exact candidate.

Until that proof exists, this record is an implementation candidate only.
