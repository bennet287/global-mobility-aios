# V1.3 I.1 — Capability Autonomy Profile Foundation

**Date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** implementation contract for the first I.1 slice; acceptance remains open until code, migrations, tests, PostgreSQL concurrency proof, and Production Proof agree.

## Purpose

I.1 introduces canonical, capability-specific autonomy truth before any Dynamic Autonomy Manager exists. The contract answers:

> For this tenant, organization position, capability, context scope, and evidence policy version: what autonomy level has the Human Board established, what ceiling and risk/authority conditions bound it, which immutable profile did it supersede, and which canonical Activities support the decision?

This slice does **not** promote or downgrade agents automatically. It does not create authority. It does not derive permission from scores, model output, provider identity, runtime identity, conversation, or self-evaluation.

## Canonical truth

The foundation uses two append-only companion records:

1. `CapabilityAutonomyProfile`
   - tenant, position, capability, and context-scoped identity;
   - explicit `A0`–`A5` autonomy level;
   - Board-declared autonomy ceiling;
   - independent authority requirement and risk ceiling;
   - immutable sequence and `supersedes_profile_id` lineage;
   - evidence-policy version;
   - Board governance Activity lineage;
   - deterministic idempotency key and record fingerprint.
2. `CapabilityAutonomyEvidence`
   - immutable links from a profile to canonical `OrganizationActivity` rows;
   - source Activity fingerprint captured at decision time;
   - deterministic evidence ordering and evidence-record fingerprint.

A profile row is never rewritten to say that it was superseded. Current/superseded state is derived from the append-only chain. This preserves historical truth and prevents a later profile from mutating the earlier decision record.

## Governance path

The only write primitive in this slice is an HTTP-independent Board command. It requires:

- an authenticated internal **human** actor;
- `admin` role;
- persistent `position_key == "board"`;
- a live `OrganizationPosition` for the target position;
- explicit expected profile sequence for an existing chain;
- target autonomy at or below the Board ceiling;
- canonical evidence Activity IDs owned by the same tenant.

The command stages an authority-class governance Activity and the profile/evidence rows in one transaction. Exact idempotent replay reuses the canonical profile. Divergent reuse of the same idempotency key fails closed.

There is deliberately **no POST/PUT/PATCH/DELETE autonomy route**. A normal API request therefore cannot choose or promote its autonomy level.

## Concurrency contract

Competing profile writes are protected by all of the following:

- expected-profile-sequence precondition;
- PostgreSQL row lock on the current profile when available;
- unique `(tenant, position, capability, context, profile_sequence)` constraint;
- unique `(tenant, supersedes_profile_id)` constraint so one profile revision cannot fork into two children;
- transaction rollback on persistence conflict.

The first-profile race is covered by the scope/sequence uniqueness rule; later races are additionally covered by the unique supersession edge and expected sequence.

## Transparency contract

The existing Board-only `/api/v1/organization/transparency` facade is extended with a read-only autonomy profile view. It exposes canonical profile/evidence lineage and derived current/superseded state without returning raw Activity payload JSON.

The read model fails closed if the profile sequence/supersession chain is inconsistent or if an evidence Activity fingerprint no longer matches the immutable fingerprint captured by the profile evidence row.

## Explicit non-goals

This slice does not implement:

- automatic autonomy promotion;
- automatic dynamic downgrade;
- capability scoring as permission;
- an organization-wide autonomy score;
- agent self-grading or self-promotion;
- provider/model-specific autonomy grants;
- replacement of the Command Gateway or constitutional authority checks;
- weakening of professional, legal, human-review, or Board-reserved floors.

## Acceptance boundary

Landing this foundation can establish the canonical I.1 truth layer, deterministic evidence lineage, Board ceiling enforcement, idempotency and concurrency controls, and a Board read model. I.1 remains open until the repository’s required SQLite/PostgreSQL test lanes and full Production Proof pass on the exact candidate commit and the roadmap/changelog are updated to that verified truth.
