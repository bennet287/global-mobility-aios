# Living Organization Advanced Rendering Adoption V1

**Date:** 2026-09-02
**Branch:** roadmap/global-mobility-aios-v12
**Status:** MIXED CLASSIFICATION — INFRASTRUCTURE ADOPTED / FLOW TRIAL / REACTION-DIFFUSION EXPERIMENT / COGNITIVE ECOLOGY OPTIONAL
**Scheduling authority:** docs/ROADMAP.md
**Technology truth:** docs/TECHNOLOGY_ADOPTION_LEDGER.md

## 1. Decision

Global Mobility AIOS uses a deliberately mixed classification for Living Organization V2:

1. **WebGPU — ADOPT**: primary advanced browser rendering/compute substrate.
2. **Three.js WebGPU/compute layer — ADOPT**: scene graph, camera, picking, spatial composition and GPU-compute integration.
3. **GPU flow/fluid simulation — TRIAL**: a strong product hypothesis for work-flow, congestion, dependency and blocker-field visualization; it must beat a strong structured analytical baseline.
4. **Reaction-diffusion fields — EXPERIMENT**: a weaker semantic hypothesis for environmental memory/pattern visualization with the hardest interpretation gate.
5. **Cognitive Ecology / Organica — OPTIONAL VIEW**: never the primary operating interface unless future evidence materially changes that conclusion.

Infrastructure adoption and visualization-hypothesis adoption are different decisions.

> **The organization causes the visualization. The visualization never silently causes the organization.**

## 2. Classification vocabulary and product jobs

### Classification vocabulary

~~~text
ADOPT
  infrastructure or product capability with a clear multi-surface role
  scheduled for implementation
  individual visualization failures do not automatically threaten the substrate

TRIAL
  strong product hypothesis
  scheduled in the roadmap
  benchmark against a maintained structured analytical baseline
  pass -> promote to product
  two failed design/benchmark iterations -> stop default-product development

EXPERIMENT
  weaker or semantically uncertain product hypothesis
  exploratory by design
  may need to establish a valid mapping before a full benchmark is meaningful
  success -> graduate to TRIAL
  repeated failure -> retire or remain explicitly lab-only

OPTIONAL VIEW
  never required for core operation
  must not displace the recognizable Organization or Structured interfaces without strong evidence
~~~

### Product jobs

### WebGPU

- render a dense living organization smoothly;
- execute field/particle/compute work away from the main interaction path where practical;
- support richer lenses without making the Cockpit sluggish.

### Three.js WebGPU/compute

- provide a maintainable spatial scene graph;
- camera/navigation and hit-testing/picking;
- compose employees, rooms, Smart Objects, evidence objects and GPU-driven fields;
- avoid building a custom graphics engine unnecessarily.

### GPU flow/fluid simulation — TRIAL

- turn WorkItem/dependency/throughput state into a legible FLOW lens;
- expose congested paths, shared blockers, stalled routes and load concentration;
- improve comprehension at scale compared with static graph/table views.

The field is derived visualization only. It cannot route WorkItems or authorize execution.

### Reaction-diffusion fields — EXPERIMENT

- reveal repeated collaboration/evidence patterns;
- expose persistent hot spots and environmental memory;
- make recurring organizational structure visible over time.

The field is a visual derivative of persisted history/metrics. It is not memory, evidence or canonical truth.

## 3. Architecture

~~~text
CANONICAL AIOS
    ↓
Live Organization Projection
    ↓
Scene Contract
    ├── deterministic state
    ├── predictive state (noncanonical)
    └── environmental state (derived/read-only)
    ↓
Three.js Spatial Scene
    ↓
WebGPU Render + Compute
    ├── employee / room rendering
    ├── interaction / picking
    ├── flow field
    ├── reaction-diffusion field
    ├── particles / heat / traces
    └── Cognitive Ecology composition
~~~

No WebGPU/Three.js/field state may become an independent source of organizational truth.

## 4. Product-value benchmark

Advanced rendering and analytical hypotheses must be compared against a maintained **structured analytical baseline** using the same canonical underlying data. The baseline may use tables, dependency graphs, matrices, timelines, heat, or animated edges; it is not defined by being visually flat.

Benchmark scenarios:

1. **Shared blocker** — identify the blocker affecting the most active WorkItems/employees.
2. **Decision attention** — identify the highest-consequence decision requiring Owner/Board attention.
3. **Flow congestion** — identify the dominant congested work route or stalled dependency chain.
4. **Evidence concentration** — identify where repeated evidence activity/contradiction is clustering.
5. **Dense organization navigation** — locate a named employee, Mission, blocker and decision in a high-density scene.
6. **Historical pattern** — identify a recurring organizational path/hot spot from environmental memory.

## 5. Quantitative gates

### Truth and correctness — hard gate

- **0** visual objects may claim a canonical relationship/state that the projection does not provide.
- Task-answer correctness using advanced views must be **no worse than the reference view**.
- Prediction/environmental layers must be visibly distinguishable from deterministic state.
- Renderer/compute state must have **zero direct command/authority path**.

Any violation is a hard failure regardless of performance or visual quality.

### Human comprehension

For blocker/flow/pattern benchmark tasks, the advanced visualization should achieve at least one of:

- **20% or more lower median time-to-correct-answer**, or
- **25% or more lower error rate**

against the simpler reference presentation, with no correctness regression.

A primitive that cannot clear this bar remains available only as optional/experimental until redesigned.

