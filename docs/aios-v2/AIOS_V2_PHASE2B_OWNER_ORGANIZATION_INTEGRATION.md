# AIOS V2 — Phase 2B Canonical Owner Home + Organization Integration

**Status:** IMPLEMENTED / PROOF PENDING
**Branch:** design/aios-v2-owner-organization
**Parent:** Phase 2 Foundation merge 4d2a29c4fa9f97af6908436225c2490d48d60127

## Scope

This slice connects the isolated V2 shell to existing governed AIOS data without replacing the legacy production surfaces.

It adds:

- canonical Owner attention
- canonical Mission summaries
- canonical recent Activity
- Living Organization scene adapter
- first Office Bible architectural blockout
- view-only spatial selection
- structured accessibility equivalent
- partial-data handling
- Organization V2 route

## Governed sources

The V2 adapter reads:

- Board packet
- HumanActionRequests
- open blockers
- Activity
- Austria Living Organization scene

No new backend truth store is introduced.

## Owner attention

Attention objects can derive from:

- current pending ExecutiveDecision records
- Board-attention RiskEscalations
- active HumanActionRequests
- open blockers requiring human action

The V2 layer ranks presentation priority but does not change the underlying authority or lifecycle.

## Missions

Mission summaries come from LivingSceneMission.

Displayed participant counts are Mission-projection participant counts.

They are not employee-presence claims.

## Architectural blockout

The first HQ blockout implements presentation zones from the Office Bible:

- Executive Terrace
- Regulatory & Evidence
- Central Atrium
- Technology & Security
- Operations Studio
- Mission Hub

Department-to-wing placement is a frontend presentation registry based on department identity.

It is not canonical organizational topology.

Canonical department counts, WorkItem counts and blocker counts remain sourced from LivingSceneDepartment.

## Truth posture

The blockout exposes and preserves:

- scene_authoritative
- renderer_authoritative
- mutations_allowed

Selection changes view focus only.

The spatial blockout performs no AIOS mutation.

If the Living Organization scene is not established, V2 renders an explicit zero/unavailable state rather than fabricated organization content.

## Structured equivalent

The Organization route includes a structured department/wing representation independent of the spatial blockout.

This is the first V2 implementation of the constitutional rule:

Every essential spatial fact must have a structured accessible equivalent.

## Routes

- /cockpit/v2
- /cockpit/v2/organization

Organization is now enabled in the V2 Owner navigation.

Future V2 domains remain disabled until implemented.

## Tests

The existing V2 foundation checks are updated.

New contract checks cover:

- governed source usage
- no fixture/random presentation source
- explicit presentation topology
- non-authority/no-mutation posture
- roster-versus-presence language
- structured fallback
- isolated V2 Organization route

## Deliberate non-goals

This slice does not yet add:

- production 3D HQ assets
- hero character GLBs
- semantic locomotion
- canonical handoff animation
- employee inspector
- Mission Room interaction
- Evidence Object
- Decision Object
- Replay V2

Those remain subsequent vertical-slice work.

## Next slice after proof

1. hero character presentation registry
2. first four role archetypes
3. employee inspector
4. Mission Room selection
5. canonical handoff semantic-animation mapping
6. governed renderer integration with architectural assets
