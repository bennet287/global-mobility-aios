# Global Mobility AIOS — Operator UI Design System v7.2

## Purpose

v7.2 refines the frontend from a clean dashboard into a premium operator workspace. The interface prioritizes daily work: active cases, priority actions, verification state, and governance controls.

## Design direction

- Timeless, calm, low-noise SaaS layout.
- Less artificial/glass styling; more operational clarity.
- Lead pipeline becomes the primary work area.
- Priority queue sits beside the pipeline for daily operator focus.
- Verification, documents, agent outputs, and governance remain visible without dominating the page.
- No autonomous actions are introduced.

## Scope

Changed frontend only:

- `apps/web/app/page.tsx`
- `apps/web/app/globals.css`
- `apps/web/lib/api.ts` keeps operator headers for protected local API calls.
- `apps/web/app/layout.tsx` keeps hydration suppression for extension-injected browser attributes.

## Safety posture

Unchanged:

- Client messages remain drafts.
- Applications are never auto-submitted.
- Human review gates sensitive actions.
- Visa/job claims require traceability.

## Verification

Run from project root:

```powershell
python scripts/check_local_quality.py
```

Run from frontend folder:

```powershell
cd apps\web
npm run build
```