### Interaction and rendering

Representative desktop target:

- target **55 FPS or better** during ordinary scene navigation;
- no sustained benchmark operation below **30 FPS**;
- p95 selection/hover/local scene-feedback initiation **100 ms or less**;
- camera navigation remains responsive during field simulation;
- field compute must not block canonical API/event processing.

First dense-scene proof fixture:

- **100 visible employees/agents**;
- **200 Smart Objects / work/evidence objects**;
- **500 relationship/flow elements**;
- bounded particles/field resolution selected to remain inside the frame budget.

These numbers are a proof fixture, not a product maximum.

### Compute-value gate

GPU compute should demonstrate a material benefit on the dense-scene benchmark versus a CPU/main-thread equivalent. Target at least one:

- **30% or more lower main-thread visualization compute time**, or
- a scene/field capability that the simpler baseline cannot sustain above the 30 FPS floor.

## 6. Primitive-specific acceptance

### WebGPU + Three.js — ADOPT substrate acceptance

PASS when:
- canonical scene data renders through the adopted scene adapter;
- picking/camera/interaction works;
- dense-scene performance clears the gates;
- fallback behavior is defined;
- no organizational semantics move into renderer state.

### GPU flow/fluid — TRIAL promotion gate

TRIAL passes into product use when:
- FLOW is deterministically seeded from canonical/derived work-graph values;
- the comparison includes a strong directed-graph/animated-edge/heat baseline rather than a weak table-only strawman;
- benchmark users identify primary congestion/shared-blocker routing at least 20% faster or with at least 25% fewer errors than that baseline;
- field instability cannot alter work state.

If the graph/heat representation wins, the FLOW product need remains valid while the fluid representation fails.

### Reaction-diffusion — EXPERIMENT graduation gate

The experiment graduates to TRIAL only when:
- environmental fields are reproducible from persisted/derived historical inputs;
- the mapping from historical inputs to field parameters is explainable enough to prevent false semantic inference;
- decay, diffusion and retention parameters remain presentation semantics rather than organizational memory;
- an initial user task demonstrates a plausible actionable signal beyond a conventional historical heatmap/path-frequency baseline.

Only after graduation to TRIAL does the normal comprehension benchmark decide whether reaction-diffusion can enter product use.

## 7. Promotion and kill conditions

**Default prominence is earned. Infrastructure adoption is not the same as visualization promotion.**

~~~text
ITERATION 1
  implement bounded hypothesis
  benchmark
  identify failure mode

ITERATION 2
  targeted redesign
  benchmark again

ITERATION 2 FAIL
  STOP default-product development
~~~

After two failed iterations, a visualization must be one of:
- **RETIRED** when no other product value exists;
- **LAB-ONLY** with an explicit experimental label; or
- **DEFERRED** until materially new evidence or a new mapping justifies another attempt.

WebGPU and Three.js remain ADOPT even if an individual visualization fails because they serve multiple product surfaces.

GPU flow/fluid is a TRIAL. Two failed iterations stop its default-product development while the FLOW need may continue through graph/heat/animated-edge representations.

Reaction-diffusion is an EXPERIMENT. If it cannot first graduate to TRIAL, or later fails two targeted TRIAL iterations, it should be retired or kept lab-only rather than protected by sunk cost.

Cognitive Ecology / Organica remains an OPTIONAL VIEW. It cannot become the default operating interface merely because its component technologies are successful.

Do not reinterpret visual impressiveness as product value.

## 8. Roadmap insertion

~~~text
M.3  renderer adapter / scene-contract compatibility
M.4  WebGPU/Three.js recognizable employee/room scene begins
M.6  Smart Objects / Board effects use GPU scene primitives where useful
M.7  FLOW lens: mandatory structured graph/heat baseline + GPU fluid TRIAL
M.8  replay / temporal organization becomes a core historical baseline
M.9  Environmental memory TRIAL:
       mandatory structured historical baseline
       reaction-diffusion EXPERIMENT
       Phantom Futures bounded experiment
M.10 Cognitive Ecology / Organica OPTIONAL VIEW + cross-view benchmark
~~~

## 9. Fallback and accessibility

A **structured analytical reference view** remains permanently maintained alongside the spatial Organization view. A simpler rendering fallback also remains available for unsupported WebGPU, low-power devices, accessibility needs, debugging, acceptance comparison and benchmark control.

Fallback is not a second truth source. Both advanced and fallback paths consume the same AIOS projection.

## 10. Completion claim

Do not claim advanced-rendering product acceptance merely because WebGPU initializes, Three.js renders, a fluid shader runs, a reaction-diffusion pattern looks good, or a demo gets positive subjective feedback.

Completion requires:
- architecture-boundary tests;
- benchmark fixtures;
- performance measurements;
- comprehension/task evidence;
- exact-head proof;
- ROADMAP / Radar / Ledger / CHANGELOG reconciliation.

## 11. Three-view product taxonomy

~~~text
ORGANIZATION
  recognizable operating interface
  employees / departments / Mission Rooms / Evidence Lab / Board Room

ANALYTICAL
  pattern and problem lenses
  FLOW / RISK / COST / EVIDENCE / BLOCKERS / optional experiments

STRUCTURED
  canonical record inspection
  tables / lineage / dependency graph / timeline / matrices
~~~

No one surface is expected to do every cognitive job. All three consume the same governed AIOS truth.

> **Use advanced graphics to make a governed digital organization substantially easier to understand and operate.**
