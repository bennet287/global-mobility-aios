# AIOS V2 — Phase 2C Mission Room + Employee Inspector

**Status:** IMPLEMENTED / PROOF PENDING
**Branch:** design/aios-v2-mission-room-inspector
**Phase 2B implementation parent:** 1c2cd5de378ba293b4d643ec1185349440fc8790
**Phase 2B merge:** 1f8a5e1a6f798931c152b45a4f145ba592022801

## Parallelization posture

This branch was intentionally started from the frozen Phase 2B proof head while Woodpecker #85 ran.

Pipeline #85 subsequently passed 4/4 and PR #35 merged. This branch remains isolated and may now target the V2 program branch for review.

## Implemented

- pure V2 Mission Room projection model
- pure V2 Employee Inspector projection model
- governed Living Organization scene hook
- selectable Mission objects
- Mission Room UI
- Employee Inspector UI
- participant mapping from LivingSceneMission.participant_position_keys
- blocker, decision and handoff linkage through canonical WorkItem IDs
- explicit no-presence and no-locomotion claims
- explicit no-mutation posture
- explicit unsupported/zero states
- responsive Mission Room and inspector layout
- contract tests included in the design-foundation test suite

## Mission Room behavior

The Organization workspace can select a canonical Mission and open a structured Mission Room view.

The Mission Room displays only supported canonical projection content:

- Mission state
- rostered participant positions
- linked blockers
- linked decisions
- linked handoff events

Participant selection opens the Employee Inspector.

Mission selection and employee selection change presentation focus only. They perform no AIOS mutation.

## Employee Inspector behavior

The inspector exposes supported employee projection fields:

- position key
- title
- department
- authority level
- organization status
- semantic presentation state
- linked WorkItem status when available
- linked Mission count
- linked blocker count
- linked decision count
- linked handoff count

It explicitly states:

- roster identity is not physical presence
- presenceClaimed = false
- locomotionClaimed = false
- no mutation is performed

## Truth rules

Mission Room:

- does not fabricate participants
- does not infer conversation
- does not infer physical presence
- does not infer work completion
- does not infer handoff duration
- only links blockers, decisions and handoffs supported by canonical identifiers

Employee Inspector:

- reads LivingSceneEmployee identity/state
- may show linked Missions, blockers, decisions and handoffs
- never converts roster identity into physical presence
- never claims locomotion
- never mutates AIOS

## Accessibility

The Mission Room is structured HTML rather than a 3D-only interaction.

Mission and employee selection use real buttons with aria-pressed state.

Essential Mission facts remain readable without the spatial renderer.

Reduced-motion behavior inherits the V2 motion-token contract.

## Deliberate non-goals

This slice does not add:

- hero character assets
- GLB rigs
- ambient locomotion runtime
- semantic handoff animation
- fabricated conversation content
- free-flight camera
- spatial mutation
- Replay integration

## Next integration

After this slice is proven and merged:

1. integrate the Character Presentation Registry
2. map first hero archetypes to canonical positions/role families
3. add visual employee selection in the governed renderer
4. add the first canonical handoff semantic animation
5. begin production HQ asset integration
