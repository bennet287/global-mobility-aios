# V1.3-D.3 — Governed Context Authority Adapters

**Status:** COMPLETE / PASS / SEALED  
**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`

## Purpose

D.1 established a safe ContextBundle envelope but deliberately left authority-bearing fields empty. D.3 makes that envelope operationally useful without weakening the trust boundary.

Permanent rule:

> **Working context may inform reasoning; it cannot create Evidence, VerifiedRules, tool authority or policy authority.**

D.3 populates those fields only from governed AIOS state through explicit `ContextAuthorityAdapter` implementations.

## First concrete adapter

The first adapter supports:

```text
source_object_type = mobility_pathway_version
```

This is intentionally domain-concrete. It moves ContextBundle toward a real Global Mobility vertical rather than creating a large generic enrichment framework with no authoritative mobility truth behind it.

## Trust chain

```text
Tenant-bound OrganizationalWorkItem
        ↓
OrganizationPosition
        ↓
ContextAuthorityAdapter registry
        ↓
MobilityPathwayVersion
        ├── MobilityPathwayVersionEvidence
        ├── VerifiedRule
        ├── SourceSnapshot / OfficialSource provenance
        └── CountryPolicy
        ↓
ContextBundle
        ├── evidence_refs
        ├── verified_rule_refs
        ├── source_snapshot_refs
        ├── policy_version
        └── allowed_tools
```

The model/runtime receives governed references. It does not decide what counts as Evidence.

## Adapter registry

D.3 introduces a static adapter contract:

```text
ContextAuthorityAdapter
        ↓
MobilityPathwayVersionAuthorityAdapter
```

The registry is deliberately explicit and bounded. A future source type such as `corporate_mobility_case` or `application` should be added as a new adapter rather than by rewriting the Context Broker.

The static module-level registry is accepted for D.3. Before source types become numerous, it should evolve into an explicit registration mechanism with duplicate-key and contract tests rather than turning the broker into a plugin framework prematurely.

## Mobility pathway authority rules

For a `mobility_pathway_version` WorkItem, D.3:

1. resolves the referenced `MobilityPathwayVersion` and parent `MobilityPathway`;
2. requires the pathway version to be published and currently effective;
3. resolves explicit `MobilityPathwayVersionEvidence` bindings;
4. resolves only rule IDs recorded on the pathway version;
5. requires every referenced `VerifiedRule` to be active, published, not retired, currently effective and country/domain compatible;
6. requires referenced rules to have valid SourceSnapshot/OfficialSource provenance;
7. resolves an unambiguous active `CountryPolicy` for the pathway country/domain when present;
8. derives tool entitlement only from the explicit position-contract namespace described below;
9. emits deterministic fingerprints into ContextBundle references and `policy_version` so changes affect `context_hash`.

Malformed, stale, contradictory or missing referenced authority fails closed with `ContextIntegrityError` through the Context Broker boundary.

## Evidence semantics

`MobilityPathwayVersionEvidence` is the first Evidence adapter because it is already an explicit governed binding between a published pathway version, an official source and a source snapshot.

No new generic Evidence table is introduced in D.3.

When a published pathway version has no explicit evidence rows:

```text
evidence_refs = ()
unknowns includes mobility_pathway_version_evidence_missing
```

This is not treated as fabricated completeness and is not silently hidden.

## Rule semantics

`verified_rule_ids_json` is parsed as an explicit list of UUIDs. D.3 does not discover arbitrary rules by semantic similarity and does not trust IDs supplied through WorkItem working context.

A referenced rule must satisfy all of the following:

```text
exists
active = true
retired_at = null
published_at != null
effective_from <= now, when set
effective_to >= now, when set
country matches pathway country
domain matches pathway domain
source_snapshot_id != null
valid official-source provenance
```

Each ContextBundle rule reference contains a deterministic fingerprint of the canonical `VerifiedRule` record. Therefore changes to rule content/effective state change the ContextBundle hash.

## SourceSnapshot semantics

SourceSnapshots are deduplicated across pathway, evidence and rule provenance.

Each source-snapshot reference carries a deterministic fingerprint over the canonical SourceSnapshot record, including captured content/hash/state. A changed snapshot therefore changes `context_hash`.

A null `SourceSnapshot.official_source_id` is not rejected automatically when the authoritative linking record itself provides a valid `official_source_id`; D.3 rejects only snapshots for which official-source provenance cannot be established or whose populated source identity conflicts with the authoritative link.

## Policy semantics

`CountryPolicy` has no explicit version/effective-window columns in the current schema. D.3 does not invent them.

Current accepted behavior:

```text
policy_version = SHA-256 fingerprint of the canonical active CountryPolicy record
```

The fingerprint therefore changes when policy content or review/update state changes.

This is sufficient for D.3 stale-context detection. Before Flight Recorder/replay treats `policy_version` as a long-lived semantic version, the fingerprint must be narrowed to an explicit semantic field contract such as country/domain/status/policy content/review state so future non-semantic ORM columns cannot create accidental replay divergence.

If no active policy exists:

```text
policy_version = None
unknowns includes country_policy_missing
```

If multiple active policies exist for the same country/domain, D.3 fails closed because authority would be ambiguous.

## WorkItem source-version semantics

For supported governed adapters, `OrganizationalWorkItem.source_object_version` is a non-authoritative caller/reference hint only.

The adapter computes the authoritative source-reference version from canonical `MobilityPathway` + `MobilityPathwayVersion` state and replaces the hint in the effective ContextBundle reference. This prevents stale or caller-controlled version labels from becoming authority.

## Tool entitlement — temporary D.3 source

D.3 intentionally avoids introducing a premature `ToolEntitlement` migration.

The temporary entitlement source is the existing versioned `OrganizationPosition.contract_json`, but only one explicit namespace is interpreted:

```json
{
  "context_authority": {
    "allowed_tools": [
      "official_source.search",
      "document.read"
    ]
  }
}
```

No other `contract_json` key grants tools.

If the namespace is absent:

```text
allowed_tools = ()
```

If the namespace exists but is malformed, context resolution fails closed.

This is deliberately transitional. After the first governed vertical proves the durable entitlement shape, tool authority should migrate into a dedicated auditable/versioned `ToolEntitlement` or equivalent capability-authority model rather than allowing `contract_json` to become a general authority dumping ground.

## MAY USE ∩ CAN DO

D.3 owns the organizational side:

```text
OrganizationPosition contract
        ↓
