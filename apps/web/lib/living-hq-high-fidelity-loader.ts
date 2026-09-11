import type { Group } from "three";
import { LIVING_HQ_HIGH_FIDELITY_ASSETS, type LivingHQAssetDefinition } from "./living-hq-high-fidelity-assets";

export type LivingHQLoadedAsset = {
  definition: LivingHQAssetDefinition;
  scene: Group;
  triangleCount: number;
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

function countSceneTriangles(scene: Group): number {
  let triangles = 0;
  scene.traverse((node: any) => {
    if (!node?.isMesh || !node.geometry) return;
    const geometry = node.geometry;
    if (geometry.index?.count) {
      triangles += Math.floor(geometry.index.count / 3);
      return;
    }
    const positions = geometry.attributes?.position?.count;
    if (typeof positions === "number") triangles += Math.floor(positions / 3);
  });
  return triangles;
}

function disposeScene(scene: Group): void {
  scene.traverse((node: any) => {
    node.geometry?.dispose?.();
    const materials = Array.isArray(node.material) ? node.material : node.material ? [node.material] : [];
    materials.forEach((material: any) => material?.dispose?.());
  });
}

export async function loadLivingHQAsset(definition: LivingHQAssetDefinition): Promise<LivingHQLoadedAsset | null> {
  if (!(await canLoadLivingHQAsset(definition))) return null;
  try {
    const { GLTFLoader } = await import("three/examples/jsm/loaders/GLTFLoader.js");
    const loader = new GLTFLoader();
    const gltf = await loader.loadAsync(definition.uri);
    const triangleCount = countSceneTriangles(gltf.scene);
    if (triangleCount > definition.maxTriangles) {
      console.warn(
        `Living HQ optional asset rejected by triangle budget: ${definition.key} (${triangleCount} > ${definition.maxTriangles})`,
      );
      disposeScene(gltf.scene);
      return null;
    }
    return { definition, scene: gltf.scene, triangleCount };
  } catch (error) {
    console.warn(`Living HQ optional asset failed to load: ${definition.key}`, error);
    return null;
  }
}

export async function loadLivingHQHighFidelityPack(): Promise<LivingHQLoadedAsset[]> {
  const results = await Promise.all(LIVING_HQ_HIGH_FIDELITY_ASSETS.map((asset) => loadLivingHQAsset(asset)));
  return results.filter((asset): asset is LivingHQLoadedAsset => asset !== null);
}
