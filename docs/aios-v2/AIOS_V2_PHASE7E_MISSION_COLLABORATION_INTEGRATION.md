# AIOS V2 Phase 7E — Mission Collaboration Integration

## Status

Working implementation slice. Phase 7E is not accepted until the exact final candidate passes repository policy, the complete V12 Production Proof, focused Chromium review, visual inspection, and clean-candidate reconstruction.

## Purpose

Phase 7E makes canonical coordination evidence visible inside the Mission experience without turning Mission topology into a claim that employees are physically or actively collaborating.

The user-visible product goal is richer Living Organization collaboration context. The semantic goal is stricter: AIOS may show governed coordination evidence only where canonical records establish the relationship.

## Canonical archaeology

The Living Organization scene exposes Missions through coverage:

`workitem_objective_topology_projection`

`LivingSceneMission` is explicitly `projection_only=true` and is based on `OrganizationalWorkItem objective_key/parent topology`.

Its `participant_position_keys` is therefore Mission topology membership. It is useful for scope and navigation, but it is not proof of active collaboration.

Phase 7D separately sealed governed conversation lifecycle under:

`organization_activity_conversation_lifecycle_v1`

The backend relationship plane makes the bridge explicit:

- employee → conversation: `participates_in_conversation`
- conversation → WorkItem: `coordinates_work`

The conversation WorkItem relation is the canonical evidence used by Phase 7E.

## Supported Phase 7E projection

A visible Mission coordination item is established only when all of the following are true:

1. Mission coverage is exactly `workitem_objective_topology_projection`.
2. Governed conversation coverage is supported by the sealed Phase 7D projection.
3. The Mission is a valid projection-only Mission with non-empty exact identifiers and unique WorkItem / participant keys.
4. The supported governed conversation WorkItem belongs to exactly one valid Mission.
5. Every exact conversation participant is also consistent with that Mission's participant topology.
6. Exact conversation participants, not the broad Mission participant list, become the coordination participants.

If a conversation WorkItem maps to zero or multiple Missions, the relation fails closed.

## Truth boundary

Phase 7E may claim:

- a canonical Mission topology scopes the relevant work,
- a supported governed conversation has exact canonical participants,
- that conversation coordinates a WorkItem inside exactly one Mission,
- governed Mission coordination evidence exists for those exact participants.

Phase 7E does **not** claim:

- employees are actively collaborating right now,
- employees are in the same room or physical location,
- physical presence,
- live speech or live dialogue,
- a persisted transcript,
- locomotion or movement toward one another,
- completion or resolution,
- an approval, authority outcome, Board action, or escalation,
- any canonical mutation.

Mission membership by itself is never labeled collaboration evidence.

## Shared projection

`apps/web/lib/v2/visible-mission-collaboration.ts` is the shared fail-closed projection used by all Phase 7E surfaces.

It consumes the already-sealed Phase 7D visible conversation collection rather than reimplementing conversation validation. This prevents Mission Room, Employee Inspector, Spatial Organization, and Structured Organization from diverging on participant or WorkItem truth.

## Visible surfaces

### Spatial Organization

A bounded presentation signal surfaces open governed Mission coordination links. It does not move characters together or simulate teamwork.

### Structured Organization

The same semantic signal is available without the Living HQ renderer. Reduced-motion preference removes the finite entrance cue while preserving all meaning.

### Mission Room

Mission participants are explicitly labeled as topology participants. A separate Governed Mission coordination section shows only exact coordination items and their exact conversation participants.

### Employee Inspector

Mission topology membership remains separate from governed coordination evidence. An employee receives a coordination item only when that employee is an exact participant in the canonical conversation used by the Mission relation.

## Coverage posture

Unsupported Mission coverage or unsupported governed conversation coverage is `Unavailable`, not canonical zero.

Established supported coverage with no matching coordination item is a legitimate empty result.

## Proof requirements

Focused pure regression:

- `apps/web/scripts/aios-v2-visible-mission-collaboration.test.mjs`

Focused Chromium proof:

- `apps/web/e2e/tests/aios-v2-mission-collaboration.spec.ts`

Required review artifacts:

- `phase7e-mission-collaboration-dark-1280.png`
- `phase7e-mission-collaboration-reduced-structured-1280.png`

V12 must run the focused Phase 7E browser spec and upload `phase7e-mission-collaboration-review`.

## Deferred successor slices

Phase 7E does not implement Owner/Board escalation, explicit completion/resolution events, or replay-specific semantic rendering. Those remain separate truth-gated slices.
