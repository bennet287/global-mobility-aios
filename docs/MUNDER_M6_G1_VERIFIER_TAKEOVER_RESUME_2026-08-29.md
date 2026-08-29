# Munder M6 — G.1 Verifier Takeover / Resume

Date: 2026-08-29

Status: IMPLEMENTED / EXACT-HEAD PROOF PENDING

## Purpose

PR #28 proved the fresh queued G.1 verifier runtime envelope locally at technical
candidate `b21e916ee9a6dcea0ca07b50cb9f6099791402fa`. This follow-up closes the
remaining interrupted-worker boundary without changing G.1 truth or authority.

## Atomic persistence correction

The original envelope let G.1 commit its independent-verification Activity before the
runtime wrapper proved terminal fence ownership. A worker superseded during provider
latency could therefore reach durable G.1 lineage before its later
`agent_completed` check failed.

Fenced runtime calls now use staged verification persistence:

1. G.1 revalidates readiness, governed context and runtime identity after provider
   latency;
2. G.1 stages the verification Activity without committing;
3. the runtime supervisor must remain healthy;
4. the caller re-resolves the current fenced session;
5. `agent_completed`, attempt completion, WorkItem completion and the staged
   verification Activity commit in one transaction;
6. a takeover/terminal-event sequence race can have only one committed winner;
7. failure finalization rolls back all uncommitted verification output first.

Direct non-runtime G.1 callers retain immediate commit for compatibility.

## Runtime identity v2

`eligibility-g1-verifier-runtime-session.v2` binds:

- verification WorkItem id and verifier position;
- bounded attempt number;
- verifier ContextBundle hash and runtime-binding hash;
- proposer trace id and proposer Activity id;
- proposer intent fingerprint;
- Decision Readiness fingerprint;
- verification idempotency fingerprint.

A takeover request must reproduce that exact token from current governed inputs. It
cannot substitute another proposal, readiness result, runtime binding or logical
verification identity.

## Takeover contract

`resume_fenced_independent_eligibility_verification_with_takeover`:

1. requires the exact running verification WorkItem and exact running/latest attempt;
2. requires the caller-observed execution token and previous fence token;
3. requires exactly one canonical running attempt;
4. revalidates the complete current G.1 execution basis;
5. reconstructs and matches the v2 execution token before any claim;
6. refuses a fresh lease;
7. appends a new durable runtime-session claim for an expired lease;
8. requires the new fence to advance;
9. re-executes G.1 on the same attempt under supervised renewal;
10. commits verification lineage and completion only under the new current fence.

No new `OrganizationExecutionAttempt` is created.

## Authority boundary

Takeover is technical recovery only. It does not:

- grant authority or autonomy;
- assert human, employee, model or provider presence;
- relax blind-review or independent provider/model/group requirements;
- change Evidence, VerifiedRule, pathway, case or readiness truth;
- satisfy the verification floor by itself;
- authorize canonical eligibility mutation or external action.

## Deliberate boundary

This slice resumes only an interrupted still-running attempt with an expired lease.
Retry after a durably finalized failed attempt remains separate. No migration, new
runtime-state table or parallel WorkItem state model is introduced.

M6 remains **PARTIAL**. After exact-head proof, the next bounded M6 target is one
additional real organization-worker adoption.

## Required exact-head proof

1. focused SQLite takeover success reuses one attempt and advances the fence;
2. fresh-session and logical-identity drift paths fail before claim/provider egress;
3. a superseded worker cannot persist independent-verification Activity;
4. existing fresh G.1 success/failure, G.4 and H.2.2 contracts remain green;
5. real PostgreSQL proves renewal and completion under the takeover fence;
6. full SQLite and workflow-equivalent PostgreSQL regression remain green;
7. repository/release/dependency/diff gates and final clean remote identity pass.
