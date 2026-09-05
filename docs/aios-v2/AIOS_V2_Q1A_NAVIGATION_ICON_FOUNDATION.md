# AIOS V2 — Q1A Navigation & Icon Foundation

## Purpose

This is the first bounded extraction from the preserved Qwen master-plan recovery snapshot. It intentionally does **not** import the 40-file recovery commit wholesale.

The slice upgrades the accepted AIOS V2 shell navigation from single-letter placeholders to a shared SVG icon system and moves the Owner navigation model into an explicit read-only contract.

## Accepted base

`58bb40f9986997b576f0a2ca0558f1183c0c00ab` — merged Phase 2O Canonical Handoff Visualization V1.

## Scope

- shared `V2Icon` SVG icon vocabulary for the seven Owner domains plus shell controls
- explicit `ownerNavigation` contract
- Home and Organization remain the only enabled V2 destinations in this slice
- Missions, Intelligence, Evidence, Decisions and History remain visible but disabled until their own accepted route slices exist
- navigation commands expose only routes that already exist in the accepted repository
- shell consumes the shared navigation/icon model instead of defining ad-hoc one-letter glyphs
- no backend authority, canonical mutation or workflow action is introduced

## Why future destinations stay disabled

The preserved Qwen recovery snapshot contains candidate implementations for several future V2 routes, but they have not yet been independently reviewed, rebased and accepted. Navigation must not make those candidate workspaces appear production-ready before their bounded slices pass validation.

## Files

- `apps/web/components/v2/V2Icon.tsx`
- `apps/web/components/v2/V2Shell.tsx`
- `apps/web/lib/v2/navigation.ts`
- `apps/web/scripts/aios-v2-navigation.test.mjs`
- `apps/web/package.json`
- `docs/aios-v2/AIOS_V2_Q1A_NAVIGATION_ICON_FOUNDATION.md`

## Acceptance

Before merge:

1. exactly one commit ahead / zero behind the accepted redesign base;
2. design-foundation test wiring includes both the accepted Phase 2O handoff test and `aios-v2-navigation.test.mjs`;
3. enabled Owner navigation routes resolve to real accepted pages;
4. disabled future destinations have no href;
5. command destinations resolve to existing pages only;
6. request-auth, production build and compiled-auth remain green;
7. Woodpecker repository-policy, backend-sqlite, frontend and postgres-governance all pass on the exact head;
8. browser review confirms desktop and mobile navigation remains understandable and keyboard-focusable.

## Recovery posture

Source ideas were salvaged from `qwen/aios-v2-masterplan-recovery` (`7cef1e0b860a9961866c716ae13a536d80da4681`), but this slice is independently reconstructed on the accepted redesign base. The recovery branch remains an archive, not a merge candidate.
