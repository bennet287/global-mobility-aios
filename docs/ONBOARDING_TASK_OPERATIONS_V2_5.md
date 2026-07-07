# Onboarding Task Operations v2.5

## Purpose

Onboarding Task Operations v2.5 turns the post-approval onboarding module from a task generator into an operator workflow.

v2.4 created six onboarding follow-ups. v2.5 adds task-level views, filters, and admin completion buttons.

## New API routes

```text
GET /api/v1/post-approval-onboarding/tasks
GET /api/v1/post-approval-onboarding/tasks/{follow_up_id}
```

The existing completion route remains:

```text
POST /api/v1/post-approval-onboarding/follow-ups/{follow_up_id}/complete
```

## New admin routes

```text
GET  /admin/post-approval-onboarding/tasks
GET  /admin/post-approval-onboarding/leads/{lead_id}
POST /admin/post-approval-onboarding/follow-ups/{follow_up_id}/complete
```

## Filters

The task list supports:

```text
?status=pending
?status=completed
```

## Design rule

Post-approval onboarding tasks are stored as `FollowUp` records and identified by the structured prefix:

```text
[post_approval_onboarding:v2.4]
```

This keeps v2.5 migration-free while providing usable task operations.
