# Global Mobility AIOS — Operator UI Design System v7.3

## Purpose

v7.3 makes the operator workspace feel smooth, seamless, and premium while adding the first native Next.js page so users no longer leave the new UI to view a lead.

## What changed

### Frontend architecture

- Extracted reusable components into `apps/web/components/`:
  - `WorkspaceShell`, `Sidebar`, `Topbar`
  - `SectionTitle`, `EmptyState`, `InlineNotice`, `DataNotice`
  - `StatusBadge`, `LeadIdentity`, `MetricPill`, `ActionCard`
  - `TruthClaimCard`, `QueueStages`, `CaseTable`, `Skeleton`
- Extracted data and form hooks into `apps/web/hooks/`:
  - `useBackendStatus` — polls `/health` every 15 seconds
  - `useWorkspaceData` — fetches all dashboard queues
  - `useLeadForm` — manages lead creation form
- Added shared utilities in `apps/web/lib/utils.ts`:
  - `titleCase`, `compactNumber`, `statusTone`

### Motion and perceived performance

- Added CSS fade-up entrance animations for panels with staggered delays.
- Added shimmer skeletons for metrics, pipeline rows, and priority actions during initial load.
- Added button spinner state for the refresh action.
- Added reduced-motion media query support.

### Navigation

- Sidebar links are now Next.js `Link` components.
- Active section state is highlighted on the dashboard.
- Brand lockup uses a custom SVG mark instead of a text badge.
- Added `app/icon.svg` as the application icon.

### First native page: lead detail

- New route: `app/leads/[id]/page.tsx`.
- Fetches `GET /api/v1/leads/{id}/detail` for full case data.
- Displays:
  - Lead header with avatar, status, and metadata
  - Case summary (email, phone, source, notes)
  - Documents list
  - Truth Engine claims
  - Controlled agent outputs
  - Applications / authority pipeline
  - Workflow timeline (runs + follow-ups)
- Dashboard pipeline rows are now clickable links to the lead detail page.

### API additions

- `lib/api.ts` gained:
  - `getLead(id)`
  - `getLeadDetail(id)`
  - `getLeadSync(id)`
  - Extended types: `LeadDetail`, `LeadSyncPayload`, `Profile`, `SourceReference`, `HumanReview`, `WorkflowRun`, `AgentRun`, `FollowUp`, `ApplicationRecord`

### Design-system polish

- Refined active navigation state.
- Added clickable table row hover state.
- Added lead detail page styles: hero header, two-column grids, timeline.
- Added back-link helper and responsive rules for the detail page.

## Scope

Changed frontend only:

- `apps/web/app/globals.css`
- `apps/web/app/page.tsx`
- `apps/web/app/layout.tsx` (metadata unchanged)
- `apps/web/app/icon.svg`
- `apps/web/app/leads/[id]/page.tsx`
- `apps/web/lib/api.ts`
- `apps/web/lib/utils.ts`
- `apps/web/components/*`
- `apps/web/hooks/*`
- `.gitignore` (added `*.tsbuildinfo`)

## Safety posture

Unchanged:

- Client messages remain drafts.
- Applications are never auto-submitted.
- Human review gates sensitive actions.
- Visa/job claims require traceability.
- No backend workflow logic changed.

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

## Next possible steps

- `v7.4` could migrate agent output review into Next.js.
- `v7.5` could migrate communication drafts.
- `v7.6` could add a command palette or keyboard shortcuts for power users.
