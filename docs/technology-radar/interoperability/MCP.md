# Model Context Protocol 2026-07-28 — AIOS Research

**State:** ASSESS / R2
**Reviewed pin:** `modelcontextprotocol/modelcontextprotocol@ca4ab3027f7c844cd3039c956438d72e8253f7f5`
**Specification:** `2026-07-28`
**Repository-license metadata:** `NOASSERTION`; explicit license review required before adoption
**Primary sources:** `https://modelcontextprotocol.io/specification/2026-07-28`, `https://blog.modelcontextprotocol.io/posts/2026-07-28/`

## Observed protocol direction

The 2026-07-28 specification introduces a request/response stateless core, self-describing requests, `Mcp-Method`/`Mcp-Name` routing headers, Multi Round-Trip Requests, cacheable deterministic list responses, authorization hardening, Tasks and a formal extensions model.

These features improve gateway deployment but do not solve AIOS authority. A routable tool name, server request for input or user-facing elicitation is not permission to perform a material action.

## AIOS boundary

```text
AI employee/runtime
→ capability request
→ trusted server/catalog resolution
→ argument/data-egress classification
→ Authority Engine
→ Command Gateway
→ McpGatewayPort
→ MCP server/tool
→ typed provider receipt
→ AIOS ActionOutput/Activity where applicable
```

MCP protocol/session/task state never becomes canonical WorkItem, Evidence, authority or Activity state.

## Catalog trust

Tool/resource/prompt descriptors are untrusted external claims. Discovery must record server identity, endpoint, transport/spec version, credential reference, TLS/trust policy, catalog hash, tool schema hash, review status, data classification, allowed tenants/purposes and expiry.

Catalog changes invalidate prior approval until policy says the change is non-material. Name equality is insufficient: a tool is identified by trusted server identity plus exact schema/version/hash.

## Per-call controls

Every call requires:

- authenticated AIOS principal and persistent position;
- current capability and skill assignment where relevant;
- server/tool allowlist and exact schema validation;
- tenant, purpose, resource and data-egress scope;
- argument normalization and prompt/tool-injection checks;
- authority/autonomy/risk/materiality decision;
- credential reference resolved outside context/prompt/memory;
- idempotency key and external-effect classification;
- timeout, budget, retry and circuit policy;
- result schema validation and durable receipt.

MRTR `input_required` is a protocol continuation, not Human Owner approval. A human response becomes authorization only through an AIOS-owned authenticated approval contract bound to the exact command fingerprint.

## Threats for R3

- tool poisoning or tool shadowing after catalog approval;
- server identity substitution and endpoint redirection;
- confused deputy through broad user/service credentials;
- malicious schema descriptions or result content;
- argument injection and over-broad data egress;
- replay of material calls;
- approval confusion through elicitation/MRTR;
- cached stale catalogs;
- cross-tenant tool/resource leakage;
- unavailable gateway/server causing fail-open fallback.

## R3 reference test

A malicious test server advertises `submit_application` beside an allowed source-retrieval tool. Discovery may record both. Retrieval may execute when its exact gates pass. Submission must be denied before any provider call, even if the model, skill metadata or MCP server says it is allowed.

## Decision

MCP is strategically relevant and may proceed to an isolated gateway contract lab after L. No SDK, server, credential or production tool is adopted by V1.3.6.
