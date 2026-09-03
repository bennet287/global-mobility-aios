# AIOS V2 — Phase 1C Component + State Audit

**Status:** COMPLETE — first component/state classification  
**Audit baseline:** `58fcec31d51d9ec1fba8e86e893721ca5735196d`  
**Documentation branch:** `docs/aios-v2-master-plan`  
**Production mutation:** none

---

# 1. Component inventory

The frontend currently contains **27 shared component files**.

## Large product components

| Component | Approx. size | Current role | V2 direction |
|---|---:|---|---|
| `LivingOrganizationScene.tsx` | 32.4 KB | structured Living Organization scene | preserve truth logic; split/rebuild presentation |
| `ClientPortalPage.tsx` | 28.3 KB | secure mobility-user portal | redesign underlying experience |
| `LivingOrganizationReplayTimeline.tsx` | 18.5 KB | canonical replay + state/diff inspection | flagship temporal component; refactor |
| `Sidebar.tsx` | 13.1 KB | experience switch + primary navigation | preserve behavior; replace IA/visual grammar |
| `LivingOrganizationWebGPUScene.tsx` | 8.5 KB | optional spatial renderer shell | preserve non-authority contract; rebuild visual scene |
| `EcosystemPortalPage.tsx` | 8.4 KB | partner/ecosystem portal | redesign |
| `AgentChatWidget.tsx` | 6.6 KB | global chat/proposal widget | replace global framing with contextual communication |
| `LivingOrganizationEnvironmentalMemory.tsx` | 6.2 KB | structured M.9.1 historical aggregate | preserve analytics; redesign representation |

## Supporting / primitive components

- `WorkspaceShell`
- `Topbar`
- `EvidenceProvenance`
- `TechnicalDisclosure`
- `InlineNotice`
- `EmptyState`
- `Skeleton`
- `StatusBadge`
- `MetricPill`
- `ActionCard`
- `SectionTitle`
- `CaseTable`
- `QueueStages`
- `TruthClaimCard`
- portal invite components
- OCR uploader
- lead identity.

---

# 2. Current state vocabulary

The existing shared components already cover many useful states:

```text
loading
ready
partial
offline
error
empty
disabled
unavailable
expired
verified
reviewed
approved
rejected
active
inactive
pending
queued
blocked
completed
initializing
```

This is a strong functional baseline, but the vocabulary is not yet governed through one V2 semantic-state taxonomy.

## V2 requirement

Create one state model separating:

### System-load state
- idle
- loading
- ready
- partial
- offline
- unavailable
- error

### Domain lifecycle state
- draft
- queued
- active
- blocked
- awaiting_owner
- under_review
- completed
- retired/superseded where applicable

### Evidence/truth state
- verified
- unsupported
- stale
- historical
- memory/aggregate
- predictive
- simulated
- recommendation
- human-authoritative

### Interaction state
- default
- hover
- focus
- active/pressed
- selected
- disabled

These layers must not be conflated in CSS tone names.

---

# 3. Primitive audit

## `ActionCard`

Current:
- generic action object
- tone-driven visual class

Finding:
useful as a small utility but too generic to be a foundational V2 domain component.

V2:
replace many use cases with:
- Owner Attention Object
- Authority Gate
- Mission Action
- Work Action.

---

## `MetricPill`

Current:
- generic compact metric.

Finding:
safe for secondary quantitative context, but should not become the default executive information primitive.

V2:
keep only for compact secondary metrics. Primary situation/comprehension should use composition rather than a wall of pills.

---

## `StatusBadge`

Current:
- generic tone-based badge with accessible label.

Finding:
useful but insufficient for V2 truth classes.

V2:
split semantic concepts:
- lifecycle badge,
- authority badge,
- evidence/truth badge,
- technical state badge.

The same colored pill should not represent every semantic category.

---

## `SectionTitle`

Current:
- generic heading helper.

V2:
preserve concept, align with the formal typography and information-depth system.

---

## `Skeleton`

Current:
contains:
- generic skeleton,
- metric skeleton,
- case-row skeleton,
- action-card skeleton.

Strength:
loading behavior is already treated as a component concern.

V2:
keep skeleton strategy but ensure skeletons do not imply data that may not exist. Spatial world should also have a truthful scene-loading state.

---

## `EmptyState`

Current:
- status-role empty state.

V2:
create differentiated empty states:
- legitimate zero state
- not-established state
- filtered-empty
- unavailable
- unsupported
- permission/authority boundary.

“Nothing here” is not one semantic state.

---

## `InlineNotice` / `DataNotice`

Current:
- inline notification/error taxonomy.

V2:
retain inline notice primitive, formalize severity tiers:
information, contextual warning, action-required, authority, critical failure.

Do not visually over-alert routine partial data.

---

## `TechnicalDisclosure`

Current:
- accessible technical disclosure
- existing tests require native/accessibility-friendly behavior.

Strength:
this component already embodies the desired V2 principle: technical provenance is available without dominating the primary surface.

V2:
**PRESERVE AND EXPAND** into a broader Provenance/Technical Disclosure system.

