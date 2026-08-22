# Global Mobility AIOS — V12.25 Integration Capability Changelog

**Date:** 2026-08-22
**Status:** DOCUMENTATION / ARCHITECTURE DIRECTION — NO NEW RUNTIME ACCEPTANCE CLAIM
**Active branch:** `roadmap/global-mobility-aios-v12`

## Summary

V12.25 formalizes a proactive Integration & Capability Radar so Global Mobility AIOS can adopt essential production infrastructure without either rebuilding commodity enterprise software or surrendering AIOS constitutional semantics to external platforms.

The accepted product/runtime sequence is unchanged:

```text
I.1–I.4 SEALED
→ J.1 SEALED
→ K.1 SEALED
→ L Live Organization NEXT
```

The new integration programme runs in parallel and is explicitly subordinate to measurable product need.

## Added canonical direction records

```text
docs/ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md
docs/AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md
docs/TECHNOLOGY_RADAR_V1_3_2.md
docs/V12_25_INTEGRATION_CAPABILITY_PROGRAMME.md
```

## Permanent integration doctrine

```text
External infrastructure provides capability.
AIOS owns meaning, truth and authority.
```

New permanent refinements:

- identity providers authenticate; AIOS authorizes;
- observability telemetry is engineering evidence, not canonical `OrganizationActivity`;
- secrets belong in a secret backend/runtime injection path, never prompts, ContextBundles, memory or activity;
- backup acceptance requires isolated restore evidence, not only backup creation;
- outbound communications must pass through a provider-neutral governed gateway;
- e-signature providers attest signing transactions but do not make mobility/legal content true;
- ERP/accounting may own bounded back-office ledgers but may not own mobility truth or Board authority;
- payment APIs never grant financial authority by their existence;
- material external integrations must remain subordinate to Command Gateway/authority/materiality policy;
- every shared integration field should have a declared master system; dual-master state is rejected by default.

## Integration priorities introduced

### P0 / NOW

- OpenTelemetry correlation for L Live Organization;
- secrets-management research/bounded pilot (OpenBao-class direction);
- PostgreSQL/object-storage backup + isolated restore proof planning;
- production-state classification into canonical/derived/cache/external.

### P0/P1 design

- Identity/SSO benchmark (Keycloak/Authentik-class);
- provider-neutral Communications Gateway contract.

### P1 later

- EU DSS + open-source e-signature platform research;
- governed external communications trial.

### Demand-gated

- ERPNext/Odoo accounting/ERP adapter benchmark;
- payment-provider adapter design;
- broader commercial operations.

## Technology Radar update

`TECHNOLOGY_RADAR_V1_3_2.md` supersedes V1.3.1 for active radar direction.

It preserves existing donor/pilot decisions and updates repository truth:

- Munder Difflin remains a strategic donor;
- Plasma Wiki/Fractal pinned source is present in V12 but remains non-adopted donor material;
- LLMLingua-2 remains the selected primary compression pilot;
- OpenTelemetry is promoted in priority for L but is not falsely represented as a new production adoption;
- no additional generic agent framework is selected;
- K.1 strengthens the preference for native organization/runtime execution because the accepted bounded execution path required no external agent framework.

## Enterprise Integration Architecture

`ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md` establishes AIOS-owned ports/contracts for future capabilities:

```text
IdentityPort
SecretsPort
ObservabilityPort
BackupPort
CommunicationPort
SignaturePort
AccountingPort
ERPPort
PaymentPort
```

These are architectural boundaries, not claims that concrete interfaces/classes already exist in source code.

## V12.25 programme sequencing

```text
Product:
  L Live Organization
  → M Board Transparency
  → N Learning / Optimization

Parallel integration:
  E0 architecture / capability radar
  → E1 observability + secrets + backup
  → E2 identity + communications contracts
  → E3 e-signature / governed external communications
  → E4 accounting / ERP / payments (demand gated)
```

No E-stage automatically authorizes the next.

## CI / proof truth

This documentation programme does not change historical proof truth.

K.1 remains accepted on its recorded technical candidate and proof evidence. Self-hosted Woodpecker parity remains the forward CI direction. Historical GitHub Actions runs remain historical GitHub Actions evidence and are not relabeled as Woodpecker runs.

No runtime test PASS is claimed for this documentation-only V12.25 change unless a real CI status becomes attached to the resulting commit.

## Explicit non-claims

V12.25 does not claim production adoption of:

- OpenBao;
- Keycloak;
- Authentik;
- Langfuse or another observability backend;
- pgBackRest/WAL-G/Restic;
- communications providers;
- Documenso/DocuSeal;
- ERPNext/Odoo;
- payment providers.

It also does not authorize:

- government submission;
- autonomous client send;
- payment execution;
- contract signing;
- autonomy mutation;
- automatic promotion/demotion;
- replacement of AIOS canonical governance by external systems.

## Next implementation direction

Continue L Live Organization as the primary product milestone.

Use the new Integration & Capability Radar to select only bounded infrastructure work that directly strengthens observed product/runtime gaps, beginning with L telemetry correlation, backup/restore proof design and a bounded secret-management pilot.
