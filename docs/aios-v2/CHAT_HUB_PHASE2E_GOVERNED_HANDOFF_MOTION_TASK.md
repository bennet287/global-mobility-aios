# ChatHub Task — AIOS V2 Phase 2E Governed Handoff Motion Descriptor

## Assignment

Implement the next pure/read-only semantic-motion slice for AIOS V2: translate a canonical LivingSceneHandoff plus the already-resolved sender/receiver character presentations into a bounded, truth-preserving handoff motion descriptor.

This task is intentionally renderer-independent so it can be developed in parallel with Phase 2D UI work.

## Base

Use the latest head of:

~~~text
design/aios-v2-character-mission-integration
~~~

Before writing files:

1. resolve and report the exact base SHA you used
2. inspect the current files listed below
3. do not assume an older ChatHub ZIP/root commit is repository evidence

Required references:

- apps/web/lib/live-organization.ts
- apps/web/lib/v2/character-presentation.ts
- apps/web/lib/v2/character-mission-presentation.ts
- skills/aios-design/characters/CHARACTER_BIBLE.md
- skills/aios-design/characters/animation-states.md
- skills/aios-design/governance/semantic-animation-contract.md

Core rule:

> **The organization causes the animation. Animation never causes the organization.**

## Allowed files

Create only:

~~~text
apps/web/lib/v2/character-semantic-motion.ts
apps/web/scripts/aios-v2-character-semantic-motion.test.mjs
docs/aios-v2/AIOS_V2_PHASE2E_GOVERNED_HANDOFF_MOTION.md
~~~

Do not modify package.json, React components, CSS, character-presentation.ts, character-mission-presentation.ts, Mission Room/Inspector files, backend files, migrations, or APIs.

We will wire the test into CI after independent review. This isolation is deliberate to avoid merge conflicts with Phase 2D.

## Canonical input

The existing canonical handoff type is:

~~~ts
export type LivingSceneHandoff = {
  activity_id: string;
  work_item_id: string;
  previous_position_key: string;
  assigned_position_key: string;
  status: string;
  occurred_at: string;
  causation_activity_id: string | null;
  canonical_basis: string;
};
~~~

The handoff record is the only authority that a handoff occurred. Character presentation metadata may only decide whether/how that event can be visually expressed.

## Required implementation

Create a pure typed function equivalent to:

~~~text
buildV2HandoffMotionDescriptor({ handoff, sender, receiver })
~~~

where handoff is canonical LivingSceneHandoff and sender/receiver are resolved V2CharacterPresentationResolution values.

## Required descriptor semantics

The result must preserve canonical evidence separately from presentation choices and expose concepts equivalent to:

~~~text
kind = handoff
activityId
workItemId
fromPositionKey
toPositionKey
occurredAt
canonicalBasis

supported
limitation

senderPresentationKey
receiverPresentationKey
senderCapabilitySupported
receiverCapabilitySupported

visualMode = bounded-transfer-emphasis
semanticAnimationActive = false

truth:
  canonicalEvent = true
  physicalDurationCanonical = false
  physicalPresenceClaimed = false
  conversationClaimed = false
  workCompletionClaimed = false
  dependencyResolutionClaimed = false
  canonicalStateWritable = false

reducedMotion:
  static sender -> receiver relation
  brief emphasis only
  no long travel
~~~

Exact field names can vary if strongly justified, but all invariants must be explicit and testable.

## Capability gate

A handoff descriptor is visually supported only if both selected character presentations declare the handoff semantic capability.

If either sender or receiver lacks the capability, supported must be false and the descriptor must provide a deterministic limitation explaining why no semantic animation may run.

Neutral fallback presentations expose no semantic capabilities, so a neutral sender or receiver should normally make handoff motion unsupported.

## Truth rules

The implementation must never infer or claim physical transfer duration, travel distance, room traversal, conversation, transcript, spoken words, work completion, dependency resolution, physical presence, approval, authority change, or semantic-state mutation.

occurred_at is canonical event time. It is not animation duration.

status must not be converted into completion unless another canonical contract explicitly establishes that truth.

## Determinism

Forbidden in the pure descriptor module:

- Math.random
- Date.now
- timers
- requestAnimationFrame
- browser event listeners
- network/API calls
- backend writes
- React
- CSS
- global mutable registries

The same inputs must produce the same descriptor.

## Immutability

Return a runtime-frozen descriptor. If it contains nested objects/arrays, freeze them deeply enough that the exported result exposes no mutation surface. Do not export a mutation API.

## Reduced motion

Reduced motion is first-class. The descriptor must provide the same canonical handoff identity as a static sender -> receiver relation with brief emphasis only and no long travel animation.

## Tests

Write executable tests that prove at least:

1. exact CEO -> CTO handoff is supported when both presentations support handoff
2. regulatory -> operations family handoff is supported when both family presentations support handoff
3. neutral sender blocks semantic handoff animation
4. neutral receiver blocks semantic handoff animation
5. canonical handoff identifiers/timestamp/basis are preserved exactly
6. animation duration is not derived from occurred_at
7. no conversation claim
8. no physical-presence claim
9. no work-completion claim
10. no canonical mutation surface
11. reduced-motion descriptor exists
12. deterministic output for identical inputs
13. descriptor and nested truth/reduced-motion metadata are frozen
14. no random/time/network/renderer activation machinery exists

Use real imports where practical rather than only regex tests. If Node/TypeScript loading needs a fallback, use a temporary external transpilation path. Do not add or commit node_modules.

## Documentation

Document canonical input, capability gate, descriptor schema, supported/unsupported behavior, truth boundaries, reduced motion, test evidence, non-goals, and future renderer integration.

## Non-goals

Do not implement visible transfer animation, walking, pathfinding, Mission-room movement, conversation animation, Board animation, blocker animation, completion animation, 3D/GLB loading, CSS, React rendering, or backend mutation.

Those come only after the pure semantic descriptor is independently reviewed.

## Verification and delivery

Run the new Phase 2E test directly, strict TypeScript verification of the new module against the current repo configuration if possible, and directly relevant Character Registry tests needed for compatibility.

Report real observed results, not expected results.

Final delivery must include:

- exact base SHA
- created files
- concise contract summary
- exact test commands
- exact pass/fail counts
- TypeScript result
- git status --short
- git diff --stat <base>...HEAD
- limitations

If the sandbox creates a root commit or detached history, explicitly state that SHA is not repository acceptance evidence.

Do not claim success for tests you did not execute.
