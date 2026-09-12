# AIOS V2 Phase 13G.1H — Owner Visual + Live-Behavior Proof

Date: 2026-09-11
Programme: Phase 13G.1 Architectural World Redesign
Status: ACTIVE — proof package implemented; acceptance remains pending actual browser artifacts and explicit Owner review.

## Purpose

13G.1H is the acceptance barrier between implementation and closure. Green CI is necessary but is not sufficient. The Living HQ must visibly demonstrate that the redesigned architectural world behaves as a live representation of governed AIOS state on desktop and phone.

## Required proof

The proof must establish all of the following in one bounded package:

1. A desktop browser view reads as one continuous modern office world rather than a set of room cards.
2. A phone browser view preserves the same office-world identity without horizontal page overflow or reverting to detached room cards.
3. Miniature employees are visibly integrated with their department/workstation context.
4. A deterministic canonical employee-state transition changes the corresponding miniature presentation without page reload.
5. The transition is caused by the refreshed Living Organization scene, not by an independent frontend simulation state machine.
6. A canonical blocker causes the affected employee/department attention state and the canonical event-reaction layer to change.
7. Empty or absent canonical records do not create handoff, conversation, Board, blocker, or work reactions.
8. `presentationOnly=true`, `presenceClaimed=false`, and `locomotionAllowed=false` remain preserved.
9. The permanent source contract remains visible and true: `Selection changes view focus only; it cannot mutate AIOS.`
10. Decorative ambience remains subordinate to performance and truth; it cannot invent work, presence, occupancy, authority, conversation, handoff, completion, or Board action.

## Implemented deterministic browser proof

`apps/web/e2e/tests/living-hq-live-behavior-proof.spec.ts`

The proof uses a fixed canonical root WorkItem and serves two successive governed scene projections for the same root:

```text
Scene A
mobility_operations_lead.semantic_state = working
blockers = []

        ↓ automatic scene refresh; no page reload

Scene B
mobility_operations_lead.semantic_state = blocked
blockers = [canonical blocker]
```

Required visible consequence:

```text
working
→ data-live-semantic-state=working
→ data-character-state=focused_work

blocked
→ data-live-semantic-state=blocked
→ data-character-state=blocked_wait
→ department data-zone-blocked=1
→ canonical event-reaction blocker count=1
```

The reverse transition is also exercised on the phone viewport so the proof is not dependent on a desktop-only composition.

## Required artifacts

The proof package saves:

- `living-hq-owner-proof-working.png`
- `living-hq-owner-proof-blocked.png`
- `living-hq-owner-proof-phone.png`

These screenshots are evidence inputs only. They do not self-approve the redesign.

## Owner visual acceptance gate

Do not mark Phase 13G.1H complete solely because tests pass. The Owner must inspect the actual screenshots/browser result and confirm that the five-second first impression now reads as:

- premium contemporary headquarters;
- one connected workplace;
- believable Operations / Technology / Evidence / Board spatial identities;
- miniature workforce integrated into the environment;
- state changes that visibly correspond to real canonical organization changes;
- no regression to square room cards, generic creature tiles, pixel tower, neon pods, or admin-dashboard composition.

If the visual result still fails that standard, Phase 13G.1 remains open even when all automated proofs are green.

## Performance acceptance

Performance and organizational results outrank cinematic polish. The proof must not require high-frequency polling, game physics, continuous expensive effects, or duplicate canonical state stores. Scene refresh remains bounded, non-overlapping, visibility-aware, and read-only. Render detail and ambient motion must degrade before canonical employee/state representation is removed.

## Closure condition

13G.1H may be marked PASS only after:

```text
exact-head build/type proof
+ desktop visible proof
+ phone visible proof
+ deterministic live state-transition proof
+ truth-boundary proof
+ performance budget preserved
+ explicit Owner visual acceptance
```

Until then, PR #147 remains a Draft candidate and Phase 13G.2 final reconciliation must not close the programme.
