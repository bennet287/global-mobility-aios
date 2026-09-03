# AIOS V2 — Phase 1E Living Organization Technical Reuse Audit

**Status:** COMPLETE — technical reuse and redesign boundary identified  
**Audit baseline:** `58fcec31d51d9ec1fba8e86e893721ca5735196d`  
**Documentation branch:** `docs/aios-v2-master-plan`  
**Production mutation:** none

---

# 1. Executive conclusion

The existing Living Organization should **not** be thrown away at the contract/governance layer.

It should be rebuilt primarily at the:

- visual representation,
- character layer,
- architectural world layer,
- camera,
- motion,
- spatial object,
- inspector/composition

layers.

The existing frontend already contains a strong reusable semantic spine:

```text
backend canonical organization state
        ↓
live-organization read models
        ↓
deterministic scene contract
        ↓
render model
        ↓
structured HTML scene
        ↓
optional non-authoritative Three/WebGPU renderer
        ↓
selection / presentation-only motion
```

Replay and Environmental Memory are also separate contracts rather than being invented inside the renderer.

This is exactly the architecture AIOS V2 needs.

---

# 2. Current reusable read-model surface

`apps/web/lib/live-organization.ts` already exposes typed models for:

- Austria Live Organization runtime snapshot
- employees
- departments
- Missions
- conversations
- handoffs
- incidents
- smart objects
- coverage
- WorkItems
- blockers
- decisions
- HumanActionRequests
- RiskEscalations
- rooms
- relationships
- deterministic scene plane
- non-canonical scene planes
- truth posture
- Replay
- as-of reconstructed state
- temporal state diff
- Environmental Memory
- Owner synthesis command.

This means V2 does **not** need to create a parallel “visual organization database.”

---

# 3. Employee contract reuse

Current `LivingSceneEmployee` includes:

```text
position_key
title
department
reports_to_position_key
authority_level
organization_status
work_item_id
work_status
semantic_state
presence_state
state_reason
```

## V2 reuse

These fields are sufficient to anchor:

- character identity mapping
- role/title
- department
- reporting topology
- seniority/authority cues
- WorkItem context
- semantic state
- explicit presence-state limitations.

## V2 gap

The character art system requires additional **presentation metadata**, but that metadata must not become canonical business truth.

Examples:

- character asset key
- silhouette archetype
- wardrobe set
- animation personality
- preferred workstation/pose family.

These should live in the Character Bible / frontend presentation registry keyed by canonical `position_key` or role taxonomy.

They must not alter the employee’s canonical organizational identity.

---

# 4. Department contract reuse

Current department projection includes:

```text
department_key
label
employee_count
work_item_count
active_blocker_count
canonical_basis
```

This is enough to drive:

- architectural zone identity
- department selection
- employee/work counts
- blocker attention
- accessible department summaries.

## V2 gap

Architecture requires a stable presentation topology:

- zone key
- architectural wing
- scene anchor
- material accent
- default camera target.

These are presentation mappings, not new canonical department truth.

---

# 5. Mission contract reuse

Current Mission projection includes:

```text
mission_key
objective_key
root_work_item_id
title
state
phase_key
participant_position_keys
work_item_ids
blocker_count
decision_count
projection_only
canonical_basis
```

This is an excellent basis for V2 Mission Rooms.

It supports:

- Mission identity
- participants
- work membership
- blocker count
- decision count
- phase/state
- canonical basis.

## V2 architectural mapping

A Mission Room can be generated from the Mission projection as a visual/navigational object.

No Mission Room should claim participants or activity beyond the supported projection.

---

# 6. Conversation contract reuse

Current conversation projection includes:

```text
conversation_id
participant_position_keys
work_item_id
status
summary
opened_activity_id
latest_activity_id
opened_at
lifecycle_at
authority_effect
transcript_persisted
canonical_basis
```

This is enough to drive truthful conversation presentation:

- participants can orient/gather,
- a conversation state can be shown,
- linked work is known,
- authority effect is known,
- transcript persistence is explicitly represented.

## Permanent V2 boundary

A conversation animation may indicate a canonical conversation relationship.

