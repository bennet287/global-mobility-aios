# AIOS V2 — Phase 1A Existing Frontend Audit Baseline

**Status:** PASS A COMPLETE — repository/information-architecture/design-debt baseline  
**Audit date:** 2026-09-03  
**Read-only product baseline:** `58fcec31d51d9ec1fba8e86e893721ca5735196d`  
**Baseline branch:** `roadmap/global-mobility-aios-v12`  
**Documentation branch:** `docs/aios-v2-master-plan`  
**Parent master plan:** `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md`

> This audit is intentionally isolated from the M.9.1 closure branch. It performs no production-code mutation while closure CI is running.

---

## 1. Executive finding

The current frontend is not a failed frontend. It is a technically capable, governance-aware product surface that has accumulated faster than its design language.

The redesign problem is therefore not “replace bad code with pretty code.”

The actual problem is:

> **AIOS has outgrown the information architecture, visual grammar, styling architecture, and spatial presentation that were sufficient while the product was smaller.**

The strongest parts should be preserved:

- canonical data boundaries,
- explicit uncertainty/proof gaps,
- authority separation,
- non-authoritative renderer policy,
- accessibility foundations,
- exact-state tests,
- structured fallback,
- Next.js/React/Three.js stack,
- Owner/Operator/Mobility experience split.

The weakest parts should be deliberately replaced or reorganized:

- navigation exposure,
- global CSS architecture,
- generic card/panel vocabulary,
- page-level visual inconsistency,
- monolithic page/data-client files,
- generic employee representation,
- stacked/pixel-like Living Organization composition,
- technical metadata appearing too early,
- insufficient motion identity,
- lack of a formal design constitution.

---

## 2. Measured repository inventory

### 2.1 Frontend file inventory

At the audited baseline, `apps/web` contains:

```text
Git tree entries                    182
Files / blobs                       125
App Router page.tsx files            44
Component files                      27
CSS files                              4
lib files                             17
design/E2E test files                 12
```

This is already a substantial product application rather than a small dashboard.

### 2.2 Framework/runtime

```text
Next.js          16.3.1
React            19.0.8
React DOM        19.0.8
TypeScript       5.8.3
Three.js         0.185.1
Typography       Geist + Geist Mono
UI framework     no heavyweight visual component framework
```

**V2 implication:** keep the framework stack. There is no justification for a framework rewrite.

The absence of a heavyweight third-party UI kit is an advantage: AIOS can establish its own visual language without fighting a pre-existing component aesthetic.

---

## 3. Route surface inventory

There are **44 App Router page surfaces**.

### Owner / governance / organization surfaces

- `/cockpit`
- `/cockpit/live-organization`
- `/cockpit/decisions`
- `/owner-inbox`
- `/board-room`
- `/validation`
- `/global-intelligence`
- `/intelligence`
- `/source-certification-review`
- `/document-intelligence`
- `/cross-department-friction`
- `/agents/review`
- `/agents/review/[id]`
- `/agents/console`
- `/automation`
- `/workspace/[department]`

### Professional / operator surfaces

- `/`
- `/profiles`
- `/eligibility`
- `/planning`
- `/pathways`
- `/timelines`
- `/communications`
- `/communications/auto`
- `/communications/drafts/[id]`
- `/communications/leads/[id]`
- `/coaching`
- `/corporate-mobility`
- `/business-advisory`
- `/investment-mobility`
- `/investment-suitability`
- `/family-office`
- `/tax-residency`
- `/authority-appointments`
- `/agency-submissions`
- `/external-agency-assignments`
- `/authority-submission-checklist`
- `/leads/[id]`
- `/opportunities`
- `/intake`

### Mobility / external surfaces

- `/my-mobility`
- `/portal`
- `/partner-portal`
- `/return`

The route count itself is not the defect. The defect is exposing too much of this route topology as peer-level navigation.

---

## 4. Navigation audit

The current `workspace-navigation.ts` already has a sound high-level product concept:

```text
Owner / Board
Professional / Operator
Mobility User
```

That split should survive V2.

### 4.1 Current primary navigation density

