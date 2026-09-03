# AIOS V2 Spatial Interaction

## Principle

Spatial UI is for:
- organization awareness
- identity
- topology
- collaboration
- handoffs
- Mission context
- temporal transformation
- emotional presence

Structured UI is for:
- detailed reading
- forms
- approvals
- legal/regulatory text
- tables
- filters
- evidence comparison
- bulk operations
- technical provenance

Never force 3D navigation for ordinary administrative work.

## Camera

Use a directed architectural camera.

Default:
- polished three-quarter / isometric-ish perspective
- readable people
- legible rooms
- obvious depth

Allowed:
- bounded zoom
- gentle pan
- employee focus
- room focus
- Mission focus
- object focus
- return to HQ

Not required:
- WASD
- first-person
- free-flight
- arbitrary orbit

## Selection

Selecting an employee:
1. camera gently reframes
2. employee receives focus treatment
3. background de-emphasizes
4. compact contextual HUD appears
5. structured workspace remains one action away

Do not default to giant modals.

## Input

### Pointer
- generous hit volumes
- hover hints
- click select
- controlled pan/zoom

### Keyboard
- traverse selectable spatial objects
- visible focus
- Enter/Space activate
- Escape back

### Touch
- no hover dependence
- comfortable targets
- controlled pinch/zoom where appropriate

## Wayfinding

Department/room positions remain stable.

Use:
- architecture
- material
- lighting
- labels
- camera presets

rather than mini-map/game HUD complexity.

## Occlusion

The active object must remain readable.

Use:
- camera reframe
- transparency/de-emphasis
- label priority
- controlled geometry visibility

rather than allowing objects to disappear behind decorative architecture.

## Structured fallback

Every essential scene entity must be represented in structured UI.

If the 3D renderer is unavailable, the user can still:
- inspect employees
- inspect Missions
- inspect evidence
- inspect decisions
- use Replay
- understand blockers/relationships

## Spatial truth

Selection changes the view.

Selection does not mutate canonical state.

Renderer remains non-authoritative.
