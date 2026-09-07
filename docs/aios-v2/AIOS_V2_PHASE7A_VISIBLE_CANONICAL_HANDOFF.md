# AIOS V2 — Phase 7A Visible Canonical Handoff Integration

## Status

Implementation candidate in progress. Acceptance requires production-browser screenshots, visual/UX inspection, accessibility and reduced-motion review, automated proof, and exact-head CI before merge.

## 1. Purpose

Phase 7A is the first visible semantic Living Organization integration slice after the formal Phase-12 hardening seal.

The repository already contained two sealed semantic layers:

1. Phase 2E — a governed `LivingSceneHandoff` → character semantic-motion descriptor.
2. Phase 2O — a presentation-only handoff visualization descriptor with a bounded sender → work object → relation → receiver → settle grammar.

Phase 2O explicitly deferred visible Living HQ integration. Phase 7A closes that specific gap without changing backend truth, persistence, authority, or the canonical Living Organization contract.

## 2. User and task

Primary user: Owner / Board-facing AIOS operator.

Task:

> Understand that a canonical work assignment handoff occurred, who the recorded sender and receiver were, which work relation it belongs to, and when it occurred—without confusing visualization with physical presence, travel, conversation, or completion.

Success condition:

- the canonical handoff is visible in Spatial Organization when semantic character treatment is supported;
- the same essential relation remains available in Structured Organization independently of the spatial renderer;
- unsupported or unavailable coverage fails closed;
- no UI interaction creates or mutates a handoff.

## 3. Canonical source and coverage

Canonical source:

`LivingOrganizationScene.deterministic.handoffs[]` / `LivingSceneHandoff`

Current live handoff coverage adapter:

`organization_work_assigned_activity_v1`

This value is taken from the existing Living Organization browser contract. Phase 7A does not invent a generic coverage state and does not infer support from arbitrary strings.

The selector supports only an explicit allow-list of recognized handoff coverage states. Unknown, partial, unavailable, or unsupported values produce no current handoff signal.

## 4. Truth-preserving latest-event rule

The visible signal is described as the latest supported canonical handoff only when that claim can be made deterministically.

Required ordering identity:

- `occurred_at`
- `activity_id`

Every supplied handoff must be orderable. If any record cannot participate in ordering, Phase 7A fails closed rather than pretending another event is certainly latest.

The newest ordered event must then satisfy the complete handoff contract:

- activity ID
- work item ID
- previous position key
- assigned position key
- status
- occurred-at timestamp
- causation activity ID as string or null
- canonical basis

A malformed newest event never causes fallback to an older event simply because the older event is easier to animate.

## 5. Exact endpoint identity

Character semantic treatment requires exactly one roster employee for each canonical endpoint position key.

Phase 7A does not infer sender or receiver identity from:

- title
- department
- authority
- visual wing
- proximity
- presentation role family

If an endpoint is missing or ambiguous, the canonical relation can remain readable in Structured Organization but semantic character animation is disabled.

## 6. Sealed semantic pipeline

The visible pipeline is:

```text
LivingSceneHandoff
        ↓
exact roster endpoints
        ↓
buildV2HandoffMotionDescriptor        (Phase 2E)
        ↓
buildV2HandoffVisualization           (Phase 2O)
        ↓
V2CanonicalHandoffSignal               (Phase 7A)
        ↓
Spatial + Structured presentations
```

Phase 7A does not duplicate or bypass the Phase 2E/2O truth gates.

## 7. Visible choreography

Full-motion Spatial mode follows the sealed Phase 2O grammar:

1. sender endpoint emphasis
2. work-assignment object activation
3. bounded sender-to-receiver relation cue
4. receiver endpoint emphasis
5. settle to a static recorded relation

The sequence executes once. It does not loop indefinitely because one historical/canonical assignment event must not visually imply a transfer that is continuously happening.

The bounded path is presentation geometry only. It is not a physical route and does not encode physical duration.

## 8. Reduced motion

Reduced-motion and Structured modes use the sealed static-relation equivalent.

They preserve:

- sender
- receiver
- assignment direction
- work item
- status
- occurrence time
- canonical provenance

They remove travel animation.

No essential handoff meaning depends on motion.

## 9. Shared motion tokens

Phase 7A introduces shared V2 motion tokens instead of component-local timing constants:

- `--aios-v2-motion-duration-micro`
- `--aios-v2-motion-duration-standard`
- `--aios-v2-motion-duration-spatial-focus`
- `--aios-v2-motion-duration-semantic-handoff`
- `--aios-v2-motion-ease-enter`
- `--aios-v2-motion-ease-exit`
- `--aios-v2-motion-ease-emphasis`

