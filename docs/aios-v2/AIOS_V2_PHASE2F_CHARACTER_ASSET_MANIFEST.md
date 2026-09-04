# AIOS V2 — Phase 2F Versioned Character Asset Manifest

**Status:** IMPLEMENTED / CI PROOF PENDING  
**Branch:** `design/aios-v2-character-asset-manifest`  
**Base:** merged AIOS V2 redesign including governed Phase 2E handoff descriptor

## Purpose

Phase 2F introduces the contract between a resolved AIOS Character Presentation and future real character assets.

This phase exists **before** GLB loading so the renderer cannot invent file paths, silently bind incompatible rigs, or claim that a model exists when no verified asset has been integrated.

The current V2 CSS miniature remains the truthful rendering fallback.

## Flow

```text
Canonical LivingSceneEmployee
        ↓
Character Presentation Registry
        ↓
Resolved Character Presentation
        ↓
Versioned Character Asset Manifest
        ↓
compatibility gate
        ↓
verified GLB available?
     ↙               ↘
   yes                no
   ↓                  ↓
GLB renderer     CSS miniature fallback
```

No branch of this flow writes canonical organization state.

## Current manifest entries

The initial manifest covers the five presentation keys currently used by the Character Registry:

- `ceo`
- `cto`
- `role-family:regulatory-compliance`
- `role-family:operations`
- `neutral-professional`

Each binding defines presentation key, binding version, expected GLB format, model URI, asset version, content hash, availability, rig class, LOD class, animation-set key, optional material profile, optional signature-prop asset, and fallback renderer contract.

## Explicit missing-asset state

No real GLB assets have been integrated in this phase. Therefore every model entry truthfully carries:

```text
format        = glb
availability  = not-integrated
uri           = null
assetVersion  = null
contentHash   = null
```

The system deliberately does **not** invent paths such as `/public/characters/ceo.glb` or `/assets/characters/cto.glb` until those assets actually exist and have been verified.

## Compatibility gate

A manifest binding is compatible only when `rigClass`, `lodClass`, and `animationSetKey` match the selected Character Presentation. A mismatch forces the CSS fallback. The asset layer may not silently retarget an incompatible character.

## Verified-model availability rule

A model is available only when manifest availability is `available`, the model URI is non-empty, asset version is non-empty, content hash is non-empty, and the presentation compatibility gate passes.

Until then:

```text
modelAvailable = false
rendererMode   = css-miniature
modelUri       = null
```

## Fallback contract

```text
renderer = css-miniature
requiredWhenModelUnavailable = true
preservesStructuredIdentity = true
mayClaimCanonicalPresence = false
mayActivateSemanticAnimation = false
```

The CSS miniature is the structured, truth-preserving fallback for missing or incompatible heavy assets.

## UI integration

`V2CharacterMiniature` resolves the selected presentation against the manifest and exposes `data-asset-compatible`, `data-asset-model-available`, and `data-asset-renderer-mode`. The Employee Inspector surfaces the current asset limitation.

At this phase, expected visible state is:

```text
css miniature
character presentation is registered
verified GLB not integrated yet
```

## Truth posture

Every resolved asset binding preserves:

```text
presentationOnly        = true
presenceClaimed         = false
canonicalStateWritable  = false
semanticAnimationActive = false
```

Asset availability must never alter role, title, authority, reporting line, department, WorkItem, semantic state, presence, decision state, or handoff occurrence. The asset layer controls only **how an already-resolved presentation may be rendered**.

## Immutability

Manifest entries are runtime-frozen. Nested model and fallback metadata are also frozen. The public API exposes only read-only lookup/resolution functions.

## Files

Added:
- `apps/web/lib/v2/character-asset-manifest.ts`
- `apps/web/scripts/aios-v2-character-asset-manifest.test.mjs`
- `docs/aios-v2/AIOS_V2_PHASE2F_CHARACTER_ASSET_MANIFEST.md`

Updated:
- `apps/web/components/v2/V2CharacterMiniature.tsx`
- `apps/web/package.json`

## Tests

The Phase 2F contract test covers presentation-only/no-presence/no-write invariants; deterministic five-key manifest coverage; no fabricated GLB availability; CEO/CTO and Regulatory/Operations compatibility; neutral fallback binding; rig/LOD/animation-set mismatch rejection; deep runtime immutability; deterministic resolution; no network/loader/timing/randomness machinery; no canonical organization truth in the manifest; and truthful miniature renderer wiring.

The test is wired into `test:design-foundation` under Node type stripping, alongside the already-accepted Phase 2E semantic-motion test.

## Non-goals

Phase 2F does not add actual GLB files, Three.js / React Three Fiber, GLTFLoader, model downloading, materials, textures, skeleton authoring, animation clips, semantic motion activation, pathfinding, physical presence, or backend state.

## Next asset implementation

A later asset-production slice may change one manifest entry from `availability = not-integrated` / `uri = null` to a verified versioned asset only after the GLB exists in the repository or approved asset store; rig, animation-set and LOD compatibility are verified; content hash is recorded; fallback still works; accessibility remains independent; and performance proof passes.

## Relationship to Phase 2E

Phase 2E defines **whether a canonical handoff is semantically eligible for presentation**. Phase 2F defines **which verified character asset may render a resolved presentation**. These are independent gates. A future renderer must satisfy both before showing a semantic 3D handoff.
