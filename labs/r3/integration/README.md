# R3 Grand Integration Trial

The Grand Integration Trial is the programme-level evidence gate. It does not rerun every vendor tool itself; it consumes their machine-readable R3 result artifacts and refuses R4 eligibility when a required lane is missing, blocked, failed, lacks a fingerprint, or reports unauthorized canonical effects.

Required runtime lanes: authority, interoperability, security, skills, sandbox,
observability, secrets, recovery, memory, orchestration, and UI.

A lane is not accepted because one JSON file exists. The Grand Trial now requires:

- at least one non-empty executed artifact for the lane;
- zero blocked/failed/critical/unauthorized-effect evidence;
- a recomputed SHA-256 result fingerprint match;
- evidence generated at the expected implementation head;
- aggregate lane coverage of the minimum T1–T8 depth defined in
  `LANE_MINIMUM_TIERS`.

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

`R4_ELIGIBLE` means only that the configured current-head R3 evidence set satisfies this engineering gate. It does not mean production adoption is authorized, and it does not satisfy the independent Austria professional-review gate.
