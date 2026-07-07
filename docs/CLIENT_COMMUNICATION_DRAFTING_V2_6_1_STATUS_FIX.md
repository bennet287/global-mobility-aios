# Client Communication Drafting v2.6.1 Status Fix

## Problem

`FollowUp.status` is enum-backed and allows:

```text
pending
scheduled
completed
cancelled
```

Client Communication Drafting v2.6 incorrectly tried to store:

```text
draft
reviewed
```

This caused SQLAlchemy enum lookup errors when the API refreshed or queried `FollowUp` records.

## Fix

v2.6.1 stores communication drafts using enum-safe `FollowUp.status` values:

```text
pending   -> public communication state: draft
completed -> public communication state: reviewed
cancelled -> public communication state: cancelled
```

The API and admin UI still display user-facing states:

```text
draft
reviewed
cancelled
```

## Repair

The safe repair script scans SQLite databases in the repository and repairs records with the client communication draft prefix:

```sql
draft    -> pending
reviewed -> completed
```

## Files changed

```text
apps/api/app/routers/client_communications.py
docs/CLIENT_COMMUNICATION_DRAFTING_V2_6_1_STATUS_FIX.md
```
