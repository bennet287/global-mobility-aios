# Plasma AI → Global Mobility AIOS Controlled Adoption V1

**Date:** 2026-08-21  
**Status:** CONTROLLED ADOPTION / PILOT APPROVED — NOT PRODUCTION ADOPTED  
**Track:** Technology Radar / Platform Evolution  
**AIOS branch context:** `roadmap/global-mobility-aios-v12`  
**Canonical architecture refinement:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`  
**Active Technology Radar:** `TECHNOLOGY_RADAR_V1_3_1.md`  
**Accepted V1.3 baseline:** H.2.4 COMPLETE / PASS / SEALED  
**H.2.2 runtime-health classification refinement:** COMPLETE / PASS / SEALED — Production Proof `32505228943`  

This file is the controlled-adoption boundary for Plasma Wiki/Fractal. The detailed canonical architecture is intentionally kept in `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` rather than duplicated here.

## Permanent rule

> **Plasma provides execution and knowledge mechanics. AIOS owns organizational meaning, Evidence, authority, autonomy, risk, canonical state and consequences.**

## Pinned baselines

```text
Plasma Wiki    1.2.0 @ b27235fa11f1d3aa4deff50e45e52ea8ddc8af44
Plasma Fractal 1.1.0 @ e629ae2b80250ab502feefe3d9d0266bc58f15b2
License        Apache-2.0
```

## Plasma Wiki boundary

```text
project / organizational knowledge
→ Plasma Wiki candidate
→ scoped indexed retrieval
→ Context Broker
→ ContextBundle
```

Hard invariants:

- Wiki != Evidence;
- Wiki != VerifiedRule;
- Wiki != canonical legal truth;
- **retrieved knowledge != executable authority**;
- custom `.wiki/wiki.py` hooks are excluded from the first pilot;
- first pilot is repository/architecture/engineering knowledge only.

## Plasma Fractal boundary

```text
AIOS Mission
→ native Mission / WorkItem contract
→ Recursive Execution Port
→ bounded Fractal execution
→ typed AIOS result
→ verification / canonicalization / governance
```

Hard invariants:

- child delegated scope <= parent delegated scope;
- child execution never creates authority;
- child/sibling nodes are not automatically independent verifiers;
- depth, descendants, parallelism, iterations, runtime, cost and tools are bounded;
- first pilot is sandboxed Linux/POSIX engineering only;
- no production credentials/database;
- Git worktrees are not security sandboxes.

## PR #7 vendor-import gate

PR #7 (`vendor/plasma-pinned-donors-v1`) is a draft and must not merge while the complete pinned donor source trees are absent.

Required sequence:

```text
exact pinned source archives
→ deterministic extraction
→ exclusion audit
→ exact source bytes committed
→ LICENSE / provenance verification
→ SOURCE_MANIFEST.txt for Wiki + Fractal
→ repository-policy / size audit
→ CI
→ review
→ merge
```

A green scaffolding CI run is not proof of a complete vendor import. Vendoring is also not production adoption.

## Track relationship

```text
Track C
H.2 bounded safety/measurement foundation CLOSED
→ V1.3-I.1 autonomy profile/evidence DESIGN ENTRY OPEN

Track B
Plasma Wiki pilot
+ Plasma Fractal engineering pilot
+ LLMLingua-2 benchmark
+ Mobility Model Benchmark / Model Router research
```

## Final rule

> **Use Plasma to improve bounded decomposition and organizational knowledge. Never let Plasma decide what is true, who has authority, how much autonomy exists, what risk applies or what consequential effect is allowed.**