Current navigation definitions expose approximately:

```text
Owner experience       15 item entries
Operator experience    26 item entries
Mobility experience     2 item entries
```

Operator navigation currently includes large direct lists for:

- Operations
- Evidence & Review
- Execution
- Business & Authority

Owner navigation includes direct entries for:

- Cockpit
- Live Organization
- Owner Inbox
- Board Room
- External Validation
- Global Intelligence
- Regulatory Intelligence
- Independent Source Review
- Document Intelligence
- Cross-department friction
- Agent Review Queue
- Agent Console
- Automation Hub
- Operations Workspace

### 4.2 Root cause

The navigation is increasingly a catalog of system capabilities.

That is a backend/module mental model.

V2 should expose a user/task mental model.

### 4.3 Selected V2 navigation

Owner:

```text
Home
Organization
Missions
Intelligence
Evidence
Decisions
History
```

Operator:

```text
Work
Profiles
Pathways
Evidence
Communication
Tools
```

Mobility:

```text
Overview
My Case
Documents
Timeline
Messages
```

Existing routes can remain during migration. They should become contextual destinations, local navigation, or command-palette results rather than all remaining persistent top-level peers.

---

## 5. Shell and accessibility audit

### Current strengths in `WorkspaceShell`

The existing shell already implements:

- a skip-to-main-content link,
- explicit `main` landmark,
- mobile menu button semantics,
- `aria-expanded`,
- `aria-controls`,
- focus capture while mobile navigation is open,
- Escape-to-close,
- focus restoration to the menu trigger,
- body-scroll suppression while mobile navigation is open.

These are valuable foundations and should be preserved.

### Current strengths in `Sidebar`

- active-route semantics with `aria-current`,
- accessible labels,
- keyboard-visible tooltip behavior,
- experience switching,
- explicit backend health state,
- theme switching.

### V2 issue

The shell is semantically stronger than it is visually/product-architecturally.

The V2 shell should therefore **refactor, not discard**, its accessibility behaviors.

---

## 6. Root layout audit

Current root layout:

- loads Geist and Geist Mono,
- applies global CSS,
- initializes theme before hydration,
- mounts a global `AgentChatWidget`.

### V2 decisions

**Keep:**
- Geist as a baseline candidate,
- pre-hydration theme initialization,
- system/light/dark concept.

**Reconsider:**
- global chat as a visually generic always-present widget.

AIOS V2 communication should become contextual:

- employee conversation,
- Mission conversation,
- Board communication,
- evidence discussion.

The underlying communication infrastructure can remain while the framing changes.

---

## 7. CSS architecture audit

### 7.1 Current CSS size

```text
app/globals.css                       429,703 bytes / 14,256 lines
app/cockpit/living-scene.css           41,651 bytes / 1,502 lines
app/cockpit/cockpit-refinements.css    17,480 bytes /   621 lines
app/cockpit/cockpit-visual-polish.css   1,843 bytes /    81 lines
```

### 7.2 Global CSS complexity measurements

`globals.css` currently contains approximately:

```text
custom-property declarations       280
selectors                         3,071
unique hex colors                   349
hardcoded hex occurrences           466
rgba/rgb function occurrences       563
border-radius declarations           480
box-shadow declarations              191
gradient uses                        154
backdrop-filter uses                  23
transition declarations               57
animation declarations                22
@keyframes                            11
!important occurrences                42
pixel-value occurrences            5,161
rem-value occurrences                120
selectors containing "card"          263
selectors containing "panel"         124
selectors containing "badge"          35
selectors containing "button"         64
```

### 7.3 Breakpoint fragmentation

The global stylesheet includes many overlapping breakpoint definitions, including variants around:

- 480
- 520
- 600
- 620
- 640
- 680
- 720
- 760
- 780
- 850
- 880
- 900
- 980
- 1000
- 1040
- 1050
- 1100
- 1120
- 1160
- 1180
- 1200
- 1280
- 1320

This indicates responsive behavior has been solved surface-by-surface rather than through a single governing responsive system.

### 7.4 Token strengths

The stylesheet already contains useful early design-system concepts:

- spacing tokens,
- radius tokens,
- text-size tokens,
- transition tokens,
- shadow tokens,
- light/dark semantic colors.

This is a useful seed, but not yet a V2 design-token architecture.

### 7.5 Token inconsistency

The root layout loads **Geist**, while a CSS custom property still declares:

`Inter, ui-sans-serif, system-ui...`

This is a concrete example of design foundations being layered over time rather than governed centrally.

### V2 conclusion

Do **not** cosmetically extend `globals.css`.

Create a V2 token/style architecture and migrate incrementally.

---

## 8. Page complexity audit

Largest current page files include:

```text
/global-intelligence             ~67.2 KB
/cockpit                         ~61.6 KB
/leads/[id]                      ~51.1 KB
/intelligence                    ~45.0 KB
/document-intelligence           ~42.6 KB
/corporate-mobility              ~41.5 KB
/pathways                        ~32.6 KB
/planning                        ~31.0 KB
/cockpit/live-organization       ~30.7 KB
/tax-residency                   ~28.3 KB
/workspace/[department]          ~27.3 KB
/owner-inbox                     ~27.2 KB
/authority-submission-checklist  ~25.7 KB
/cross-department-friction       ~24.0 KB
/source-certification-review     ~23.6 KB
/profiles                        ~23.4 KB
```

Large files are not automatically bad, but this distribution signals that many routes currently own too much:

- data loading,
- state management,
- presentation composition,
- domain translation,
- interaction logic.

V2 should introduce reusable domain-object and workspace composition layers rather than reproduce large bespoke page files.

---

## 9. API client architecture audit

`apps/web/lib/api.ts` is currently approximately:

```text
189,175 bytes
5,675 lines
217 exported type/interface definitions
247 exported functions
```

It contains a very broad cross-product API surface:

- leads,
- profiles,
- agents,
- communication,
- eligibility,
- portals,
- automation,
- applications,
- authorities,
- pathways,
- planning,
- documents,
- intelligence,
- regulatory governance,
- evidence,
- and more.

### Finding

This is a **frontend domain monolith**.

It works, but V2 should not build new design architecture on top of an ever-larger single client module.

### V2 direction

Gradually introduce domain clients, e.g.:

```text
lib/api/
  core/
  organization/
  missions/
  employees/
  evidence/
  decisions/
  intelligence/
  operator/
  mobility/
```

Migration should preserve request-auth behavior and not break proven API contracts.

---

## 10. Existing component architecture

Largest components:

```text
LivingOrganizationScene.tsx                ~32.4 KB
ClientPortalPage.tsx                       ~28.3 KB
LivingOrganizationReplayTimeline.tsx       ~18.5 KB
Sidebar.tsx                                ~13.1 KB
LivingOrganizationWebGPUScene.tsx           ~8.5 KB
EcosystemPortalPage.tsx                     ~8.4 KB
AgentChatWidget.tsx                         ~6.6 KB
LivingOrganizationEnvironmentalMemory.tsx   ~6.2 KB
WorkspaceShell.tsx                          ~4.0 KB
```

Smaller generic primitives currently include:

- `ActionCard`
- `MetricPill`
- `StatusBadge`
- `SectionTitle`
- `InlineNotice`
- `TechnicalDisclosure`
- `Skeleton`
- `TruthClaimCard`
- `EvidenceProvenance`

### Finding

The existing primitive set is useful but still strongly “dashboard/card/status” oriented.

### V2 direction

Add domain-native objects:

- Mission Surface
- Work Object
- Employee Identity
- Evidence Object
- Source Object
- Decision Object
- Authority Gate
- Handoff Signal
- Friction Signal
- Temporal Lens
- Environmental Pattern Surface
- Provenance Drawer
- Owner Attention Object.

---

## 11. Cockpit audit

Current Cockpit is highly data-grounded and governance-aware.

It explicitly states, among other things:

- server authorization remains authoritative,
- backend authorization remains authoritative,
- the Cockpit does not directly mutate blockers/dependencies or publish regulated outcomes,
- durable Activity coverage limitations remain explicit.

