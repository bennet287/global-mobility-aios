# AIOS V2 — Phase 2E: Governed Handoff Motion Descriptor

Status: implemented (pure, read-only, renderer-independent)
Base: `design/aios-v2-character-mission-integration` @ `d3d11622a4a221e366995366b3e8eac9d14a3959`
Core invariant:

> **The organization causes the animation. Animation never causes the organization.**

---

## 1. Summary

Phase 2E adds a pure, deterministic, read-only translation from a canonical
`LivingSceneHandoff` plus already-resolved sender/receiver character
presentations into a bounded, truth-preserving **handoff motion descriptor**.
The descriptor states what a renderer *may* render later. It never starts an
animation: creation always carries `semanticAnimationActive = false`.

Created files (nothing else was modified):

- `apps/web/lib/v2/character-semantic-motion.ts` — the descriptor module
- `apps/web/scripts/aios-v2-character-semantic-motion.test.mjs` — executable tests
- `docs/aios-v2/AIOS_V2_PHASE2E_GOVERNED_HANDOFF_MOTION.md` — this document

## 2. Canonical input

The only authority that a handoff occurred is the canonical record
(`apps/web/lib/live-organization.ts`):

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

The builder receives the canonical handoff plus resolved presentations:

~~~ts
buildV2HandoffMotionDescriptor({
  handoff,            // LivingSceneHandoff
  sender,             // V2CharacterPresentationResolution
  receiver,           // V2CharacterPresentationResolution
})
~~~

Character presentation metadata may only decide **whether/how** the event can
be visually expressed — never **whether** it happened.

## 3. Capability gate

Semantic handoff rendering is supported **only** when BOTH the sender and the
receiver presentations declare the `"handoff"` capability in
`supportedSemanticAnimationCapabilities` **and** the supplied presentation
identities match the canonical handoff endpoints exactly
(`sender.identity.positionKey === previous_position_key` and
`receiver.identity.positionKey === assigned_position_key`).

- If either side lacks the capability: `supported = false`, the descriptor
  exposes a deterministic `limitation` code, and **no semantic animation may
  be activated**.
- Neutral fallback presentations expose no semantic capabilities, so a neutral
  sender or receiver normally produces an unsupported descriptor.

Limitation codes (deterministic, mutually exclusive, evaluated in this order):

| code | condition |
|---|---|
| `canonical-handoff-record-missing-or-incomplete` | handoff record absent or any required field empty |
| `sender-and-receiver-presentation-identities-mismatch` | both supplied presentation identities disagree with canonical endpoints |
| `sender-presentation-identity-mismatch` | sender presentation identity disagrees with `previous_position_key` |
| `receiver-presentation-identity-mismatch` | receiver presentation identity disagrees with `assigned_position_key` |
| `sender-presentation-lacks-handoff-capability` | sender not capable (receiver is) |
| `receiver-presentation-lacks-handoff-capability` | receiver not capable (sender is) |
| `sender-and-receiver-presentations-lack-handoff-capability` | neither side capable |

## 4. Descriptor schema

~~~ts
{
  kind: "handoff",
  // Canonical evidence preserved exactly:
  activityId, workItemId, fromPositionKey, toPositionKey,
  causationActivityId, occurredAt, canonicalBasis,
  handoffStatus,                      // verbatim echo of status; no semantics added
  // Gate outcome:
  supported, limitation,
  senderPresentationKey, receiverPresentationKey,
  senderCapabilitySupported, receiverCapabilitySupported,
  senderIdentityMatchesCanonicalHandoff,
  receiverIdentityMatchesCanonicalHandoff,
  // Rendering contract:
  visualMode: "bounded-transfer-emphasis",
  semanticAnimationActive: false,
  truth: { ... },                     // see §5
  reducedMotion: { ... },             // see §6
}
~~~

`handoffStatus` is a verbatim echo of `LivingSceneHandoff.status`. It is not
converted into completion unless another canonical contract explicitly
establishes that truth (none does today).

## 5. Truth boundaries

`descriptor.truth` explicitly declares:

- `canonicalEvent` / `canonicalEventSource` — the event is canonical because
  the `LivingSceneHandoff` record says so (never because presentation data
  exists).
- `occurredAtIsEventTimeOnly: true` and `occurredAtIsAnimationDuration: false`
  — `occurred_at` is canonical event time and must **never** become animation
  duration. The descriptor contains no numeric timing fields at all.

The descriptor explicitly claims **none** of the following (each is a literal
`false` field, so the type system itself prevents drift):

- physical transfer duration
- physical travel / travel distance
- room traversal
- physical presence
- conversation
- transcript
- spoken words
- work completion
- dependency resolution
- authority change
- approval / rejection
- canonical state mutation (`truth.canonicalStateWritable = false`)

## 6. Reduced motion (first-class)

The descriptor always carries a reduced-motion form — also for unsupported
gatings — describing the same canonical handoff identity as a **static
sender → receiver relation with brief emphasis only**, never a long travel
animation:

~~~ts
reducedMotion: {
  mode: "static-relation-brief-emphasis",
  relation: "<previous_position_key> -> <assigned_position_key>",
  fromPositionKey, toPositionKey,
  direction: "sender-to-receiver",
  briefEmphasisOnly: true,
  forbidsLongTravelAnimation: true,
  preservesCanonicalIdentity: true,
}
~~~

