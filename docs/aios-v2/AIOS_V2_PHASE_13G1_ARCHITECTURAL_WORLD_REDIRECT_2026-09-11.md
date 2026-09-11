# AIOS V2 Phase 13G.1 — Living HQ Architectural World Redesign

**Status:** ACTIVE — Owner rejected the prior Phase 13G visual candidate.

## Why this slice exists

Phase 13A–13F successfully established governed Living HQ semantics, spatial focus, inspectors, canonical handoffs, governed conversation cues, and Mission/Board convergence. The final Owner visual review rejected the result because the visible world still reads as stylized room cards / square boxes with substantially the same creature language rather than a materially redesigned modern headquarters.

Green CI is therefore insufficient. Phase 13 is not visually sealed.

## New visual north star

The Living HQ must read at first glance as a **premium contemporary office headquarters**, not a dashboard whose cards are styled as rooms.

The architectural reference direction supplied and accepted by the Owner is:

- continuous open-plan office architecture;
- glass-and-timber partitions and meeting rooms;
- warm timber desks and flooring accents;
- neutral stone/concrete/carpet surfaces;
- exposed or architecturally articulated ceilings with track/linear lighting;
- large windows and believable interior depth;
- plants, lounge areas, equipment, screens, chairs and real workplace furniture;
- miniature stylized AI employees physically composed *inside the rendered environment* as presentation figures;
- Operations, Technology, Evidence and Board expressed as zones of one headquarters rather than independent rectangular UI cards;
- contextual HUDs anchored to the world, with detailed inspectors appearing only when selected;
- elevated / God’s-eye / cutaway perception where useful, while preserving believable office proportions and materials.

## First-glance acceptance tests

A successful desktop frame must immediately communicate:

1. **modern office / digital company headquarters**;
2. **one continuous architectural world with distinct functional zones**;
3. **miniature employees integrated into that world**;
4. **governed AIOS information illuminating the environment rather than defining its geometry**.

It must *not* primarily communicate:

- dashboard card grid;
- square boxes pretending to be rooms;
- pixel tower;
- neon sci-fi pods;
- floating avatar cards;
- generic repeated creatures;
- toy-room diorama geometry without credible office architecture.

## Spatial programme

### Operations / Mission workspace
Open-plan collaborative command floor with long desks, multiple workstations, wall displays and a nearby glass collaboration pod. Canonical Mission and blocker state may influence presentation labels/status cues only.

### Technology workspace
Technical desk cluster / build area with monitors and infrastructure cues. It remains presentation-only and cannot imply tool execution or physical presence.

### Evidence Lab
Quieter glass-partitioned analysis area with review stations, document/evidence display surfaces and more focused lighting. Evidence state is read-only; the environment cannot certify evidence.

### Board / Executive room
Architecturally premium enclosed glass room with a genuine conference table, executive seating and stronger visual hierarchy. Board-attention/decision/human-action records may be surfaced, but the room cannot imply Board occupancy or Board action.

### Shared workplace fabric
Circulation paths, planting, lounge seating, storage, acoustic treatments, lighting, screens and architectural transitions should make the zones feel like parts of one office rather than isolated components.

## Character direction

The existing generic/repeated creature appearance is not the target. Employees should become an original miniature executive/workforce character system with:

- recognisable silhouettes before labels;
- role-specific wardrobe and accessories;
- head/hair/face/proportion variation;
- department visual identity without turning employees into status badges;
- credible desk/chair/environment placement;
- restrained presentation animation derived only from already-governed presentation state.

CEO / CTO / Regulatory / Operations archetypes should be visually distinguishable without requiring the role text.

## HUD direction

HUD is subordinate to the world. Prefer compact glass/neutral contextual overlays anchored near zones/entities. Avoid large persistent panels covering the architecture. Selection and drill-down remain local view state only.

Permanent literal contract:

> Selection changes view focus only; it cannot mutate AIOS.

## Truth boundary — unchanged

This visual redesign does not reopen Phase 13A–13F semantics.

- presentation state != canonical truth;
- room presentation != occupancy;
- character placement != physical presence or employee location;
- animation cannot create work, presence, communication, handoff, evidence, decision, completion, authority, occupancy or availability;
- locomotion remains disallowed unless future governed semantics explicitly earn it;
- conversation cues remain canonical-only;
- handoff cues remain canonical-only;
- Mission/Board context remains canonical-only;
- Board-room presentation != Board action;
- local spatial selection remains view state only.

## Implementation sequence

### 13G.1A — Architectural shell
Replace the three-card chamber composition with a continuous office-world composition: floor plane, architectural ceiling/lighting, glass partitions, circulation, windows, furniture silhouettes, planting and differentiated zones. Preserve existing canonical room keys/data attributes in the semantic DOM even if their visual geometry changes completely.

### 13G.1B — Zone interiors
Give Operations/Mission, Technology, Evidence and Board distinct believable workplace functions and material/lighting treatments without separating them into card boxes.

### 13G.1C — Character art correction
Replace/rework the current roster presentation so miniature employees read as people/characters inhabiting the office world rather than avatar cards. Preserve M.4.1 truth mapping and no-presence/no-locomotion boundaries.

### 13G.1D — World-anchored state cues
Integrate governed Mission, blocker, evidence, handoff, conversation and Board-attention cues as subtle world/HUD annotations. Do not create a dashboard farm.

### 13G.1E — Mobile composition
Use an HQ viewport + focused drill-down model. Do not simply stack a desktop room/card grid vertically.

### 13G.1F — Visual proof
Generate fresh desktop and phone screenshots. Owner acceptance requires an obvious material difference at first glance. Existing semantic, responsive, reduced-motion, forced-colors, structured fallback, Q17 and Q18 gates remain required.

## Relationship to PR #146

PR #146 remains Draft and is not an accepted visual candidate. Its acceptance/reconciliation work can be reconstructed only after this architectural correction is visually accepted. Do not merge #146 in its rejected visual state.

## Definition of done

Phase 13G.1 is done only when the saved visual proof looks unmistakably like a modern premium office headquarters and the Owner explicitly accepts the result. Passing tests alone cannot satisfy this slice.
