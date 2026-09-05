# AIOS V2 Q3 — Owner Situation Room

Status: implementation candidate only. Final acceptance requires reconstruction onto the latest accepted redesign head after Q2, local frontend validation, browser review, and exact-head Woodpecker proof.

## Goal

Turn Owner Home from a general canonical overview into an attention-first Situation Room that lets the Owner understand, within a few seconds:

1. what governed records require attention,
2. which Missions have linked blockers,
3. which decision records require awareness,
4. the current Living Organization context,
5. what meaningful Activity changed recently.

The slice is presentation-only and reuses the existing `useV2OwnerOrganization()` read path. It adds no backend endpoint, no database mutation, no workflow authority and no parallel source of truth.

## Locked priority order

The visual order is deliberately:

1. **Needs attention** — current Board/authority, human-action, blocker and risk records returned by the existing Owner aggregation.
2. **Mission condition** — canonical Mission state plus blocker/decision/participant counts from the Living Organization projection.
3. **Organization condition** — compact architectural projection and roster/work context.
4. **Significant change** — recent canonical Activity records.

Decision awareness is also elevated into the five-second scan band so it is visible before deep inspection.

## Truth posture

The Situation Room must not infer that:

- a person is physically present,
- a character is located in a room,
- an employee is walking or travelling,
- a conversation or meeting occurred,
- a handoff completed,
- work completed merely because presentation state changed,
- authority changed,
- approval or rejection occurred,
- missing source data means that nothing requires attention.

Roster counts remain roster counts. Mission blocker counts come from canonical Mission projection fields. Attention counts describe returned governed records. Source failures are shown explicitly as partial/unavailable coverage.

## Five-second scan

The summary band contains only derived context from already-loaded data:

- governed attention records returned,
- Missions with one or more linked blockers,
- current decision-attention records,
- recent Activity records returned.

These are not KPIs or performance scores.

## Implementation boundaries

Expected files for this slice:

- `apps/web/components/v2/V2OwnerHomePrototype.tsx`
- `apps/web/components/v2/V2OwnerSituationRoom.tsx`
- `apps/web/components/v2/V2OwnerSituationRoom.module.css`
- `apps/web/lib/v2/owner-situation.ts`
- `apps/web/scripts/aios-v2-owner-situation-room.test.mjs`
- `apps/web/package.json`

No shell, navigation, backend, API or database changes are required.

## Responsive behavior

The Situation Room uses a wide editorial hero and attention-first two-column desktop layout. At tablet widths the priority/context panels collapse to one column. The five-second scan becomes two columns and then one column on narrow phones. The Living Organization preview remains available without forcing horizontal overflow.

## Acceptance requirements

Before merge, the final reconstructed candidate must prove:

- focused Q3 test PASS,
- full design-foundation PASS,
- request-auth PASS,
- production build and TypeScript PASS,
- compiled-auth PASS,
- desktop browser review,
- 390 × 844 mobile review,
- reduced-motion review,
- no horizontal overflow,
- repository-policy PASS,
- backend-sqlite PASS,
- frontend PASS,
- postgres-governance PASS.

The Q3 development branch may be prepared in parallel with Q2, but its final accepted commit must be reconstructed as a direct child of the accepted Q2 merge.
