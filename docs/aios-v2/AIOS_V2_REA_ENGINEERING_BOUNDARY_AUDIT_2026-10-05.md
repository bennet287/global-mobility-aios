# REA engineering-provider boundary audit

Date: 2026-10-05. Decision scope: source and duplicate/authority assessment, not provider admission, installation, an executable adapter or a live engineering qualification.

## Decision

REA is a justified Phase 21 interoperability candidate for evidence-backed software investigation and reconstruction specifications. Its first executable integration requires the concrete Phase 17 tool-invocation boundary below. Keep REA invocation and active capabilities disabled until that boundary is implemented and independently verified. An agent must not register, launch or install REA for itself, select an arbitrary provider, or acquire the entire catalog by virtue of a skill label.

REA can support investigation; it does not recover original source or certify the correctness of an AIOS reconstruction. AIOS retains work assignment, actor authority, artifact authorization, resource ceilings, evidence review, implementation tests and promotion. No existing phase seal, deployment gate, paid-call authority or GRSI promotion changes through this audit.

The user requested this assessment ahead of the next production probe. The representative compiled agent-journey work remains separate and unmerged; the accepted Phase 22 checkpoint is still organization-task correlation. This document is a dated domain decision, not a second current-state or acceptance ledger.

## Verified source identities

AIOS audit base: `fe82e22e2e1e443bb2dc9c30c0ef67bec773121b` on `design/aios-v2-complete-redesign`. Refresh GitHub before dependent implementation.

