# Admin UI Sync v2.2 Readiness Draft Guard

## Purpose

Admin UI Sync v2.2 blocks draft creation for leads that are not readiness-clear.

v2.1 blocked drafts for converted/final authority states. The remaining visible issue was that truth-blocked leads still showed `Create Controlled Draft` because they had no active application records.

## Rule

Controlled draft creation is allowed only when:

```text
readiness_stage == ready_for_human_approval
blockers == []
warnings == []
no active/final application exists
```

Blocked leads now show:

```text
Draft Blocked: Not Ready
```

## Files changed

```text
apps/api/app/routers/application_draft_control.py
apps/api/app/routers/admin_ui_sync.py
```

## Design rule

No application draft should be created before truth and document prerequisites are clear.
