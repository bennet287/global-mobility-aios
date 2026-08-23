# L Live Organization — Acceptance Operations

**Status:** L IMPLEMENTED / ACCEPTANCE PENDING
**Technical predecessor:** `a85384e60f9275332e02971ae8a9997899393b40`
**Technical proof:** Woodpecker Pipeline #70 — 4/4 PASS
**Migration head:** `0081_capability_autonomy_evidence_evaluation_policy`

This runbook covers the remaining evidence work for L. It does not redefine AIOS authority, benchmark truth, or milestone acceptance.

## Acceptance boundary

The deterministic J→K→L integration proof is a **lineage and backend-integration proof**, not a live-model-quality proof. It proves the persisted path through WorkItem, execution attempt, AgentRun, ActionOutput, Activity, owner synthesis and replay. Real model/provider quality must be evidenced separately.

The remaining L evidence requires:

1. a first real independent professionally reviewed Austria benchmark tranche;
2. a real configured-provider success that passes the live-provider acceptance gate;
3. real provider-failure evidence;
4. a real guarded Austria L-cycle proving current official-source equivalence immediately before K.1 execution.

No provider/model identity grants organizational authority. No L acceptance evidence authorizes external action.

## Board/Cockpit authentication

The transparency and owner-synthesis routes are intentionally Board-only. The organization auth mapping resolves `admin` to `position_key=board`; operator and specialist identities are not permitted to use these Board endpoints.

The browser client sends local header-auth on loopback development by default, using role `admin` when no public local role is configured. The API intentionally keeps `AUTH_ALLOW_HEADER_ROLE=false` by default, so local development must opt in explicitly before those headers are accepted.

For a local Cockpit session, start the API on loopback only:

```powershell
$env:PYTHONPATH="apps/api"
$env:AUTH_ALLOW_HEADER_ROLE="true"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Do not enable header-role auth on an externally reachable production API. Production/non-loopback use must rely on the authenticated application session/cookie. A 401 means the request was not authenticated; a 403 under an operator/specialist session is expected governance behavior and is not a reason to weaken the Board route.

The Live Organization UI must also preserve this distinction: an authentication/access failure means persisted state is **unavailable**, not that no Austria cycle exists. Only a successful `established=false` response may be rendered as “no cycle exists yet.”

## Live-provider acceptance configuration

Before a live acceptance attempt:

```powershell
$env:LLM_PROVIDER = "deepseek" # or moonshot
$env:LLM_FALLBACK_TO_TEMPLATE = "false"
# Configure the matching provider API key and model in the normal secret/config path.
python scripts/evaluate_austria_live_provider.py --check-config
```

`live_provider_acceptance_ready` must be `true`.

Acceptance-mode invariants:

- template fallback must be disabled;
- a configured API key must be present;
- provider response identity is checked against the configured provider/model using `exact-v1` matching;
- no undocumented alias or version normalization is accepted;
- provider/model authority remains false;
- fresh retrieval is required for the complete guarded L-cycle.

The global product fallback default is intentionally not changed. The strict no-fallback rule belongs to acceptance execution so a provider failure cannot silently become a deterministic success candidate.

## Candidate discovery

```powershell
python scripts/evaluate_austria_live_provider.py --list-candidates --tenant-key default
```

Use only a root with `fresh_live_execution_candidate=true`.

## One-shot / partial-failure rule

A live evaluation consumes specialist WorkItems as durable execution proceeds. If one specialist succeeds and a later specialist fails, the successful durable output is retained as evidence and the root is no longer a clean two-specialist acceptance candidate.

Do **not** delete or rewrite that evidence to force a retry. Record/inspect the failed execution evidence, create a **new canonical J objective**, and use the new fresh root for the next complete acceptance attempt.

This preserves audit truth and avoids presenting a mixed old/new execution as one clean acceptance run.

## Guarded fresh-retrieval + live-provider execution

```powershell
python scripts/evaluate_austria_live_provider.py `
  --execute-live `
  --tenant-key default `
  --root-work-item-id <ROOT_WORK_ITEM_ID>
```

