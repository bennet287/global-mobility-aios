# Operator UI Design System v7.0

## Purpose

This milestone introduces a modern operator-facing frontend for Global Mobility AIOS without changing backend workflow logic, database models, safety controls, or release tags.

The goal is to make the MVP feel like a serious SaaS/operator command center while preserving the project rule that all sensitive actions remain human-reviewed.

## Scope

Changed frontend-only files:

```text
apps/web/app/layout.tsx
apps/web/app/page.tsx
apps/web/app/globals.css
apps/web/lib/api.ts
apps/web/README.md
```

Added documentation:

```text
docs/OPERATOR_UI_DESIGN_SYSTEM_V7_0.md
```

## Design Direction

The new UI is a dark, high-contrast command center with:

- Persistent operator sidebar
- Sticky top bar
- Hero panel explaining the system posture
- KPI cards for CRM and truth-review status
- Lead intake form
- Recent lead pipeline list
- Application readiness stage cards
- Document verification queue
- Agent output review summary
- Truth resolution queue
- Recent truth claim cards with confidence indicators
- Safety invariant panel
- Deep links to existing FastAPI admin/operator pages

## Safety Boundaries Preserved

This milestone does not add autonomous execution. The following invariants remain true:

```text
auto_send = disabled
automatic_submission = disabled
automatic_lead_conversion = disabled
human_review_required = true
```

The frontend provides visibility and navigation only. It does not auto-send messages, auto-submit applications, bypass review queues, or convert leads automatically.

## API Usage

The frontend now uses the existing backend endpoints more accurately:

```text
GET /health
GET /api/v1/crm/summary
GET /api/v1/truth/resolution-queue
GET /api/v1/applications/queue
GET /api/v1/documents/verification-queue
GET /api/v1/agent-output-reviews/dashboard
POST /api/v1/leads
```

Optional operational queues are loaded defensively. If a queue endpoint is unavailable, the UI shows a scoped warning instead of breaking the entire dashboard.

## Local Run

Backend:

```powershell
cd "C:\Users\Bennet Allryn\Downloads\global-mobility-aios\global-mobility-aios"
$env:PYTHONPATH="apps/api"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd "C:\Users\Bennet Allryn\Downloads\global-mobility-aios\global-mobility-aios\apps\web"
npm install
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Open:

```text
http://localhost:3000
```

## Verification

Recommended backend gate from repository root:

```powershell
python scripts/check_local_quality.py
```

Recommended frontend gate from `apps/web`:

```powershell
npm run build
```

## Next UI Milestones

### v7.1 Operator Dashboard Redesign

Polish the FastAPI `/admin/v2` page or connect the Next.js dashboard more deeply to lead detail APIs.

### v7.2 Lead Detail Experience

Create a dedicated lead detail screen with:

- Timeline
- Document checklist
- Truth evidence
- Agent outputs
- Communication drafts
- Application lifecycle

### v7.3 Demo Landing Page

Create an investor/demo landing screen that explains:

- What the system automates
- What remains human-controlled
- Current demo metrics
- Start-demo workflow steps

### v7.4 Customer Portal

Separate customer-facing portal from operator/admin screens.
