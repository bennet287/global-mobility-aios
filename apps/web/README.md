# Global Mobility AIOS Web

Next.js dashboard for CRM operations and Truth Review Queue actions.

## Features

1. KPI cards for CRM and truth queue status.
2. Lead intake form connected to `POST /api/v1/leads`.
3. Recent leads table from `GET /api/v1/dashboard/summary`.
4. Truth queue list and filters from `GET /api/v1/truth/queue`.
5. Approve/reject reviewer actions using `POST /api/v1/truth/queue/{audit_id}/resolve`.

## Local Run

From `apps/web`:

```bash
npm install
npm run dev
```

Set API base URL with `NEXT_PUBLIC_API_BASE_URL` if your API is not on `http://localhost:8000`.
