# L Live Organization — Acceptance Operations

**Status:** L IMPLEMENTED / ACCEPTANCE PENDING
**Technical predecessor:** `1037f020adfb8e8b99849050bd75cf1035ed2e96`
**Technical proof:** Woodpecker Pipeline #72 — 4/4 PASS
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

Supported acceptance providers are `deepseek`, `moonshot`, and `gemini`. They share the same acceptance boundary: hosted-model execution is technical capability only; it does not grant organizational authority or external-action permission.

Configure exactly one provider in the normal local secret/config path, disable deterministic fallback, and check readiness before consuming a fresh objective.

DeepSeek example:

```powershell
$env:LLM_PROVIDER = "deepseek"
$env:DEEPSEEK_API_KEY = "<local-secret>"
$env:DEEPSEEK_MODEL = "deepseek-chat"
$env:LLM_FALLBACK_TO_TEMPLATE = "false"
python scripts/evaluate_austria_live_provider.py --check-config
```

Moonshot example:

```powershell
$env:LLM_PROVIDER = "moonshot"
$env:MOONSHOT_API_KEY = "<local-secret>"
$env:MOONSHOT_MODEL = "kimi-k1-5"
$env:LLM_FALLBACK_TO_TEMPLATE = "false"
python scripts/evaluate_austria_live_provider.py --check-config
```

Gemini example:

```powershell
$env:LLM_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "<local-secret>"
$env:GEMINI_MODEL = "gemini-3.7-flash"
$env:GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
$env:LLM_FALLBACK_TO_TEMPLATE = "false"
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

Gemini uses Google's OpenAI-compatible chat-completions boundary through the existing AIOS-owned provider abstraction. AIOS does not infer whether a Gemini request was billed on a free or paid tier from the model response; Gemini `estimated_cost_usd` remains `null` unless a future billing-aware evidence source can establish actual cost. Billing assumptions are not acceptance evidence.

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

The Gemini integration does not create a special alias exception. Until a documented mapping is explicitly reviewed and tested, a provider-reported value other than the configured `GEMINI_MODEL` fails the live-provider acceptance candidate exactly as it does for the other providers.

## Provider-failure evidence

Acceptance also requires a real provider-failure observation. Run that evidence exercise only on a disposable fresh acceptance objective. With fallback disabled, the provider exception must not become a template success. Inspect the persisted `OrganizationExecutionAttempt` and specialist WorkItem failure state/last-error correlation after the failure.

Do not expose API keys in logs, screenshots, review records, commits, or chat transcripts.

## Professional-review handoff

The source benchmark remains immutable and `NOT_REVIEWED`. The first real tranche should review all three current Austria benchmark cases together. Prepare the immutable reviewer packet outside the repository:

```powershell
python scripts/prepare_austria_professional_review.py `
  --prepare-packet `
  --output D:\austria-professional-review-packet.json
```

The packet includes each exact source-case fingerprint, supplied facts, source labels, official-source references, claim boundary, and allowed review decisions.

Prepare a separate fail-closed return template for the reviewer:

```powershell
python scripts/prepare_austria_professional_review.py `
  --prepare-return-template `
  --output D:\austria-professional-review-return.json
```

The return template pre-binds only AIOS-owned source identity fields: benchmark/schema identity, each `source_case_id`, and each exact `source_case_fingerprint`. Reviewer-owned fields intentionally remain `null`, including:

- review/batch identifiers;
- `created_at` and `reviewed_at`;
- professional review record reference;
- reviewer identity reference;
- reviewer credential/standing reference;
- `independent_review`;
- review decision;
- reviewed labels;
- reviewer notes.

An untouched return template is intentionally invalid and must not be treated as professional evidence.

The external reviewer must complete the `mobility-professional-review-v1` return bundle with genuine durable references for:

- the professional review record;
- the reviewer identity;
- the reviewer credential/standing evidence;
- timezone-aware creation/review timestamps;
- the exact case fingerprint already bound by AIOS;
- the independent-review assertion only when independence has actually been established.

Decision semantics:

- `CONFIRMED` — retain the source labels exactly and return them as `reviewed_labels`;
- `CORRECTED` — return the complete corrected `reviewed_labels`; at least one labeled dimension must differ;
- `DISPUTED` — held outside the promoted professional denominator;
- `NEEDS_MORE_FACTS` — held outside the promoted professional denominator.

AIOS validates those references structurally. It does **not** prove that the referenced person exists, is independent, or holds the claimed credential. Real-world verification evidence must be retained outside the compiler and linked by those references.

Validate a returned bundle with:

```powershell
python scripts/prepare_austria_professional_review.py `
  --validate-bundle D:\austria-professional-review-return.json
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