### Strength

This is exactly the truth discipline V2 must preserve.

### Weakness

The current file is ~61.6 KB and combines many operational intelligence regions:

- owner attention,
- jurisdiction intelligence,
- Activity stream,
- blockers,
- dependencies,
- overdue work,
- human requests,
- department drill-down.

This creates an executive surface that is rich but cognitively dense.

### V2 direction

Cockpit becomes **Owner Home / executive situation room**, with:

1. organization situation,
2. needs attention,
3. active Missions,
4. live organization preview,
5. recent meaningful change.

Proof/provenance remain available but do not dominate the first viewport.

---

## 12. Living Organization audit

### 12.1 Existing strengths

The current Living Organization already has unusually strong governance boundaries.

It distinguishes:

- deterministic/canonical projection,
- predictive plane,
- environmental-memory plane,
- renderer authority,
- scene authority,
- mutation permission,
- canonical conversations,
- canonical handoffs.

It also preserves:

- structured fallback,
- read-only behavior,
- non-authoritative renderer,
- explicit mismatch handling,
- replay,
- environmental memory,
- optional GPU field trial.

These are significant assets.

### 12.2 Current employee representation

The structured scene currently renders employees with:

- initials inside a `scene-avatar`,
- title,
- position key,
- semantic state,
- authority level,
- WorkItem/status text,
- blocker/conversation indicators.

This is truthful but visually generic.

### 12.3 Current spatial representation

The scene still contains strongly diagrammatic concepts:

- scene planes,
- department zone cards,
- employee grid,
- “Mission Room” block,
- Evidence Lab block,
- smart-object strips.

This is closer to an engineering visualization than a premium architectural organization.

### 12.4 Current WebGPU/Three renderer posture

The optional renderer is intentionally:

```text
scene_authoritative = false
selection authority = none
canonical mutation = none
```

This is excellent and should be permanent.

### 12.5 Current motion contract

Existing employee-presentation code explicitly enforces:

```text
presentationOnly  = true
locomotionAllowed = false
presenceClaimed   = false
```

Current canonical mappings allow restrained stationary presentation states for working, blocked, awaiting owner, queued, completed, etc.

### V2 implication

V2 motion must extend this safely rather than erase it.

Create separate layers:

```text
AMBIENT LIFE
presentation-only; no work/presence claim

SEMANTIC MOTION
requires supported canonical relationship/event/state
```

Permanent rule:

> The organization causes the animation. Animation never causes the organization.

---

## 13. Character-system opportunity

The repository already contains **42 role-card documents**, including:

- AI CEO / CEO
- CTO
- CISO
- COO
- CFO
- CMO
- CHRO
- CLO
- CPO
- VP Engineering
- Lead Architect
- Security Lead
- SOC Lead / Analyst
- Threat Analyst
- Regulatory/public-policy roles
- Product roles
- Finance roles
- Recruitment/HR
- Communications
- Operations agents
- Eligibility/visa/document roles
- advisors and specialists.

This is extremely useful.

### V2 decision

Do not invent character personality solely from aesthetics.

The **Character Bible should map from real role-card/domain identity** into:

- silhouette,
- professional styling,
- personality,
- posture,
- signature props,
- motion grammar,
- authority/seniority cues.

The character system should therefore be a visual interpretation of existing organizational identity, not an independent fictional roster.

---

## 14. Office/world architecture finding

The current spatial UI proves canonical placement and relationship concepts, but does not yet provide a coherent architectural world.

V2 must replace the stacked/pixel/room-card mental model with:

> **a miniature architectural headquarters/campus/diorama**

Required stable topology:

- Executive Terrace / Board
- Central Atrium
- Mission Hub
- Regulatory / Evidence wing
- Technology / Security wing
- Operations Studio
- Case/client work areas
- coffee/lounge/courtyard/terrace.

This structure must support both:

- organizational cognition,
- visual identity.

It must not become a game level.

---

## 15. Motion audit

Current CSS contains only a modest animation system relative to the size of the application:

```text
animation declarations    ~22
@keyframes                 11
```

