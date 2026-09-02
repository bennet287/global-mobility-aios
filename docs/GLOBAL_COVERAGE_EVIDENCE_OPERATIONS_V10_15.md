# Global Coverage Evidence Operations v10.15

## Purpose

This increment accelerates the remaining Phase 10B evidence work without weakening
coverage or review gates. It adds a prioritized worklist and immutable batch
submission for jurisdiction immigration-rule assessments and primary
immigration-authority/source certifications.

It does **not** claim that global coverage is complete. Registry inclusion,
batch submission, and pending proposals remain distinct from reviewed evidence.

## Coverage worklist

`GET /api/v1/global-intelligence/registry/coverage-worklist` returns required
jurisdictions ordered by their most important unresolved evidence gap. Operators
can filter by region and by one of these gap types:

- immigration-rule assessment;
- reviewed primary authority;
- reviewed primary source;
- authority onboarding;
- official-source onboarding;
- fresh active monitor;
- active human-published verified rule.

The worklist is derived from the active immutable registry release and current
coverage ledger. It does not create or modify evidence.

## Controlled evidence batches

`POST /api/v1/global-intelligence/registry/coverage-batches` accepts up to 50
unique alpha-2 jurisdictions. Each row may propose:

- an immigration-rule relationship assessment;
- a primary authority/source certification;
- or both.

A batch is atomic. If any jurisdiction, parent relationship, authority, source,
HTTPS requirement, domain relationship, or pending-review constraint fails,
none of the batch is persisted.

The normalized release-and-item payload is SHA-256 keyed. Resubmitting the same
evidence package returns the original batch and creates no duplicate proposals.
Display names, notes, and submitter identity do not change the evidence identity.

## Review boundary

Batch submission creates only `pending_review` records. Existing individual
review endpoints remain the only way to approve or reject each assessment and
certification. The authenticated reviewer must be different from the proposer.

Batch progress is derived from linked review records and reports pending,
approved, rejected, superseded, and missing states. The immutable batch itself is
not rewritten when reviews occur.

## Data model

Migration `0030_global_coverage_evidence_batches` adds:

- `jurisdiction_coverage_evidence_batches` for release, payload hash, submitter,
  notes, counts, and immutable submission time;
- `jurisdiction_coverage_evidence_batch_items` for exact jurisdiction, registry
  entry, linked assessment/certification IDs, row number, and row payload hash.

## API and workspace

- `GET /api/v1/global-intelligence/registry/coverage-worklist`
- `GET /api/v1/global-intelligence/registry/coverage-batches`
- `GET /api/v1/global-intelligence/registry/coverage-batches/{batch_id}`
- `POST /api/v1/global-intelligence/registry/coverage-batches`

The `/global-intelligence` Coverage tab now includes gap/region filters, a
prioritized work queue, controlled JSON evidence packages, immutable batch
history, and live review progress.

## Audit and safety

Every new batch writes `jurisdiction_coverage_evidence_batch_submitted` with the
active registry release, payload key, and operation counts. The batch stores no
claim that a jurisdiction is covered.

`global_coverage_claim_ready` remains false until all existing Phase 10B release
gates pass for every required jurisdiction.

## Remaining Phase 10B work

The software workflow is ready for controlled scale, but evidence collection and
independent human review still must be completed for every required jurisdiction:

1. approve an independent, inherited, shared/coordinated, or not-applicable
   immigration-rule relationship;
2. approve at least one primary immigration authority and official source;
3. maintain a fresh monitor and at least one active human-published verified rule.
