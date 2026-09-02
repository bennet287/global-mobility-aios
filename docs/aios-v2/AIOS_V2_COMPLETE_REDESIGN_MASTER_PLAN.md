# AIOS V2 — Complete Product & Frontend Redesign Master Plan

**Document status:** DESIGN / EXECUTION BASELINE  
**Version:** 1.0  
**Date:** 2026-09-03  
**Repository:** `bennet287/global-mobility-aios`  
**Program:** Global Mobility AIOS  
**Scope:** Whole-product frontend redesign — UI, UX, Living Organization, characters, architectural world, motion, spatial interaction, governance visualization, accessibility, performance, migration, QA, and rollout.

---

## 0. Executive decision

AIOS V2 will not be a cosmetic reskin of the existing application. It will be a **whole-product frontend and interaction redesign** built on the strong existing backend/domain architecture.

The selected product thesis is:

> **AIOS = Executive Intelligence × Living Organization × Spatial Computing × Architectural Character World**

The product should feel like:

> **a premium operating system for a living digital company whose employees, missions, evidence, decisions, history, authority, and organizational state are visible, understandable, truthful, and alive.**

The redesign is governed by six equal first-class systems:

1. **UX System**
2. **UI System**
3. **Character System**
4. **Office / World Architecture System**
5. **Motion + Spatial Interaction System**
6. **Governance + Product Truth System**

Cross-cutting all six: accessibility, responsive behavior, performance, visual regression, usability validation, product consistency, CI proof, and truth-preserving presentation.

Characters and architecture are **not decorative additions**. They are core interaction systems of the Living Organization. The 3D environment is **not a separate simulation**; it is another representation of the same canonical AIOS state that powers structured product surfaces.


# 1. Program sequencing and hard precondition

## 1.1 Current M.9.1 state

Before V2 implementation begins, M.9.1 must be sealed.

- implementation: **COMPLETE**
- exact implementation head: `92b846ebd9f03c418b3435390c9a4bd5c4a7c138`
- local exact-head proof: **PASS**
- Woodpecker exact-head proof: **PASS — 4/4 workflows**
- PR #32: **MERGED**
- actual merge SHA: `3ebba28bdb2c7f3fd546968a02bcda59e9f742f6`
- ROADMAP closure commit: **PENDING**
- closure-head Woodpecker proof: **PENDING**
- M.9.1 sealed: **NOT YET**

## 1.2 No redesign contamination rule

Until M.9.1 is sealed, no AIOS V2 production changes belong on the roadmap/closure path: no character redesign, office rewrite, navigation rewrite, CSS reset, design-token migration, or redesign dependency changes.

```text
M.9.1 implementation head 92b846...
        ↓
Woodpecker implementation-head proof ✅
        ↓
PR #32 merged ✅
        ↓
ROADMAP closure commit
        ↓
Woodpecker closure-head proof
        ↓
M.9.1 COMPLETE / PASS / SEALED
        ↓
clean AIOS V2 branch
        ↓
design-system foundation
        ↓
prototype
        ↓
controlled migration
```

## 1.3 Branch strategy

After sealing M.9.1, branch from the exact sealed roadmap head.

Recommended program branch:

`design/aios-v2-complete-redesign`

Possible implementation slices:

- `design/aios-v2-foundation`
- `design/aios-v2-shell`
- `design/aios-v2-cockpit`
- `design/aios-v2-characters`
- `design/aios-v2-world`
- `design/aios-v2-semantic-motion`
- `design/aios-v2-evidence-decisions`
- `design/aios-v2-replay-memory`
- `design/aios-v2-operator`
- `design/aios-v2-mobility`
- `design/aios-v2-hardening`

Exact branch topology can be simplified, but every slice must remain reviewable and provable.


# 2. Scope: what is being redesigned

This is a redesign of the **whole product experience**, not only `/cockpit/live-organization`.

In scope:

- application shell
- navigation
- Owner / Board experience
- Professional / Operator experience
- Mobility-user experience
- Cockpit / Owner Home
- Living Organization
- Missions
- employees
- departments
- Board Room
- decisions
- Owner attention
- evidence
- provenance
- regulatory/global intelligence
- replay
- temporal reconstruction
- temporal comparison
- environmental memory
- communications
- automation surfaces
- profiles/cases/pathways
- timelines
- documents
- validation/review
- responsive behavior
- light/dark presentation
- accessibility equivalents
- renderer fallback
- motion and animation
- character art
- office architecture
- spatial objects
- styling architecture
- design-system testing
- visual regression
- CI acceptance

# 3. What is explicitly NOT being rewritten

Preserve unless separately governed:

- FastAPI backend
- PostgreSQL canonical state
- Redis/background workers
- organization models
- agents/AI employees
- WorkItems
- mission/objective model
- evidence architecture
- official-source architecture
- VerifiedRules
- SourceSnapshots
- executive decisions
- authority boundaries
- HumanActionRequests
- replay model
- M.8 as-of reconstruction
- M.8 temporal diff
- M.9.1 environmental memory
- provenance
- governance invariants
- provider abstraction
- Next.js
- React
- Three.js
- Woodpecker CI
- test discipline

V2 is a **frontend/product architecture redesign over an existing governed domain architecture**, not a backend reboot.


# 4. Existing frontend baseline

Confirmed current stack:

- Next.js `16.3.1`
- React `19.0.8`
- React DOM `19.0.8`
- Three.js `0.185.1`
- TypeScript `5.8.3`
- Geist / Geist Mono
- no heavyweight third-party UI framework defining the visual identity

Important observations:

- `apps/web/app/globals.css` is approximately **430 KB**
- `Sidebar.tsx` is approximately **13 KB**
- `LivingOrganizationScene.tsx` is approximately **32 KB**
- `LivingOrganizationReplayTimeline.tsx` is approximately **18 KB**
- `WorkspaceShell` already contains useful accessibility behavior: skip link, mobile-navigation focus management, focus restoration, Escape-to-close, ARIA labeling
- a global `AgentChatWidget` is mounted from the root layout
- navigation already distinguishes Owner / Board, Professional / Operator, and Mobility User

The three-experience split is useful. The problem is that the interface increasingly exposes **software/module topology** rather than **human task topology**.