The guarded cycle first retrieves the current official sources and verifies equivalence against governed snapshots. Only then may K.1 live-provider execution run. Successful retrieval attestations are attached to the exact ActionOutput/AgentRun/execution-attempt lineage.

Exit codes:

- `0` — the complete guarded cycle is a full L reasoning-evidence candidate;
- `2` — configuration/domain/precondition rejection, or an evaluation that does not qualify as a full candidate;
- `1` — unexpected runtime/provider/retrieval failure; inspect durable execution-attempt/work-item evidence.

A successful CLI exit is evidence input, not automatic milestone sealing.

## Provider response-model policy

The current acceptance policy is deliberately conservative:

```text
configured provider == provider-reported provider
configured model    == provider-reported model
```

Provider comparison is case-insensitive; model comparison is exact. If a provider later returns a documented alias/versioned identifier, add an explicit reviewed mapping with regression coverage. Do not infer aliases from string prefixes or silently accept a different model.

## Provider-failure evidence

Acceptance also requires a real provider-failure observation. Run that evidence exercise only on a disposable fresh acceptance objective. With fallback disabled, the provider exception must not become a template success. Inspect the persisted `OrganizationExecutionAttempt` and specialist WorkItem failure state/last-error correlation after the failure.

Do not expose API keys in logs, screenshots, review records, commits, or chat transcripts.

## Professional-review handoff

The source benchmark remains immutable and `NOT_REVIEWED`. Prepare a review packet for an independent qualified professional:

```powershell
python scripts/prepare_austria_professional_review.py `
  --prepare-packet `
  --case-id at-rwr-shortage-software-di-no-job-offer-2026-01 `
  --output .test-tmp/austria-professional-review-packet.json
```

The packet includes the exact source-case fingerprint, supplied facts, source labels, official-source references, claim boundary, and allowed review decisions.

The external reviewer must return a `mobility-professional-review-v1` bundle containing genuine durable references for:

- the professional review record;
- the reviewer identity;
- the reviewer credential/standing evidence;
- a timezone-aware review timestamp;
- the exact case fingerprint;
- the independent-review assertion only when independence has actually been established.

AIOS validates those references structurally. It does **not** prove that the referenced person exists, is independent, or holds the claimed credential. Real-world verification evidence must be retained outside the compiler and linked by those references.

Validate a returned bundle with:

```powershell
python scripts/prepare_austria_professional_review.py `
  --validate-bundle <PATH_TO_REAL_REVIEW_BUNDLE.json>
```

Exit code `0` means at least one CONFIRMED/CORRECTED case is structurally promotable. It still does not replace real-world reviewer/credential verification.

Never use `test-only`, placeholder, invented or self-authored professional-review references as L acceptance evidence.

## Deferred critics — after L seal

These are valid engineering concerns but are not current acceptance blockers:

- split the Austria-heavy objective/runtime and live-organization services by responsibility before or when a second country/route arrives;
- extract a mobility-domain canonical-source resolver, reusable specialist-evidence reasoning, and route-agnostic objective-topology validation when a second vertical proves the abstraction;
- replace fallback error-string prefix classification with a typed runtime/provider error-code contract while retaining compatibility for historic persisted rows;
- move shared test builders from private imports into `conftest.py` or a dedicated test-support module;
- continue decomposing read-only runtime-quality diagnostics before adding broader cost/model/retrieval metadata.

Do not perform a broad Austria-to-generic refactor merely to satisfy aesthetics while L acceptance evidence is still incomplete.

## Local secret/proof hygiene

Local Woodpecker environment files and disposable proof artifacts are ignored by repository policy. Keep the sanitized `.env.woodpecker.example` separate from real credentials. Never commit `.env.woodpecker` or backup copies containing secrets.
