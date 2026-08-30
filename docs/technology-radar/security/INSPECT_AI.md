# Inspect AI — AIOS Evaluation-Lab Research

**State:** ASSESS / R2
**Reviewed pin:** `UKGovernmentBEIS/inspect_ai@56c9cae65844c87479b10e212a93b91e1a17c351`
**License:** MIT
**Primary source:** `https://inspect.aisi.org.uk/`

## Fit

Inspect AI is an open-source evaluation framework developed by the UK AI Security Institute and Meridian Labs. It provides datasets, agents, tools, scorers, evaluation sets, logs, MCP/custom tools, tool approval and multiple sandbox backends.

Best proposed role:

```text
AIOS Evaluation Laboratory
→ deterministic task datasets
→ governed target adapters
→ tools/sandboxes/approval
→ scorers
→ attributed evaluation artifacts
```

It is well suited to authority-bypass, source-grounding, tool-selection, provider-comparison and longer-horizon agent evaluations.

## Risks

- powerful tools and sandboxes create their own credential/network boundary;
- evaluation logs may contain prompts, outputs or sensitive fixture data;
- scorer/model judgment can be fallible and non-deterministic;
- framework task/agent state must not become AIOS organization truth;
- installing broad optional integrations creates supply-chain and isolation burden.

## R3 test

Run synthetic allow/deny and source-injection tasks with no production access. Require exact dataset/tool/scorer versions, deterministic structural scorers where possible, tool-approval denial tests, sandbox/network declarations and artifact hashes.

## Decision

Leading Evaluation Lab foundation candidate. No package or production integration is approved by V1.3.6.
