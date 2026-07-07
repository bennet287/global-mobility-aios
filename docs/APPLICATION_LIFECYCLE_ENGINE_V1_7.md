# Application Lifecycle Engine v1.7

## Purpose

Application Lifecycle Engine v1.7 separates application lifecycle state from readiness state.

Before this module, the application queue continued to show a lead as `ready_for_human_approval` even after an application record had moved to `submitted`. That was not a safety issue, but it mixed two different concepts:

```text
readiness stage = whether prerequisites are satisfied
lifecycle stage = current state of the application record
```

## Current lifecycle projection

The module reads `ApplicationRecord.status` and projects it as the lifecycle stage.

Examples:

```text
draft
approved
submitted
```

This module is read-only for v1.7. It does not add new enum values or mutate application records.

## API routes

```text
GET /api/v1/applications/{application_id}/detail
GET /api/v1/applications/lifecycle-queue
GET /api/v1/applications/leads/{lead_id}/lifecycle
```

## Admin route

```text
GET /admin/application-lifecycle
```

## Design rule

Do not use readiness stage as a replacement for lifecycle stage. A submitted application may still have readiness state `ready_for_human_approval`, because readiness is about prerequisites, not lifecycle state.
