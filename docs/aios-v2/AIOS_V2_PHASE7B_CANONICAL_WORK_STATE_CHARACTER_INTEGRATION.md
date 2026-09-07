# AIOS V2 — Phase 7B Canonical Work-State Character Integration

## Status

Implementation slice. Acceptance requires exact-head Repository Policy + V12 Production Proof, production-browser evidence, screenshot review, reduced-motion review, and clean one-commit ancestry on the accepted Phase 7A merge.

## Accepted base

`626aad23c209a827e27cbdd8c7bf94dbf683c144`

Phase 7A visibly integrated canonical handoffs. Phase 7B closes the next repository-confirmed semantic gap: the Living Organization employee projection already carried canonical `semantic_state`, and the existing M.4.1 mapping already defined truthful stationary presentation states, but the V2 Living HQ character renderer did not consume them.

## Canonical authority

Phase 7B consumes only `LivingSceneEmployee.semantic_state` and echoes `presence_state`, `work_item_id`, and `state_reason` when supplied. It reuses the sealed M.4.1 mapping in `living-organization-employee-presentation.ts`.

Supported states:

| Canonical employee state | V2 presentation | Visible label |
| --- | --- | --- |
| `working` | focused work | `WORK` |
| `blocked` | blocked attention | `BLOCKED` |
| `awaiting_owner` | awaiting attention | `OWNER` |
| `queued` | queued wait | `QUEUED` |
| `completed` | settled state | `DONE` |
| unknown/unsupported | neutral ambient fallback | no semantic badge |

The employee semantic state is itself the authority for this presentation. A `work_item_id` is preserved when present but is not fabricated or required in order to echo an already-canonical employee semantic state.

## Renderer precedence

Semantic state and ambience remain separate systems.

When a supported canonical work state exists, the character uses `V2CanonicalWorkStateSurface` and the presentation-only ambient renderer is not layered underneath it. Unknown or unsupported semantic state falls back to the existing ambient renderer, whose semantic truth flags remain false.

This preserves the governance requirement:

> The organization causes the animation. Animation never causes the organization.

## Truth boundary

Phase 7B may communicate the employee's canonical work-state family. It does **not** claim:

- physical presence;
- physical location;
- physical travel or locomotion;
- conversation;
- collaboration;
- a handoff event;
- exact blocker title/type/severity;
- blocker resolution;
- a completion event or completion timestamp;
- any canonical mutation.

In particular, canonical employee state `blocked` permits a blocked-attention presentation but does not authorize Phase 7B to render the linked blocker object or severity. That belongs to Phase 7C and requires canonical `LivingSceneBlocker` evidence and coverage.

Likewise, canonical employee state `completed` permits a settled state presentation but does not imply that Phase 7B observed or replays a completion event.

## Motion

Persistent canonical work state may retain restrained presentation motion while that state remains canonical. Durations come only from shared V2 motion tokens:

- `--aios-v2-motion-duration-semantic-work`
- `--aios-v2-motion-duration-semantic-blocked`
- `--aios-v2-motion-duration-semantic-wait`
- `--aios-v2-motion-duration-semantic-settle`

No component-local semantic timing constant is authoritative.

Reduced motion uses `static-posture-and-label`; semantic animation is disabled while the canonical state remains visible through text/posture/badge.

## Structured equivalent

Structured Organization echoes the same canonical employee state in roster text and `data-canonical-semantic-state`. The state therefore remains understandable without color, motion, or the Living HQ renderer.

## Automated proof

Static/model proof:

`apps/web/scripts/aios-v2-visible-work-state.test.mjs`

Production browser proof:

`apps/web/e2e/tests/aios-v2-work-state-character.spec.ts`

Browser scenarios cover:

1. `working`, `blocked`, `awaiting_owner`, `queued`, and `completed` presentations;
2. unknown state falling back to ambience rather than semantic animation;
3. semantic renderer precedence over ambience;
4. no physical-presence/location/travel/locomotion claim;
5. no blocker-detail/resolution claim;
6. no completion-event claim;
7. reduced-motion static presentation;
8. Structured equivalent;
9. zero AIOS writes and zero page errors.

Visual review artifact must contain:

- `phase7b-work-states-dark-1280.png`
- `phase7b-work-states-reduced-structured-1280.png`

## Explicit deferrals

Phase 7B does not close all Phase 7 semantic integration. Remaining successor slices include:

- Phase 7C canonical blocker object/severity integration;
- governed conversation presentation;
- Mission collaboration;
- Owner/Board escalation;
- explicit completion/resolution event presentation;
- replay-specific semantic rendering.

No full Phase 7 completion claim is permitted from this slice alone.
