/**
 * AIOS V2 — Character Art Prototype (Phase 2J)
 *
 * Pure, deterministic adapter that maps PRESENTATION metadata
 * to visual art-prototype descriptors.
 *
 * This module NEVER:
 *   - uses employee title, authority, or seniority
 *   - reads canonical semantic state
 *   - infers physical location or presence
 *   - uses Date.now, Math.random, performance.now
 *   - fetches, writes, or imports any backend/API/database
 *
 * It maps ONLY from exact presentation keys:
 *   "ceo", "cto", "role-family:regulatory-compliance",
 *   "role-family:operations", "neutral-professional"
 */

export const CHARACTER_ART_PROTOTYPE_CONTRACT = Object.freeze({
  contractId: "aios-v2.character-art-prototype",
  contractVersion: "1.0.0",
  presentationOnly: true,
  physicalPresenceClaimed: false,
  physicalLocationClaimed: false,
  canonicalStateWritable: false,
  semanticAnimationActive: false,
} as const);

export type CharacterArtArchetype =
  | "ceo"
  | "cto"
  | "regulatory-compliance"
  | "operations"
  | "neutral-professional";

export type CharacterArtSilhouetteKey =
  | "structured-executive"
  | "technical-angular"
  | "tidy-measured"
  | "practical-balanced"
  | "understated-neutral";

export type CharacterArtWardrobeProfile =
  | "tailored-executive-jacket"
  | "asymmetric-technical-jacket"
  | "conservative-blazer"
  | "smart-functional-jacket"
  | "simple-blazer";

export type CharacterArtAccentToken =
  | "brass"
  | "steel-cyan"
  | "teal"
  | "amber"
  | "silver";

export type CharacterArtPropProfile =
  | "executive-tablet"
  | "technical-tablet"
  | "document-folder"
  | "compact-organizer"
  | "none";

export type CharacterArtHeadShapeProfile =
  | "broad-authoritative"
  | "angular-precise"
  | "rounded-meticulous"
  | "friendly-practical"
  | "standard-neutral";

export type CharacterArtExpressionProfile =
  | "calm-authority"
  | "analytical-focus"
  | "quiet-attentiveness"
  | "approachable-readiness"
  | "neutral-professional";

export type CharacterArtDetailDensity = "rich" | "standard" | "minimal";

export type CharacterArtPrototypeModel = {
  readonly presentationKey: string;
  readonly archetype: CharacterArtArchetype;
  readonly silhouette: CharacterArtSilhouetteKey;
  readonly wardrobe: CharacterArtWardrobeProfile;
  readonly accent: CharacterArtAccentToken;
  readonly prop: CharacterArtPropProfile;
  readonly headShape: CharacterArtHeadShapeProfile;
  readonly expression: CharacterArtExpressionProfile;
  readonly detailDensity: CharacterArtDetailDensity;
  readonly accessibilityDescription: string;
  readonly presentationOnly: true;
  readonly physicalPresenceClaimed: false;
  readonly physicalLocationClaimed: false;
  readonly canonicalStateWritable: false;
  readonly semanticAnimationActive: false;
};

export const CHARACTER_ART_ACCENT_PALETTE = Object.freeze({
  brass: Object.freeze({
    token: "brass" as const,
    primary: "#C9A36A",
    soft: "rgba(201, 163, 106, 0.22)",
    gloss: "#E4C98F",
  }),
  "steel-cyan": Object.freeze({
    token: "steel-cyan" as const,
    primary: "#5B9BD5",
    soft: "rgba(91, 155, 213, 0.22)",
    gloss: "#8FC0EA",
  }),
  teal: Object.freeze({
    token: "teal" as const,
    primary: "#4EA8A0",
    soft: "rgba(78, 168, 160, 0.22)",
    gloss: "#80C9C3",
  }),
  amber: Object.freeze({
    token: "amber" as const,
    primary: "#D29766",
    soft: "rgba(210, 151, 102, 0.22)",
    gloss: "#E8B98C",
  }),
  silver: Object.freeze({
    token: "silver" as const,
    primary: "#8896AB",
    soft: "rgba(136, 150, 171, 0.18)",
    gloss: "#A8B4C4",
  }),
} as const);

