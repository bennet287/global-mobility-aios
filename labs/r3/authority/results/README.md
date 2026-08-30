# R3 Authority Evidence — Initial Corpus, Load and Outage Pass

**Date:** 2026-08-30

**Status:** INITIAL R3 EVIDENCE CAPTURED / DECISION PENDING

**Production authority:** none
**Data:** synthetic/non-personal only

## Candidate identity

| Candidate | Version | Release commit | Verified release artifact SHA-256 |
|---|---|---|---|
| OPA | v1.19.1 | `54896f9f28515d14b31a93e6ef5737bb85866e30` | `fc932e644652d5634bc0d7a5e5f455dd26ebf5b243682a81eddf6d387a901e2e` |
| OpenFGA | v1.18.1 | `69efbd95b3d44afb2e2567d485dcc792c7d79e3f` | `0158afbdee45a64384f1646dc63c9e75ff5661994dfa57efdf1147139d1284b7` |

Docker Desktop was unavailable. The official Windows AMD64 release assets were
downloaded into ignored lab storage, verified against their published checksums,
and run with in-memory state on loopback ports only. Both processes were stopped
after capture and ports `18080`, `18081` and `18181` were verified closed.

## Technical candidates

```text
common contract/corpus base       db8d7a7524651c5586e2f8d4d8148fb6dc302abb
correctness/load implementation   239f12fbdd03afa5edea0bda0f205cf2c17afd94
outage identity implementation    46a45a064340bcc3cb1011194d12982c263b10dd
```

## Results

| Candidate | Correctness | Critical effects | 10k errors | p50 | p95 | p99 | Throughput |
|---|---:|---:|---:|---:|---:|---:|---:|
| OPA | 120/120 | 0 | 0 | 41.372 ms | 145.966 ms | 202.045 ms | 451.80 req/s |
| OpenFGA | 120/120 | 0 | 0 | 41.450 ms | 144.783 ms | 213.329 ms | 442.50 req/s |

Load shape for each candidate:

```text
1 cold request
1,000 asynchronous warm-up requests
10,000 measured requests
concurrency 25
Windows loopback / synthetic allowed decision
```

Observed process memory after exact-candidate runs:

```text
OPA working set       42,344,448 bytes
OpenFGA working set   50,962,432 bytes
```

After both servers were stopped, a real allowed-case request produced:

```text
OPA       DENY / ENGINE_UNAVAILABLE / unauthorized canonical effects 0
OpenFGA   DENY / ENGINE_UNAVAILABLE / unauthorized canonical effects 0
```

## Machine-readable evidence

| File | Embedded result SHA-256 |
|---|---|
| `opa-correctness-20260830-002.json` | `963a213b8819d6e8f945ca79d7c7a08d147d5f22aa5cade7d16f05612b154e0d` |
| `openfga-correctness-20260830-002.json` | `5c7fdbb3c46b9e3676a49f4e06e85124947dde90365ca29151d66a6c1fffbb4a` |
| `opa-benchmark-20260830-002.json` | `0660de942c4be8d0f8b4c9c71366067860b73f296538729ae43111d774157eac` |
| `openfga-benchmark-20260830-002.json` | `63599f1d69f6185726cb20fa4461122cc4cfe063254d7a0ee21decf4a520aa2c` |
| `opa-outage-20260830-002.json` | `ff9e2ec477929d6f4546b0fae0fcf72257a6f8d3c34da8d729b51b4045337609` |
| `openfga-outage-20260830-002.json` | `5a25d46ee348fad924c1e209f10c618503e0530a6b34eb1923eb76bf976ba7a3` |

## Honest interpretation

Both candidates pass the initial bounded gate. This does not select a winner.

- OPA evaluated the complete context-heavy request.
- OpenFGA answered the relationship/permission question while AIOS retained
  tenant, capability, delegation, jurisdiction and approval preflight.
- The expected corpus decisions come from an AIOS-owned deterministic oracle;
  they are not independent professional or production evidence.
- These results do not cover persistent policy/grant synchronization, policy
  mutation testing, Cedar's 30-case challenge, image/SBOM scanning, decision-log
  operations, multi-process availability or R4 shadow mode.

Required disposition for both candidates remains:

```text
CONTINUE_R3_WITH_SPECIFIC_GAP
```

Neither engine has production authority, production credentials, real case data,
an AIOS runtime integration or an R4 recommendation.