# 5. Core product problems

## 5.1 Information hierarchy
Technical and operational facts too often compete at similar visual weight. V2 must show meaning first, evidence next, provenance on demand.

## 5.2 Navigation density
Many top-level routes and duplicated tools expose implementation structure. V2 should expose fewer conceptual destinations plus contextual access and command/search.

## 5.3 Visual identity
The current product is functional but insufficiently distinctive. V2 must be recognizably AIOS without depending on temporary fashion gimmicks.

## 5.4 Living Organization
Current employees are generic and the environment reads too much like a stacked/pixel office prototype. V2 requires original character identities, architectural world design, ambient life, and truthful semantic motion.

## 5.5 Whole-product consistency
Cockpit, Missions, Evidence, Decisions, Replay, Employees, Board, Intelligence, Operator, and Mobility should feel like different views into the same organization.


# 6. Final design positioning

## 6.1 Product character

AIOS should feel:

- intelligent
- calm
- capable
- premium
- deliberate
- contemporary
- human-readable
- alive
- trustworthy
- governed
- spatial when useful
- forensic when necessary

## 6.2 Fashionability rule

“Fashionable” does not mean copying short-lived UI trends.

> Contemporary enough to feel current in 2026+, disciplined enough not to look dated in 2030.

## 6.3 Balance

Conceptual target:

- **80% premium professional operating system**
- **20% emotional living-world experience**

This is a design metaphor, not a measurable requirement. Structured UI remains the fastest way to perform detailed work; the Living Organization becomes the emotional/organizational understanding layer.


# 7. AIOS Design Constitution

- **AIOS-UX-01 — Truth hierarchy before visual hierarchy.** Make truth easier to understand without changing its meaning.
- **AIOS-UX-02 — What matters before how it is stored.** Operational meaning first; evidence/provenance deeper.
- **AIOS-UX-03 — Complexity is progressively disclosed.** Complexity may be reorganized but not deceptively hidden.
- **AIOS-UX-04 — Not everything gets equal weight.** Routine metrics must not compete with authority decisions.
- **AIOS-UX-05 — Authority is unmistakable.** Owner/Board actions receive restrained prominence.
- **AIOS-UX-06 — Recognition over recall.** Consistent locations, icons, objects, language, and motion.
- **AIOS-UX-07 — Spatial and temporal continuity.** Preserve where the user came from and what changed.
- **AIOS-UX-08 — Animation cannot invent truth.** Semantic motion requires supported organizational state.
- **AIOS-UX-09 — Employees are identities.** Characters must be recognizable beyond labels.
- **AIOS-UX-10 — Architecture communicates organization.** Departments and authority zones have stable spatial meaning.
- **AIOS-UX-11 — Immediate feedback.** Inputs are visibly acknowledged without false optimism.
- **AIOS-UX-12 — Structured accessibility equivalent.** Every essential spatial fact exists semantically outside 3D.
- **AIOS-UX-13 — Truth classes are visually distinct.** Canonical, memory, prediction, simulation, recommendation, human authority, unknown/unavailable do not collapse.
- **AIOS-UX-14 — Aesthetic quality is functional quality.**
- **AIOS-UX-15 — No trend without purpose.**
- **AIOS-UX-16 — Stable mental models.** Same object behaves consistently across surfaces.
- **AIOS-UX-17 — Primary action scarcity.** Focused surfaces have only a few equal-weight primary actions.
- **AIOS-UX-18 — Uncertainty remains visible.** Simplification never turns unsupported/stale/non-authoritative state into certainty.

Meta-law:

> **Visual clarity must never reduce truth clarity.**

Motion law:

> **The organization causes the animation. Animation never causes the organization.**


# 8. UX laws and human factors

The AIOS Design Skill must encode, not merely mention, the relevant laws.

## Hick’s Law
Reduce simultaneous choice count; use contextual actions and progressive disclosure.

## Fitts’s Law
Provide generous hit areas, including invisible interaction volumes around spatial characters/objects.

## Jakob’s Law
Keep familiar software interaction patterns for navigation, search, forms, filters, tables, drawers, focus, and confirmation even though AIOS has a unique visual identity.

## Miller’s Law / working memory
Use grouping, persistent selections, contextual summaries, and visible relationships instead of forcing users to remember internal codes or long lists.

## Tesler’s Law
AIOS complexity cannot disappear. Put it at the correct cognitive layer.

## Doherty Threshold
Provide immediate response/acknowledgement. Exact timing and load budgets are **PROPOSED until measured**.

## Von Restorff Effect
Reserve visual exception for real exception: Owner attention, authority, blocker, critical failure, abnormal risk, important stale evidence.

## Serial Position Effect
Place highest priority where scanning naturally begins; avoid burying decisive action among metadata.

## Peak-End Rule
Polish Mission creation/completion, handoffs, evidence verification, Board resolution, replay comparison, and error recovery.

## Goal Gradient
Show truthful stages/blockers, never invented completion percentages.

## Zeigarnik Effect
Keep unfinished authority/blocker/evidence work discoverable without creating notification anxiety.

## Aesthetic–Usability Effect
Premium visual quality is functional, but cannot substitute for good task structure.

## Occam’s Razor
Do not use 3D, charts, holograms, or animation when a simpler representation answers the question better.


# 9. Gestalt + cognitive ergonomics

## Gestalt
- Proximity: employee + WorkItem, Mission + participants, evidence + source, decision + authority.
- Similarity: same semantic classes share visual grammar.
- Common region: departments, Mission Rooms, evidence groups, Board contexts.
- Continuity: flows, timelines, handoffs, navigation.
- Closure: compact forms may use perceptual closure only where state remains unambiguous.
- Figure/ground: active Mission/employee/decision must be visually dominant.
- Common fate: shared motion communicates relationships only when supported.

**Common fate is a signature AIOS opportunity.** A real handoff can be understood from movement without another arrow diagram.

## Cognitive ergonomics checklist
Every design review considers:
- cognitive load
- working memory
- recognition vs recall
- decision fatigue
- interruption cost
- change blindness
- inattentional blindness
- context switching
- scan paths
- spatial memory
- error recovery
- trust calibration
- information scent

