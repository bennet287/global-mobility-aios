# AIOS V2 — Phase 2J: Character Art Direction Prototype V1

**Status:** independently reviewed implementation candidate · repository CI pending
**Base branch:** `design/aios-v2-complete-redesign`
**Repository:** `bennet287/global-mobility-aios`
**Verified base SHA:** `6850fd5fbdac0a12f8b7008138c3f6fbb7eaafb4`

## Purpose

Phase 2J establishes an isolated visual language for AIOS AI employees as premium miniature executive characters rather than generic avatars, emoji, game sprites, or dashboard icons.

The prototype does **not** replace `V2CharacterMiniature` yet. It exists so character identity, silhouette, accessibility, reduced motion, and future GLB translation can be independently reviewed before production adoption.

## Design philosophy

The visual target is an original **premium miniature executive figurine** language:

- expressive but enterprise-appropriate proportions;
- compact body with slightly oversized head for readability;
- distinct jacket, head, hair, and prop silhouettes;
- restrained role accents that supplement rather than define identity;
- polished presentation suitable for a modern AI headquarters;
- no copyrighted-character imitation.

The intended balance is approximately 60% premium animation-film character language, 30% enterprise professionalism, and 10% futuristic AI personality.

## Archetypes

### CEO — calm strategic presence

- silhouette: structured executive;
- wardrobe: tailored jacket and lapel structure;
- prop: upright executive tablet;
- accent: brass;
- facial language: calm composed expression.

### CTO — analytical precision

- silhouette: technical angular;
- wardrobe: asymmetric technical jacket;
- prop: angled technical tablet;
- accent: steel cyan;
- facial language: focused neutral expression.

### Regulatory / Compliance — quiet attentiveness

- silhouette: tidy measured;
- wardrobe: conservative blazer;
- prop: evidence/document folder;
- accent: teal;
- facial language: restrained attentive expression.

### Operations — practical readiness

- silhouette: practical balanced;
- wardrobe: functional smart jacket with sleeve-layering cue;
- prop: compact organizer;
- accent: amber;
- facial language: approachable readiness.

### Neutral professional — understated fallback

- silhouette: deliberately less distinctive;
- wardrobe: simple blazer;
- prop: none;
- accent: silver;
- detail density: minimal.

## Role differentiation

Role presentation is not color-only. The prototype differentiates archetypes through:

1. jacket shoulder/torso geometry;
2. head geometry;
3. hair silhouette;
4. prop presence and shape;
5. facial micro-language;
6. restrained accent color as a secondary cue.

The art resolver accepts only exact presentation keys:

- `ceo`
- `cto`
- `role-family:regulatory-compliance`
- `role-family:operations`
- `neutral-professional`

Unknown keys resolve to the neutral professional fallback. Title-like or authority-like extra fields cannot select an archetype.

## Truth boundaries

Every art model preserves:

| Flag | Value |
| --- | --- |
| `presentationOnly` | `true` |
| `physicalPresenceClaimed` | `false` |
| `physicalLocationClaimed` | `false` |
| `canonicalStateWritable` | `false` |
| `semanticAnimationActive` | `false` |

Character art never grants authority, mutates organization state, claims physical location, claims physical presence, or activates semantic handoff/conversation/completion behavior.

## Accessibility

- the outer figure exposes an archetype-derived accessible description;
- decorative SVG internals are `aria-hidden`;
- role distinction is structural, not color-only;
- inspector presentation remains readable without ambient motion.

## Motion

Only presentation-only ambient motion exists in this prototype:

- subtle breathing;
- blink in inspector presentation;
- tiny prop idle movement;
- bounded hover elevation.

All of it is disabled under `prefers-reduced-motion: reduce`.

No walking, physical travel, conversation, governed handoff, room movement, work completion, or collaboration animation is implemented here.

## Independent review hardening

Qwen3.7 Plus supplied the initial five-file Phase 2J draft but explicitly reported that it could not execute git, Node, TypeScript, or screenshots. Its output was therefore treated as untrusted visual/code input rather than repository evidence.

Independent AIOS review found the following issues before upstream integration:

1. the draft test harness could not safely load the TypeScript production module and skipped core runtime checks;
2. raw source-regex tests falsely failed when comments merely mentioned forbidden APIs or inputs;
3. CSS-module variables were declared under global `:root` instead of remaining scoped to the prototype;
4. SVG gradient IDs were archetype-based, allowing DOM ID collisions when multiple characters of the same archetype render together;
5. the accessible description was duplicated by both the figure label and a second visually-hidden copy;
6. the draft encoded a fixed human-like skin gradient even though role identity must not imply demographic traits;
7. the CTO tablet's static angle could conflict with CSS transform animation;
8. SVG blink/prop transform origins did not explicitly use local fill boxes.

The reviewed implementation corrects those issues by:

- using real Node type stripping for the runtime contract suite;
- testing title/authority independence behaviorally rather than with brittle source-word bans;
- scoping CSS variables to `.root`;
- using React `useId()` for per-instance SVG paint IDs;
- exposing one explicit accessible name;
- using a neutral figurine surface material rather than role-specific skin mapping;
- nesting the CTO static tablet transform outside the idle-animation group;
- using `transform-box: fill-box` for SVG micro-motion.

## Test evidence

Observed raw Qwen draft run:

```text
29 passed
6 failed
11 skipped
```

The skipped checks were caused by the draft's regex-based TypeScript fallback failing to load the production module. Several failures were false positives against comments that described forbidden APIs.

Observed reviewed preflight:

```bash
node --experimental-strip-types --test apps/web/scripts/aios-v2-character-art-prototype.test.mjs
```

Result:

```text
29 passed
0 failed
0 skipped
```

Isolated strict TypeScript 5.8.3 verification of the production `.ts` + `.tsx` surface also passed with exit code 0.

Fresh Woodpecker/browser evidence is still required before adoption into the production miniature renderer.

## Files

- `apps/web/components/v2/V2CharacterArtPrototype.tsx`
- `apps/web/components/v2/V2CharacterArtPrototype.module.css`
- `apps/web/lib/v2/character-art-prototype.ts`
- `apps/web/scripts/aios-v2-character-art-prototype.test.mjs`
- `docs/aios-v2/AIOS_V2_PHASE2J_CHARACTER_ART_PROTOTYPE.md`

## Future GLB translation

| Prototype concept | Future asset equivalent |
| --- | --- |
| jacket/head/hair SVG geometry | mesh topology / sculpt |
| role accent palette | material accent parameters |
| prop geometry | rigged accessory mesh |
| neutral figurine surface | material family, independent from role authority |
| blink | facial blendshape/clip |
| breathing | idle animation clip |
| prop micro-motion | accessory animation clip |
| compact/inspector modes | LOD / presentation-camera policy |

## Limitations

1. This remains an isolated SVG/CSS prototype, not the production `V2CharacterMiniature`.
2. No accepted browser screenshot exists yet for the reviewed repository candidate.
3. No GLB mesh, texture, rig, or production character asset is introduced.
4. The prototype test is intentionally not wired into `apps/web/package.json` yet to avoid colliding with the active Phase 2G branch; CI wiring belongs in the later integration slice after the roster base settles.

## Source attribution

Qwen3.7 Plus supplied the initial visual/code draft and pushed nothing to GitHub. AIOS independently verified the real repository base, reproduced the draft test failures/skips, hardened the implementation, and created this reviewed repository candidate separately.
