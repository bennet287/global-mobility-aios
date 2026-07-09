# Demo Navigation Polish v5.3

## Goal

v5.3 adds a compact local demo command center so the operator can move through the validated demo path without hunting across browser tabs.

## Added

- `GET /admin/demo`
- `GET /api/v1/admin-demo/navigation`
- Demo hub link in the shared Admin v2 navigation.
- Demo hub link in Admin v2 quick links.
- Tests for the HTML hub and JSON navigation payload.

## Demo Hub Includes

- Current demo state counts.
- Primary demo flow links:
  - Admin v2
  - Agent Console
  - Agent Review Queue
  - Communication Drafts
  - Audit Logs
- Supporting workspace links.
- Local demo commands.
- Safety rules.

## Safety Rules

- Controlled agents create internal operator outputs only.
- Agent output conversion creates reviewable client communication drafts only.
- Client communication drafts require human review.
- No automatic email, WhatsApp, portal message, application submission, or lead conversion is performed.

## Verification

Expected local quality gate after this patch:

```text
53 passed, 1 warning
Local quality gate passed.
```

The remaining warning is the existing external Starlette `TestClient` warning.
