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

const STATUS_COLOR: Record<string, number> = {
  working: 0x55b98a,
  blocked: 0xd76f59,
  awaiting_owner: 0xd5a74f,
  queued: 0x6d92ad,
  completed: 0x7e9b87,
};

const DESK_ANCHORS: ReadonlyArray<readonly [number, number]> = [
  [-7.35, 1.42], [-4.35, 3.92], [-1.35, 1.42], [-5.95, 5.92],
  [-2.95, 5.92], [0.05, 5.92], [0.55, 3.35], [2.95, 3.35],
  [5.35, -0.85], [5.35, -3.85], [6.10, -2.75], [7.15, -2.75],
  [8.20, -2.75], [9.20, -2.75], [6.10, -5.55], [7.15, -5.55],
];

export function LivingHQAssetBackedCanvas({
  renderModel,
  assetPackAvailableOverride,
}: LivingHQAssetBackedCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const modelRef = useRef(renderModel);
  const renderRef = useRef<(() => void) | null>(null);
  const statusMaterialsRef = useRef<Map<string, any>>(new Map());
  const activeMountsRef = useRef(0);
  modelRef.current = renderModel;

  /*
   * Renderer lifetime is independent from the canonical scene refresh. Canonical changes
   * recolor tiny semantic markers and request one render; they never rebuild WebGL, reload
   * GLBs, or create a continuous animation loop. AIOS execution remains the priority.
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
      const assetPackAvailable = assetPackAvailableOverride ?? (saveData ? false : await detectLivingHQAssetPack());
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
      renderer.toneMappingExposure = 1.04;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xa8b3ae);
      scene.fog = new THREE.Fog(0xb4bbb5, 24, 62);
      const camera = new THREE.PerspectiveCamera(43, 1, 0.1, 160);

      scene.add(new THREE.HemisphereLight(0xfff5df, 0x26383d, 1.72));
      const sun = new THREE.DirectionalLight(0xffe9c3, 3.15);
      sun.position.set(-7, 11, 8);
      sun.castShadow = true;
      sun.shadow.mapSize.set(1024, 1024);
      scene.add(sun);

      const assetRoots: any[] = [];
      let humanSource: any | null = null;

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

        if (loaded.definition.kind === "human") {
          humanSource = root;
          continue;
        }

        /* Environment/furniture/prop packs are authored in the shared HQ coordinate system. */
        root.position?.set?.(0, 0, 0);
        root.scale?.set?.(1, 1, 1);
        scene.add(root);
        assetRoots.push(root);
      }

      statusMaterialsRef.current.clear();
      const employees = modelRef.current.departmentZones.flatMap((zone) => zone.employeeSlots.map((slot) => slot.employee));
      const isMobile = window.matchMedia("(max-width: 760px)").matches;
      const humanCap = isMobile
        ? LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumVisibleHumansMobile
        : LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumVisibleHumansDesktop;
      const visibleEmployees = employees.slice(0, humanCap);

      if (humanSource) {
        visibleEmployees.forEach((employee, index) => {
          const anchor = DESK_ANCHORS[index % DESK_ANCHORS.length];
          const overflowRow = Math.floor(index / DESK_ANCHORS.length);
          const clone = humanSource.clone?.(true) ?? null;
          if (!clone) return;
          clone.position?.set?.(anchor[0] + overflowRow * 0.5, 0, anchor[1] + overflowRow * 0.6);
          clone.rotation.y = index % 4 === 3 ? -0.18 : Math.PI;
          clone.scale?.set?.(0.96, 0.96, 0.96);
          scene.add(clone);
          assetRoots.push(clone);

          const statusColor = STATUS_COLOR[employee.semantic_state] ?? 0x8b969c;
          const statusGeometry = new THREE.SphereGeometry(0.04, 8, 6);
          const statusMaterial = new THREE.MeshStandardMaterial({
            color: statusColor,
            emissive: statusColor,
            emissiveIntensity: employee.semantic_state === "blocked" ? 1.55 : 1.05,
          });
          const status = new THREE.Mesh(statusGeometry, statusMaterial);
          status.position.set(anchor[0] + 0.28 + overflowRow * 0.5, 1.9, anchor[1] + overflowRow * 0.6);
          scene.add(status);
          assetRoots.push(status);
          statusMaterialsRef.current.set(employee.position_key, statusMaterial);
        });
      }

      activeMountsRef.current += 1;
      canvas.dataset.rendererActiveMounts = String(activeMountsRef.current);
      canvas.dataset.assetCount = String(loadedAssets.length);
      canvas.dataset.assetVisibleHumans = String(humanSource ? visibleEmployees.length : 0);
      canvas.dataset.presentationOnly = "true";
      canvas.dataset.presenceClaimed = "false";
      canvas.dataset.locomotionAllowed = "false";
      canvas.dataset.canonicalPlacementOnly = "true";

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
          camera.position.set(7.2, 9.4, 15.8);
          camera.lookAt(0.15, 0.9, -1.0);
          camera.fov = 47;
        } else {
          camera.position.set(10.6, 8.4, 14.2);
          camera.lookAt(0.35, 1.0, -1.2);
          camera.fov = 41;
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
        statusMaterialsRef.current.clear();
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

    for (const zone of renderModel.departmentZones) {
      for (const { employee } of zone.employeeSlots) {
        const material = statusMaterialsRef.current.get(employee.position_key);
        if (!material) continue;
        const color = STATUS_COLOR[employee.semantic_state] ?? 0x8b969c;
        material.color?.setHex?.(color);
        material.emissive?.setHex?.(color);
        material.emissiveIntensity = employee.semantic_state === "blocked" ? 1.55 : 1.05;
      }
    }
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
