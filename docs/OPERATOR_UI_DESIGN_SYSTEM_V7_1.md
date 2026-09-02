# Global Mobility AIOS — Operator UI Design System v7.1

## Purpose

v7.1 replaces the first stylized dashboard with a calmer, timeless operator workspace. The goal is to make the product feel like a professional internal agency system rather than a decorative AI demo.

## Design direction

- Neutral editorial layout instead of heavy glassmorphism.
- Warm off-white background, white cards, soft borders, restrained green accent.
- Full-width workspace that better uses desktop screens.
- Smaller, denser metric cards and queue panels.
- Reduced marketing hero copy.
- Operational content first: pipeline, truth review, documents, agents, controls.
- Offline-tolerant UX: the frontend still renders cleanly when the backend is not running.

## Safety posture

The UI continues to expose the same safety controls:

- Client messages remain drafts.
- Applications are never submitted automatically.
- Operator approval is required.
- Visa and job claims use traceable sources.

No backend workflow logic, database model, sending behavior, submission behavior, or human-review control is changed by this milestone.

## Hydration fix

`apps/web/app/layout.tsx` uses `suppressHydrationWarning` on both `html` and `body`. This prevents browser-extension-injected body attributes from triggering a Next.js hydration overlay during development.

## Backend connectivity behavior

The dashboard now treats backend data as progressively loaded. If FastAPI is offline, the page shows an offline banner and empty-state cards instead of throwing a full command-center load failure.

## Changed files

```text
apps/web/app/layout.tsx
apps/web/app/page.tsx
apps/web/app/globals.css
apps/web/lib/api.ts
docs/OPERATOR_UI_DESIGN_SYSTEM_V7_1.md
```

## Verification

```powershell
cd apps/web
npm run build
```

Then from repository root:

```powershell
python scripts/check_local_quality.py
```