The semantic handoff sequence currently uses the prototype-reviewed token value `1280ms` and centralized emphasis easing. Canonical `occurred_at` never becomes animation duration.

These values remain design-system values and may be revised only through visual/prototype review rather than by individual components.

## 10. Reusable product component

Phase 7A introduces:

`V2CanonicalHandoffSignal`

It is a domain-native Handoff Signal rather than a generic card.

It exposes:

- recorded canonical sender → receiver relation
- assignment/work object
- canonical status
- activity identity
- occurrence time
- expandable provenance
- explicit truth boundary

Spatial and Structured variants consume the same model.

## 11. Authority and mutation posture

Permanent properties:

- presentation only
- renderer non-authoritative
- canonical state writable = false
- no POST/PATCH/PUT/DELETE introduced
- no authority action introduced
- selecting Organization representation remains local view state only

## 12. Forbidden implications

The visible signal must never claim or imply:

- literal physical presence
- literal physical location
- physical travel between employees
- physical transfer duration
- room traversal
- conversation or spoken words
- collaboration beyond the recorded handoff relation
- work completion
- dependency resolution
- approval/rejection
- authority change

The interface states this boundary explicitly.

## 13. Structured equivalent

Structured Organization renders the same canonical relation independently of Living HQ.

This satisfies the spatial law:

> Every essential spatial fact must have a structured accessible equivalent.

If character semantic treatment is unsupported, Structured Organization keeps the canonical sender/receiver relation readable and labels the semantic-presentation limitation.

## 14. Accessibility and responsive posture

The signal uses semantic section/heading/content structure and readable text for all essential information.

Requirements:

- no color-only meaning
- no motion-only meaning
- no hover-only information
- provenance uses native `details/summary`
- summary target is at least 44 CSS px high
- long IDs and canonical basis values wrap
- phone layout stacks sender, relation, and receiver
- OS reduced-motion is honored

## 15. Browser acceptance scenarios

Phase 7A browser proof uses the current real coverage string:

`organization_work_assigned_activity_v1`

Required scenarios:

1. Spatial desktop, supported canonical CEO → CTO handoff
   - signal visible
   - exact activity ID preserved
   - exact coverage preserved
   - Phase 2O mode = `bounded-transfer-sequence`
   - semantic sequence has exactly one iteration
   - canonical status/time visible
   - zero writes
   - zero page errors

2. Structured + reduced motion
   - same canonical relation visible
   - mode = `static-relation`
   - no travel animation
   - work item readable
   - zero writes

3. unavailable handoff coverage
   - no current handoff signal shown
   - no fabricated fallback

## 16. Visual-review evidence

The V12 browser lane generates a dedicated CI artifact:

`phase7a-visible-handoff-review`

Expected review PNGs:

- `phase7a-visible-handoff-dark-1280.png`
- `phase7a-visible-handoff-reduced-structured-1280.png`

These screenshots are review evidence, not canonical data and not Q15 visual-regression baselines.

The Phase 7A slice cannot be accepted solely because automated tests are green. The generated production-browser screenshots must be independently inspected before merge under the accepted AIOS UI design-system methodology.

## 17. Automated proof

Focused unit/static proof:

`apps/web/scripts/aios-v2-visible-handoff.test.mjs`

It verifies:

- real live coverage support
- fail-closed unsupported coverage
- deterministic latest ordering
- no older-event fallback after malformed newest event
- exact endpoint identity
- reduced-motion Phase 2O grammar
- truth flags
- deep immutability
- no random/clock/network/DOM machinery in the pure selector
- centralized motion-token use
- no infinite semantic handoff animation

Browser proof:

`apps/web/e2e/tests/aios-v2-visible-handoff.spec.ts`

The test is wired into the complete V12 Living Organization + V2 hardening browser lane.

## 18. Before / after

Before Phase 7A:

- canonical handoff existed;
- Phase 2E semantic descriptor existed;
- Phase 2O visualization descriptor existed;
- visible Living HQ integration was explicitly deferred.

After Phase 7A:

- supported canonical handoff events become visibly understandable in Living HQ;
- the same relation is available in Structured Organization;
- full and reduced-motion behavior follow the sealed semantic contracts;
- unsupported coverage and unsupported endpoint presentation fail closed.

## 19. Explicitly deferred

Phase 7A does not claim Phase 7 is complete.

Still separate successor slices include supported mappings for:

- WorkItem semantic state
- blocker response
- governed conversation
- Mission collaboration
- Owner / Board escalation
- canonical completion
- Replay-specific visible semantic animation where exact replay coverage/cursor rules apply

Ambient coffee, glance, local walking, and lounge behavior remain presentation-only and must never be used as substitutes for these semantic mappings.