| Item | Observation at audit time | Limit |
| --- | --- | --- |
| Upstream source | [`morluto/rea`](https://github.com/morluto/rea/tree/4c8dc39f439b5283b077c6aa47f262714d7c4bbd), commit `4c8dc39f439b5283b077c6aa47f262714d7c4bbd` | Source snapshot; no installed server or published tarball verified |
| User fork | `bennet287/reverse-engineering-` main at `405732a7f55e3033c29533b18f7d8313dbd28570` | Upstream is now 27 commits ahead, zero behind; the earlier identical-head observation is stale |
| Package/server | `rea-agents@3.2.1`; server `io.github.morluto/rea`, version `3.2.1`, npm/stdio metadata points upstream | Same version string does not imply same executable build |
| Declared catalog | 122 MCP tools, 75 primary CLI commands, six MCP prompts; 14 provider declarations | Counts do not establish platform availability, entitlement or installed capability |
| Declared combined catalog SHA-256 | `a87e48bc626cb4361f494c074e71852304bfedee17fbba89976d32bb6244f230` | Current source metadata; replaces the earlier `39c2c4c55c1197e5a8c05c829bf9ba024d2508ed3a59b672f95c5ed19c016a5c` observation, not a runtime attestation |
| Declared tools/provider digests | tools `1a32398486b1e65f50a1a81de2d8867e6a4c296c165bf9994e53034b466c41b4`; providers `c5a88a49990fafc8244972ee8ff543fc19995eb79db960da55f6a311e15340d1` | Catalog/schema/provider-declaration fingerprints are distinct from package/build integrity |
| License | Repository declares MIT | This license does not grant rights over investigation targets, their assets or decompiled output |

Source owners: upstream `package.json`, `server.json`, `docs/product-catalog.json`, `src/catalogIdentity.ts`, `src/generatedMcpToolCatalog.ts` and `LICENSE` at the pinned commit. The catalog identity hashes canonical contract descriptions, schemas, effects, CLI names and prompts; it is not an executable-code hash or publisher authentication. The generated SDK schema projection is not interchangeable with the direct Zod projection used by `catalogIdentity.ts`: a separately reconstructed projection can yield a different digest. This audit reads declarations and source; it does not claim to have reproduced the installed runtime catalog.

Do not mix fork source with an upstream npm binary and call them the same build. Future admission must bind the exact source/build or package artifact integrity, server/protocol/catalog observation, provider identity/version and approved transport. A modified fork needs its own build provenance. Unknown provider versions and mismatches remain blockers. A provider's self-reported digest cannot authorize itself.

## Capabilities and effects

REA exposes native investigation through Hopper/Ghidra, static managed inspection, artifact and JavaScript/Electron analysis, passive observation, comparisons and evidence/reconstruction workflows. Platform/provider support varies: the inspected Ghidra contract specifies 12.1.4 with a full 64-bit JDK 21, Linux x64 or macOS x64/arm64; Windows x64 is experimental native x86-64 PE P0 with separate exclusions. Managed PE inspection and native decompilation are different execution boundaries; static call/value-flow inference is not an observed runtime trace.

| Class | Example | AIOS boundary |
| --- | --- | --- |
| Staged static inspection | `inspect_managed_artifact` | Exact authorized artifact, bounded parsing, isolated worker, no arbitrary host path |
| Existing analysis reads | procedure/xref/byte queries | Same admitted provider/session/target identity; no ambient cross-work access |
| Native analysis/import | Ghidra/Hopper decompilation | Provider process startup, private projects/caches and parser exposure; target need not execute for this to have side effects |
| Passive observation | browser/CDP or process observation | Separate process/session scope and capture/privacy/network policy; passive is not absence of network access or sensitive content |
| Evidence persistence | export/import bundle | Explicit write/read roots, bounded content and retention; not a read-only filesystem operation |
| Active execution | capture scenarios, process launch, controlled replay | Separate higher-risk admission and work/human authorization; excluded from the first adapter |

Upstream `src/contracts/toolEffects.ts` distinguishes target/session mutation, filesystem writes, process launches, network access and UI changes. MCP annotations are hints derived from these effects, not AIOS permission grants. In particular, apparently static tools can mutate the REA evidence session and carry `readOnlyHint=false`; do not authorize tools through that flag alone.

Upstream `SECURITY.md` and README explicitly describe providers running with the operating-system user's permissions. Authenticated local bridges, temporary Ghidra projects and resource settings are not a security sandbox. Extracted JavaScript replay has a distinct Linux isolation contract; that does not confer sandboxing on other providers, observers or process capture.

No setup wizard, npm lifecycle, provider executable, target binary or REA server was run for this audit. Analyze authorized artifacts on an isolated engineering worker without production credentials, customer data, deployment mounts or general outbound authority. The isolation must be independently verified; the word "read-only" cannot establish it.

## AIOS owners to reuse

All AIOS paths below refer to the audit base.

| Concern | Existing owner | Required use and limitation |
| --- | --- | --- |
| Context/work identity | `apps/api/app/services/organization_context_broker.py` | Resolve tenant-bound WorkItem, current assignment, canonical references and context hash; caller JSON cannot supply authority |
| Tool entitlement | `organization_context_authority.py::_position_allowed_tools` | Reads only `OrganizationPosition.contract_json.context_authority.allowed_tools`; reuse this transitional canonical source |
| Runtime availability | `organization_agent_runtime.py` | Fresh context, version/hash checks and intersection with `AgentRuntimeProfile.available_tools`; runtime binding is technical availability, not authenticated authorization |
| Trusted actor | `organization_command.py` | Trusted command context and canonical actor/tenant/position binding; `system_bound_agent_command_context` is an internal helper, not authentication |
| Work execution | `organization_governance.py`; `OrganizationExecutionAttempt` | Reuse lifecycle, claim/token and cancellation/pause checks; no second agent execution store |
| Output/provenance | `OrganizationalActionOutput.evidence_json/output_json`; `AuditLog` | Bounded unverified observation references tied to the existing execution attempt; no automatic knowledge promotion |
| Material commands | `organization_governance_kernel.py`; `organization_governed_work.py` | Preserve material-action/authority evaluation; a dataclass is not an independently authenticated grant |
| Skills/competency | `organization_skill_registry.py`; `organization_skill_work_matching.py` | Applicability is diagnostic and tool/permission prerequisites are excluded; capability evidence does not grant tool execution |
| Existing external execution | `automation_connector.py`; `external_action_gates.py` | Reuse lifecycle, pre-use audit and failure patterns; delivery authority/configuration is not MCP engineering authority |
| Outcome/promotion | `organization_contribution.py`; `organization_autonomy_evidence_profile.py` | Attempts, outputs and telemetry do not prove attributable outcomes or permit self-grading |

There is no general canonical Evidence entity for this integration. Existing context evidence references resolve domain-specific `MobilityPathwayVersionEvidence`; REA bundles must not be inserted there by assertion. There is also no generic dispatcher consuming `EmployeeRuntimeBinding.allowed_tools`, admitted MCP session owner, pinned provider registry, artifact-custody/authorization contract or external engineering evidence validator. The current specialist provider exposes no tools.

Two existing model limits matter: OrganizationPosition is a global registry, not tenant-scoped; the WorkItem carries the tenant. The broker's active-position lookup checks `status` but not `suspended_at`. A dispatcher must independently enforce canonical suspension, current assignment, lifecycle, cancellation and global pause at invocation time. Do not extend the broker's diagnostic guarantees into claims of executable isolation.

## First executable slice

The narrow proposed pilot is **static managed-artifact inspection**, rather than blanket admission of native analysis, runtime tracing or reconstruction workflows. Candidate exact tools are `inspect_managed_artifact` and `get_evidence_bundle`; this proposal grants neither tool today. The managed provider declares identity `rea-dotnet-static`, version `1`, with no process/network/filesystem-write capability effects. Source routing lazily selects it for that operation, but opening/profile resolution and configured server startup still need independent effect verification. Its initial file read has no artifact-size ceiling; execution-free parsing is not memory/resource isolation. Ghidra's documented resource settings likewise do not establish a per-operation deadline, fixed queue limit or fixed response-size ceiling. AIOS must supply these limits rather than infer them from provider metadata.

The pilot must satisfy these predicates before a transport call:

1. Receive a trusted actor, resolve the canonical WorkItem/position/tenant and current execution attempt/token, and reject suspended, stale, cancelled, paused, reassigned or non-executable work.
2. Rebuild the existing context and runtime binding immediately before dispatch. Require the exact qualified tool in both canonical allowance and the admitted runtime profile. No caller-selected profile, skill label, provider response or wildcard can expand it.
3. Resolve an explicit, reviewed artifact authorization through the owning human/work contract: source/provenance, authorized custodian, intended purpose, target SHA-256, permitted inspection/reconstruction scope and expiry/revocation. A hash identifies bytes, not permission. This owner is missing and must be designed explicitly rather than inferred from arbitrary WorkItem JSON.
4. Stage immutable bytes under a bounded worker root, verify the target hash before use and after inspection, and reject symlink escapes, traversal, changed bytes and target/session substitution. Do not forward arbitrary caller filesystem paths.
5. Establish an AIOS-owned isolated transport/session, pinned package/build/catalog/provider identity and exact schemas. Use a fresh session per authorized investigation. `get_evidence_bundle` must be limited to that session so it cannot reveal another WorkItem's evidence.
6. Bound arguments, parser resources, time, output size and evidence count; apply fixed errors/redaction and preserve unknown outcome after timeout/disconnection. Persist pre-call provenance through the existing attempt/audit owner and bounded results through its action output. Do not introduce automatic retry or implied cleanup.

A deterministic fake transport can verify that every denial prevents dispatch and that allowed calls retain provenance. It cannot establish installed REA, provider isolation, actual decompilation or engineering competency. Only then run a separately attributed pilot on an AIOS-owned or otherwise explicitly authorized synthetic managed artifact. Installation/admission and active capabilities remain separate work.

## Evidence and review contract

Preserve target digest, artifact authorization reference, AIOS tenant/work/attempt/token, exact tool, argument fingerprint, source/build/catalog identity, provider identity/version, analysis/session lineage, evidence IDs and bundle/content hashes. Retain REA confidence/authority labels, analysis-profile commitments, limitations, truncation/unknowns, execution environment and cleanup disposition as observations, not authenticated facts.

Upstream `src/domain/evidence.ts` includes content-linked `ev_` IDs, subject digest and local path, provider, operation/parameters, raw/normalized results, confidence, authority, locations and evidence links; some environment/subject fields can be null and analysis profile is optional. The parser recomputes the semantic evidence ID; regex validation alone is insufficient. The ID excludes subject name/local path and is not a commitment to every envelope field. The bundle supplies manifests and residual unknowns, but no inherent top-level bundle hash, universal byte/count limit, AIOS work/transport identity or session/timestamp binding. AIOS must add those commitments and verify them independently. `EvidenceBundleFiles.ts` supports caller-path reads/writes. Independently validate the admitted schemas and required linkage, bound content, and restrict/redact paths and raw data before persistence. A valid hash detects changed committed content; it does not establish truth, rightful acquisition, safe execution or an authorized publisher. Missing required linkage remains unknown.

Treat all tool text/code as untrusted observation material. REA's reconstruction coverage/verification measures its own obligations and comparisons; it cannot satisfy AIOS review, competency, VerifiedRule, contribution or GRSI contracts by itself. Reconstruction should produce an independently reviewed behavioral specification and an implementation suited to AIOS, with its own tests. Target authorization and applicable rights remain a human-owned requirement; the REA repository license does not authorize copying target code/assets or bypassing access/licensing controls.

## Exit and remaining work

This audit is complete when source identities/corrections and existing owners are independently reviewed and reconciled into the existing state/roadmap/handoff. It does not close Phase 17 or Phase 21, qualify a live provider, or change whole-product production acceptance. Next: design the missing artifact-authorization and provider/session admission contracts, then implement and verify the narrow dispatcher/adapter. Resume the separate Phase 22 representative journey and remaining live gate evidence afterward according to the user's priority.
