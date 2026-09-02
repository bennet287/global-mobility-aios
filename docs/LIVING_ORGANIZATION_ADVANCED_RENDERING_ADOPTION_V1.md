# Living Organization Advanced Rendering Adoption V1

**Date:** 2026-09-02
**Branch:** roadmap/global-mobility-aios-v12
**Status:** ADOPTED / BOUNDED M IMPLEMENTATION SCHEDULED / PRODUCT-VALUE PROOF REQUIRED
**Scheduling authority:** docs/ROADMAP.md
**Technology truth:** docs/TECHNOLOGY_ADOPTION_LEDGER.md

## 1. Decision

Global Mobility AIOS adopts the following advanced rendering/computational visualization capabilities for Living Organization V2:

1. **WebGPU** — primary advanced browser rendering/compute substrate.
2. **Three.js WebGPU/compute layer** — scene graph, camera, picking, spatial composition and GPU-compute integration.
3. **GPU flow/fluid simulation** — work-flow, congestion, dependency and blocker-field visualization.
4. **Reaction-diffusion fields** — environmental memory, recurring pattern and organizational hot-spot visualization.

These are product capabilities, not decorative experiments.

> **The organization causes the visualization. The visualization never silently causes the organization.**

## 2. Product job for each adopted capability

### WebGPU

- render a dense living organization smoothly;
- execute field/particle/compute work away from the main interaction path where practical;
- support richer lenses without making the Cockpit sluggish.

### Three.js WebGPU/compute

- provide a maintainable spatial scene graph;
- camera/navigation and hit-testing/picking;
- compose employees, rooms, Smart Objects, evidence objects and GPU-driven fields;
- avoid building a custom graphics engine unnecessarily.

### GPU flow/fluid simulation

- turn WorkItem/dependency/throughput state into a legible FLOW lens;
- expose congested paths, shared blockers, stalled routes and load concentration;
- improve comprehension at scale compared with static graph/table views.

The field is derived visualization only. It cannot route WorkItems or authorize execution.

### Reaction-diffusion fields

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

Advanced rendering must be compared against a simpler reference view using the same canonical underlying data.

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

### WebGPU + Three.js

PASS when:
- canonical scene data renders through the adopted scene adapter;
- picking/camera/interaction works;
- dense-scene performance clears the gates;
- fallback behavior is defined;
- no organizational semantics move into renderer state.

### GPU flow/fluid

PASS when:
- FLOW is deterministically seeded from canonical/derived work-graph values;
- benchmark users identify primary congestion/shared-blocker routing 20% faster or with 25% fewer errors than static baseline;
- field instability cannot alter work state.

### Reaction-diffusion

PASS when:
- environmental fields are reproducible from persisted/derived historical inputs;
- recurring hot spots/patterns can be identified faster or more accurately than the non-field baseline;
- decay/retention parameters remain presentation semantics rather than organizational memory.

## 7. Default-UX promotion rule

Adoption is already decided. **Default prominence is earned.**

If a capability passes, it may be promoted into the default Living Organization experience where useful.

If it fails:
- keep it adopted but bounded;
- identify whether the failure is mapping, interaction, performance or cognitive overload;
- redesign and rerun;
- retain the clearer baseline as default meanwhile.

Do not reinterpret visual impressiveness as product value.

## 8. Roadmap insertion

~~~text
M.3  renderer adapter / scene-contract compatibility
M.4  WebGPU/Three.js employee/room scene path begins
M.6  Smart Objects / Board effects use GPU scene primitives where useful
M.7  FLOW lens introduces GPU flow/fluid field
M.8  replay exercises temporal scene performance
M.9  environmental memory introduces reaction-diffusion / traces
M.10 full Cognitive Ecology composition and cross-view value benchmark
~~~

## 9. Fallback and accessibility

A simpler reference/fallback representation remains available for unsupported WebGPU, low-power devices, accessibility needs, debugging, acceptance comparison and benchmark control.

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

> **Use advanced graphics to make a governed digital organization substantially easier to understand and operate.**
