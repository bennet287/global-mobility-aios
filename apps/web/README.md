# Global Mobility AIOS Web Frontend

Repository-owned Next.js interface for the Global Mobility AIOS owner, operator,
Living HQ and mobility-portal surfaces.

## What this frontend does

The web app exposes governed, truth-preserving interfaces for:

- Owner Home, Organization, Missions, Intelligence, Evidence, Decisions and History;
- Living HQ and its structured analytical fallback;
- operator cockpit, pathways, queues and controlled-agent review;
- mobility portal overview, documents, messages and timeline;
- specialist workspaces and bounded administrative surfaces.

It does **not** auto-send client messages, submit applications, convert leads, or bypass human review.

## Requirements

- **Node.js 24** — the accepted/proven frontend runtime; the repository-root `.nvmrc` declares this major
- **Next.js 16.3.4** / React 19.0.8 as locked by `package-lock.json`
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

The Playwright suite under `e2e/tests/` supplies the accepted browser, visual,
accessibility, responsive, structured-fallback, Living HQ and mobility-portal
contracts. The root V12 Production Proof workflow runs the governed browser
subset on the exact candidate head; use the workflow definition as the command
authority rather than maintaining a second list here.

## Representative API endpoints

```text
GET /health
GET /api/v1/crm/summary
GET /api/v1/truth/resolution-queue
GET /api/v1/applications/queue
GET /api/v1/documents/verification-queue
GET /api/v1/agent-output-reviews/dashboard
POST /api/v1/leads
```

This is a representative legacy/core subset, not a complete route inventory.
The request clients and their tests are the source of truth for current frontend
API consumption. Operational reads fail closed or degrade explicitly: a missing
source is shown as unavailable and is never converted into invented canonical
state.

## Build

```powershell
npm run build
```
