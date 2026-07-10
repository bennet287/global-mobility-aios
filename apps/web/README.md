# Global Mobility AIOS Web Frontend

Modern operator command center for the Global Mobility AIOS backend.

## What this frontend does

The web app gives operators a polished SaaS-style interface for:

- CRM lead intake
- Lead pipeline visibility
- Truth Engine queue visibility
- Application readiness overview
- Document verification overview
- Controlled agent output visibility
- Safety invariant visibility
- Deep links to backend admin/operator pages

It does **not** auto-send client messages, submit applications, convert leads, or bypass human review.

## Requirements

- Node.js compatible with Next.js 15
- Backend running on `http://127.0.0.1:8000`

## Run locally

From the repository root, start the backend first:

```powershell
$env:PYTHONPATH="apps/api"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then run the frontend:

```powershell
cd apps/web
npm install
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Open:

```text
http://localhost:3000
```

## API endpoints used

```text
GET /health
GET /api/v1/crm/summary
GET /api/v1/truth/resolution-queue
GET /api/v1/applications/queue
GET /api/v1/documents/verification-queue
GET /api/v1/agent-output-reviews/dashboard
POST /api/v1/leads
```

The operational queue requests are defensive: if one queue is unavailable, the page continues to render and shows a scoped warning.

## Build

```powershell
npm run build
```
