# AIOS V2 — Phase 2 Foundation Slice

**Status:** IMPLEMENTED / PROOF PENDING  
**Branch:** `design/aios-v2-foundation`  
**Parent:** AIOS V2 governing baseline `57bca2615a59c03186420ee1d8ad2892aac00205`

## Scope

This first production-code slice deliberately does **not** replace the existing Cockpit.

It creates an isolated V2 preview at:

`/cockpit/v2`

## Added

### V2 scoped style foundation
- `apps/web/styles/v2/tokens.css`
- `apps/web/styles/v2/motion.css`
- `apps/web/styles/v2/foundation.css`

All V2 tokens are scoped to `.aios-v2-root` so legacy pages remain untouched.

### V2 shell
- `apps/web/components/v2/V2Shell.tsx`

Implements the selected Owner mental model:
- Home
- Organization
- Missions
- Intelligence
- Evidence
- Decisions
- History

Only Home is enabled in this foundation slice; unimplemented V2 destinations are visibly disabled rather than linked to fake routes.

### Owner Home foundation
- `apps/web/components/v2/V2OwnerHomePrototype.tsx`

Establishes:
- executive hierarchy
- restrained material language
- Organization viewport slot
- Owner attention slot
- backend-health grounding
- explicit refusal to invent canonical Mission/employee/authority data

### Isolated route
- `apps/web/app/cockpit/v2/layout.tsx`
- `apps/web/app/cockpit/v2/page.tsx`

### Test
- `apps/web/scripts/aios-v2-foundation.test.mjs`

The existing `test:design-foundation` script now includes the V2 contract test.

## Truth posture

This slice intentionally does not claim:
- active Mission counts
- active employee counts
- employee presence
- handoffs
- Evidence state
- Owner authority feed

until those canonical data sources are connected.

## Accessibility

Foundation includes:
- semantic navigation
- `aria-current`
- disabled destination semantics
- labeled command placeholder
- real main landmark
- reduced-motion tokens
- responsive layout

## Next implementation slice

After this foundation proves green:

1. connect canonical Owner attention data
2. create V2 domain read adapter
3. connect canonical Mission summary
4. mount governed Living Organization viewport
5. preserve structured fallback
6. begin architectural HQ blockout