## Interruption tiers
- Tier 0: ambient
- Tier 1: contextual
- Tier 2: attention
- Tier 3: authority
- Tier 4: critical operational failure

No “emergency” styling without a real severity basis.


# 10. Information-depth model

Every major entity should support five depths:

- **L0 Ambient:** How is the organization generally doing?
- **L1 Attention:** What needs action?
- **L2 Context:** Who/what/where/why?
- **L3 Evidence:** What supports this?
- **L4 Provenance/Internals:** Which canonical objects/events/contracts/versions/fingerprints/providers/timestamps produced it?

This depth model should shape both routes and components.


# 11. New information architecture

## Owner / Board
Primary:
1. Home
2. Organization
3. Missions
4. Intelligence
5. Evidence
6. Decisions
7. History

Contextual/secondary:
Owner Inbox, validation, source review, agent review, automation internals, cross-department friction, department workspaces.

## Professional / Operator
Primary:
1. Work
2. Profiles
3. Pathways
4. Evidence
5. Communication
6. Tools

## Mobility User
Primary:
1. Overview
2. My Case
3. Documents
4. Timeline
5. Messages

Internal governance terminology should not leak into the Mobility experience unless needed for transparency.


# 12. Preliminary route migration matrix

Exact consolidation/deletion must be validated in the Phase 1 route audit.

| Current route | V2 conceptual home | Initial action |
|---|---|---|
| `/cockpit` | Owner Home | Redesign |
| `/cockpit/live-organization` | Organization | Rebuild as flagship |
| `/owner-inbox` | Decisions / Attention | Contextualize |
| `/board-room` | Decisions / Board | Redesign |
| `/validation` | Evidence / Review | Consolidate |
| `/global-intelligence` | Intelligence | Redesign |
| `/intelligence` | Intelligence / Regulatory | Redesign |
| `/source-certification-review` | Evidence / Source Review | Consolidate |
| `/document-intelligence` | Evidence / Documents | Redesign |
| `/cross-department-friction` | Organization / Friction | Contextualize |
| `/agents/review` | Organization / Governance / Tools | Contextualize |
| `/agents/console` | Organization / Employees / Tools | Redesign/contextualize |
| `/automation` | Tools / Automation | Redesign |
| `/` | Operator Work | Redesign |
| `/profiles` | Profiles | Redesign |
| `/eligibility` | Work / Eligibility | Redesign |
| `/planning` | Work / Planning | Redesign |
| `/pathways` | Pathways | Redesign |
| `/timelines` | Work / Timeline | Redesign |
| `/communications` | Communication | Redesign |
| `/coaching` | Tools / Agent Coaching | Contextualize |
| `/corporate-mobility` | Tools / Corporate | Preserve + redesign |
| `/business-advisory` | Tools / Advisory | Preserve + redesign |
| `/investment-mobility` | Tools / Investment | Preserve + redesign |
| `/investment-suitability` | Tools / Investment | Audit consolidation |
| `/family-office` | Tools / Family Office | Preserve + redesign |
| `/tax-residency` | Tools / Tax | Preserve + redesign |
| `/authority-appointments` | Work / Authority | Contextualize |
| `/agency-submissions` | Work / Authority | Contextualize |
| `/external-agency-assignments` | Work / Authority | Contextualize |
| `/authority-submission-checklist` | Work / Authority | Contextualize |
| `/my-mobility` | Mobility Overview | Redesign |
| `/portal` | Mobility Case | Redesign |
| `/partner-portal` | External ecosystem | Audit separately |
| `/workspace/*` | Contextual workspaces | Audit/normalize |
| `/leads/*` | Operator Work | Audit/normalize |
| `/opportunities` | Business/Operator domain | Audit placement |
| `/intake` | Work / Intake | Redesign |
| `/return` | Domain-specific workflow | Audit placement |

No route is removed merely to make navigation shorter. Deep links and workflow capability must be preserved or explicitly migrated.


# 13. Navigation interaction model

## Primary rail
Expose conceptual destinations only.

## Context/local navigation
Show subdomains only after entering a domain.

## Command palette
Power navigation for entity search, route navigation, and safe commands. It does not bypass governance/confirmation.

## Universal search
Search understands entity types:
Mission, employee, WorkItem, evidence, source, decision, profile/case, conversation, page/tool.


# 14. UI visual identity

## Selected aesthetic
**Contemporary architectural luxury + premium operating-system restraint.**

Core language:
- graphite/ink
- warm off-white
- smoked/translucent overlays used sparingly
- fine metallic detail
- muted champagne warmth
- selective cool technical accents
- soft architectural shadows
- precise hairline borders
- controlled negative space
- strong editorial hierarchy
- refined numeric typography

Explicitly reject:
- generic AI purple gradients
- cyberpunk
- neon-outline everything
- hologram spam
- glow overload
- glass everywhere
- giant rounded-card grids
- emoji semantics
- template-looking SaaS dashboards


# 15. Color, typography, grid, spacing, material

## Color layers
Foundation:
canvas, base, raised, inset, overlay, spatial overlay, subtle/strong border, primary/secondary/tertiary/inverted text.

Semantic:
success, warning, critical, blocked, awaiting owner, active, queued, completed, unavailable, unknown, stale, informational.

Truth classes:
canonical, human-authoritative, AI recommendation, memory/aggregate, prediction, simulation, historical reconstruction, unsupported.

Department accents (directional, values **PROPOSED**):
- Executive: muted champagne/warm metallic
- Technology: precise cool blue
- Security: indigo/graphite
- Regulatory: warm amber/parchment
- Operations: teal
- Intelligence: cool cyan

Never communicate state through color alone.

## Typography
Geist/Geist Mono remain strong baseline candidates. Define roles: display, page title, section, object title, body, compact body, label, caption, metadata, numeric, status, technical.

Mono is appropriate for hashes, IDs, fingerprints, provider/model identifiers, contract versions, diagnostics.

## Layout families
Owner Home, domain overview, Mission, Evidence, Decision, Employee, Inspector, Operator dense work, Mobility user, Living Organization, split spatial+structured, replay/compare, full-screen focus.

## Spacing
Possible prototype scale `4, 8, 12, 16, 24, 32, 48, 64, 96`; **PROPOSED** until visual validation.