## 7. Supported vs. unsupported behavior

| | supported | unsupported |
|---|---|---|
| `supported` | `true` | `false` |
| `limitation` | `null` | deterministic code (§3) |
| canonical evidence | preserved exactly | preserved exactly |
| `semanticAnimationActive` | `false` (renderer may activate later, governed by this descriptor) | `false` (must not activate) |
| `reducedMotion` | present | present |

## 8. Determinism & immutability

The module contains no random sources, no clocks, no timers, no scheduling
primitives, no browser event listeners, no network/API calls, no backend
writes, no React, no CSS, and no global mutable registries. All imports are
`import type` only — there is zero runtime coupling. Identical inputs produce
a deeply identical result. The returned descriptor and every nested
truth/reduced-motion structure are deep-frozen; no mutation API is exported.

## 9. ChatHub draft test evidence (observed, not expected)

Commands (executed):

~~~text
cd apps/web
NODE_PATH=/tmp/aios-ts-kit/node_modules \
AIOS_TYPESCRIPT_ENTRY=/tmp/aios-ts-kit/node_modules/typescript/lib/typescript.js \
  node --test scripts/aios-v2-character-semantic-motion.test.mjs
# -> 17 tests, 17 pass, 0 fail

NODE_PATH=/tmp/aios-ts-kit/node_modules \
  node --test scripts/aios-v2-character-registry.test.mjs
# -> 24 tests, 24 pass, 0 fail  (Character Registry compatibility)

node --test scripts/aios-v2-character-mission-integration.test.mjs
# -> 7 tests, 7 pass, 0 fail    (Phase 2D sibling compatibility)

/tmp/aios-ts-kit/node_modules/typescript/bin/tsc -p /tmp/tscheck/tsconfig.json --pretty false
# -> exit 0, no errors (strict; repo-matching compilerOptions; external harness)
~~~

The evidence in this section is the ChatHub draft evidence captured before independent repository hardening. The hardened upstream branch adds endpoint-identity and empty-status acceptance cases and requires fresh repository CI proof.

The test file prefers executable imports: it loads the real TypeScript modules
(native type stripping on Node ≥ 22.18, otherwise a temporary **external**
transpile fallback using the `typescript` compiler; never repo-local
`node_modules`) and executes them against real frozen Character Registry
records — including the real neutral fallback with zero semantic
capabilities. One structural test comment-strips the module source and asserts
the absence of random/time/timer/listener/network/React/CSS machinery and that
every import is type-only.

Covered cases: CEO→CTO supported; regulatory→operations family supported;
neutral sender blocks; neutral receiver blocks; exact identifier preservation;
`occurred_at` exactness and non-duration; exact `canonical_basis`; no
physical-duration/travel/traversal claims; no conversation/transcript/spoken
words; no presence; no completion/dependency/authority/approval claims and
verbatim status; no mutation surface (frozen writes throw; single pure
export); reduced-motion form (incl. unsupported case); determinism; deep
freezing; no activation machinery; missing/incomplete canonical input gating.

## 10. Non-goals

No visible transfer animation, walking, pathfinding, Mission-room movement,
conversation/Board/blocker/completion animation, 3D/GLB loading, CSS, React
rendering, or backend mutation. Those come only after independent review of
this pure descriptor.

## 11. Future renderer integration

A later Phase 2D/2F renderer slice may consume this descriptor to run a
bounded transfer emphasis: it must read `supported`, `visualMode`,
`truth`, and `reducedMotion`; it must respect the limitation codes; it must
keep `semanticAnimationActive` as a renderer-owned runtime flag that this
module never sets; it must use `occurredAt` only as displayed event time.

## 12. Limitations

- Base-SHA note: the working sandbox reconstructed the upstream tree of
  `d3d11622a4a221e366995366b3e8eac9d14a3959` (verified tree-identical via the
  GitHub API: all 2145 file hashes match the branch head). Any sandbox-local
  commit SHA is NOT repository acceptance evidence; upstream should apply
  these three files on top of the branch head above.
- Strict TypeScript verification ran against a temporary external harness
  mirroring `apps/web/tsconfig.json` compilerOptions (`strict`, ES2022,
  bundler resolution) rather than the repo's full Next.js project compile,
  which requires repo `node_modules`.
- The descriptor expresses *eligibility* only; no renderer consumes it yet.


## 13. Independent repository review hardening

Before upstream integration, AIOS independently reviewed the ChatHub draft and
added a second gate that binds the resolved character identities to the
canonical handoff endpoints. Capability compatibility alone is insufficient:
a handoff-capable but wrong character must never animate another employee's
canonical event.

The complete-record guard was also aligned with this document: an empty
`status` is incomplete, and `causation_activity_id` must be either a string
or `null`.

Additional acceptance cases cover swapped sender/receiver identities, a
handoff-capable but wrong sender, and empty canonical status. Repository CI
evidence for this hardened version is recorded only after the new upstream
branch is tested; the original ChatHub 17/17 result remains evidence for the
submitted draft, not automatically for these independent corrections.
