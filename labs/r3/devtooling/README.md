# R3 Development-Model Tooling Benchmark

This lane evaluates coding-model output without making any development model part
of the AIOS runtime.

The benchmark is intentionally provider-neutral. It can be used later with a
local model, a manually copied external model response, or another development
model, but the evaluator never upgrades user-reported identity into verified
provider identity.

## Prepare the task packet

```powershell
python -m labs.r3.devtooling.prepare_packet `
  --output D:\gmai-dev-model-packet.json
```

Give only that packet to the candidate model and save its single Python-file
answer as, for example, `D:\candidate.py`.

## Evaluate safely

Candidate code executes only inside Microsandbox with:

```text
Network.none()
256 MiB memory
1 CPU
no host volumes
no credentials
12 second wall timeout
standard-library test fixture
```

Run:

```powershell
python -m labs.r3.devtooling.evaluate_candidate `
  --candidate-file D:\candidate.py `
  --candidate-name local-model-name `
  --provenance LOCAL_MODEL_USER_REPORTED `
  --run-id dev-model-20260831-001 `
  --output labs/r3/devtooling/results/dev-model-20260831-001.json
```

With no candidate output supplied, the harness records
`execution_blocked=true`. That is the correct zero-credit state.

The benchmark tests five AIOS-relevant coding problems:

1. `CAN DO != MAY DO` authorization.
2. VerifiedRule precedence over memory/model claims.
3. replay/idempotency.
4. secret redaction.
5. UI state vs canonical authority.

A pass is only bounded development-tool evidence. It does not grant model
authority, runtime inclusion, repository write authority, or production
adoption.
