# AIOS V2 — Phase 1D Visual-System Audit

**Status:** COMPLETE — measured visual-system baseline  
**Audit baseline:** `58fcec31d51d9ec1fba8e86e893721ca5735196d`  
**Documentation branch:** `docs/aios-v2-master-plan`  
**Production mutation:** none

---

# 1. Executive visual finding

The current frontend does not lack styling effort.

It has the opposite problem:

> **a large amount of styling exists, but it has accumulated as local visual solutions instead of one governed product-design language.**

This matters because “make it prettier” would add another layer on top of the same problem.

AIOS V2 needs a visual-system reset with controlled migration.

---

# 2. CSS scale

Measured current CSS:

```text
app/globals.css                       429,703 bytes
                                      14,256 lines

app/cockpit/living-scene.css           41,651 bytes
                                       1,502 lines

app/cockpit/cockpit-refinements.css    17,480 bytes
                                         621 lines

app/cockpit/cockpit-visual-polish.css   1,843 bytes
                                          81 lines
```

Total authored CSS represented by these four files is already roughly **490 KB**.

This is not a reason for a destructive rewrite. It is evidence that V2 must introduce a clean migration boundary.

---

# 3. Global CSS measurements

`globals.css` contains approximately:

| Measurement | Count |
|---|---:|
| custom-property declarations | 280 |
| selectors | 3,071 |
| unique hex values | 349 |
| hardcoded hex occurrences | 466 |
| RGB/RGBA function occurrences | 563 |
| border-radius declarations | 480 |
| box-shadow declarations | 191 |
| gradient uses | 154 |
| backdrop-filter declarations | 23 |
| transition declarations | 57 |
| animation declarations | 22 |
| @keyframes | 11 |
| !important | 42 |
| pixel-valued tokens/declarations | 5,161 |
| rem-valued declarations | 120 |
| selector references containing “card” | 263 |
| selector references containing “panel” | 124 |
| selector references containing “badge” | 35 |
| selector references containing “button” | 64 |

The counts are not quality scores by themselves. Together they show visual vocabulary proliferation.

---

# 4. Primary visual debt: surface proliferation

The current CSS heavily uses:

- cards,
- panels,
- pills,
- badges,
- rounded containers,
- shadows,
- gradients.

This results in a familiar enterprise/SaaS visual grammar:

```text
container
  ↓
rounded card
  ↓
heading
  ↓
metric/badge
  ↓
another rounded card
```

That grammar is useful for prototypes and dense apps, but it is not distinctive enough for AIOS V2.

## V2 design correction

Keep generic surfaces as implementation primitives, but make user-facing composition domain-native:

- Mission Surface
- Evidence Object
- Decision Object
- Authority Gate
- Employee Identity
- Department Zone
- Temporal Lens
- Handoff Signal.

---

# 5. Color-system audit

The stylesheet already contains useful semantic families:

- green
- amber
- red
- blue
- light/dark foundations.

However, **349 unique hex values** and **466 hardcoded hex occurrences** show that many later surfaces bypass the token layer.

## Existing strength

Early foundation variables include:

- `--bg`
- `--surface`
- `--surface-strong`
- `--surface-muted`
- `--ink`
- `--ink-muted`
- `--line`
- semantic green/amber/red/blue.

## Problem

Later CSS introduces many one-off colors for:

- Cockpit
- Board
- Live Organization
- dark mode
- specific panels
- decorative states.

This prevents reliable semantic meaning.

## V2 requirement

Every color must belong to one of these layers:

### Foundation
- canvas
- base
- raised
- inset
- overlay
- border
- primary/secondary/tertiary text.

### Semantic lifecycle
- active
- blocked
- awaiting owner
- warning
- critical
- completed
- stale
- unavailable.

### Truth class
- canonical
- human authority
- AI recommendation
- memory/aggregate
- prediction
- simulation
- historical reconstruction
- unsupported/unknown.

### Department identity
- Executive
- Technology
- Security
- Regulatory
- Operations
- Intelligence.

Department accents must never replace semantic status.

---

# 6. Fashionability audit

Current styles already contain examples of:

- large editorial headings,
- gradients,
- translucent cards,
- blur,
- deep dark surfaces,
- accent colors.

These are not inherently wrong.

The problem is inconsistency and trend mixing.

## V2 selected visual thesis

> **Contemporary architectural luxury + premium operating-system restraint**

Fashionability comes from:

- composition,
- typography,
- material discipline,
- light,
- motion,
- character art,
- architecture,
- spatial continuity.

Not from:

- more neon,
- more glass,
- more gradients,
- more glow.

---

# 7. Typography audit

Root layout loads:

- Geist
- Geist Mono

But the global CSS also declares a legacy/base custom property using:

`Inter, ui-sans-serif, system-ui...`

This is direct evidence that typography evolved in layers.

## V2 decision

Geist remains a strong baseline candidate because it supports:

- dense enterprise work,
- high legibility,
- neutral modernity.

AIOS identity should primarily come from:

- scale,
- weight,
- tracking,
- line length,
- editorial composition,
- spacing,
- numeric typography,
- mono usage for technical provenance,

rather than adopting a novelty display font.

## Required V2 type roles

- display
- executive/page title
- section title
- domain-object title
- body
- compact body
- label
- caption
- metadata
- numeric metric
- status
- technical/provenance.

---

# 8. Radius audit

Approximately **480 border-radius declarations** exist in global CSS.

This does not mean radius should disappear.

It means radius currently acts as a generic “modern UI” treatment rather than a tightly controlled material property.

## V2 rule

Radius is based on object/material role:

- control
- compact object
- work surface
- inspector
- modal/authority
- spatial HUD.

No arbitrary page-level radius invention.

---

# 9. Shadow/depth audit

Approximately **191 box-shadow declarations** exist in global CSS.

V2 should reduce arbitrary shadow variety.

Depth must indicate:

- surface hierarchy,
- interaction elevation,
- overlay status,
- authority/modal state,
- spatial HUD separation.

Depth is semantic, not decoration.

---

# 10. Gradient audit

Approximately **154 gradient uses** exist.

Gradients can remain valuable for:

- atmospheric hero backgrounds,
- spatial lighting,
- subtle material depth,
- data fields.

But gradients must not become the identity shorthand for “AI.”

## Reject

- generic purple AI gradient
- every hero using a different decorative gradient
- gradient buttons without semantic reason.

---

# 11. Glass/translucency audit

Approximately **23 backdrop-filter declarations** exist.

This is moderate, not catastrophic.

V2 should preserve translucency selectively for:

- floating inspectors,
- command palette,
- spatial HUD,
- temporary overlays.

Dense reading surfaces should be more opaque.

Glass is a material, not a default component style.

---

# 12. Responsive/breakpoint audit

Current global CSS contains many independently chosen breakpoint values, including ranges around:

```text
480
520
600
620
640
680
720
760
780
850
880
900
980
1000
1040
1050
1100
1120
1160
1180
1200
1280
1320
```

There are also min-width and compound ranges.

## Finding

Responsive behavior is real and substantial, but breakpoint choice has accumulated by page/feature.

## V2 requirement

Define a small responsive mode system:

```text
mobile
tablet
laptop
desktop
wide
```

with explicit layout-family behavior.

Exact pixel boundaries remain **PROPOSED** until prototype validation.

---

# 13. Spacing audit

Existing root tokens already include:

```text
4
8
12
16
20
24
32
40
48
```

This is a useful foundation.

V2 should normalize to an intentional spacing scale and eliminate arbitrary one-off padding/gap values over time.

A possible V2 scale:

```text
4
8
12
16
24
32
48
64
96
```

remains **PROPOSED**.

Migration should be evidence-based rather than mechanically replacing every old value.

---

# 14. Motion audit

Across the large global stylesheet, there are only roughly:

- 22 animation declarations
- 11 keyframe definitions
- 57 transition declarations.

The dedicated Living Organization CSS currently has no CSS animation declarations.

## Finding

The current product has interaction transitions, but motion is not yet a coherent brand/product language.

## V2 requirement

Formal motion classes:

1. micro feedback
2. control state
3. panel/inspector
4. navigation continuity
5. spatial camera/focus
6. ambient character
7. semantic character
8. handoff/transfer
9. Board/authority attention
10. replay/temporal transition
11. reduced-motion equivalent.

Motion tokens must be centralized.

---

# 15. Iconography audit

The existing Sidebar implements a substantial set of inline SVG icons directly in React.

Strength:

- consistent stroke treatment inside that component,
- no visual dependency on a generic UI framework.

Weakness:

- icon grammar is component-local rather than governed as an AIOS icon system.

## V2 requirement

Create one icon vocabulary for:

- Home
- Organization
- Mission
- Employee
- Department
- Work
- Evidence
- Source
- Decision
- Authority
- Blocker
- Risk
- Conversation
- Handoff
- Replay
- Compare
- Memory
- Prediction
- Automation
- Human Review
- External Source/Authority
- Technical/Provider.