Living-scene CSS itself currently has no CSS animation declarations.

### Finding

Motion is not yet a strong product-language layer.

### V2 requirement

Create formal motion tokens and categories:

- micro feedback,
- panel transitions,
- navigation continuity,
- spatial focus,
- ambient character animation,
- semantic transfer/handoff,
- mission collaboration,
- Board escalation,
- replay transition,
- reduced-motion equivalents.

Motion must be deterministic where semantic.

---

## 16. Responsive audit

There is substantial responsive work, but breakpoint fragmentation shows it has accumulated locally.

### Preserve

The application already considers mobile navigation and multiple viewport sizes.

### Replace

V2 should define explicit responsive modes:

- ultrawide,
- desktop,
- laptop,
- tablet landscape,
- tablet portrait,
- mobile,
- reduced-motion,
- low-power,
- renderer fallback.

Breakpoints should be tokenized and tied to layout families rather than route-specific guesswork.

---

## 17. Existing test/governance strength

Current frontend testing is a major strength.

`design-foundation.test.mjs` currently has **28 named tests**, covering:

- typography/tokens,
- keyboard/landmark foundations,
- provenance disclosure,
- action hierarchy,
- Board acronyms,
- stable structural columns,
- label associations,
- mobile summary behavior,
- shell behavior,
- role-based shells,
- compact rail,
- grounded product-facing presentation,
- Cockpit hierarchy,
- owner intelligence,
- department drill-down,
- friction,
- Owner Inbox,
- Mobility user safety,
- Operator composition,
- evidence/provenance taxonomy,
- accessibility,
- mobile composition.

Living Organization tests additionally prove:

- replay coverage gaps,
- no mutation,
- evidence/supersession queries,
- GPU trial default-off,
- truthful empty/loading state,
- bounded Owner commands,
- blocker gating,
- exact replay,
- projection failure,
- structured fallback,
- renderer update behavior,
- WebGPU-disabled fallback,
- employee presentation without fabricated presence/locomotion.

### V2 implication

Design quality is already testable in this repository.

The V2 Design Skill should extend this precedent into:

- token enforcement,
- anti-pattern rules,
- navigation limits,
- semantic-animation contracts,
- truth-class presentation,
- reduced-motion behavior,
- accessible structured equivalents,
- visual regression.

---

## 18. Design-system debt classification

### P0 — foundational

1. Information architecture
2. V2 Design Constitution
3. token architecture
4. CSS migration boundary
5. Character Bible
6. Office Bible
7. semantic animation contract
8. accessibility/fallback rules

### P1 — flagship product

1. Owner Home
2. Living Organization
3. Missions
4. Employees
5. Evidence
6. Decisions / Board
7. Replay / Compare
8. Environmental Memory.

### P2 — migration

1. Operator workspaces
2. specialist tools
3. authority workflows
4. Mobility user
5. legacy route consolidation.

---

## 19. Preliminary route migration classification

### Rebuild as flagship

- `/cockpit`
- `/cockpit/live-organization`
- `/cockpit/decisions`
- `/board-room`

### Redesign into primary V2 domains

- `/global-intelligence`
- `/intelligence`
- `/document-intelligence`
- `/pathways`
- `/planning`
- `/profiles`
- `/communications`
- `/`
- `/my-mobility`

### Contextualize / consolidate

- `/owner-inbox`
- `/validation`
- `/source-certification-review`
- `/cross-department-friction`
- `/agents/review`
- `/agents/console`
- `/automation`
- `/coaching`
- authority-operation routes.

### Audit specialist-domain placement before deciding

- corporate mobility
- business advisory
- investment mobility
- investor suitability
- family office
- tax residency
- opportunities
- intake
- partner portal
- return flow.

No deletion occurs from this preliminary classification.

---

## 20. V2 technical migration rules from this audit

