# Agent2Agent Protocol 1.0 — AIOS Research

**State:** RESEARCH / R2
**Reviewed pin:** `a2aproject/A2A@f63dbb48271940ca5bd421f87e27e4d6ec002795`
**Latest released specification observed:** `1.0.0`
**License:** Apache-2.0
**Primary sources:** `https://a2a-protocol.org/latest/specification/`, `https://a2a-protocol.org/latest/blog/2026/08/27/a-new-chapter-for-a2a-joining-the-agentic-ai-foundation/`

## Observed protocol direction

A2A 1.0 defines Agent Cards, AgentSkill capability descriptions, authenticated interfaces, messages, tasks, artifacts, streaming/push updates, version negotiation and authorization responsibilities. On 2026-08-27 A2A announced acceptance as a Growth Stage project of the Agentic AI Foundation.

An AgentSkill is a capability claim made by an external agent. It is never an AIOS skill assignment, authority grant, professional credential or trust decision.

## AIOS boundary

```text
external agent / Agent Card
→ A2A Gateway quarantine + identity/trust verification
→ safe capability projection
→ authority + data-sharing policy
→ canonical AIOS WorkItem proposal
→ Human/Board/Command Gateway gate where required
→ A2A message/task
→ external task/artifact receipt
→ validation/reconciliation
→ AIOS ActionOutput/Activity where applicable
```

A2A task state remains external execution state. AIOS owns the canonical WorkItem and decides whether an artifact is accepted, rejected or requires review.

## Agent Card handling

Store a reviewed external-agent registration containing:

- provider/agent identity and trust reference;
- exact card hash/signature verification result;
- supported interfaces and protocol versions;
- security schemes and credential reference;
- declared capabilities/skills as untrusted metadata;
- permitted tenant/purpose/data classification;
- allowed task/artifact schemas;
- rate, budget, timeout and expiry;
- revocation and incident status.

Inbound card changes require re-review when identity, endpoint, security, interfaces, skills or schemas change.

## Inbound requests

An external A2A request authenticates the remote agent but does not authorize it. The gateway validates tenant, purpose, schema, data classification, replay/idempotency and trust policy, then creates only a proposed governed WorkItem or rejects the request. It cannot directly mutate canonical case/Evidence/authority state.

## Outbound delegation

Outbound delegation requires an AIOS WorkItem, exact scope, allowed external agent/interface, minimized ContextBundle projection, authority decision, external-effect classification, budget/deadline and reconciliation plan. The external agent cannot widen scope, delegate further or claim completion beyond the accepted artifact contract.

## Threats for R3

- agent impersonation or unsigned/stale card substitution;
- skill inflation leading to inferred permission;
- version downgrade and interface confusion;
- task/artifact state treated as canonical truth;
- remote scope expansion or undeclared delegation;
- cross-tenant message/artifact leakage;
- push callback SSRF/credential abuse;
- duplicate messages/tasks and replay;
- malicious artifact/source content;
- unavailable remote agent leaving ambiguous local state.

## R3 reference test

An external agent advertises `immigration_application_submission`. AIOS may expose it as an untrusted discovery candidate. It may not create a skill assignment, permission or submission command. Without explicit AIOS authority and retained Human Owner approval, no external task is created.

## Decision

A2A remains research-only until a concrete independent-agent collaboration need exists. The internal Skill Registry may later publish a safe AgentSkill subset; inbound Agent Cards never populate the canonical registry automatically.
