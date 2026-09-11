import type { Group } from "three";
import { LIVING_HQ_HIGH_FIDELITY_ASSETS, type LivingHQAssetDefinition } from "./living-hq-high-fidelity-assets";

export type LivingHQLoadedAsset = {
  definition: LivingHQAssetDefinition;
  scene: Group;
};

export async function canLoadLivingHQAsset(definition: LivingHQAssetDefinition): Promise<boolean> {
  try {
    const response = await fetch(definition.uri, { method: "HEAD", cache: "force-cache" });
    if (!response.ok) return false;
    const rawLength = response.headers.get("content-length");
    if (!rawLength) return true;
    const contentLength = Number.parseInt(rawLength, 10);
    return Number.isFinite(contentLength) && contentLength <= definition.maxTransferBytes;
  } catch {
    return false;
  }
}

export async function detectLivingHQAssetPack(): Promise<boolean> {
  const hero = LIVING_HQ_HIGH_FIDELITY_ASSETS.find((asset) => asset.key === "hq-office-shell");
  const human = LIVING_HQ_HIGH_FIDELITY_ASSETS.find((asset) => asset.key === "professional-human-base");
  if (!hero || !human) return false;
  const [heroAvailable, humanAvailable] = await Promise.all([
    canLoadLivingHQAsset(hero),
    canLoadLivingHQAsset(human),
  ]);
  return heroAvailable && humanAvailable;
}

export async function loadLivingHQAsset(definition: LivingHQAssetDefinition): Promise<LivingHQLoadedAsset | null> {
  if (!(await canLoadLivingHQAsset(definition))) return null;
  try {
    const { GLTFLoader } = await import("three/examples/jsm/loaders/GLTFLoader.js");
    const loader = new GLTFLoader();
    const gltf = await loader.loadAsync(definition.uri);
    return { definition, scene: gltf.scene };
  } catch (error) {
    console.warn(`Living HQ optional asset failed to load: ${definition.key}`, error);
    return null;
  }
}

export async function loadLivingHQHighFidelityPack(): Promise<LivingHQLoadedAsset[]> {
  const results = await Promise.all(LIVING_HQ_HIGH_FIDELITY_ASSETS.map((asset) => loadLivingHQAsset(asset)));
  return results.filter((asset): asset is LivingHQLoadedAsset => asset !== null);
}
