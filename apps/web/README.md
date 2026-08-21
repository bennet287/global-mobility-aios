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

- **Node.js 24** — the accepted/proven frontend runtime; the repository-root `.nvmrc` declares this major
- **Next.js 16.3.1** / React 19.0.8 as locked by `package-lock.json`
- Backend running on `http://127.0.0.1:8000`

Node 20 is not the accepted frontend proof runtime because the request/auth contract uses Node's TypeScript strip-types support. Verify `node --version` before installing or testing frontend dependencies.

## Run locally

From the repository root, start the backend first:

```powershell
$env:PYTHONPATH="apps/api"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then run the frontend with the committed lockfile:

```powershell
cd apps/web
npm ci
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Use `npm install` only when intentionally changing dependency declarations/lock state; ordinary setup and proof should use `npm ci`.

Open:

```text
http://localhost:3000
```

## Frontend proof commands

The accepted V12 Production Proof lane runs the following under Node 24:

```powershell
npm ci
npm audit --audit-level=high
npm run test:design-foundation
npm run test:request-auth
npx tsc --noEmit
npm run build
npm run test:compiled-auth
```

There is not yet a Playwright/browser E2E suite; that remains a later production-proof improvement.

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
