# R3 Authority Lane

OpenFGA and OPA run against the identical 120-scenario AIOS corpus. Cedar is a
real CLI challenger over the hard subset and can be expanded to the full corpus.
This lane is isolated Technology Radar R3 research: no engine can authorize
product behavior or mutate AIOS canonical authority state.

## Exact candidates

```text
OpenFGA  v1.18.1
OPA      v1.19.1
Cedar    CLI v4.12.0
```

All pins are lab dependencies, not production dependencies.

## Constitutional boundary

AIOS owns canonical action metadata. Caller-controlled context cannot remove
mandatory authority, human-approval, tenant, or jurisdiction requirements.

```text
AIOS request
  -> canonical action metadata
  -> constitutional preflight
  -> candidate engine
  -> normalized ALLOW/DENY
  -> machine-readable fingerprinted evidence
```

`CAN DO != MAY DO` remains the governing invariant.

## Current closure status

Implementation exists for:

- OpenFGA and OPA 120-case correctness harnesses.
- 10,000-request performance benchmarks.
- fail-closed real-engine outage probes.
- seven-mode adapter chaos matrices.
- 12 constitutional invariants.
- 10 dangerous policy mutations.
- OPA canonical-action metadata hardening.
- real Cedar CLI policy/evaluation path.
- unified authority evidence rollup.

Real Cedar and the new closure artifacts must still be executed locally before
the lane may be classified as R3 complete.

## 1. Pull the authority branch

```powershell
cd D:\gmai-r3-authority
git pull origin radar/r3-authority
git rev-parse HEAD
```

Expected remote checkpoint begins with:

```text
5e4c232
```

## 2. Run unit/contract tests first

```powershell
python -m pytest labs/r3/authority/tests -q
python -m labs.r3.common.generate_fixtures --check
```

Do not continue to evidence capture if these fail.

## 3. Install and verify Cedar CLI

Cedar CLI v4.12.0 publishes a prebuilt Windows x64 binary and official
PowerShell installer.

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://github.com/cedar-policy/cedar/releases/download/cedar-policy-cli-v4.12.0/cedar-policy-cli-installer.ps1 | iex"

cedar --version
```

The real R3 result must show zero reference-fallback executions.

## 4. Start OpenFGA and OPA

```powershell
docker compose -f labs/r3/authority/docker-compose.yml up -d
```

Then execute the existing correctness and benchmark harnesses if a fresh
current-head result is desired:

```powershell
python -m labs.r3.authority.run_candidate --candidate openfga --output labs/r3/authority/results/openfga-correctness-20260830-004.json --run-id openfga-correctness-20260830-004

python -m labs.r3.authority.run_candidate --candidate opa --output labs/r3/authority/results/opa-correctness-20260830-004.json --run-id opa-correctness-20260830-004

python -m labs.r3.authority.benchmark --candidate openfga --run-id openfga-benchmark-20260830-004 --output labs/r3/authority/results/openfga-benchmark-20260830-004.json

python -m labs.r3.authority.benchmark --candidate opa --run-id opa-benchmark-20260830-004 --output labs/r3/authority/results/opa-benchmark-20260830-004.json
```

## 5. Run real Cedar challenger

Start with the hard subset:

```powershell
python -m labs.r3.authority.run_cedar_challenger --hard-subset-only --output labs/r3/authority/results/cedar-real-20260830-004.json --run-id cedar-real-20260830-004
```

A qualifying artifact requires:

```text
reference_fallback_count = 0
real_cedar_execution_count = scenario_count
failures = 0
critical_failures = 0
```

The explicit `--use-reference-fallback` option is diagnostic only and never
qualifies as empirical Cedar evidence.

## 6. Capture static controls

```powershell
python -m labs.r3.authority.static_evidence --output labs/r3/authority/results/authority-static-20260830-004.json --run-id authority-static-20260830-004
```

Required:

```text
invariants  12/12
mutations   10/10 detected
```

## 7. Run expanded chaos matrix

These tests deliberately inject connection refusal, timeout, HTTP 500,
malformed JSON, empty result, partial result, and unknown decision.

```powershell
python -m labs.r3.authority.chaos_matrix --candidate openfga --output labs/r3/authority/results/openfga-chaos-20260830-004.json --run-id openfga-chaos-20260830-004

python -m labs.r3.authority.chaos_matrix --candidate opa --output labs/r3/authority/results/opa-chaos-20260830-004.json --run-id opa-chaos-20260830-004
```

Every probe must return DENY with zero unauthorized canonical effects.

## 8. Stop containers and capture real-engine outage

```powershell
docker compose -f labs/r3/authority/docker-compose.yml down --volumes

python -m labs.r3.authority.chaos_probe --candidate openfga --run-id openfga-outage-20260830-004 --output labs/r3/authority/results/openfga-outage-20260830-004.json

python -m labs.r3.authority.chaos_probe --candidate opa --run-id opa-outage-20260830-004 --output labs/r3/authority/results/opa-outage-20260830-004.json
```

## 9. Verify every evidence fingerprint

```powershell
python -m labs.r3.common.verify_results labs/r3/authority/results/*.json
```

No artifact with a fingerprint mismatch, non-zero unauthorized canonical
effect, or critical failure is admissible.

## 10. Build unified authority rollup

```powershell
python -m labs.r3.authority.rollup --run-id authority-rollup-20260830-004 --output labs/r3/authority/results/authority-r3-rollup-20260830-004.json
```

The rollup advances only when all required coverage gates are present:

```text
OpenFGA correctness 120
OPA correctness 120
OpenFGA benchmark >= 10,000
OPA benchmark >= 10,000
OpenFGA real outage fail closed
OPA real outage fail closed
OpenFGA adapter chaos
OPA adapter chaos
real Cedar hard subset >= 76 with zero fallback
12 invariants + 10 mutations
unauthorized canonical effects = 0
critical failures = 0
```

Only then may the authority lane be proposed as `ADVANCE_TO_R4`.

## Evidence boundary

R3 PASS does not mean production adoption. OpenFGA, OPA, and Cedar remain
Technology Radar candidates until a later separately authorized R4/shadow or
adoption decision. No R3 result grants AI employees product authority.
