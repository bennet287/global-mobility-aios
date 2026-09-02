# Global Mobility AIOS — Supplemental Austria AI Domain Corroboration

**Status:** IMPLEMENTED TOOLING / NO CORROBORATION RESULT CLAIMED
**Milestone:** L — Live Organization
**Evidence class:** supplemental AI domain-quality evidence only
**Professional-review effect:** NONE

## Purpose

The existing K.1/L live-provider outputs proved safe organizational execution, provenance, provider failure behavior, owner synthesis and replay. They did not independently classify all three Austria benchmark cases from substantive official-source text.

This supplemental harness therefore performs a separate, deliberately blind domain-review exercise:

```text
immutable Austria benchmark facts
+ fresh official-source content
+ independent provider A
+ independent provider B
(+ independent provider C where configured)
        ↓
blind case classifications
        ↓
post-response comparison against source-curated labels
        ↓
multi-model corroboration report
```

The models never receive the benchmark `expected` labels or benchmark rationale in their prompt.

## Non-substitution boundary

This tool does **not** change:

```text
professional_review_status = NOT_REVIEWED
```

and may never produce `PROFESSIONALLY_REVIEWED` provenance.

Even a unanimous matching result means only:

```text
independent multi-model AI corroboration
```

It does not mean:

```text
professional legal review
Austrian authority determination
legal advice
permission for autonomous client-facing action
```

The existing professional-review compiler remains unchanged and is the only repository path that can compile genuine professional-review evidence.

## Safety properties

The harness:

- loads the immutable three-case Austria benchmark;
- generates a blind packet containing case facts and source fingerprints but no expected labels/rationale;
- retrieves each benchmark government source fresh using the existing source-retrieval security boundary;
- provides models with deterministic relevant excerpts and full-content/excerpt hashes;
- treats source text as untrusted reference material, not instructions;
- requires every model to set `final_authority_decision=false`;
- requires source-grounded refs from the supplied official sources;
- records exact configured vs response provider/model identity;
- compares model labels against benchmark labels only **after** model output is returned;
- requires at least two distinct qualifying providers for a multi-model corroboration candidate;
- preserves all disagreement/failure instead of converting it to success;
- writes the review bundle outside the repository by default;
- performs no canonical case mutation, no external filing, no client communication and no authority expansion.

The fresh retrieval in this harness is evaluation input. It is not a replacement for the canonical L fresh-retrieval attestation workflow and does not mutate governed source authority.

## Prepare the blind packet

From the repository root:

```powershell
python scripts/evaluate_austria_ai_domain_review.py `
  --prepare-packet `
  --output D:\austria-ai-domain-review-blind-packet.json
```

Expected properties:

```text
case_count                        3
expected_labels_excluded          true
professional_review_status_effect NONE
```

## Run independent providers

The current provider abstraction supports:

```text
gemini
deepseek
moonshot
```

Configure API keys/models through the existing local environment. Do not paste or commit credentials.

Example with Gemini + DeepSeek:

```powershell
$env:LLM_FALLBACK_TO_TEMPLATE="false"

python scripts/evaluate_austria_ai_domain_review.py `
  --run `
  --providers gemini,deepseek `
  --output D:\austria-ai-domain-review-results.json
```

Example with all three configured providers:

```powershell
python scripts/evaluate_austria_ai_domain_review.py `
  --run `
  --providers gemini,deepseek,moonshot `
  --output D:\austria-ai-domain-review-results.json
```

A single provider may be run for diagnosis, but cannot create a multi-model corroboration candidate:

```powershell
python scripts/evaluate_austria_ai_domain_review.py `
  --run `
  --providers gemini `
  --output D:\austria-ai-domain-review-gemini.json
```

The single-provider command is expected to exit with code `2` even when that provider succeeds, because the corroboration floor is two distinct qualifying providers.

## Candidate semantics

Exit code `0` requires all of the following:

1. at least two distinct provider runs are structurally valid;
2. configured provider/model identity exactly matches returned provider/model identity;
3. every qualifying model reviews all three cases exactly once;
4. every qualifying model keeps `final_authority_decision=false`;
5. each model cites only supplied official source refs;
6. qualifying models are unanimous case-by-case;
7. every qualifying model's classification and pathway match the immutable source-curated benchmark labels.

Exit code `2` means the run is not a multi-model corroboration candidate, including disagreement, provider/configuration failure, malformed output, model identity mismatch, insufficient provider count or benchmark mismatch.

## Current L relationship

This tooling directly addresses the observed K.1 quality gap without rewriting historical evidence:

```text
K.1/L runtime safety evidence        ACCEPTED
supplemental AI domain corroboration TOOL IMPLEMENTED / RESULT PENDING
professional Austria review          PENDING
final exact-current-head proof       PENDING
L overall                            IMPLEMENTED / ACCEPTANCE PENDING
M                                    NOT STARTED
```

A future policy decision may use a clean multi-model corroboration result as evidence to decide whether external professional validation is a production/legal-correctness gate rather than an engineering-progress gate. That policy decision must be explicit; this tool does not make it automatically.
