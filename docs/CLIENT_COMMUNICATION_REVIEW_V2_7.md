# Client Communication Review v2.7

## Goal

v2.7 completes the safe human review loop for generated client communication drafts.

The system still does not send email, WhatsApp, or portal messages automatically.

## Workflow

```text
Generate draft
-> Human previews draft
-> Human edits draft if needed
-> Human marks draft reviewed
-> Send/export remains blocked inside the MVP
```

## Enum-safe storage rule

`FollowUp.status` remains enum-safe:

```text
pending   -> public communication status: draft
completed -> public communication status: reviewed
cancelled -> public communication status: cancelled
```

The database does not store `draft` or `reviewed` in `FollowUp.status`.

## Added API routes

```text
GET   /api/v1/client-communications/reviewed
GET   /api/v1/client-communications/drafts/{draft_id}/preview
PATCH /api/v1/client-communications/drafts/{draft_id}
POST  /api/v1/client-communications/leads/{lead_id}/mark-all-reviewed
POST  /api/v1/client-communications/drafts/{draft_id}/send-blocked
```

Existing draft generation and mark-one-reviewed routes remain supported.

## Added admin routes

```text
GET  /admin/client-communications/reviewed
GET  /admin/client-communications/drafts/{draft_id}
POST /admin/client-communications/drafts/{draft_id}/edit
POST /admin/client-communications/leads/{lead_id}/mark-all-reviewed
```

## Safety behavior

Drafts can be edited only while their public communication status is `draft`.

Reviewed drafts are locked until a future reopen/replacement workflow is added.

The send-blocker endpoint always blocks automatic sending:

```text
draft    -> blocked because human review is required
reviewed -> blocked because automatic sending is disabled in the MVP
```

## Encoding cleanup

Communication template output is normalized to avoid common mojibake artifacts and non-ASCII dash characters in draft subjects and bodies.

## Verification

Run:

```powershell
python -m compileall apps/api/app
python scripts/check_repo_policy.py --root .
```

Expected:

```text
Repository policy check passed.
```