---

## `EvidenceProvenance`

Current:
- list/listitem/note semantics
- evidence stage/state/boundary presentation.

Strength:
domain-aware component rather than purely generic card.

V2:
evolve into:
- Evidence Object
- Provenance Drawer
- Source lineage
- verification/freshness/history layers.

This is a strong candidate for preservation through refactoring.

---

## `TruthClaimCard`

Current:
- claim + confidence presentation.

Finding:
important domain concept but “card” language is generic and confidence must remain carefully calibrated.

V2:
convert into an Evidence/Claim object with explicit:
- source,
- authority,
- confidence,
- verification,
- uncertainty,
- provenance.

---

# 4. Table/list audit

## `CaseTable`

Strengths:
- explicit table/row roles
- accessible label.

V2:
preserve semantic table/list behavior.
Do not replace dense operational tabular information with spatial/visual cards just for style.

## `QueueStages`

Current:
simple stage rows.

V2:
formalize as process/stage representation where stages are real. Avoid invented progress percentages.

---

# 5. Shell components

## `WorkspaceShell`

Current strengths:
- skip link
- main landmark
- focus containment
- Escape handling
- focus restoration
- mobile navigation state.

V2 classification:

**PRESERVE BEHAVIOR / REBUILD PRESENTATION**

The shell should become a V2 foundation primitive rather than be discarded.

## `Sidebar`

Current strengths:
- experience switching
- active route semantics
- theme action
- backend health
- keyboard/focus tooltips.

Current weakness:
- primary navigation density and module-oriented IA.

V2 classification:

**REBUILD IA + VISUALS, PRESERVE ACCESSIBILITY/BEHAVIORAL LESSONS**

## `Topbar`

Current:
- title/kicker
- load-state indicator
- refresh button.

Finding:
functional, but too route-template-like for V2 if used identically everywhere.

V2:
replace one universal topbar with layout-family headers:
- Executive Situation Header
- Domain Header
- Mission Header
- Evidence Header
- Decision/Authority Header
- Operator Workspace Header.

Shared status/refresh primitives remain reusable.

---

# 6. Communication component audit

## `AgentChatWidget`

Current states:
- open/closed
- loading
- error
- queued
- disabled

Current visual constructs:
- chat panel
- message bubble
- avatar
- proposal card/actions
- links.

Finding:
it is a generic global chatbot abstraction layered over an organizational product.

V2 decision:

**Do not preserve the global generic framing as the primary experience.**

Instead create contextual communication surfaces:
- Employee conversation
- Mission conversation
- Case conversation
- Board/authority discussion
- Evidence discussion.

Underlying API/message infrastructure can remain.

Proposal/approval actions must inherit authority semantics from their domain, not from generic chat buttons.

---

# 7. Mobility portal components

## `ClientPortalPage`

Current state coverage is strong:
- loading
- error
- expired
- verified
- approved
- reviewed
- completed
- empty
- ready
- disabled
- alert/status semantics.

Finding:
the portal already has a distinct security/access model and should not be forced into the same density as Owner/Operator UI.

V2 classification:

**REDESIGN AS ITS OWN LAYOUT FAMILY**

Preserve:
- secure access boundary
- token/access flow
- explicit errors
- next-action clarity
- protected-record separation.

## `EcosystemPortalPage`

Current states:
- loading
- error
- expired
- active
- disabled
- pending
- empty.

V2:
separate external-partner identity from internal Operator UI, while reusing AIOS trust/material language.

## Invite components

`ClientPortalInvite` and `EcosystemPortalInvite` already distinguish invitation/error/loading behavior.

V2:
preserve functional flows; re-skin through the new external-access design family.

---

# 8. Living Organization component graph

Current top-level flow:

```text
/cockpit/live-organization
        │
        ├── LivingOrganizationScene
        │       └── LivingOrganizationWebGPUScene
        │
        ├── LivingOrganizationReplayTimeline
        │
        └── LivingOrganizationEnvironmentalMemory
```

This is a good architectural separation of:
- live deterministic projection,
- optional renderer,
- temporal history,
- historical aggregate memory.

V2 should preserve this **semantic separation**, even if visual composition changes radically.

---

# 9. `LivingOrganizationScene` audit

Current component includes:

- lens console
- Owner analytical commands
- scene coverage
- projection planes
- structured reference
- flow baseline
- flow nodes/edges/handoffs
- department topology
- Mission Room
- employee grid
- canonical conversations
- canonical handoffs
- evidence/authority content
- truth/authority footer.

Current semantic data attributes include:

- active lens
- lens availability
- owner query
- flow authority
- department zone
- presence state
- conversation ID
- WorkItem ID
- handoff Activity ID
- smart-object state.

### Strength

It is highly testable and truth-explicit.

### Weakness

One component is carrying too many separate visual responsibilities and exposes governance mechanics alongside primary scene comprehension.

### V2 split

Recommended component architecture:

```text
LivingOrganizationWorkspace
  ├── OrganizationSceneViewport
  │   ├── HeadquartersRenderer
  │   ├── CharacterLayer
  │   ├── SmartObjectLayer
  │   ├── SemanticMotionLayer
  │   └── SelectionLayer
  │
  ├── OrganizationContextHUD
  ├── LensControls
  ├── OrganizationInspector
  ├── ReplayControls
  └── StructuredOrganizationFallback
```

The canonical read model remains separate from the renderer.

---

# 10. `LivingOrganizationWebGPUScene` audit

Current strengths:

- explicit initializing/ready/unavailable phases
- renderer backend reporting
- non-authoritative scene marker
- fallback status
- live accessibility copy
- GPU field trial gating
- renderer can fail while structured UI remains.

V2 classification:

**PRESERVE RUNTIME CONTRACT; REBUILD SCENE CONTENT**

Permanent invariants:

```text
renderer_authoritative = false
canonical mutation      = false
structured fallback     = always available
```

The new architectural HQ and characters must plug into this governance pattern rather than bypass it.

---

# 11. Replay component audit

`LivingOrganizationReplayTimeline` already supports:

- temporal events,
- state inspection,
- compare start,
- diff,
- coverage,
- unsupported dimensions,
- errors,
- empty states,
- pressed/selected controls.

V2 classification:

**FLAGSHIP REFACTOR**

Retain:
- exact Activity-cursor semantics
- coverage boundary
- A/B comparison
- unsupported dimensions
- no mutation.

Add:
- spatial temporal lens
- scene transitions
- structured change summary
- clear appeared/disappeared/changed grammar
- reduced-motion mode.

---

# 12. Environmental Memory component audit

Current structured component contains:

- routing memory
- department × event-kind heat
- temporal density
- coverage/boundary
- explicit non-authoritative/non-predictive posture.

V2 classification:

**PRESERVE STRUCTURED ANALYTICS + ADD OPTIONAL SPATIAL REPRESENTATION**

Structured view remains the accessible/provable baseline.

Spatial overlays may express:
- flow traces
- activity fields
- time density

but must remain visibly memory/aggregate.

---

# 13. Component anti-pattern findings

The current component layer still relies heavily on generic nouns:

```text
card
panel
pill
badge
notice
topbar
```

These are useful implementation primitives but should not become the product vocabulary users perceive.

V2 user-facing vocabulary should center on:

```text
Mission
Employee
Work
Evidence
Source
Decision
Authority
Handoff
Blocker
Department
Replay
Memory
Conversation
```

The implementation can still use primitive surfaces internally.

---

# 14. V2 component preservation map

## Preserve behavior nearly intact

- WorkspaceShell accessibility logic
- TechnicalDisclosure semantics
- CaseTable semantic table behavior
- EmptyState accessibility role
- renderer non-authority/fallback policy
- replay truth boundaries
- environmental-memory truth boundaries.

## Refactor heavily

- Sidebar
- Topbar
- EvidenceProvenance
- ClientPortalPage
- EcosystemPortalPage
- ReplayTimeline
- EnvironmentalMemory.

## Rebuild presentation

- LivingOrganizationScene
- LivingOrganizationWebGPUScene
- AgentChatWidget framing.

## Reduce importance / replace with domain objects

- ActionCard
- MetricPill
- generic StatusBadge
- generic SectionTitle as primary visual identity
- TruthClaimCard “card” framing.

---

# 15. Required V2 state primitives

Before migrating pages, implement:

1. `LoadState`
2. `LifecycleState`
3. `TruthClass`
4. `AuthorityState`
5. `AttentionTier`
6. `EvidenceState`
7. `HistoricalCoverageState`
8. `RendererState`
9. `InteractionState`

These should drive both:
- tokens/styles,
- accessibility labels,
- component variants.

---

# 16. Required V2 layout/component families

Create:

- `V2WorkspaceShell`
- `ExecutiveHeader`
- `DomainHeader`
- `MissionHeader`
- `AuthorityHeader`
- `ContextInspector`
- `ProvenanceDrawer`
- `AttentionObject`
- `MissionSurface`
- `EmployeeIdentity`
- `WorkObject`
- `EvidenceObject`
- `SourceObject`
- `DecisionObject`
- `AuthorityGate`
- `HandoffSignal`
- `FrictionSignal`
- `TemporalLens`
- `EnvironmentalPatternSurface`
- `StructuredSpatialFallback`.

Exact names can evolve, but semantic responsibilities should remain.

---

# 17. Phase 1C verdict

```text
27 shared components inventoried
state vocabulary identified
shell accessibility preservation path identified
generic component debt identified
Living Organization component graph mapped
replay/memory preservation path identified
V2 component families derived

Pass C — COMPLETE
```

Next:

**Phase 1D — Visual-System Audit**

It will quantify and classify:
- colors
- typography
- radius
- shadows
- gradients
- glass/translucency
- card/panel saturation
- breakpoints
- spacing
- iconography
- dark/light inconsistencies
- motion
- hard-coded visual values

and convert that evidence into the V2 UI constitution.