## Material grammar
Canvas, base work surface, raised object, inset detail, floating inspector, authority surface, spatial HUD, transient notice, technical disclosure.

Translucency is mainly for transient/floating spatial layers, not dense reading surfaces.


# 16. Domain-native components

AIOS should stop thinking primarily in generic cards.

Create:
- Mission Surface
- Work Object
- Employee Identity
- Employee Presence Object
- Evidence Object
- Source Object
- Decision Object
- Authority Gate
- Friction Signal
- Risk Signal
- Collaboration Thread
- Handoff / Transfer Signal
- Temporal Lens
- Replay Cursor
- Compare Delta
- Environmental Pattern Surface
- Department Surface
- Board Decision Surface
- Provenance Drawer
- Owner Attention Object
- Command Surface

Each component defines applicable states: default, hover, focus, active, selected, disabled, loading, unavailable, error, warning, critical, historical, predicted, memory/aggregate.


# 17. Cockpit / Owner Home V2

Cockpit becomes an **executive situation room**, not a KPI dashboard.

First viewport answers:
1. What is happening?
2. What needs me?
3. What is the organization doing?

Concept:

```text
┌──────────────────────────────────────────────────────────┐
│ AIOS                          Search / Command / Profile  │
├──────────────────────────────────────────────────────────┤
│ Good evening                                             │
│ Organization summary                                    │
│                                                         │
│ Missions · Attention · Supported active organization    │
├─────────────────────────────┬────────────────────────────┤
│ LIVE ORGANIZATION PREVIEW   │ NEEDS ATTENTION            │
│ miniature HQ                │ Board / evidence / blocker │
├─────────────────────────────┴────────────────────────────┤
│ Mission activity / temporal narrative                   │
└──────────────────────────────────────────────────────────┘
```

No count or presence claim is shown unless supported.


# 18. Missions, employees, Board, decisions, evidence

## Mission
First-class object across 2D and spatial UI. Contains purpose, status, owner/sponsor, participants, WorkItems, dependencies, blockers, evidence, decisions, conversations, recent Activity, next action, authority, and history.

No fake progress percentage.

## Employee
Persistent identity with role, department, responsibility, supported current work state, Mission, WorkItem, blockers, Activity, conversations, handoffs, contributed evidence/decisions, and technical runtime details behind disclosure.

## Board Room
Quiet, authoritative, low-noise, high-clarity. Primary decision + authority + recommendation/outcome + evidence + material uncertainty + linked Mission/work + lineage + authorized action.

## Decision
Status, authority, route, outcome, work links, evidence, source fingerprint, supersession, timestamps, history. Recommendation must never look identical to human approval.

## Evidence
Collapsed: source, title/claim, verification, freshness, jurisdiction, authority cue. Expanded: retrieval, fingerprint, snapshot, rules, source authority, professional review, history, dependencies.

Evidence must look like evidence, not a generic database record.


# 19. Character system — final art direction

Original **stylized miniature adult professionals**:
- compact professional body
- slightly oversized expressive head
- adult facial structure
- expressive hands
- strong footwear silhouette
- clean geometry
- high-end materials
- contemporary wardrobe
- subtle stylization
- strong role silhouette

Not:
- photoreal
- uncanny-valley
- pixel
- generic emoji/avatar
- childish/baby workforce
- identical model + shirt color
- direct copy of Boss Baby, Funko, Sims, or any franchise

References inform proportion, charm, expressiveness, polish, and miniature readability only.

Characters must communicate:
- role
- personality
- seniority
- department
- current state

Labels confirm identity; labels should not be the only identity mechanism.


# 20. CHARACTER_BIBLE schema

Each persistent employee design defines:
- canonical identity mapping
- display name
- role
- department
- seniority
- personality
- silhouette
- proportion class
- head shape
- facial language
- hair
- eye/brow expression
- wardrobe
- footwear
- accessories
- signature object
- default posture
- movement personality
- gaze
- idle behavior
- work behavior
- review behavior
- blocker behavior
- waiting behavior
- conversation behavior
- authority behavior
- handoff behavior
- completion behavior
- reduced-motion equivalent
- accessibility description
- LOD requirements
- rig/skeleton class
- animation set

## Hero role direction

### CEO
Contemporary tailoring, calm confidence, deliberate locomotion, measured gestures, strategic briefing object, high seniority without stereotypical excess.

### CTO
Architectural technical jacket/overshirt, compact technical device, quicker analytical gestures, system-surface interaction.

### CISO
Sharper geometry, controlled posture, restrained movement, alert gaze, security-display interaction, disciplined darker materials.

### Regulatory Intelligence
Evidence/source cues, precise reading/comparison gestures, research-table behavior, deliberate motion.

### Operations
Practical contemporary wardrobe, higher movement frequency, desk ↔ Mission ↔ colleague paths, case/work objects.

Acceptance: hide labels and users should still broadly distinguish executive, technical, security, regulatory, and operations roles.


# 21. Character runtime state model

## Ambient/presentation
May occur without claiming literal organizational work:
breathing, blinking, posture shift, glance, stretch, local desk motion, casual tablet interaction, coffee, window look, local walking, social idle gesture.

## Semantic
Requires supported AIOS state:
working, queued, waiting, awaiting_owner, blocked, reviewing, collaborating, handoff, conversation, Mission meeting, Board/authority, completed/settled.

Permanent invariant:

> **The organization causes the animation. Animation never causes the organization.**

Create a versioned mapping registry:

```text
canonical event/state
   ↓
presentation interpretation
   ↓
allowed animation
   ↓
fallback static/accessible representation
```

No renderer infers unsupported semantics from decorative motion.


# 22. Office/world architecture — final direction

The pixel tower / stacked compartment metaphor is retired rather than reskinned.

Target:

> **premium miniature architectural headquarters / campus / diorama that has come alive**

Conceptual topology:

```text
                       EXECUTIVE TERRACE
                CEO Studio ─ Board Chamber
                         │
                   Strategy Lounge
                         │

     REGULATORY /       CENTRAL       TECHNOLOGY /
       EVIDENCE ──────── ATRIUM ───── SECURITY
          │                │                │
 Evidence Library       Mission Hub      Systems Studio
 Regulatory Lab         Collaboration    Engineering
 Source Observatory     Rooms            Security Center
                           │
                     OPERATIONS STUDIO
                           │
                Case / Client / Work Cells
                           │
           Courtyard · Coffee · Lounge · Terrace
```

This is organizational topology, not a mandate for literal boxes.


# 23. Architectural language + department identity

Use:
- open atrium
- terraced levels
- bridges
- transparent partitions
- curved circulation where useful
- courtyards
- greenery
- warm architectural light
- material contrast
- refined furniture
- subtle embedded technology
- collaboration and focus areas
- private authority spaces

Department character:

### Executive
Quiet, negative space, refined wood/stone/metal, fewer objects, strategy surfaces.

### Technology
Precision, modular furniture, system walls, technical displays, prototyping surfaces, cooler task accents.

### Security
Focused, controlled, clear boundaries, low noise, restrained dark tone.

### Regulatory / Evidence
Warmer library/research cues, evidence walls, source tables, comparison surfaces.

### Operations
Open, kinetic, Mission boards, shared tables, case stations, higher circulation.

### Communal
Coffee bar, lounge, courtyard, greenery, informal niches, terrace, soft seating. Communal space is essential to make the organization feel inhabited.


# 24. Architecture as UI + smart spatial objects

The environment communicates state.

Mission Room:
- active → subtle illumination + mission surface + supported participants/objects
- blocked → controlled warning treatment + blocker object
- awaiting Owner → authority cue, no theatrical flashing

Evidence Lab:
spatial representations of VerifiedRule, SourceSnapshot, official source, document, professional review.

Board Room:
calm normally; restrained prominence and pending decision object when authority is required.

Formal spatial-object classes:
- Mission Table/Object
- Evidence Wall/Object
- Board Table
- Decision Object
- Source Terminal
- Risk Object/Beacon
- System Monitor
- Case/Work Station
- Conversation Surface
- Handoff/Transfer Object
- Blocker Object
- Timeline/Replay Object

Each defines canonical backing entity, display state, hover/focus, click, keyboard equivalent, screen-reader equivalent, historical behavior, unavailable behavior, reduced-motion behavior, and LOD behavior.


# 25. Spatial memory, camera, and interaction

Major rooms remain spatially stable so users learn the organization.

Desired learned mental model:
- Board above/near executive atrium
- Regulatory in evidence wing
- Security near Technology
- Mission Rooms central
- Operations connected to active case work

## Camera
Directed architectural camera:
- default three-quarter/isometric-ish architectural view
- bounded zoom
- gentle pan
- employee focus
- room focus
- Mission focus
- object focus
- return-to-HQ

Not required:
WASD, free flight, first-person, arbitrary orbit, game controls.

## Selection
Click employee → gentle reframe → background de-emphasis → compact context HUD → structured workspace one action away.

The product is not a game.


# 26. Motion system

Motion communicates:
- cause
- continuity
- hierarchy
- relationship
- state change
- completion
- transfer
- attention
- spatial orientation

It does not exist merely to look modern.

Proposed timing tokens (**PROPOSED until prototype validation**):
- micro: `100–160 ms`
- standard: `180–260 ms`
- panel: `240–360 ms`
- navigation: `280–420 ms`
- spatial focus: `400–700 ms`
- semantic character animation: natural clip duration

Define shared easing tokens; components do not invent arbitrary easing.

## Reduced motion
Full design mode:
- remove unnecessary travel/parallax
- replace large camera glides with short fades/cuts
- reduce ambient loops
- preserve semantic state through static cues

No essential meaning depends on animation.


# 27. Time and atmosphere

Optional morning/day/evening atmosphere may affect:
- sky/exterior tone
- skylight
- shadows
- window brightness
- interior warmth
- architectural accent light

Atmosphere is presentation only. It must not imply employee presence, work hours, workload, or live activity without backing state.


# 28. Living Organization as emotional center

Living Organization becomes the visual representation of the organization itself, not a novelty page.

Entry points:
- full Organization view
- Owner Home live-HQ preview
- Mission context
- Replay temporal mode
- Environmental Memory analysis mode

Interactions:
employee → Employee
Mission Room → Mission
Evidence Object → Evidence
Board Room → Decisions
Department → Department
Timeline → Replay

Structured UI and Living Organization are two representations of one canonical system.

## Division of responsibility
Spatial UI: awareness, identity, topology, relationships, collaboration, handoffs, Mission context, temporal transformation.

Structured UI: reading, forms, approvals, legal/regulatory text, tables, filters, evidence comparison, bulk work, technical provenance.

Never require a user to navigate a 3D scene to complete an ordinary administrative task.


# 29. Replay + Environmental Memory V2

## Replay
Existing M.8 provides canonical Activity replay, as-of reconstruction, and A/B comparison.

Spatial replay may allow:
timeline cursor → supported reconstruction → office/people/objects update.

Never fabricate unsupported history such as unsupported risk history, SourceSnapshot history, transcript content, historical evidence content, or other dimensions not proven by the reconstruction contract.

Compare:
- appeared
- disappeared
- changed
- unchanged omitted where appropriate

## Environmental Memory
M.9.1 remains canonical projection, non-authoritative, non-predictive, read-only, visualization-only.

Keep the structured analytics and optionally add:
- routing frequency → flow traces
- department/event heat → activity field
- hourly density → temporal overlay
- event-kind totals → pattern layer

Memory/aggregate must never look like live canonical truth.


# 30. Intelligence, communication, notifications, visualization
## Intelligence
Distinguish observation, source, interpretation, recommendation, VerifiedRule, evidence, and uncertainty. AI synthesis must not visually masquerade as official fact.

## Contextual communication
Move from generic global chatbot framing toward organizational communication:
- CTO conversation is visibly CTO context
- Mission conversation belongs to Mission
- Board conversation carries authority context
- evidence discussion carries evidence references

Underlying messaging can remain.

## Owner attention
Create one coherent attention model instead of badge spam. Aggregate Board decisions, authority requests, critical blockers, evidence freshness issues, important validation failures, and meaningful Mission changes.

