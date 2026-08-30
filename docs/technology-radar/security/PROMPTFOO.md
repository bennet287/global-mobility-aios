# Promptfoo — AIOS Red Team Research

**State:** EXISTING PILOT COMPLETE / TRIAL-ELIGIBLE; RED TEAM LAB ROLE R2
**Reviewed pin:** `promptfoo/promptfoo@90fa399b941364363f57288fbf305b6d6aaff7ed`
**License:** MIT
**Primary sources:** `https://www.promptfoo.dev/docs/red-team/quickstart/`, `https://www.promptfoo.dev/docs/red-team/agents/`, `https://www.promptfoo.dev/docs/red-team/mcp-security-testing/`

## Fit

Promptfoo is the leading current application-oriented adversarial test candidate. Its red-team tooling targets models, RAG applications and agents, and its documentation includes agent and MCP security testing.

Best proposed role:

```text
authorized AIOS test target
← Promptfoo attack/test generation
→ raw result
→ AIOS reproduction + triage
→ reviewed SecurityFinding
```

Priority test families include prompt/source/tool injection, authority escalation, excessive agency, data/secret leakage, tenant/object/function authorization failures, malicious MCP catalogs/results and replay abuse.

## Risks

- attack generation can be non-deterministic and create false positives/negatives;
- target adapters may expose credentials, private prompts or broad endpoints;
- generated attack content is untrusted and may be dual-use;
- a tool-generated pass/fail is not an accepted AIOS finding;
- hosted or plugin features require separate data-egress and dependency review.

## R3 security-lab test

Target a disposable AIOS-like Command Gateway fixture. Prove denied authority escalation, malicious tool advertisement, fixture-only data handling, exact config/version capture, reproducible findings, false-positive disposition and complete cleanup.

## Decision

Retain trial eligibility and prioritize the isolated Red Team Lab role. Historical pilot status does not authorize production targeting or automatic finding acceptance.
