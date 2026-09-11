"use client";

import { useEffect, useRef } from "react";

import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import {
  chooseLivingHQHighFidelityMode,
  LIVING_HQ_HIGH_FIDELITY_BUDGET,
} from "../lib/living-hq-high-fidelity-assets";
import {
  detectLivingHQAssetPack,
  loadLivingHQHighFidelityPack,
} from "../lib/living-hq-high-fidelity-loader";

export function LivingHQAssetBackedCanvas({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let disposed = false;
    let cleanup: (() => void) | null = null;

    void (async () => {
      const saveData = Boolean((navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData);
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const assetPackAvailable = saveData ? false : await detectLivingHQAssetPack();
      if (disposed) return;

      const mode = chooseLivingHQHighFidelityMode({
        rendererReady: true,
        reducedMotion,
        saveData,
        assetPackAvailable,
      });
      canvas.dataset.renderMode = mode;
      canvas.dataset.assetPackAvailable = String(assetPackAvailable);

      if (mode !== "three-assets") return;

      const [THREE, loadedAssets] = await Promise.all([
        import("three"),
        loadLivingHQHighFidelityPack(),
      ]);
      if (disposed || loadedAssets.length === 0) return;

      const renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumDevicePixelRatio));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.06;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      const scene = new THREE.Scene();
      scene.background = null;
      const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 160);
      camera.position.set(11.8, 5.2, 17.4);
      camera.lookAt(0, 1.5, -0.8);

      scene.add(new THREE.HemisphereLight(0xfff5df, 0x26383d, 1.75));
      const sun = new THREE.DirectionalLight(0xffe9c3, 3.25);
      sun.position.set(-7, 11, 8);
      sun.castShadow = true;
      scene.add(sun);

      const assetRoots: any[] = [];
      for (const loaded of loadedAssets) {
        const root: any = loaded.scene;
        root.traverse?.((node: any) => {
          if (!node?.isMesh) return;
          node.castShadow = loaded.definition.kind !== "environment";
          node.receiveShadow = true;
        });

        if (loaded.definition.kind === "environment") {
          root.scale?.set?.(1, 1, 1);
          root.position?.set?.(0, 0, 0);
        } else if (loaded.definition.kind === "furniture") {
          root.scale?.set?.(0.92, 0.92, 0.92);
          root.position?.set?.(-2.8, 0, 1.2);
        } else if (loaded.definition.kind === "prop") {
          root.scale?.set?.(0.9, 0.9, 0.9);
          root.position?.set?.(4.5, 0, 3.4);
        } else if (loaded.definition.kind === "human") {
          root.scale?.set?.(1, 1, 1);
          root.position?.set?.(-5.0, 0, 1.0);
        }

        scene.add(root);
        assetRoots.push(root);
      }

      canvas.dataset.assetCount = String(loadedAssets.length);
      canvas.dataset.canonicalEmployeeCount = String(
        renderModel.departmentZones.reduce((sum, zone) => sum + zone.employeeSlots.length, 0),
      );
      canvas.dataset.presentationOnly = "true";
      canvas.dataset.presenceClaimed = "false";
      canvas.dataset.locomotionAllowed = "false";

      const render = () => renderer.render(scene, camera);
      const resize = () => {
        const rect = canvas.getBoundingClientRect();
        const width = Math.max(320, Math.floor(rect.width || 960));
        const height = Math.max(360, Math.floor(rect.height || 680));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        render();
      };

      resize();
      const observer = new ResizeObserver(resize);
      observer.observe(canvas);
      render();

      cleanup = () => {
        observer.disconnect();
        for (const root of assetRoots) {
          root.traverse?.((node: any) => {
            node.geometry?.dispose?.();
            if (Array.isArray(node.material)) node.material.forEach((material: any) => material?.dispose?.());
            else node.material?.dispose?.();
          });
        }
        renderer.dispose();
      };
    })();

    return () => {
      disposed = true;
      cleanup?.();
    };
  }, [renderModel]);

  return (
    <canvas
      ref={canvasRef}
      className="living-hq-asset-canvas"
      aria-hidden="true"
      data-presentation-only="true"
      data-authority="none"
      data-render-mode="detecting"
    />
  );
}