type ArchetypeDefinition = {
  readonly archetype: CharacterArtArchetype;
  readonly silhouette: CharacterArtSilhouetteKey;
  readonly wardrobe: CharacterArtWardrobeProfile;
  readonly accent: CharacterArtAccentToken;
  readonly prop: CharacterArtPropProfile;
  readonly headShape: CharacterArtHeadShapeProfile;
  readonly expression: CharacterArtExpressionProfile;
  readonly detailDensity: CharacterArtDetailDensity;
  readonly accessibilityDescription: string;
};

const ARCHETYPE_REGISTRY: Readonly<Record<string, ArchetypeDefinition>> = Object.freeze({
  ceo: Object.freeze({
    archetype: "ceo",
    silhouette: "structured-executive",
    wardrobe: "tailored-executive-jacket",
    accent: "brass",
    prop: "executive-tablet",
    headShape: "broad-authoritative",
    expression: "calm-authority",
    detailDensity: "rich",
    accessibilityDescription:
      "Miniature executive character with structured tailored jacket, brass accent lapel, and composed upright tablet — presenting calm, approachable authority.",
  }),
  cto: Object.freeze({
    archetype: "cto",
    silhouette: "technical-angular",
    wardrobe: "asymmetric-technical-jacket",
    accent: "steel-cyan",
    prop: "technical-tablet",
    headShape: "angular-precise",
    expression: "analytical-focus",
    detailDensity: "rich",
    accessibilityDescription:
      "Miniature technical character with asymmetric panel jacket, steel-cyan accent seams, and angled data tablet — presenting precise, analytical focus.",
  }),
  "role-family:regulatory-compliance": Object.freeze({
    archetype: "regulatory-compliance",
    silhouette: "tidy-measured",
    wardrobe: "conservative-blazer",
    accent: "teal",
    prop: "document-folder",
    headShape: "rounded-meticulous",
    expression: "quiet-attentiveness",
    detailDensity: "standard",
    accessibilityDescription:
      "Miniature compliance character with conservative blazer, teal accent, and held document folder — presenting quiet, meticulous attentiveness.",
  }),
  "role-family:operations": Object.freeze({
    archetype: "operations",
    silhouette: "practical-balanced",
    wardrobe: "smart-functional-jacket",
    accent: "amber",
    prop: "compact-organizer",
    headShape: "friendly-practical",
    expression: "approachable-readiness",
    detailDensity: "standard",
    accessibilityDescription:
      "Miniature operations character with smart functional jacket, warm amber accent, and compact organizer — presenting approachable, practical readiness.",
  }),
  "neutral-professional": Object.freeze({
    archetype: "neutral-professional",
    silhouette: "understated-neutral",
    wardrobe: "simple-blazer",
    accent: "silver",
    prop: "none",
    headShape: "standard-neutral",
    expression: "neutral-professional",
    detailDensity: "minimal",
    accessibilityDescription:
      "Miniature neutral professional character with understated blazer and no distinctive prop — a compatible, intentionally less role-specific fallback.",
  }),
});

const KNOWN_PRESENTATION_KEYS: readonly string[] = Object.freeze(Object.keys(ARCHETYPE_REGISTRY));

export function resolveCharacterArtPrototype(input: {
  readonly presentationKey: string;
}): CharacterArtPrototypeModel {
  const key = typeof input.presentationKey === "string" ? input.presentationKey.trim() : "";
  const definition = ARCHETYPE_REGISTRY[key] ?? ARCHETYPE_REGISTRY["neutral-professional"];
  const resolvedKey = ARCHETYPE_REGISTRY[key] ? key : "neutral-professional";

  return Object.freeze({
    presentationKey: resolvedKey,
    archetype: definition.archetype,
    silhouette: definition.silhouette,
    wardrobe: definition.wardrobe,
    accent: definition.accent,
    prop: definition.prop,
    headShape: definition.headShape,
    expression: definition.expression,
    detailDensity: definition.detailDensity,
    accessibilityDescription: definition.accessibilityDescription,
    presentationOnly: true,
    physicalPresenceClaimed: false,
    physicalLocationClaimed: false,
    canonicalStateWritable: false,
    semanticAnimationActive: false,
  });
}

export function getKnownArtPrototypeKeys(): readonly string[] {
  return KNOWN_PRESENTATION_KEYS;
}

export function hasDedicatedArtArchetype(presentationKey: string): boolean {
  return Object.prototype.hasOwnProperty.call(ARCHETYPE_REGISTRY, presentationKey);
}
