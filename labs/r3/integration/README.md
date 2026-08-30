# R3 Grand Integration Trial

The Grand Integration Trial is the programme-level evidence gate. It does not rerun every vendor tool itself; it consumes their machine-readable R3 result artifacts and refuses R4 eligibility when a required lane is missing, blocked, failed, lacks a fingerprint, or reports unauthorized canonical effects.

Required lanes: authority, interoperability, security, observability, secrets, recovery, memory, and orchestration.

It also runs a deterministic cross-lane sovereignty attack covering poisoned memory, capability-vs-authority confusion, security-tool advice, telemetry, optimistic UI state, secret outage, and Human Owner gating.

```powershell
python -m labs.r3.integration.grand_trial `
  --run-id grand-integration-20260831-001 `
  --output labs/r3/integration/results/grand-integration-20260831-001.json `
  <result-json-1> <result-json-2> ...

python -m labs.r3.integration.scorecard `
  --output labs/r3/integration/results/final-scorecard.v1.json `
  <result-json-1> <result-json-2> ...
```

`R4_ELIGIBLE` means only that the configured R3 evidence set satisfies this engineering gate. It does not mean production adoption is authorized, and it does not satisfy the independent Austria professional-review gate.
