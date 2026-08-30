# R3 Authority Lane

OpenFGA and OPA run against the identical 120-scenario AIOS corpus. Cedar
challenges them on the hardest ~76 scenarios. This lane is isolated research:
no engine can authorize product behavior.

## Exact candidates

```text
OpenFGA  v1.18.1  release commit 69efbd9
OPA      v1.19.1  release commit 54896f9
Cedar    challenger — reference-oracle contract until real Cedar CLI is wired
```

All pins are explicit lab dependencies, not production dependencies. The
OpenFGA release is the current patch after security-sensitive v1.18.0 changes;
OPA v1.19.1 was built with an updated Go toolchain addressing standard-library
vulnerabilities.

## Boundary under test

AIOS retains context-heavy and constitutional preconditions. The external engine
answers only its bounded policy/relationship question. Any engine outage,
malformed response or ambiguous result is `DENY`.

```text
AIOS request
  -> canonical action metadata (authority/approval/jurisdiction)
  -> tenant/capability/delegation/jurisdiction/approval preflight
  -> candidate engine
  -> normalized ALLOW/DENY + reason
  -> machine-readable result
```

## Run when Docker is available

```bash
docker compose -f labs/r3/authority/docker-compose.yml up -d
python -m pytest labs/r3/authority/tests -q

python -m labs.r3.authority.run_candidate --candidate opa --output .test-tmp/opa-correctness.json --run-id opa-correctness-20260830-001
python -m labs.r3.authority.run_candidate --candidate openfga --output .test-tmp/openfga-correctness.json --run-id openfga-correctness-20260830-001

python -m labs.r3.authority.benchmark --candidate opa --run-id opa-benchmark-20260830-001 --output .test-tmp/opa-benchmark.json
python -m labs.r3.authority.benchmark --candidate openfga --run-id openfga-benchmark-20260830-001 --output .test-tmp/openfga-benchmark.json

docker compose -f labs/r3/authority/docker-compose.yml down --volumes

python -m labs.r3.authority.chaos_probe --candidate opa --run-id opa-outage-20260830-001 --output .test-tmp/opa-outage.json
python -m labs.r3.authority.chaos_probe --candidate openfga --run-id openfga-outage-20260830-001 --output .test-tmp/openfga-outage.json

python -m labs.r3.authority.run_cedar_challenger --output .test-tmp/cedar-challenger.json --run-id cedar-challenger-20260830-001 --use-reference-fallback --hard-subset-only
```

The committed unit suite uses `httpx.MockTransport`; it proves adapter contracts
and fail-closed behavior without claiming that either real server has passed R3.

## Additional R3 surfaces

- `labs/r3/authority/contracts/` — AIOS-owned canonical request/decision/delegation/approval/evidence schemas.
- `labs/r3/authority/invariants.py` — 12 property invariants checked against the corpus.
- `labs/r3/authority/policy_mutations.py` — 10 dangerous policy mutations that the reference oracle must detect.
- `labs/r3/authority/cedar_adapter.py` — Cedar challenger contract with reference-oracle fallback.
- `labs/r3/authority/run_cedar_challenger.py` — Cedar harness over the hard subset.
