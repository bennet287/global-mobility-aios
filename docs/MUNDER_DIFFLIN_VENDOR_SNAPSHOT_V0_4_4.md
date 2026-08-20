# Munder Difflin v0.4.4 — Vendored Donor Snapshot

**Date:** 2026-08-20  
**Status:** Frozen donor source imported for AI-assistant inspection  
**AIOS branch:** `roadmap/global-mobility-aios-v12`  
**Vendor path:** `vendor/munder-difflin/v0.4.4/`  
**Upstream:** `chaitanyagiri/munder-difflin`  
**Tag:** `v0.4.4`  
**Upstream commit:** `4b6f8b71ef904a1df908c03430934d1ecda9a744`  
**Original uploaded ZIP SHA-256:** `8c7a152873f72a2ddbb2f508a02bfe49903c8feb1ba59d1aaec30befa4b6e82a`

## Purpose

The Munder Difflin donor source is vendored directly inside the Global Mobility AIOS repository so future AI assistants, developers and architecture reviews can inspect the exact frozen `v0.4.4` implementation without depending on the upstream repository's moving `main` branch or repeatedly retrieving the donor project from outside the AIOS repository.

This snapshot is **reference material, not production AIOS implementation code**.

Canonical adoption policy remains:

`docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

## Snapshot contents

The vendored snapshot preserves the donor material most useful for AIOS implementation analysis:

- `src/` application source;
- `test/` donor tests;
- runtime resources and built-in Skills;
- `tools/`, `scripts/` and prototypes;
- package and TypeScript/Electron configuration;
- `README.md`;
- `DESIGN.md`;
- `HIVE.md`;
- `MEMORY_GRAPH_SPEC.md`;
- `SPEC.md`;
- `TELEMETRY.md`;
- donor changelog/release/security/contribution documentation;
- upstream MIT license;
- `SOURCE_MANIFEST.txt`;
- `AIOS_VENDOR_METADATA.md`.

## Deliberate exclusions

The snapshot intentionally excludes material that is unnecessary or unsuitable for the AIOS donor reference:

- `node_modules`;
- build/dist/out caches and generated output;
- release executables/installers;
- heavy documentation video/media and generated website output;
- transient logs/worktrees;
- bundled LimeZu pixel-art assets.

Munder's upstream `LICENSE` explicitly states that its bundled pixel-art assets are **not** covered by the MIT license and that the LimeZu free-version art is non-commercial. AIOS therefore does not vendor those assets. The relevant attribution notice is retained where available.

This exclusion also matches the accepted AIOS product direction: the Munder pixel-office presentation is being replaced by a completely redesigned premium modern 2D/2.5D Living Organization with modern cartoon AI employees.

## Read-only donor rule

Do not gradually edit this directory into AIOS production code.

Preferred flow:

```text
vendor/munder-difflin/v0.4.4/<donor module>
        ↓
architecture/adoption review
        ↓
DIRECT REUSE / PORT / ADAPT / REIMPLEMENT / REJECT
        ↓
AIOS-owned interface / adapter / service
        ↓
AIOS tests + governance + acceptance
```

AIOS-native adaptations belong in normal AIOS packages/modules and remain governed by the Context Broker, authority/autonomy contracts, Evidence model, Canonicalization, Command Gateway, Transparency Layer and Organizational Immune System.

## AI-assistant usage

When analyzing Munder-derived features, assistants should prefer the vendored path over the upstream repository whenever the `v0.4.4` baseline is intended.

Examples:

```text
vendor/munder-difflin/v0.4.4/src/main/hive.ts
vendor/munder-difflin/v0.4.4/src/main/breaker.ts
vendor/munder-difflin/v0.4.4/src/main/skills.ts
vendor/munder-difflin/v0.4.4/src/main/webhook.ts
vendor/munder-difflin/v0.4.4/src/main/transcript.ts
vendor/munder-difflin/v0.4.4/src/shared/agentProvider.ts
vendor/munder-difflin/v0.4.4/src/shared/triggers.ts
vendor/munder-difflin/v0.4.4/src/renderer/src/scene/office/OfficeFloor.tsx
vendor/munder-difflin/v0.4.4/src/renderer/src/components/ToolWaterfall.tsx
vendor/munder-difflin/v0.4.4/src/renderer/src/components/MemoryGraphPanel.tsx
```

The upstream repository may still be consulted when intentionally comparing newer versions, security fixes or post-`v0.4.4` changes, but it is no longer required to inspect the frozen donor baseline.

## Provenance and integrity

Two provenance anchors are retained:

```text
Upstream tag/commit
v0.4.4
4b6f8b71ef904a1df908c03430934d1ecda9a744
```

and the SHA-256 of the exact ZIP uploaded for the AIOS analysis:

```text
8c7a152873f72a2ddbb2f508a02bfe49903c8feb1ba59d1aaec30befa4b6e82a
```

These allow later reviewers to distinguish this frozen donor snapshot from future Munder releases or modified AIOS-native adaptations.
