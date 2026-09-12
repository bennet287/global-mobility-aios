"use client";

import { useEffect, useState } from "react";

import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import { chooseLivingHQHighFidelityMode, type LivingHQHighFidelityMode } from "../lib/living-hq-high-fidelity-assets";
import { detectLivingHQAssetPack } from "../lib/living-hq-high-fidelity-loader";
import { LivingHQAssetBackedCanvas } from "./LivingHQAssetBackedCanvas";
import { LivingHQPhotorealCanvas } from "./LivingHQPhotorealCanvas";

type RendererMode = LivingHQHighFidelityMode | "detecting";

export function LivingHQAdaptiveRenderer({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const [mode, setMode] = useState<RendererMode>("detecting");

  useEffect(() => {
    let disposed = false;
    void (async () => {
      const saveData = Boolean((navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData);
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const rendererReady = typeof WebGLRenderingContext !== "undefined";
      const assetPackAvailable = rendererReady && !saveData ? await detectLivingHQAssetPack() : false;
      if (disposed) return;
      setMode(chooseLivingHQHighFidelityMode({ rendererReady, reducedMotion, saveData, assetPackAvailable }));
    })();
    return () => {
      disposed = true;
    };
  }, []);

  if (mode === "three-assets") {
    return <LivingHQAssetBackedCanvas renderModel={renderModel} assetPackAvailableOverride />;
  }

  if (mode === "three-procedural") {
    return <LivingHQPhotorealCanvas renderModel={renderModel} />;
  }

  /* During detection/save-data fallback, the semantic DOM/CSS architecture remains visible. */
  return null;
}
