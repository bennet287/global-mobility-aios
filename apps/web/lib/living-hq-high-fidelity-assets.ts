export type LivingHQAssetKind = "environment" | "human" | "furniture" | "prop";
export type LivingHQAssetLOD = "hero" | "standard" | "fallback";

export type LivingHQAssetDefinition = {
  key: string;
  kind: LivingHQAssetKind;
  lod: LivingHQAssetLOD;
  uri: string;
  maxTransferBytes: number;
  maxTriangles: number;
  instanced: boolean;
  optional: boolean;
};

export const LIVING_HQ_HIGH_FIDELITY_ASSETS: readonly LivingHQAssetDefinition[] = [
  {
    key: "hq-office-shell",
    kind: "environment",
    lod: "hero",
    uri: "/assets/living-hq/hq-office-shell.glb",
    maxTransferBytes: 1_800_000,
    maxTriangles: 90_000,
    instanced: false,
    optional: true,
  },
  {
    key: "professional-human-base",
    kind: "human",
    lod: "standard",
    uri: "/assets/living-hq/professional-human-base.glb",
    maxTransferBytes: 620_000,
    maxTriangles: 18_000,
    instanced: true,
    optional: true,
  },
  {
    key: "office-furniture-kit",
    kind: "furniture",
    lod: "standard",
    uri: "/assets/living-hq/office-furniture-kit.glb",
    maxTransferBytes: 820_000,
    maxTriangles: 32_000,
    instanced: true,
    optional: true,
  },
  {
    key: "office-props-kit",
    kind: "prop",
    lod: "fallback",
    uri: "/assets/living-hq/office-props-kit.glb",
    maxTransferBytes: 320_000,
    maxTriangles: 12_000,
    instanced: true,
    optional: true,
  },
] as const;

export const LIVING_HQ_HIGH_FIDELITY_BUDGET = {
  maximumOptionalTransferBytes: 3_600_000,
  maximumVisibleHumansDesktop: 28,
  maximumVisibleHumansMobile: 10,
  maximumDevicePixelRatio: 1.75,
  targetOrdinaryFps: 50,
  sustainedFpsFloor: 35,
  lazyLoadMarginPx: 420,
} as const;

export type LivingHQHighFidelityMode = "css-fallback" | "three-procedural" | "three-assets";

export function chooseLivingHQHighFidelityMode(input: {
  rendererReady: boolean;
  reducedMotion: boolean;
  saveData: boolean;
  assetPackAvailable: boolean;
}): LivingHQHighFidelityMode {
  if (!input.rendererReady || input.saveData) return "css-fallback";
  if (input.assetPackAvailable && !input.reducedMotion) return "three-assets";
  return "three-procedural";
}

export function totalOptionalTransferBudget(): number {
  return LIVING_HQ_HIGH_FIDELITY_ASSETS.reduce((sum, asset) => sum + asset.maxTransferBytes, 0);
}
