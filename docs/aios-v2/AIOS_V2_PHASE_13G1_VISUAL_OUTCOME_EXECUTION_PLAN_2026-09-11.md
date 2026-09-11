# AIOS V2 Phase 13G.1 — Exact Visual Outcome Execution Plan

**Status:** ACTIVE / OWNER-DIRECTED VISUAL CORRECTION
**Parent programme:** Phase 13 — Living HQ flagship convergence
**Sealed semantic base:** Phase 13F merge `310b73a2eec63f9f0b2f3a0d53752867c1097359`
**Rejected closure candidate:** PR #146 remains Draft and must not be merged in its rejected visual state.

## 1. Exact outcome

The target is not another styling pass. The final Living HQ desktop hero must visually read as a premium contemporary digital-company headquarters comparable in spatial experience to the Owner-approved reference concept: one continuous office world, architectural depth, believable furniture/materials, miniature employees integrated into the workplace, and restrained AIOS state overlays anchored to the environment.

The office is the primary product surface. UI augments the office; UI does not become the office.

### Five-second test

Without reading labels, a first-time viewer must immediately perceive:

1. a modern premium office headquarters;
2. one connected workplace with depth and circulation;
3. open-plan working areas plus glass-partitioned specialist/executive spaces;
4. miniature employees belonging inside that environment;
5. a live digital organization rather than a dashboard/card grid.

If the first impression is cards, square rooms, tiles, panels, a game board, a pixel tower, repeated creatures, or a conventional admin dashboard, the candidate fails visual acceptance even if all automated tests pass.

## 2. Composition target

### Desktop hero frame

Use a wide elevated architectural camera. The viewport should expose foreground, middle ground and background simultaneously.

- **Left / foreground:** AIOS identity integrated into an architectural wall or environmental feature; compact organization summary may live on a real display surface rather than a floating dashboard column.
- **Centre / foreground-to-midground:** Operations / Mission open-plan floor with real desk clusters, chairs, monitors, task lighting, planting and miniature employees.
- **Centre / background:** Evidence Lab behind glass, visibly quieter and more analytical.
- **Centre-right:** Technology/build cluster integrated into the open floor rather than a separate card.
- **Right / background:** premium glass Board / Executive room with conference table, executive seating and strong visual hierarchy.
- **Right / foreground:** lounge / shared workplace fabric, planting and architectural furniture to prevent the world becoming only workstations.
- **Across scene:** circulation path, ceiling/lighting system, windows/glazing, flooring/material transitions and depth cues connect all zones.

No functional zone may be visually implemented as a standalone rectangular UI card masquerading as architecture.

## 3. Architectural language

### Materials

Primary palette is restrained and architectural: warm timber, smoked/clear glass, matte dark metal, neutral stone/concrete, carpet/acoustic textile, soft upholstery and living greenery. Accent colour comes mainly from canonical AIOS state/HUD cues, not neon room shells.

### Ceiling and lighting

Use articulated/exposed ceiling structure, linear or track lighting, local pendant/task lighting and differentiated pools of light. Evidence may be slightly cooler/focused; Board warmer/premium; Operations balanced and energetic. Lighting must establish depth rather than merely decorate card borders.

### Floor and circulation

Create a continuous floor plane with material changes that indicate function without enclosing every zone. Preserve a visible circulation route through the HQ. Rugs/carpet zones, timber transitions and raised/recessed details may create hierarchy.

### Glass architecture

Evidence and Board should use believable glass partitions/frames/doors. Glass must create transparency and depth while preserving the sense of one headquarters.

### Furniture and workplace objects

Desks, monitor groups, office chairs, meeting tables, lounge furniture, plants, shelving/storage, wall displays, lighting fixtures and small workplace props should make the environment legible before any label appears.

## 4. Functional zone specification

### Operations / Mission

Open-plan command workspace. Long or grouped collaborative desks, multiple workstations, mission display surfaces and nearby collaboration space. Canonical active Mission/blocker state may alter small state cues only. The visual does not create or route work.

### Technology

Integrated technical/build cluster with denser monitor/equipment language and a distinct but connected identity. Do not isolate it in a card or sci-fi pod.

### Evidence Lab

Glass-partitioned focused analysis room with review stations and evidence/document display surfaces. Canonical evidence-valid state may be displayed. The room never certifies evidence.

### Board / Executive

Premium glass conference room with genuine conference table and executive seating. Canonical Board-attention risk/current decision/human-action state may be surfaced. The room never asserts occupancy or Board action.

### Shared fabric

Plants, lounge seating, circulation, storage, acoustic treatment and architectural transitions are mandatory. They make the environment a workplace rather than a diagram.

## 5. Character redesign

Current repeated creature presentation is rejected.

The new character system is an original stylized miniature workforce with human-readable office archetypes. It may use slightly exaggerated proportions for charm, but should not resemble generic blobs/creatures or floating avatar cards.

Required differentiation dimensions:

- silhouette and body proportion;
- face/head/hair shape;
- wardrobe cut and formality;
- accessories/tools;
- workstation context;
- restrained department accents;
- pose language.

CEO, CTO/Technology, Regulatory/Evidence and Operations archetypes must be recognisable without reading labels.

Characters should be composed into desks, chairs and architectural zones. They must not float over the scene as cards.