## Data visualization
Every chart answers a question. Require explicit units/axes, accessible equivalents where needed, semantic color consistency, uncertainty visibility, and clear aggregation labels.


# 31. Accessibility + responsive

Target **WCAG 2.2 AA** for structured product UI.

Preserve/improve:
- skip navigation
- keyboard operation
- visible focus
- logical focus order
- focus restoration
- Escape semantics
- semantic landmarks/headings
- accessible names
- status announcements
- no color-only meaning
- contrast
- zoom/scaling
- reduced motion
- screen-reader equivalents
- no hover-only essential actions
- accessible error recovery

Spatial rule:
every essential scene entity has a structured representation.

Renderer failure must not block core product use.

Responsive modes:
- ultrawide
- desktop
- laptop
- tablet landscape
- tablet portrait
- mobile
- low-power
- reduced motion
- no-WebGPU/WebGL fallback

Mobile should not literally reproduce the desktop 3D scene; use organization snapshot + structured entities where appropriate.


# 32. Performance + asset pipeline

Principle:
**the application shell becomes usable before heavy 3D finishes loading.**

Proposed asset pipeline:

```text
Blender
  ↓
GLB / glTF
  ↓
mesh optimization
  ↓
texture compression
  ↓
rig/skeleton normalization
  ↓
animation clips
  ↓
LOD generation
  ↓
runtime scene
```

Character optimization:
shared rig families where possible, animation reuse, atlases, LOD, offscreen suspension, simplified distant rendering.

Environment optimization:
instancing, lightweight/baked lighting where appropriate, compressed textures, culling, lazy room/detail loading.

Exact budgets for initial JS, scene size, texture memory, polycount, draw calls, FPS, and interaction latency remain **PROPOSED until measured on the prototype**.


# 33. Frontend technical/CSS architecture

Keep Next.js + React + TypeScript + Three.js.

Introduce a V2 layer without destabilizing all legacy pages at once.

Recommended structure:

```text
apps/web/
  styles/
    foundations/
      reset.css
      tokens.css
      typography.css
      motion.css
    themes/
      light.css
      dark.css
    primitives/
      surface.css
      control.css
      layout.css
    domains/
      mission.css
      evidence.css
      decision.css
      employee.css
    spatial/
      organization.css
      overlays.css

  components/
    v2/
      primitives/
      domains/
      shell/
      spatial/
      inspectors/
```

Do not add another massive override layer to `globals.css`.

Migration:
1. tokens
2. primitives
3. V2 shell
4. incremental surface migration
5. isolate legacy selectors
6. remove legacy CSS only after references disappear
7. track CSS size and ownership

Token classes:
foundation colors, semantic colors, truth classes, departments, typography, spacing, radius, border, elevation, opacity, blur, motion, z-index, content widths, shell dimensions, breakpoints, spatial HUD dimensions.


# 34. AIOS Design Skill

Create:

```text
skills/aios-design/
├── SKILL.md
├── constitution/
├── ux/
├── ui/
├── characters/
├── architecture/
├── spatial/
├── motion/
├── governance/
├── product/
├── quality/
└── references/
```

`SKILL.md` must state:

> Never begin AIOS frontend implementation from aesthetics alone. First identify the user goal, information hierarchy, applicable UX laws, governance/truth constraints, accessibility needs, interaction model, spatial implications, responsive behavior, and performance implications. Then implement using the AIOS design system.

Required subfiles include:

### Constitution
`design-principles.md`, `truth-preserving-design.md`, `anti-patterns.md`, `decision-log.md`

### UX
`ux-laws.md`, `gestalt.md`, `cognitive-ergonomics.md`, `information-architecture.md`, `interaction-design.md`, `navigation.md`, `usability-heuristics.md`, `accessibility.md`

### UI
`visual-identity.md`, `color.md`, `typography.md`, `layout-grid.md`, `spacing.md`, `materials.md`, `elevation.md`, `iconography.md`, `components.md`, `data-visualization.md`, `responsive-ui.md`

### Characters
`CHARACTER_BIBLE.md`, `proportions.md`, `facial-language.md`, `silhouettes.md`, `wardrobes.md`, `personalities.md`, `executive-roles.md`, `specialist-roles.md`, `animation-states.md`, `interactions.md`, `rigging-lod.md`

### Architecture
`OFFICE_BIBLE.md`, `headquarters.md`, `department-zones.md`, `mission-rooms.md`, `board-room.md`, `evidence-lab.md`, `communal-spaces.md`, `furniture.md`, `materials-lighting.md`, `environmental-smart-objects.md`

### Spatial
`camera.md`, `wayfinding.md`, `selection.md`, `spatial-overlays.md`, `navigation.md`, `occlusion-lod.md`, `structured-fallback.md`

### Motion
`motion-language.md`, `ambient-animation.md`, `semantic-animation.md`, `character-locomotion.md`, `handoffs.md`, `conversations.md`, `transitions.md`, `reduced-motion.md`

### Governance
`canonical-visualization.md`, `authority.md`, `prediction.md`, `memory.md`, `uncertainty.md`, `historical-state.md`, `semantic-animation-contract.md`

### Product
`owner-home.md`, `living-organization.md`, `missions.md`, `employees.md`, `evidence.md`, `decisions.md`, `board-room.md`, `intelligence.md`, `replay.md`, `environmental-memory.md`, `operator.md`, `mobility-user.md`, `communications.md`

### Quality
`performance.md`, `accessibility.md`, `responsive.md`, `usability-testing.md`, `visual-regression.md`, `design-review.md`, `acceptance-gates.md`

Character Bible + Office Bible + Motion Language + Spatial Interaction + Truth-Preserving Design are hard preconditions for Living Organization V2 implementation.


# 35. Design review gates

Every redesigned surface must pass:

- **Goal:** user immediately knows purpose.
- **Attention:** most important state/action dominates.
- **Hick:** not too many equal choices.
- **Fitts:** comfortable targets.
- **Tesler:** complexity at correct layer.
- **Recognition:** user recognizes rather than memorizes.
- **Truth:** presentation cannot misrepresent canonical state.
- **Consistency:** uses AIOS primitives/tokens.
- **Character:** identity/state reads correctly where relevant.
- **Spatial:** space communicates useful relationships.
- **Motion:** animation communicates cause/continuity.
- **Accessibility:** task works without mouse/motion/3D/color dependency.
- **Responsive:** target devices work.
- **Performance:** visual quality does not destroy responsiveness.
- **Distinctiveness:** screenshot cannot plausibly be any generic SaaS template.

