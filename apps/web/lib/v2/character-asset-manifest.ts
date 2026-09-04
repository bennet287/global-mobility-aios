import type {
  CharacterAnimationSetKey,
  CharacterLodClass,
  CharacterPresentationRecord,
  CharacterRigClass,
} from "./character-presentation";

export const CHARACTER_ASSET_MANIFEST_CONTRACT = Object.freeze({
  manifestId: "aios-v2.character-asset-manifest",
  contractVersion: "1.0.0",
  presentationOnly: true,
  presenceClaimed: false,
  canonicalStateWritable: false,
  missingAssetPolicy: "structured-css-miniature-fallback",
} as const);

export type CharacterAssetAvailability = "not-integrated" | "available";
export type CharacterAssetFormat = "glb";
export type CharacterFallbackRenderer = "css-miniature";

export type CharacterModelAsset = {
  readonly format: CharacterAssetFormat;
  readonly uri: string | null;
  readonly assetVersion: string | null;
  readonly contentHash: string | null;
  readonly availability: CharacterAssetAvailability;
};

export type CharacterAssetFallback = {
  readonly renderer: CharacterFallbackRenderer;
  readonly requiredWhenModelUnavailable: true;
  readonly preservesStructuredIdentity: true;
  readonly mayClaimCanonicalPresence: false;
  readonly mayActivateSemanticAnimation: false;
};

export type CharacterAssetManifestEntry = {
  readonly presentationKey: string;
  readonly bindingVersion: string;
  readonly model: CharacterModelAsset;
  readonly rigClass: CharacterRigClass;
  readonly lodClass: CharacterLodClass;
  readonly animationSetKey: CharacterAnimationSetKey;
  readonly materialProfileKey: string | null;
  readonly signaturePropAssetKey: string | null;
  readonly fallback: CharacterAssetFallback;
  readonly presentationOnly: true;
  readonly presenceClaimed: false;
  readonly canonicalStateWritable: false;
};

export type CharacterAssetManifest = {
  readonly manifestId: string;
  readonly contractVersion: string;
  readonly presentationOnly: true;
  readonly entries: readonly CharacterAssetManifestEntry[];
};

export type ResolvedCharacterAssetBinding = {
  readonly presentationKey: string;
  readonly manifestEntry: CharacterAssetManifestEntry | null;
  readonly compatible: boolean;
  readonly modelAvailable: boolean;
  readonly rendererMode: "glb" | CharacterFallbackRenderer;
  readonly modelUri: string | null;
  readonly limitation: string;
  readonly presentationOnly: true;
  readonly presenceClaimed: false;
  readonly canonicalStateWritable: false;
  readonly semanticAnimationActive: false;
};

const FALLBACK: CharacterAssetFallback = Object.freeze({
  renderer: "css-miniature",
  requiredWhenModelUnavailable: true,
  preservesStructuredIdentity: true,
  mayClaimCanonicalPresence: false,
  mayActivateSemanticAnimation: false,
});

function freezeEntry(entry: CharacterAssetManifestEntry): CharacterAssetManifestEntry {
  Object.freeze(entry.model);
  Object.freeze(entry.fallback);
  return Object.freeze(entry);
}

function unavailableModel(): CharacterModelAsset {
  return Object.freeze({
    format: "glb",
    uri: null,
    assetVersion: null,
    contentHash: null,
    availability: "not-integrated",
  });
}

const ENTRIES: readonly CharacterAssetManifestEntry[] = Object.freeze([
  freezeEntry({
    presentationKey: "ceo",
    bindingVersion: "1.0.0",
    model: unavailableModel(),
    rigClass: "rig-hero-humanoid-v1",
    lodClass: "lod-hero",
    animationSetKey: "aios-v2:animation-set:hero-ceo",
    materialProfileKey: null,
    signaturePropAssetKey: null,
    fallback: FALLBACK,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
  }),
  freezeEntry({
    presentationKey: "cto",
    bindingVersion: "1.0.0",
    model: unavailableModel(),
    rigClass: "rig-hero-humanoid-v1",
    lodClass: "lod-hero",
    animationSetKey: "aios-v2:animation-set:hero-cto",
    materialProfileKey: null,
    signaturePropAssetKey: null,
    fallback: FALLBACK,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
  }),
  freezeEntry({
    presentationKey: "role-family:regulatory-compliance",
    bindingVersion: "1.0.0",
    model: unavailableModel(),
    rigClass: "rig-standard-humanoid-v1",
    lodClass: "lod-standard",
    animationSetKey: "aios-v2:animation-set:family-regulatory-compliance",
    materialProfileKey: null,
    signaturePropAssetKey: null,
    fallback: FALLBACK,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
  }),
  freezeEntry({
    presentationKey: "role-family:operations",
    bindingVersion: "1.0.0",
    model: unavailableModel(),
    rigClass: "rig-standard-humanoid-v1",
    lodClass: "lod-standard",
    animationSetKey: "aios-v2:animation-set:family-operations",
    materialProfileKey: null,
    signaturePropAssetKey: null,
    fallback: FALLBACK,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
  }),
  freezeEntry({
    presentationKey: "neutral-professional",
    bindingVersion: "1.0.0",
    model: unavailableModel(),
    rigClass: "rig-standard-humanoid-v1",
    lodClass: "lod-standard",
    animationSetKey: "aios-v2:animation-set:neutral-professional",
    materialProfileKey: null,
    signaturePropAssetKey: null,
    fallback: FALLBACK,
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
  }),
]);

