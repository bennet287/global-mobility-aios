# Global Mobility AIOS — V1.3-D.3 Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Slice:** V1.3-D.3 — Governed Context Authority Adapters  
**Status:** COMPLETE / PASS / SEALED

## Accepted scope

D.3 turns the D.1 ContextBundle from a safe envelope into a governed, truth-bearing execution context for the first concrete Global Mobility source type:

```text
source_object_type = mobility_pathway_version
```

Accepted authority chain:

```text
Tenant-bound OrganizationalWorkItem
        ↓
OrganizationPosition
        ↓
ContextAuthorityAdapter
        ↓
MobilityPathwayVersion
        ├── MobilityPathwayVersionEvidence
        ├── VerifiedRule
        ├── SourceSnapshot / OfficialSource provenance
        └── CountryPolicy
        ↓
ContextBundle
```

Accepted invariants:

- working context cannot create Evidence, VerifiedRules, policy authority or tool authority;
- referenced pathway versions must be published and currently effective;
- referenced VerifiedRules must exist, be active, published, not retired, currently effective and country/domain compatible;
- rule and Evidence provenance must resolve through SourceSnapshot / OfficialSource relationships;
- missing pathway Evidence is visible through `unknowns` and does not fabricate completeness;
- missing CountryPolicy is visible and is not fabricated;
- ambiguous active CountryPolicy state fails closed;
- tool entitlement is derived only from the explicit transitional `context_authority.allowed_tools` namespace of the governed position contract;
- missing tool namespace produces an empty authoritative tool set;
- malformed tool authority fails closed;
- canonical pathway, Evidence, rule, SourceSnapshot and policy fingerprints participate in ContextBundle identity;
- global pathway/rule/policy/provenance catalogue records remain reusable while tenant isolation is enforced at the OrganizationalWorkItem boundary;
- no provider/model/runtime identity enters ContextBundle;
- no database migration is introduced by D.3.

## Canonical local acceptance evidence

The Human Owner reported the prescribed D.2/D.3 acceptance sequence green on the canonical Windows V12 checkout.

Exact reported evidence:

```text
Focused context/runtime/authority/transparency neighborhood   36 passed / 1 warning / 0 failed
Repository policy                                             PASS
Full API regression                                           961 passed / 5 skipped / 1 warning / 0 failed
Database migration check                                      PASS
Migration head                                                0076_organization_position_active_identity
Registered tables                                             118
Physical schema                                               ok
Database revision                                             0076_organization_position_active_identity
Local DB schema check                                         PASS
Actual tables                                                 118
Physical tables                                               119
Infrastructure tables                                         ["alembic_version"]
git diff --check                                              clean
V12 branch status                                             clean / synchronized
```

Known non-blocking warning:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

## Clarifications preserved by the seal

### WorkItem `source_object_version`

For a supported governed authority adapter, `OrganizationalWorkItem.source_object_version` is treated as a non-authoritative caller/reference hint. The authoritative version used by ContextBundle is recomputed from canonical pathway/pathway-version state. This prevents stale or caller-supplied version strings from becoming authority.

### CountryPolicy fingerprint

D.3 currently fingerprints the canonical active `CountryPolicy` record. This is accepted for the D.3 boundary because semantic policy changes are reflected in ContextBundle identity. Before Flight Recorder/replay semantics depend on long-lived policy-version stability, the fingerprint should be narrowed to an explicit semantic field contract so future non-semantic ORM columns cannot create accidental replay divergence.

### Tool-entitlement storage

`OrganizationPosition.contract_json.context_authority.allowed_tools` is explicitly transitional. It must not become a general authority dumping ground. Once the first governed vertical proves the durable entitlement shape, tool authority should move to a dedicated auditable/versioned capability or ToolEntitlement model.

## Non-claims

This acceptance does not claim:

- a GitHub CI PASS;
- semantic memory/collaboration enrichment;
- runtime/provider execution;
- Munder runtime adoption;
- a durable ToolEntitlement table;
- replay/Flight Recorder completion;
- full V1.3 completion.

No attached GitHub status checks were available for this slice, so no CI result is asserted.

## Seal decision

V1.3-D.3 is accepted as the first governed Context Authority adapter boundary. Context authority is now ready to support a real end-to-end mobility vertical before additional runtime power is attached.