M.4.1 remains authoritative: working -> focused work pulse; blocked -> blocked attention pulse; awaiting_owner/queued -> waiting; completed -> settled idle; unknown -> static. `presentationOnly=true`, `presenceClaimed=false`, `locomotionAllowed=false` remain permanent for this programme.

## 6. HUD / information hierarchy

The approved reference principle is world-anchored intelligence.

Persistent UI should be limited to essentials. Zone labels may use compact translucent HUD chips anchored near Operations, Technology, Evidence and Board. Selection may reveal richer inspector detail. Recent activity/status surfaces may exist at edges but cannot dominate the world.

The environment remains understandable when HUD overlays are mentally removed.

Permanent literal contract:

`Selection changes view focus only; it cannot mutate AIOS.`

## 7. Motion and life

Motion should make the headquarters feel alive without inventing organization truth.

Allowed presentation examples: monitor glow, light sweep, subtle plant/environment drift, supported M.4.1 state pulses, canonical handoff cues, canonical conversation cues and focus transitions.

Not allowed: decorative walking presented as employee location, fake talking, fake coffee breaks, inferred room entry, inferred occupancy, invented handoffs, invented work or Board action.

## 8. Mobile outcome

Phone is not a vertically stacked desktop office/card grid.

Use a dedicated HQ viewport that preserves the architectural hero, with focus navigation to Operations / Technology / Evidence / Board and a separate contextual drill-down below/over the viewport. Preserve touch targets, no horizontal body overflow, readable fallback and truth-state labels.

## 9. Implementation work packages

### 13G.1A — Continuous architectural shell

Replace the existing three-room/card axis visually with one continuous office-world shell. Establish camera/perspective, floor, ceiling, glazing, windows, circulation, major partitions, material zones and depth layers. Preserve canonical room keys and semantic DOM contracts even where visual geometry changes.

**Gate:** screenshot clearly reads as one office before detailed furniture/characters.

### 13G.1B — Workplace interiors

Build Operations/Mission, Technology, Evidence, Board and shared/lounging interiors with distinct furniture, equipment, material and lighting identities.

**Gate:** every zone is recognisable spatially without relying on large labels.

### 13G.1C — Miniature workforce art system

Replace the rejected repeated-creature/card presentation with differentiated miniature workforce characters and integrate them into the environment.

**Gate:** CEO / Technology / Regulatory-Evidence / Operations archetypes are distinguishable without role text; no floating avatar-card impression.

### 13G.1D — World-anchored governed intelligence

Recompose existing spatial focus, inspector, handoff, conversation, Mission/blocker/evidence/Board context as compact world-anchored cues and contextual drill-down. Do not introduce a dashboard farm.

**Gate:** governed state is discoverable while architecture remains visually dominant.

### 13G.1E — Cinematic depth and supported life

Tune lighting, depth, shadows, glass, material separation, focus transitions and allowed ambient/state-driven motion.

**Gate:** desktop frame has foreground/midground/background depth and no neon-box/pixel-tower appearance.

### 13G.1F — Mobile HQ composition

Implement the dedicated mobile viewport/focus/drill-down composition.

**Gate:** phone is intentional, readable and spatial; no horizontal body overflow and no naive room-card stack.

### 13G.1G — Owner visual proof

Generate exact-head desktop and phone screenshots before expensive final sealing. Compare against the five-second test and this specification.

**Gate:** explicit Owner acceptance. CI cannot override Owner visual rejection.

### 13G.2 — Final acceptance and reconciliation

Only after 13G.1G passes: reconstruct useful acceptance/reconciliation work from Draft PR #146 onto the accepted architectural base; run Repository Policy, targeted Living HQ browser proof, full V12, Q17 and Q18; inspect artifacts; reconcile ROADMAP/README/final checklist; merge exact accepted head and verify merge commit.

## 10. Truth boundaries

This programme changes presentation, not canonical organization semantics.

- presentation state != canonical truth;
- animation != canonical activity;
- room presentation != occupancy;
- character placement != physical presence or employee location;
- Mission-room presentation does not route work;
- Evidence Lab presentation does not certify evidence;
- Board-room presentation != Board action;
- handoff cues remain canonical-only;
- conversation cues remain canonical-only;
- local spatial selection remains view state only;
- no new work/evidence/decision/authority/presence/occupancy/availability may be created by the visual layer.

## 11. Proof strategy

Do not spend full V12 cycles on obviously rejected visuals.

For 13G.1A–F use targeted types/build/browser screenshot checks appropriate to the changed surface. Inspect screenshots at each material milestone. Once 13G.1G receives Owner acceptance, normalize the candidate and run the full exact-head seal ladder.

## 12. Definition of done

The architectural correction is complete only when all of the following are true:

- desktop first impression is a premium contemporary headquarters;
- office remains legible with labels ignored;
- architecture is continuous rather than a set of room cards;
- Operations, Technology, Evidence and Board have distinct spatial identities;
- miniature employees are integrated into the environment and no longer read as repeated generic creatures;
- HUD is subordinate to architecture;
- mobile has an intentional HQ viewport/drill-down composition;
- sealed Phase 13A–F truth boundaries remain intact;
- responsive/reduced-motion/forced-colors/structured fallback remain valid;
- performance/asset budgets remain acceptable;
- Owner explicitly accepts desktop and phone visual proof;
- final exact-head CI/proof passes after acceptance.