If it looks generic, it requires another design pass.


# 36. Anti-pattern register

Fail design review unless a documented exception exists:

- generic SaaS card farm
- pixel office
- stacked apartment/tower office
- generic AI avatar
- identical character bodies with shirt-color role coding
- childish/baby-looking workforce
- photoreal uncanny-valley workforce
- purple-gradient AI identity
- cyberpunk neon overload
- hologram spam
- excessive glow
- glassmorphism everywhere
- free-fly game camera
- 3D required for ordinary work
- fake meetings
- fake handoffs
- fake employee presence
- semantic animation without evidence
- raw governance metadata dominating primary UX
- color-only status
- giant navigation inventories
- equal-weight metric walls
- motion without reduced-motion equivalent
- independent page-specific visual systems
- arbitrary CSS values
- unbounded component variants
- alerts used for normal information
- hidden uncertainty


# 37. Prototype strategy

Do not redesign dozens of routes before proving the language.

Build one representative vertical slice:

1. V2 shell/navigation
2. Owner Home
3. live HQ viewport
4. one Mission
5. one Board decision
6. one Evidence object
7. one employee inspector
8. four hero characters: CEO, CTO, Regulatory, Operations
9. representative architecture: atrium, executive area, evidence zone, technology zone, Mission Room, communal area
10. ambient animation
11. one real semantic state transition
12. reduced-motion mode
13. no-3D structured fallback

Prototype questions:
- Does it look uniquely AIOS?
- Can Owner see what needs attention?
- Do characters look adult/professional?
- Are roles recognizable without labels?
- Does office feel architectural rather than game-like?
- Is 3D useful?
- Is spatial → structured transition natural?
- Does motion clarify relationships?
- Is reduced-motion excellent?
- Is shell usable before scene load?
- Does evidence/provenance remain easy to inspect?
- Does it feel premium rather than flashy?


# 38. Implementation phase roadmap

## Phase 0 — Seal M.9.1
ROADMAP closure → Woodpecker 4/4 → exact closure SHA → SEALED.

## Phase 1 — Audit + Constitution
Route/component/CSS/interaction/accessibility/performance inventories; AIOS Design Skill; UX/UI/Character/Office/Motion/Governance documents; IA; migration matrix.

## Phase 2 — V2 Foundation
Tokens, type, color, spacing, materials, elevation, icon strategy, motion tokens, primitives, semantic/truth statuses, shell, command palette skeleton, themes.

## Phase 3 — Owner Home
Executive situation room, attention model, Mission summary, organization preview, contextual navigation, technical disclosure, responsive variants.

## Phase 4 — Character production system
Proportions, CEO/CTO/Regulatory/Operations, rig strategy, animation state machine, ambient/semantic clips, LOD, accessibility descriptions.

## Phase 5 — Headquarters architecture
HQ blockout, atrium, Executive, Technology/Security, Regulatory/Evidence, Mission Hub, Operations, communal spaces, lighting/materials, camera, wayfinding.

## Phase 6 — Living Organization V2
Scene runtime, employee placement, selection, department/Mission selection, smart objects, structured fallback, ambient life, semantic registry.

## Phase 7 — Canonical semantic integration
WorkItem, blocker, handoff, conversation, Mission collaboration, Board escalation, completion mappings + tests.

## Phase 8 — Evidence + Decisions + Board
Evidence Object, provenance inspector, Decision Object, authority gate, Board V2, uncertainty language, history/source drill-down.

## Phase 9 — Replay + Compare + Environmental Memory
Temporal lens, replay scrubber, as-of spatial reconstruction, A/B comparison, change highlights, memory overlays, structured equivalents.

## Phase 10 — Operator migration
Work, Profiles, Eligibility, Planning, Pathways, Evidence, Communication, specialist tools, authority workflows.

## Phase 11 — Mobility-user migration
Overview, My Case, Documents, Timeline, Messages, simplified trust model.

## Phase 12 — Hardening
Responsive, keyboard, screen reader, contrast, zoom, reduced motion, fallback, profiling, asset optimization.

## Phase 13 — Legacy retirement
Redirects/aliases, dead components, CSS removal, unused assets, nav cleanup, docs.

## Phase 14 — V2 acceptance
Full CI, visual regression, browser E2E, accessibility, usability, performance evidence, design review, governance review, release notes.


# 39. CI / QA strategy

Forward CI: **self-hosted Woodpecker**.

Existing lanes:
- repository-policy
- backend-sqlite
- frontend
- postgres-governance

V2 additions should include:
- token/design-foundation tests
- anti-pattern/static design tests
- automated accessibility
- reduced-motion tests
- responsive screenshots
- visual regression
- renderer contracts
- semantic-animation contracts
- fallback-mode E2E

GitHub hosted Actions quota exhaustion is not a product failure; historical Actions evidence remains historical evidence.

## Visual regression states
Owner Home light/dark, authority attention, Board pending, Evidence verified/stale/unsupported, Mission active/blocked, employee states, Living Organization default/selected, reduced motion, fallback renderer, replay, compare, environmental-memory overlay.

## Semantic motion tests
Every mapping has canonical input fixture, expected presentation, negative unsupported test, reduced-motion equivalent, and replay behavior when relevant.

## Accessibility
Automated + keyboard-only + screen-reader smoke + 200% zoom + touch + fallback.

## Performance
Measure shell interactivity, scene load, scene memory, frame stability, route transition, animation jank, data-heavy surfaces, low-power behavior. Hard numeric thresholds are set only after measured prototypes.

## Usability
Owner, Operator, Mobility task suites; track task completion, time, first-click correctness, errors, confidence, and qualitative comprehension.


# 40. Risk register