export const characterAssetManifest: CharacterAssetManifest = Object.freeze({
  manifestId: CHARACTER_ASSET_MANIFEST_CONTRACT.manifestId,
  contractVersion: CHARACTER_ASSET_MANIFEST_CONTRACT.contractVersion,
  presentationOnly: true,
  entries: ENTRIES,
});

const ENTRY_INDEX: ReadonlyMap<string, CharacterAssetManifestEntry> = new Map(
  characterAssetManifest.entries.map((entry) => [entry.presentationKey, entry]),
);

export function getCharacterPresentationKey(record: CharacterPresentationRecord): string {
  if (record.registration.kind === "exact-position") {
    return record.registration.canonicalPositionKey;
  }
  if (record.registration.kind === "role-family-fallback") {
    return record.registration.presentationPositionKey;
  }
  return "neutral-professional";
}

export function getCharacterAssetManifestEntry(
  presentationKey: string,
): CharacterAssetManifestEntry | null {
  return ENTRY_INDEX.get(presentationKey) ?? null;
}

function compatibilityLimitation(
  record: CharacterPresentationRecord,
  entry: CharacterAssetManifestEntry | null,
): string | null {
  if (!entry) {
    return "No versioned asset-manifest entry exists for this character presentation.";
  }
  if (entry.rigClass !== record.rigClass) {
    return "Asset-manifest rig class does not match the selected character presentation.";
  }
  if (entry.lodClass !== record.lodClass) {
    return "Asset-manifest LOD class does not match the selected character presentation.";
  }
  if (entry.animationSetKey !== record.animationSetKey) {
    return "Asset-manifest animation set does not match the selected character presentation.";
  }
  return null;
}

export function resolveCharacterAssetBinding(
  record: CharacterPresentationRecord,
): ResolvedCharacterAssetBinding {
  const presentationKey = getCharacterPresentationKey(record);
  const entry = getCharacterAssetManifestEntry(presentationKey);
  const incompatibility = compatibilityLimitation(record, entry);

  if (!entry || incompatibility) {
    return Object.freeze({
      presentationKey,
      manifestEntry: entry,
      compatible: false,
      modelAvailable: false,
      rendererMode: "css-miniature",
      modelUri: null,
      limitation:
        incompatibility ??
        "No compatible versioned character asset is available; use the structured CSS miniature fallback.",
      presentationOnly: true,
      presenceClaimed: false,
      canonicalStateWritable: false,
      semanticAnimationActive: false,
    });
  }

  const modelAvailable =
    entry.model.availability === "available" &&
    typeof entry.model.uri === "string" &&
    entry.model.uri.length > 0 &&
    typeof entry.model.assetVersion === "string" &&
    entry.model.assetVersion.length > 0 &&
    typeof entry.model.contentHash === "string" &&
    entry.model.contentHash.length > 0;

  return Object.freeze({
    presentationKey,
    manifestEntry: entry,
    compatible: true,
    modelAvailable,
    rendererMode: modelAvailable ? "glb" : entry.fallback.renderer,
    modelUri: modelAvailable ? entry.model.uri : null,
    limitation: modelAvailable
      ? "Versioned character asset is compatible with the selected presentation."
      : "Character presentation is registered, but no verified GLB asset is integrated yet; use the CSS miniature fallback.",
    presentationOnly: true,
    presenceClaimed: false,
    canonicalStateWritable: false,
    semanticAnimationActive: false,
  });
}
