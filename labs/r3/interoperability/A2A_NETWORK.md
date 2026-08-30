
# A2A real-network depth

The pinned SDK is `a2a-sdk 1.1.3`, implementing A2A protocol 1.0.

This lab adds two real loopback transports to the existing in-process governed
A2A fixture:

- JSON-RPC 2.0 over HTTP/SSE, including Agent Card discovery.
- gRPC using the SDK's generated `A2AService` and `GrpcHandler`.

Both transports execute the same synthetic lifecycle:

```text
stream
  WORKING → COMPLETED

start
  INPUT_REQUIRED
      ↓
continue with same task_id
  COMPLETED

hold + return_immediately
  WORKING
      ↓
cancel_task
  CANCELED
```

All remote task state, stream events and artifacts remain observations. They do
not create WorkItems, Evidence, VerifiedRules, AuthorityGrants or external
actions.

Install the optional server/gRPC extras:

```powershell
python -m pip install -r labs/r3/interoperability/requirements.txt

python -m labs.r3.interoperability.run_a2a_network `
  --run-id a2a-network-20260831-001 `
  --output labs/r3/interoperability/results/a2a-network-20260831-001.json
```

If either optional transport cannot load, that transport is recorded as blocked
and the command exits 2 after attempting the other one. An executed failing
transport exits 1. This is implementation only until a real run artifact exists.