| Risk | Mitigation |
|---|---|
| Visual design outruns truth model | Governance system + semantic animation contract |
| 3D becomes a game | Structured UI remains primary for work; bounded camera |
| Characters become childish | Adult facial structure + professional wardrobe + Character Bible |
| Fashion becomes dated | Restrained architectural base; limited trend gimmicks |
| Performance collapses | Progressive loading, LOD, instancing, shared rigs, measurement |
| Route migration breaks workflows | Migration matrix, aliases, staged E2E |
| Accessibility is sacrificed | Structured equivalent constitutional requirement |
| CSS debt grows | V2 tokens/styles, incremental migration, tracked deletion |
| Too many custom components | Domain object taxonomy + primitive layer |
| Redesign destabilizes backend milestones | Separate branches, preserve contracts, seal first |


# 41. Locked design decisions

Locked unless prototype evidence justifies reopening:

1. Whole project redesign, not Live Organization only.
2. Backend/domain architecture preserved.
3. Six first-class design systems.
4. Characters + architecture are core interaction systems.
5. Pixel tower retired.
6. Original stylized miniature adult-professional characters.
7. Photoreal, uncanny, childish, generic avatars rejected.
8. Architectural miniature HQ/campus/diorama.
9. Living Organization is emotional center.
10. Structured UI remains fastest detailed-work path.
11. AIOS does not become a game.
12. Directed camera, not free flight.
13. Ambient and semantic motion are separate.
14. Semantic motion requires supported state.
15. Essential spatial facts have structured accessible equivalents.
16. Replay shows only proven historical dimensions.
17. Environmental Memory remains visibly memory/aggregate.
18. Navigation follows user mental model rather than module inventory.
19. Generic card-farm design rejected.
20. Purple-gradient AI branding rejected.
21. Fashionability must remain durable.
22. Character Bible + Office Bible precede Living Organization V2.
23. V2 implementation begins only after M.9.1 is sealed.

# 42. Open decisions

Decide through prototype/profiling:
- exact colors
- spacing/radius values
- exact motion timings
- character head/body ratio
- rendering technique
- lighting
- polycounts/textures
- LOD thresholds
- asset budget
- target FPS by device
- WebGPU-specific enhancements
- raw Three.js vs any helper abstraction
- icon package vs custom set
- command-palette exact behavior
- route alias strategy
- token implementation technology

These are deliberately not guessed now.


# 43. Required artifacts before mass implementation

- [ ] M.9.1 closure proof
- [ ] Master Plan committed into V2 program
- [ ] AIOS Design Skill
- [ ] Design Constitution
- [ ] UX Laws
- [ ] Information Architecture
- [ ] Visual Identity
- [ ] Token specification
- [ ] Character Bible
- [ ] Office Bible
- [ ] Motion Language
- [ ] Spatial Interaction specification
- [ ] Truth-Preserving Design
- [ ] Semantic Animation Contract
- [ ] Accessibility specification
- [ ] Performance strategy
- [ ] Route migration matrix
- [ ] Component migration matrix
- [ ] Prototype acceptance checklist
- [ ] V2 CI additions


# 44. Definition of “AIOS-looking”

A surface qualifies as AIOS V2 when:
- hierarchy is decisive
- domain objects are recognizable
- typography is controlled
- spacing is deliberate
- materials feel architectural
- metadata does not dominate
- status is truthful
- authority is clear
- provenance remains accessible
- motion is meaningful
- keyboard works
- reduced motion works
- no-3D fallback works
- it cannot easily be mistaken for a generic SaaS template

# 45. Definition of Living Organization quality

Successful when:
- office reads as architecture
- characters read as persistent employees
- roles are distinguishable
- ambient life exists
- semantic actions are truthful
- Mission relationships are understandable
- departments are spatially memorable
- selection feels natural
- camera is never a burden
- structured detail is one transition away
- replay is meaningful
- performance is acceptable
- accessibility equivalents exist


# 46. Immediate execution sequence

1. **Close M.9.1**
   - write ROADMAP closure record
   - commit closure on top of actual merge `3ebba28bdb2c7f3fd546968a02bcda59e9f742f6`
   - run all four Woodpecker lanes on closure head
   - record closure SHA/proof
   - classify M.9.1 COMPLETE / PASS / SEALED

2. **Create AIOS V2 program branch**
   - branch from sealed closure head
   - no unrelated backend work

3. **Commit this Master Plan**
   - make it the design/execution baseline

4. **Create `skills/aios-design/`**
   - Constitution, UX, UI, Characters, Architecture, Spatial, Motion, Governance, Product, Quality

5. **Perform repository-wide frontend audit**
   - routes, components, CSS, states/interactions, tests, accessibility, performance

6. **Build V2 vertical-slice prototype**
   - shell, Owner Home, live HQ, Mission, Evidence, Board decision, four hero characters, representative architecture, ambient + semantic motion, structured fallback

7. **Review prototype against this plan**
   - only then mass-migrate the frontend


# 47. Publication status

```text
AIOS V2 master direction        LOCKED
Whole-project redesign          APPROVED
UX                              IN SCOPE
UI                              IN SCOPE
Characters                      IN SCOPE
Office/world architecture       IN SCOPE
Motion/spatial interaction      IN SCOPE
Governance/product truth        IN SCOPE
Accessibility/performance       IN SCOPE

M.9.1 implementation            COMPLETE
M.9.1 implementation CI         PASS
M.9.1 PR                        MERGED
M.9.1 ROADMAP closure           PENDING
M.9.1 closure CI                PENDING
M.9.1 SEALED                    NO

AIOS V2 implementation          NOT STARTED
Reason                          awaiting clean M.9.1 closure
```

# 48. Final program principle

We are not trying to make AIOS “prettier.”

We are making the frontend **worthy of the architecture underneath it**.

AIOS already has the difficult substrate: truth, governance, employees, work, evidence, decisions, authority, conversations, replay, temporal reconstruction, comparison, and environmental memory.

V2 makes that substrate comprehensible and emotionally legible through excellent UX, distinctive UI, memorable characters, meaningful architecture, disciplined motion, spatial cognition, accessible structured equivalents, and truth-preserving presentation.

> **Open AIOS and immediately feel that a real digital organization is operating — then be able to inspect, understand, govern, and prove every important claim beneath that feeling.**

---

**End — AIOS V2 Complete Product & Frontend Redesign Master Plan v1.0**