ContextBundle.allowed_tools
        = MAY USE
```

D.2 owns the technical side:

```text
AgentRuntimeProfile.available_tools
        = CAN DO
```

Effective runtime tools remain:

```text
MAY USE ∩ CAN DO
```

A provider/runtime can never grant organizational tool authority.

## Tenant boundary

`MobilityPathwayVersion`, `VerifiedRule`, `CountryPolicy` and SourceSnapshot catalogue/provenance records are global canonical reference data in the current schema; they do not carry `tenant_key`.

Tenant isolation therefore remains at the `OrganizationalWorkItem` boundary. D.3 first resolves the WorkItem through the existing non-disclosing tenant-aware command contract. A tenant cannot probe another tenant's WorkItem merely because both may reference the same global pathway catalogue record.

No fictional tenant field is added to global canonical pathway truth.

## Deterministic replay/staleness behavior

The ContextBundle hash now incorporates:

- canonical pathway-version fingerprint;
- Evidence-binding fingerprints;
- VerifiedRule fingerprints;
- SourceSnapshot fingerprints;
- active CountryPolicy fingerprint;
- position-derived tool entitlements.

Therefore the same governed state produces the same `context_hash`, while meaningful authority-state changes produce a different hash.

This provides a base for later AgentRun/Flight Recorder replay and stale-context detection.

## Explicit non-goals

D.3 does not add:

- memory retrieval;
- collaboration summaries;
- related-case discovery;
- Mission Room state;
- provider/model selection;
- runtime execution;
- Munder runtime adoption;
- new external actions;
- new authority levels;
- a new Evidence database;
- a ToolEntitlement migration.

Those concerns remain downstream.

## Acceptance matrix

Canonical local acceptance on the Windows V12 checkout:

```text
Deterministic bundle with governed Evidence/rules       PASS
Pathway-version change changes context hash             PASS
Active-rule change changes context hash                 PASS
CountryPolicy change changes policy/context hash        PASS
SourceSnapshot change changes context hash              PASS
Unpublished/retired/expired rule fails closed           PASS
Malformed/wrong-country rule fails closed               PASS
Foreign-tenant WorkItem remains non-disclosing          PASS
Missing pathway Evidence is empty but visible           PASS
Missing CountryPolicy is visible, not fabricated        PASS
Tool entitlement comes only from position contract      PASS
No tool namespace produces empty tools                  PASS
Malformed tool namespace fails closed                   PASS
Working context cannot self-promote authority           PASS
No runtime/provider identity enters ContextBundle       PASS
Adapter registry remains explicit and bounded           PASS
Repository policy                                       PASS
Full API regression                                     961 passed / 5 skipped / 1 warning / 0 failed
Migration/schema checks                                 PASS
git diff --check                                        clean
V12 branch status                                       clean / synchronized
```

Canonical acceptance record:

`docs/V1_3_D3_ACCEPTANCE_2026-08-20.md`

No GitHub CI PASS is claimed because no attached status checks were present.

## Seal decision

V1.3-D.3 is COMPLETE / PASS / SEALED.

The next bounded step should use these sealed contracts inside a real end-to-end Global Mobility workflow. Additional runtime/provider abstraction should be introduced only where that vertical needs it, not as another horizontal framework phase.