Whether these are custom SVGs or a curated icon source remains open until V2 foundation work.

---

# 16. Light/dark audit

Theme initialization and light/dark tokens exist.

That is a strong baseline.

V2 should preserve both but enforce:

- equivalent hierarchy,
- equivalent contrast,
- equivalent truth semantics,
- no dark-mode-only neon identity,
- spatial scene lighting separated from UI theme semantics.

The 3D world may have environmental light, while UI overlays still follow product theme.

---

# 17. Cockpit-specific visual layering

Cockpit has:

- base global styles
- `cockpit-refinements.css`
- `cockpit-visual-polish.css`
- separate Living Organization CSS.

This is useful historical evidence that the Cockpit has been iteratively improved without one consolidated design system.

## V2 correction

Do not add:
`cockpit-v2-final-polish.css`.

Instead:

```text
tokens
  ↓
primitives
  ↓
domain objects
  ↓
layout family
  ↓
Cockpit composition
```

---

# 18. Living Organization visual audit

`living-scene.css` is ~41.6 KB but has:

- no CSS animations,
- limited material depth relative to the ambition,
- structured grid/room/panel presentation.

This matches the user-visible problem:

> it communicates state, but it does not yet feel like a fashionable living architectural organization.

V2 should move the visual center of gravity from CSS room boxes to:

- actual architectural geometry,
- lighting,
- characters,
- camera,
- spatial objects,
- meaningful overlays.

Structured HTML remains as the accessible fallback/inspector layer.

---

# 19. Selected V2 visual material palette

Directional only; exact values remain open.

## Foundation

- deep graphite / ink
- warm off-white
- soft stone
- smoked transparent overlay
- fine metallic/champagne detail
- restrained cool technical accent.

## Spatial architecture

- refined light stone
- warm wood
- smoked/clear glass
- brushed metal
- dark technical composite
- controlled greenery
- soft textiles in communal zones.

## Department accents

Use sparingly and semantically secondary.

---

# 20. V2 token families to create

```text
color.foundation.*
color.semantic.*
color.truth.*
color.department.*

type.family.*
type.size.*
type.weight.*
type.tracking.*
type.lineHeight.*

space.*
radius.*
border.*
shadow.*
elevation.*
opacity.*
blur.*

motion.duration.*
motion.easing.*

layout.width.*
layout.rail.*
layout.inspector.*
layout.breakpoint.*

spatial.hud.*
spatial.selection.*
spatial.depth.*
```

---

# 21. Static design-lint opportunities

Because this repository already has design-foundation tests, V2 can automatically reject some forms of design drift.

Candidate checks:

- no new arbitrary root hex values outside token files
- no new uncontrolled breakpoint values
- no new direct global “card” style families without review
- V2 components use semantic tokens
- reduced-motion behavior exists for V2 motion
- truth-class attributes exist where required
- Owner authority surfaces use designated authority primitives
- spatial semantic motion declares canonical basis
- renderer remains non-authoritative.

Do not make lint so rigid that legitimate data visualization or 3D materials become impossible.

---

# 22. Visual anti-patterns confirmed by audit

The following are not merely theoretical; the existing styling scale makes them important V2 guardrails:

- card accumulation
- panel accumulation
- arbitrary radius
- arbitrary color
- local breakpoint invention
- page-specific visual grammar
- decorative gradient proliferation
- generic badge semantics
- CSS polish layers added after architecture.

V2 must prevent recurrence through system design.

---

# 23. Migration plan

## Stage 1
Freeze old visual expansion except required bug fixes.

## Stage 2
Introduce V2 token files.

## Stage 3
Introduce V2 primitives and domain objects.

## Stage 4
Build V2 shell/Owner Home prototype isolated from old selectors.

## Stage 5
Migrate flagship surfaces.

## Stage 6
Migrate operator/external surfaces.

## Stage 7
Delete legacy CSS only when references are proven gone.

No big-bang stylesheet deletion.

---

# 24. Phase 1D verdict

```text
CSS scale quantified
color proliferation quantified
surface/card/panel proliferation quantified
radius/shadow/gradient usage quantified
breakpoint fragmentation identified
type-layer inconsistency identified
motion maturity identified
icon-system opportunity identified
V2 token families derived
migration strategy confirmed

Pass D — COMPLETE
```

Next:

**Phase 1E — Living Organization Technical Reuse Audit**

This pass will determine exactly which current scene/replay/renderer/memory structures survive into:

- Character V2
- HQ V2
- smart objects
- semantic locomotion
- conversations
- handoffs
- Replay V2
- Environmental Memory V2.
