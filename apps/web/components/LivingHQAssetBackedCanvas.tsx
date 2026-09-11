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

type LivingHQAssetBackedCanvasProps = {
  renderModel: LivingSceneRenderModel;
  assetPackAvailableOverride?: boolean;
};

export function LivingHQAssetBackedCanvas({
  renderModel,
  assetPackAvailableOverride,
}: LivingHQAssetBackedCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const modelRef = useRef(renderModel);
  const renderRef = useRef<(() => void) | null>(null);
  const activeMountsRef = useRef(0);
  modelRef.current = renderModel;

  /*
   * Renderer lifetime is deliberately independent from the 5s canonical scene refresh.
   * Canonical changes update metadata/overlays without rebuilding WebGL, reloading GLBs,
   * or re-allocating GPU resources. Visual quality must never tax organization execution.
   */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let disposed = false;
    let cleanup: (() => void) | null = null;
    let started = false;

    const start = async () => {
      if (started || disposed) return;
      started = true;

      const saveData = Boolean((navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData);
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const assetPackAvailable =
        assetPackAvailableOverride ?? (saveData ? false : await detectLivingHQAssetPack());
      if (disposed) return;

      const mode = chooseLivingHQHighFidelityMode({
        rendererReady: true,
        reducedMotion,
        saveData,
        assetPackAvailable,
      });
      canvas.dataset.renderMode = mode;
      canvas.dataset.assetPackAvailable = String(assetPackAvailable);
      canvas.dataset.assetPipelineBudgeted = "true";
      canvas.dataset.renderCadence = "on-demand";

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
      sun.shadow.mapSize.set(1024, 1024);
      scene.add(sun);

      const assetRoots: any[] = [];
      for (const loaded of loadedAssets) {
        const root: any = loaded.scene;
        root.traverse?.((node: any) => {
          if (!node?.isMesh) return;
          node.castShadow = loaded.definition.kind === "human" || loaded.definition.kind === "furniture";
          node.receiveShadow = true;
          if (node.material) {
            const materials = Array.isArray(node.material) ? node.material : [node.material];
            materials.forEach((material: any) => {
              if ("envMapIntensity" in material) material.envMapIntensity = Math.min(material.envMapIntensity || 1, 1.15);
            });
          }
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

      activeMountsRef.current += 1;
      canvas.dataset.rendererActiveMounts = String(activeMountsRef.current);
      canvas.dataset.assetCount = String(loadedAssets.length);
      canvas.dataset.presentationOnly = "true";
      canvas.dataset.presenceClaimed = "false";
      canvas.dataset.locomotionAllowed = "false";

      const render = () => {
        if (!disposed && document.visibilityState === "visible") renderer.render(scene, camera);
      };
      renderRef.current = render;

      const resize = () => {
        const rect = canvas.getBoundingClientRect();
        const width = Math.max(320, Math.floor(rect.width || 960));
        const height = Math.max(360, Math.floor(rect.height || 680));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        if (width < 600) {
          camera.position.set(9.8, 5.4, 24.2);
          camera.lookAt(0.2, 1.35, -0.8);
          camera.fov = 52;
        } else {
          camera.position.set(11.8, 5.2, 17.4);
          camera.lookAt(0, 1.5, -0.8);
          camera.fov = 46;
        }
        camera.updateProjectionMatrix();
        render();
      };

      resize();
      const observer = new ResizeObserver(resize);
      observer.observe(canvas);
      const handleVisibility = () => {
        if (document.visibilityState === "visible") render();
      };
      document.addEventListener("visibilitychange", handleVisibility);
      render();

      cleanup = () => {
        observer.disconnect();
        document.removeEventListener("visibilitychange", handleVisibility);
        renderRef.current = null;
        for (const root of assetRoots) {
          root.traverse?.((node: any) => {
            node.geometry?.dispose?.();
            if (Array.isArray(node.material)) node.material.forEach((material: any) => material?.dispose?.());
            else node.material?.dispose?.();
          });
        }
        renderer.dispose();
      };
    };

    const intersection = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting || entry.intersectionRatio > 0)) {
          void start();
          intersection.disconnect();
        }
      },
      { rootMargin: `${LIVING_HQ_HIGH_FIDELITY_BUDGET.lazyLoadMarginPx}px` },
    );
    intersection.observe(canvas);

    return () => {
      disposed = true;
      intersection.disconnect();
      cleanup?.();
    };
  }, [assetPackAvailableOverride]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const employeeCount = renderModel.departmentZones.reduce((sum, zone) => sum + zone.employeeSlots.length, 0);
    const activeCount = renderModel.departmentZones.reduce(
      (sum, zone) => sum + zone.employeeSlots.filter((slot) => ["working", "blocked", "awaiting_owner", "queued"].includes(slot.employee.semantic_state)).length,
      0,
    );
    const blockedCount = renderModel.departmentZones.reduce(
      (sum, zone) => sum + zone.employeeSlots.filter((slot) => slot.employee.semantic_state === "blocked").length,
      0,
    );
    canvas.dataset.canonicalEmployeeCount = String(employeeCount);
    canvas.dataset.canonicalActiveEmployees = String(activeCount);
    canvas.dataset.canonicalBlockedEmployees = String(blockedCount);
    renderRef.current?.();
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
