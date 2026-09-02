# Technology Radar Wave E1 — Bounded SecretsPort Pilot

**Date:** 2026-08-31
**Branch:** `roadmap/global-mobility-aios-v12`
**State:** IMPLEMENTED / BOUNDED PILOT
**Production backend adoption:** NOT CLAIMED
**Milestone effect:** L remains IMPLEMENTED / ACCEPTANCE PENDING; M remains NOT STARTED

## Purpose

Technology Radar V1.3.5 permits a bounded secrets-manager pilot alongside Milestone L when a real credential lifecycle justifies the boundary. The hosted LLM provider boundary already carries real provider credentials, so this tranche introduces the AIOS-owned secret-reference seam without making a secrets backend a new truth, authority or production dependency.

Target shape:

```text
AIOS configuration
→ optional secret reference
→ SecretsPort
→ bounded secret backend
→ runtime credential injection
→ existing provider adapter
```

Permanent boundary:

```text
secret retrieval != organizational authority
secret backend != Context / Memory / Evidence
provider credential != permission to execute a material action
```

## Implemented scope

The pilot adds `app/core/secrets.py` with:

- `SecretReference` parsing;
- an AIOS-owned `SecretsPort` protocol;
- `EnvironmentSecretsPort` for explicit `env://VARIABLE_NAME` references;
- a minimal OpenBao KV-v2 reader for explicit `openbao://path#field` references;
- fail-closed resolution when a configured reference cannot be resolved;
- no in-process secret-value cache, so a subsequent resolution observes rotation or revocation rather than reusing an old value.

The LLM provider settings add optional reference fields for DeepSeek, Moonshot and Gemini. Existing direct API-key settings remain backward-compatible when no reference is configured. Explicit constructor keys remain available for deterministic tests and bounded operator injection.

## OpenBao pilot guardrails

OpenBao is deliberately not promoted to production adoption by this tranche.

The adapter:

- refuses resolution when `APP_ENV` is `production` or `prod`;
- requires an explicit bootstrap token;
- defaults to the KV mount `secret`;
- defaults to the allowed path prefix `aios/nonprod/`;
- rejects a referenced path outside that prefix before network egress;
- supports an optional Vault/OpenBao namespace header;
- reads KV-v2 through `/v1/<mount>/data/<path>`;
- does not log or persist returned secret values;
- translates retrieval/response failures into a bounded `SecretResolutionError`.

A configured reference is authoritative. Resolution failure does not silently fall back to a plaintext credential, because that would hide rotation/revocation/configuration failure.

## Focused proof

Local focused proof executed against the implemented boundary:

```text
python -m pytest -q tests/test_secrets.py tests/test_llm_secret_references.py
10 passed
```

The tests cover:

- reference parsing;
- current environment-value resolution;
- fail-closed configured-reference behavior;
- non-production OpenBao guard;
- allowed-path enforcement;
- KV-v2 URL and namespace/header behavior;
- rotation visibility across repeated resolution;
- revocation/HTTP failure visibility;
- LLM credential-reference integration;
- explicit provider-key bypass for deterministic injection.

## CI truth

GitHub Actions attached to source head `b83fa84432da14d72be1014ce8021eb794154680` reported workflow-level failure, but inspection showed zero executed steps for all four Production Proof jobs. Runner identifiers were absent. This is runner/infrastructure startup evidence, not repository-test failure and not an exact-head PASS.

Forward production proof remains the self-hosted Woodpecker path already defined by the roadmap. Final exact-current-head proof remains pending after this documentation reconciliation.

## Promotion gates

Production promotion of an OpenBao-class backend remains demand-gated and requires a separate tranche that proves, at minimum:

1. a concrete deployment/credential lifecycle need;
2. bootstrap identity/token handling that does not create a second unmanaged secret;
3. least-privilege policy and tenant/runtime scope;
4. operational rotation and revocation against a real backend;
5. outage/failover and recovery behavior;
6. telemetry that exposes failure without exposing secret values;
7. deployment/runbook proof;
8. exact-current-head acceptance evidence.

This pilot does not seal L, begin M, increase autonomy, authorize provider egress, authorize external action, or make OpenBao canonical AIOS truth.
