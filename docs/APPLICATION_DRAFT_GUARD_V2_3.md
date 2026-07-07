# Application Draft Guard v2.3

## Purpose

Application Draft Guard v2.3 hardens the legacy application draft endpoint:

```text
POST /api/v1/applications/leads/{lead_id}/draft
```

Admin UI Sync v2.2 and the controlled-draft endpoint already block drafting when truth/document readiness is not clear. v2.3 applies the same rule to the older legacy endpoint so API callers cannot bypass the guard.

## Rule

Draft creation through the legacy endpoint is allowed only when:

```text
readiness_stage == ready_for_human_approval
blockers == []
warnings == []
no active/final application exists
```

If the lead is blocked by truth, has missing documents, or has warnings, the endpoint returns:

```text
409 Conflict
blocker: readiness_not_clear
```

## Design rule

No application draft should be created before truth and document prerequisites are clear, regardless of whether the request comes from Admin v2, the controlled-draft endpoint, or the legacy draft endpoint.
