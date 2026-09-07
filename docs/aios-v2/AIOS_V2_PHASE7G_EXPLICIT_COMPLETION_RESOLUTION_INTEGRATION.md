# AIOS V2 Phase 7G — Explicit Completion / Resolution Integration

## Purpose

Phase 7G makes completed and resolved organization state visible only when the canonical organization record contains explicit transition evidence. A settled character pose, missing blocker marker, elapsed time, or generic status styling is never promoted into a completion/resolution event.

## Canonical evidence

### WorkItem completion

A WorkItem completion claim requires both:

- `status == "completed"`
- non-null `completed_at`

The canonical command layer already persists both and emits `organization.work.completed.v1` with `payload_json.status == "completed"`. Phase 7G may display the canonical timestamp from the WorkItem read model; it must not synthesize a new timestamp from Activity ordering.

### Blocker resolution / waiver

A blocker resolution claim requires the canonical blocker record to satisfy the existing database truth contract:

- `status == "resolved"`
- non-null `resolved_at`
- non-empty `resolution_summary`
- non-null `resolving_actor_type`
- non-empty `resolving_actor_id`

A blocker waiver claim requires:

- `status == "waived"`
- non-null `waived_at`
- non-empty `waived_by_human_id`
- non-empty `waiver_reason`

The current Living Scene V5 blocker DTO is lossy: `_scene_blockers()` reads `resolved_at` / `waived_at` for elapsed-time calculation but does not expose the transition timestamp or outcome evidence. Phase 7G therefore extends the read-only scene blocker projection with those already-canonical fields. It does not create or mutate blocker state.

No dedicated blocker-resolution Activity contract is assumed by this phase.

### Decision outcomes

A decision outcome is explicit only when the canonical decision record has a terminal outcome and non-null `decided_at`. Phase 7G may display that evidence; pending decision state is not completion.

## Truth boundaries

Phase 7G must not claim:

- physical celebration, travel, presence, or room attendance;
- that a WorkItem is complete from `semantic_state == "completed"` alone;
- that a blocker is resolved because its marker disappeared;
- that a blocker is resolved/waived from elapsed time;
- that mitigation is resolution;
- that a decision is approved from visual placement or authority level;
- that a transition happened at `scene_generated_at`;
- canonical mutation from any V2 presentation component.

Spatial and Structured Organization must expose equivalent semantic evidence. Reduced motion removes decorative transition motion while preserving timestamps, outcomes, and provenance.

## Read-model extension

The Living Scene contract remains backward-compatible. `LivingSceneBlocker` gains optional fields:

- `resolved_at`
- `resolution_summary`
- `resolving_actor_type`
- `resolving_actor_id`
- `waived_at`
- `waived_by_human_id`
- `waiver_reason`

Existing blocker coverage remains `organization_blocker_canonical_records` because these are fields from the same canonical records, not a new source plane.

## Acceptance

Phase 7G is accepted only after:

1. backend projection tests prove canonical transition fields survive into the Living Scene without mutation;
2. pure frontend projection tests fail closed on status/timestamp/outcome mismatches;
3. Spatial and Structured/reduced-motion Chromium proof shows equivalent completion/resolution evidence;
4. production browser screenshots are independently inspected;
5. Repository Policy and V12 Production Proof pass on the exact final candidate SHA.
