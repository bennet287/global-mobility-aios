# AIOS V2 — Q12 Accessibility & Semantic Hardening

## Status

Implementation candidate. Acceptance requires exact-head local/browser proof and the normal repository CI lanes before merge.

## Accepted base

Q12 is built directly from the accepted Q11 merge:

`6b1078b2e0299487c889aeaefca91dbc77df6ff6`

Branch:

`design/aios-v2-q12-accessibility`

## Scope

Q12 is a presentation/accessibility hardening slice. It does not alter canonical AIOS data, authority, permissions, source coverage, Mission/Evidence/Decision/History state, presence, location, movement, collaboration, completion, approval, freshness, validity, health, urgency, or success semantics.

Implemented corrections:

- Align the shared Search / Command trigger's accessible name with its visible label.
- Keep Owner navigation native and programmatically current through `aria-current="page"`.
- Replace forced `listbox` / `option` roles on command-palette navigation links with native navigation/link semantics.
- Promote the four Owner Home situation-room section titles from visual-only `<strong>` elements to structural `h2` headings while retaining one page `h1`.
- Give the Living Organization situation panel an explicit labelled structural relationship.
- Guarantee a visible `:focus-visible` indicator for native interactive elements across the V2 root.
- Preserve the phone Owner rail's 48px targets and add scroll padding so focus outlines are not clipped at the horizontal viewport edge.
- Preserve forced-colors and reduced-motion behavior.
- Add dedicated static Q12 accessibility regressions and focused Chromium coverage.
- Advance the Q11 responsive browser assertion to the corrected Search / Command accessible name.

## Command palette semantic decision

Command results are destinations, not selectable values in a combobox/listbox model. The existing entries are Next.js links and navigation remains the action. Q12 therefore keeps the links native instead of overriding them with `role="option"` and `aria-selected`.

Arrow-key focus movement remains a convenience inside the dialog, but it does not redefine link semantics.

## Heading decision

Owner Home now follows:

- `h1` — route/page identity
- `h2` — Needs attention
- `h2` — Mission condition
- `h2` — Organization condition
- `h2` — Significant change

Metric labels, source posture, row titles, badges and decorative labels remain non-heading text.

## Truth boundary

Accessibility interaction is presentation-only. Keyboard focus, navigation focus, dialogs, viewport changes, theme selection, reduced-motion preferences and semantic markup never mutate canonical organizational state.

No new backend fetch or write path is introduced by Q12.

## Required acceptance

At minimum:

- `npm run test:accessibility`
- `npm run test:responsive`
- `npm run test:design-foundation`
- `npm run test:request-auth`
- `npm run build`
- `npm run test:compiled-auth`
- `npx playwright test tests/aios-v2-accessibility.spec.ts --project=chromium`
- existing Q11 responsive Chromium regression
- desktop and phone review in Light and Dark
- keyboard-only Search / Command and Guided Experience review
- exact-head repository-policy, backend-sqlite, frontend and postgres-governance CI proof

Do not claim Q12 complete until those checks pass on the exact candidate head.