It must **not fabricate transcript content** when `transcript_persisted` or the history contract does not support it.

Ambient social gestures remain presentation-only and must be visually/semantically separate from canonical conversation.

---

# 7. Handoff contract reuse

Current handoff projection includes:

```text
activity_id
work_item_id
previous_position_key
assigned_position_key
status
occurred_at
causation_activity_id
canonical_basis
```

This is one of the strongest V2 opportunities.

A canonical handoff can drive:

```text
sender
   ↓
visual transfer object
   ↓
receiver
```

or:

```text
sender leaves local workspace
   ↓
moves toward collaboration point
   ↓
transfer occurs
   ↓
receiver resumes supported state
```

provided the exact visual semantics are bounded.

## V2 semantic animation rule

The handoff animation may communicate the persisted assignment relationship.

It must not imply:

- physical presence as real-world truth,
- elapsed transfer duration as canonical,
- conversational content,
- work completion,
- dependency resolution

unless separately supported.

---

# 8. Room contract reuse

Current room contract already recognizes:

- `mission_room`
- `evidence_lab`
- `board_room`

with:

```text
room_key
room_type
label
state
metric_label
metric_value
projection_only
canonical_basis
```

This directly supports the V2 architectural world.

## V2 change

Instead of rendering rooms as HTML/diagram boxes, map room types into real architectural zones/objects.

The contract remains the meaning layer; the Office Bible defines visual form.

---

# 9. Smart-object contract reuse

Current smart objects include:

```text
object_key
object_type
label
state
metric_label
metric_value
projection_only
canonical_basis
```

This is ideal for V2 Spatial Objects.

Possible V2 mappings:

- Mission Table
- Evidence Wall
- Source Terminal
- Decision Object
- Risk/Blocker object
- Board Table
- Case Station
- Replay object.

No new object type should be presented as canonical unless the backend contract supports it or the object is explicitly marked as presentation/navigation-only.

---

# 10. Relationship contract reuse

Current relationship projection includes:

```text
relationship_key
relationship_type
source_type
source_id
target_type
target_id
canonical_basis
```

This supports a V2 relationship layer.

Use cases:

- reporting lines
- Mission membership
- work relationships
- handoffs
- evidence/decision links where projected.

## Visual rule

Prefer spatial grouping/common fate/object interaction over permanent arrow spaghetti.

Relationship arrows become an analytical lens, not the default architecture.

---

# 11. Truth posture is a permanent foundation

Current scene truth posture includes:

```text
canonical_authority
scene_authoritative
renderer_authoritative
prediction_authoritative
environmental_authoritative
scene_mutations_allowed
```

V2 must retain this model.

## Permanent invariants

```text
scene renderer authority       none
renderer mutation authority    none
prediction authority           none unless separately governed
environmental-memory authority none
```

A beautiful V2 renderer does not gain authority merely because it is visually persuasive.

---

# 12. Current render-model architecture

`buildLivingSceneRenderModel` already separates canonical scene data from renderer-ready presentation.

It creates:

- employee slots
- WorkItem associations
- presentation state
- department zones
- room references
- structured flow baseline
- flow trial model.

It explicitly sets:

`sceneAuthoritative: false`

## V2 decision

Keep a render-model/adaptation layer.

Do not pass arbitrary backend data directly into Three scene code.

V2 architecture:

```text
canonical frontend read model
       ↓
V2 Organization Presentation Model
       ↓
Structured UI
       ├── accessible tree/list/inspectors
       └── Spatial Renderer Model
              ↓
         Three/WebGPU scene
```

---

# 13. Renderer-policy reuse

Current renderer policy:

- refuses an authoritative scene model,
- constrains selection shape,
- limits selectable entity classes,
- prevents duplicate active mount on the same canvas.

This should be preserved and extended.

## V2 selection types to consider

Current:

- department
- employee
- room
- smart_object

Potential V2 extension after contract review:

- Mission
- WorkItem
- Evidence
- Decision
- conversation
- handoff
- replay delta.

Extensions should be explicit and validated rather than accepting arbitrary selection payloads.

---

# 14. Three/WebGPU adapter reuse

Current renderer:

- uses Three `WebGPURenderer`
- detects actual backend
- falls back through renderer capability
- limits pixel ratio
- supports resize
- disposes resources
- tracks renderer data attributes
- can update model without remounting
- keeps structured UI available
- exposes selection
- marks presence as unclaimed.

## V2 decision

Keep the runtime pattern.

Rebuild the generated geometry/assets.

Current primitives such as:

- box torso
- sphere head
- simple zone placement

are prototype representations only.

Replace with:

- optimized GLB character assets
- architectural HQ assets
- animation mixer/clip system
- shared rigs
- smart-object assets
- material/light system
- LOD.

---

# 15. Current employee presentation contract

Existing presentation state intentionally guarantees:

```text
presentationOnly  = true
locomotionAllowed = false
presenceClaimed   = false
```

This is the correct M.4.1 safety posture.

## V2 evolution

Do **not** simply flip `locomotionAllowed=true`.

Instead introduce two movement domains:

### Ambient local locomotion

Presentation-only:
- short walk to coffee
- posture reposition
- local room movement
- lounge movement.

Must not claim canonical work routing/presence.

### Semantic locomotion

Triggered by a supported relationship/event:
- handoff
- Mission collaboration
- Board/authority event
- conversation lifecycle where sufficiently supported.

Each semantic locomotion type needs a contract and test.

---

# 16. Lens system reuse

Current lenses already include concepts such as:

- Mission
- Flow
- Blockers
- risk
- evidence
- decisions
- cost where available.

They carry:

- availability
- count
- summary
- canonical basis.

This is a strong V2 system.

## V2 decision

Keep the lens concept but redesign the control.

The lens selector should not dominate the default emotional scene.

Possible V2 lenses:

- Default organization
- Mission
- Flow
- Evidence
- Decisions
- Risk/Friction
- Memory
- Replay change.

Unavailable lenses remain visibly unavailable rather than fabricated.

---

# 17. Structured FLOW baseline reuse

Current analytics derive a read-only structured flow from canonical projections.

It includes:

- nodes
- edges
- handoffs
- blocker counts
- risk signals
- owner attention
- overdue state
- canonical basis.

Importantly, parent WorkItem topology is explicitly **not promoted to dependency truth**.

This distinction must survive V2.

## V2 use

Structured FLOW can power:

- analytical overlay
- handoff route highlighting
- Mission/work flow inspector
- optional spatial traces.

It must not become “the company is flowing this way” if the contract only supports topology/assignment.

---

# 18. GPU FLOW trial boundary

The current GPU flow field has explicit:

- trial version
- presentation formula
- promotion gates
- non-authoritative posture
- no mutation
- no throughput/dependency truth.

## V2 decision

Do not promote the current FLOW trial merely because V2 is more visual.

V2 may preserve it as an optional analytical layer until benchmark/promotion requirements are satisfied.

The new HQ redesign is independent of FLOW trial promotion.

---

# 19. Owner analytical-query reuse

Current analytics expose bounded Owner queries such as:

- blocked over a threshold
- overdue work
- incomplete evidence
- risk/decision-related queries.

They return:

- items
- summary
- canonical basis
- limitation.

This is exactly how V2 should integrate analytical commands.

## V2 use

Command palette / Organization command surface can invoke:

```text
“Show blocked missions”
“Show owner decisions”
“Show incomplete evidence”
```

and then visually focus supported objects.

The command changes the **view**, not canonical state.

---

# 20. Replay reuse

Current Replay is a separate read-only contract with:

- exact persisted Activity events
- coverage
- truncation
- no authority
- no mutation.

M.8.2 state reconstruction includes supported/unsupported dimensions.

M.8.3 diff compares two reconstructed states and omits unchanged entities.

## V2 decision

This becomes the temporal engine for Living Organization Replay V2.

Do not rebuild history inside Three.js.

Pipeline:

```text
Replay cursor
   ↓
backend/front-end replay state contract
   ↓
V2 presentation model
   ↓
structured + spatial reconstruction
```

Unsupported dimensions stay visually unavailable.

---

# 21. Environmental Memory reuse

Current Environmental Memory already carries:

- source Replay contract version
- time window
- coverage
- event-kind aggregates
- path frequency
- heat cells
- temporal buckets
- unsupported dimensions
- canonical projection
- non-authoritative
- non-predictive
- visualization-only.

## V2 use

Structured:
- tables/lists/heat/timeline.

Spatial:
- optional routing traces
- activity field
- temporal density layer
- department pattern overlay.

Memory must never visually collapse into live state.

---

# 22. Architectural world mapping

The existing room/department/Mission/smart-object models allow a clean V2 world mapping.

Recommended separation:

```text
CANONICAL ENTITY
  employee / department / Mission / room / work / handoff
        ↓
PRESENTATION REGISTRY
  asset / zone / layout / animation / material
        ↓
ARCHITECTURAL SCENE
```

The Office Bible owns the second and third layers.

---

# 23. Character registry mapping

Recommended V2 frontend registry:

```ts
position_key / role family
  → character archetype
  → model asset
  → wardrobe variant
  → material variant
  → rig class
  → idle personality
  → semantic animation capability
```

The registry must never rewrite:

- role
- authority
- WorkItem
- semantic state
- presence state.

---

# 24. Semantic animation registry

Required V2 architecture:

```text
canonical input
  + required evidence
  + presentation interpretation
  + allowed animation
  + forbidden implication
  + reduced-motion equivalent
  + replay behavior
```

Example:

## Handoff

Canonical input:
`LivingSceneHandoff`

Allowed:
- transfer object,
- sender/receiver focus,
- bounded path animation.

Forbidden implication:
- physical duration is real,
- conversation occurred,
- work was completed.

Reduced motion:
- static highlighted relationship + short state transition.

---

# 25. Ambient-life registry

Ambient actions are explicitly presentation-only.

Examples:

- blink
- breathe
- stretch
- local typing
- read tablet
- sip coffee
- local lounge movement
- glance at display
- look through window.

Ambient behavior must not:

- create a WorkItem claim
- create a conversation
- create presence truth
- create a handoff
- create a blocker
- create authority action.

This registry is how AIOS can feel alive without lying.

---

# 26. What can be reused unchanged vs rewritten

## Preserve strongly

- live read-model contracts
- truth posture
- Replay contracts
- replay state/diff contracts
- Environmental Memory contract
- renderer non-authority assertion
- structured fallback principle
- selection validation principle
- renderer lifecycle/resource discipline
- lens availability/canonical-basis pattern
- analytical-query limitation pattern.

## Refactor

- render model
- selection entity expansion
- lens UI
- structured scene composition
- replay UI
- memory UI.

## Replace visually

- primitive employee geometry
- primitive room/zone geometry
- static employee grid
- stacked room/scene presentation
- current spatial visual style.

## Add

- Character Bible registry
- Office Bible topology
- GLB asset pipeline
- animation state machine
- ambient behavior registry
- semantic animation registry
- pathfinding/bounded locomotion presentation layer
- camera language
- smart-object visual registry
- LOD/performance system.

---

# 27. V2 technical architecture proposal

```text
Live Organization API
Replay API
Environmental Memory API
        │
        ▼
typed domain read clients
        │
        ▼
Organization Presentation Model
        │
        ├─────────────────────────────┐
        │                             │
        ▼                             ▼
Structured Organization UI      Spatial Scene Model
        │                             │
        │                             ▼
        │                       Three/WebGPU
        │                             │
        │                       Character Runtime
        │                       Architecture Runtime
        │                       Motion Runtime
        │                             │
        └──────── inspectors/navigation ───────┘
```

No spatial layer writes canonical state.

---

# 28. Phase 1E verdict

```text
scene contracts audited
employee/department/Mission mappings audited
conversation/handoff reuse identified
room/smart-object reuse identified
truth posture preserved
render-model boundary preserved
Three/WebGPU runtime pattern preserved
Replay reuse defined
Environmental Memory reuse defined
semantic/ambient motion boundary defined
Character/Office presentation registries defined

Pass E — COMPLETE
```

Next:

**Phase 1F — Create the AIOS Design Skill**

The repository audit is now sufficient to write the governing design skill from evidence rather than taste.