1. **Do not rewrite frameworks.**
2. **Do not remove governance language from the product; move it to correct information depth.**
3. **Do not discard current accessibility behavior.**
4. **Do not discard structured Living Organization fallback.**
5. **Do not allow Three.js renderer to become authoritative.**
6. **Do not extend the 430 KB global CSS as the primary V2 strategy.**
7. **Do not continue a 189 KB single API client indefinitely.**
8. **Do not mass-migrate routes before V2 primitives and prototype are accepted.**
9. **Do not design characters independently from real role identities.**
10. **Do not design office architecture independently from organizational topology.**
11. **Do not implement semantic locomotion before a canonical mapping contract exists.**
12. **Do not force 3D for detailed work.**

---

## 21. First audit verdict by system

| System | Current engineering strength | Current design maturity | V2 action |
|---|---:|---:|---|
| Canonical truth boundaries | Very high | High | Preserve |
| Authority UX correctness | High | Medium-high | Preserve + simplify hierarchy |
| Accessibility shell | High | Medium | Preserve + systematize |
| Navigation concept | Medium-high | Medium | Keep experience split; rebuild IA |
| Navigation density | Low-medium | Low | Major redesign |
| Visual identity | Medium | Low-medium | Replace with V2 language |
| Design tokens | Medium | Low-medium | Rebuild/normalize |
| CSS architecture | Low | Low | Controlled migration |
| Component vocabulary | Medium | Medium-low | Introduce domain-native objects |
| Data client architecture | Functional | Low scalability | Domain split |
| Cockpit | High information value | Medium | Recompose |
| Living Organization truth | Very high | High | Preserve |
| Living Organization art | Prototype | Low | Rebuild |
| Character identity | Minimal/generic | Low | New system |
| Office architecture | Prototype | Low | New system |
| Motion | Bounded/correct | Low expressive maturity | Expand safely |
| Replay | High | Medium visual maturity | Flagship V2 |
| Environmental Memory | High truth discipline | Early visual maturity | Spatial + structured V2 |
| Frontend tests | Very high | High | Extend |

---

## 22. Phase 1A conclusion

The redesign thesis is confirmed by the repository itself:

> **AIOS has a strong brain and a governed truth model, but its frontend presentation has accumulated as a collection of increasingly capable surfaces rather than a single mature product-design system.**

The correct response is not incremental beautification.

The correct response is:

```text
audit
  ↓
Design Constitution
  ↓
UX / IA
  ↓
UI foundations
  ↓
Character Bible
  ↓
Office Bible
  ↓
Motion + semantic mapping
  ↓
representative vertical slice
  ↓
measured validation
  ↓
controlled whole-product migration
```

---

# 23. Next audit passes

## Pass B — route-by-route behavioral audit

For every route:

- user type,
- user goal,
- canonical data source,
- mutations/actions,
- authority class,
- primary task,
- current hierarchy,
- duplicated capability,
- V2 conceptual home,
- migration action,
- compatibility requirement.

## Pass C — component + state audit

For every major component:

- semantic purpose,
- duplicated patterns,
- variants,
- loading/empty/error/partial states,
- accessibility,
- responsive behavior,
- V2 primitive/domain-object mapping.

## Pass D — visual-system audit

Catalog:

- color families,
- type roles,
- radius families,
- shadows,
- cards/panels,
- borders,
- iconography,
- density,
- gradients,
- material patterns,
- light/dark inconsistencies.

## Pass E — Living Organization technical audit

Trace:

```text
API scene/replay/memory contracts
   ↓
frontend read models
   ↓
render model
   ↓
structured scene
   ↓
WebGPU/Three adapter
   ↓
presentation state
   ↓
renderer policy
   ↓
tests
```

Then define exactly what can be reused for V2 characters/world.

## Pass F — V2 Design Skill construction

Use audit evidence to create:

- Constitution
- UX
- UI
- Characters
- Architecture
- Spatial
- Motion
- Governance
- Product
- Quality

---

# 24. Audit status

```text
Pass A — repository/design-debt baseline       COMPLETE
Pass B — route behavior                        NEXT
Pass C — component/state                       PENDING
Pass D — visual system                         PENDING
Pass E — Living Organization technical         PENDING
Pass F — AIOS Design Skill                     PENDING

Production V2 code                              NOT STARTED
M.9.1 closure branch                            UNTOUCHED BY AUDIT
```

