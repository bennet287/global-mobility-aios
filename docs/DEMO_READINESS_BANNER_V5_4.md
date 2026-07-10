# Demo Readiness Banner v5.4

## Goal

v5.4 adds a compact readiness banner to the local demo/admin experience so the operator can see demo readiness immediately.

## Added

- Demo readiness fields in `GET /api/v1/admin-demo/navigation`.
- Readiness banner on `GET /admin/demo`.
- Readiness banner on `GET /admin/v2`.
- Tests for the demo hub, navigation JSON, and Admin v2 banner.

## Banner Contents

- Demo readiness status.
- Demo lead count.
- Demo controlled-agent run count.
- Demo client draft count.
- Auto-send safety state.
- Quality gate reminder.

Example:

```text
Demo ready | 4 leads | 6 agent runs | 6 drafts | auto-send disabled | quality gate: local check required
```

## Readiness Logic

The banner reports `ready` when:

- Exactly 4 demo leads exist.
- At least 5 client communication drafts exist.
- Required agent statuses are present:
  - `approved`
  - `completed`
  - `converted`
  - `rejected`
- Required audit actions are present:
  - `controlled_agent_run`
  - `agent_output_approved`
  - `agent_output_rejected`
  - `agent_output_converted_to_client_draft`
  - `client_draft_reviewed`

## Safety

This patch is display-only. It does not run agents, approve outputs, convert drafts, send messages, reset data, or change database schema.

## Verification

Expected local quality gate after this patch:

```text
54 passed, 1 warning
Local quality gate passed.
```

The remaining warning is the existing external Starlette `TestClient` warning.
