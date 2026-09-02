# Controlled Coverage Baseline Capture v10.18

## Purpose

This increment connects independently approved Phase 10B evidence batches to the
existing controlled source-retrieval system. It queues official-source monitors
only after both the jurisdiction immigration-rule assessment and primary
source certification have been approved.

Baseline capture stores evidence. It does not publish a verified rule, certify a
jurisdiction as coverage-ready, or make a global-coverage claim.

## Review gate

A batch item is eligible only when all of the following are true:

- the linked immigration-rule assessment is `approved`;
- the linked primary authority/source certification is `approved`;
- the certification still points to the exact onboarded authority and source;
- the official source is active;
- the source monitor exists and is active or recoverable from an earlier error;
- no immutable source snapshot has already been captured;
- no retrieval run is already queued or running.

Pending, rejected, mismatched, inactive, or incomplete evidence remains visible
but cannot be queued.

## Controlled retrieval lifecycle

`POST /api/v1/global-intelligence/registry/coverage-batches/{batch_id}/capture-baselines`
creates durable `queued` retrieval-run rows before dispatching Celery work. The
worker receives the exact retrieval-run ID, updates that record in place, and
preserves existing SSRF, HTTPS, domain allowlist, redirect, timeout, response-size,
content-type, and parser controls.

The first successful source capture becomes an immutable `baseline` snapshot.
Subsequent runs continue through the existing `unchanged`, `changed`, or
`not_modified` lifecycle. A changed snapshot can create a pending regulatory
change, but no rule is published without the existing classification, review,
and publication gates.

## Idempotency and failure behavior

- Repeating the queue action does not duplicate a queued or running monitor.
- A source with an existing snapshot is reported as `baseline_ready` and is not
  queued again by the baseline workflow.
- Failed retrievals can be deliberately requeued after the operator reviews the
  error posture.
- Broker dispatch failures mark the pre-created retrieval run as `queue_failed`.
- Duplicate Celery delivery returns an already completed run instead of
  capturing duplicate evidence.

## Interfaces

- `GET /api/v1/global-intelligence/registry/coverage-batches/{batch_id}/baseline-status`
- `POST /api/v1/global-intelligence/registry/coverage-batches/{batch_id}/capture-baselines`
- Coverage workspace: per-batch baseline counts and **Capture approved baselines**
- PowerShell: `scripts/Capture-ApprovedCoverageBaselines.ps1`

## Audit and safety

Queueing writes `coverage_baseline_capture_queued` with the evidence batch,
monitor IDs, and durable retrieval-run IDs. Existing retrieval completion and
failure audit events remain authoritative for each monitor run.

The response explicitly states:

- no verified rule is published;
- no global coverage claim is created;
- approved assessment and certification are required.

## Database and verification

No new table is required. The database head remains
`0031_global_coverage_source_onboarding` because the workflow reuses the existing
source monitor, retrieval run, immutable snapshot, regulatory change, and audit
models.

Automated coverage verifies independent-review gating, idempotent queueing,
durable run creation, exact run reuse by the worker, baseline snapshot capture,
API behavior, and the no-rule/no-coverage boundary.
