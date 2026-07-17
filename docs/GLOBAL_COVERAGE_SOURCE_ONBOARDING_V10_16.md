# Global Coverage Source Onboarding v10.16

## Purpose

Phase 10B already had a prioritized worklist and immutable evidence batches, but an operator
still had to create each regulatory authority, official source, and source monitor separately
before proposing primary-source certification. v10.16 closes that operational gap without
changing the evidence or review standard.

## Atomic onboarding package

A coverage batch item may now include `source_onboarding`. The active registry release supplies
the canonical jurisdiction code, name, type, parent, and region. The caller supplies only the
authority, official source, monitor, and certification evidence fields.

For each valid row the service transactionally:

1. creates or updates the registry-bound regulatory authority;
2. creates or updates the HTTPS official source;
3. creates or updates the allowlisted source monitor;
4. creates a pending primary immigration authority/source certification proposal;
5. records the linked IDs and canonical payload hash on the immutable batch item.

If any row fails, the complete batch rolls back, including all authority, source, monitor,
certification, item, and audit rows created by that transaction.

## Security and ownership controls

The existing controlled source-onboarding rules remain active:

- HTTPS is mandatory;
- credentials in URLs are rejected;
- only the standard HTTPS port is accepted;
- allowed domains must be explicit hostnames without wildcards, schemes, paths, or ports;
- the source hostname must be covered by the allowlist;
- the source domain must be declared by the authority;
- an existing source cannot be silently reassigned to another jurisdiction or authority;
- parser profiles and redirect limits remain validated.

## Human review boundary

Source onboarding is an administrative operation, not certification. Every newly onboarded
source receives a `pending_review` certification proposal. A different authenticated reviewer
must approve it. The batch submitter cannot self-approve, and the global coverage release gate
remains blocked until every required jurisdiction also has fresh monitoring, a published
verified rule, and an approved immigration-rule relationship.

## API and workspace

`POST /api/v1/global-intelligence/registry/coverage-batches` accepts `source_onboarding` inside
each item. The Global Intelligence Coverage workspace includes a ready-to-edit JSON template,
onboarding counts, and immutable batch progress.

## Migration

Migration `0031_global_coverage_source_onboarding` adds the source-onboarding count and linked
authority, source, and monitor provenance columns to the existing coverage batch ledger.
