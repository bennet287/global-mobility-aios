# AIOS V2 Phase 7D — Governed Conversation Integration

## Scope

Phase 7D makes the existing canonical Living Organization conversation lifecycle visible in the V2 Organization experience. It does not create chat truth, simulated dialogue, physical co-location, authority outcomes, replay semantics, or canonical writes.

## Canonical source

The accepted coverage adapter is exactly:

`organization_activity_conversation_lifecycle_v1`

Anything else fails closed and is presented as unavailable rather than as an empty canonical result.

The visible projection consumes only `LivingSceneConversation`, `LivingSceneEmployee`, and `LivingSceneWorkItem` records from the deterministic Living Organization scene.

## Required proof before presentation

A conversation is visible only when all of the following are true:

- the coverage adapter exactly matches the canonical conversation lifecycle source;
- the conversation has a non-empty identity, WorkItem identity, lifecycle state, and summary;
- at least two unique participant position keys are present;
- every participant position key resolves uniquely to the canonical scene roster;
- the linked WorkItem resolves uniquely in the canonical scene WorkItem collection;
- the WorkItem's assigned position is one of the canonical conversation participants;
- `authority_effect` is exactly `none`;
- `transcript_persisted` is exactly `false`.

Malformed, ambiguous, unsupported, or overclaiming records are omitted rather than repaired heuristically.

## Presentation surfaces

### Spatial Organization

The spatial representation receives a bounded, one-shot lifecycle cue for open governed conversations. The cue does not make characters walk, talk, meet, or change rooms. It is presentation-only evidence adjacent to the Living HQ stage.

The cue's transition runs once and is disabled under `prefers-reduced-motion`.

### Structured Organization

The renderer-free Structured representation receives the same canonical conversation collection and the same unavailable state. It has no motion dependency.

### Mission Room

Mission Room exposes only conversations whose exact WorkItem belongs to the selected canonical Mission. It shows lifecycle status, summary, participant titles, WorkItem identity, `authority effect: none`, and that the transcript is not persisted.

### Employee Inspector

Employee Inspector exposes only conversations whose canonical participant list contains the selected exact position key. Unsupported conversation coverage is shown as `Unavailable`, not `0`.

## Permanent truth boundaries

Phase 7D asserts only canonical conversation lifecycle evidence.

It does **not** assert:

- live speech or dialogue;
- a verbatim or persisted transcript;
- physical presence or co-location;
- room entry or movement;
- a decision, approval, escalation, or other authority effect;
- completion or resolution of linked work;
- historical replay state;
- any mutation to canonical organization state.

## Deferred slices

The following remain outside Phase 7D:

- richer Mission collaboration behavior;
- Owner / CEO / Board escalation visualization;
- explicit completion and resolution consequences;
- replay / as-of historical conversation state;
- canonical write controls;
- synthetic dialogue or ambient employee chatter.

## Validation

Focused proof lives in:

`apps/web/scripts/aios-v2-visible-conversation.test.mjs`

It verifies exact coverage gating, participant and WorkItem linkage, anti-overclaim fields, fail-closed malformed records, exact selectors, and UI truth attributes.
