# Application Engine v1.6 — Application Count Matching

## Purpose

Application draft creation was working, but `/api/v1/applications/queue` and readiness output still showed `applications: 0`.

## Root cause

SQLite stores SQLAlchemy UUID values as 32-character hex strings, while API routes and JSON responses use hyphenated UUID strings or `uuid.UUID` objects.

## Fix

- Added `_uuid_match_key()`.
- Updated `_records_for_lead()` to count `ApplicationRecord` rows by normalized UUID match.
- Kept `blocked_truth_rejected` as a computed readiness stage only.
- Kept persisted application workflow status as `draft`, `approved`, or `submitted`.

## Expected behavior

For a lead with created drafts:

```text
counts.applications >= 1
stage = blocked_truth_rejected
can_approve = false
can_submit = false
```
