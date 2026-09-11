"use client";

import { useEffect, useMemo, useRef } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import { LIVING_HQ_HIGH_FIDELITY_BUDGET } from "../lib/living-hq-high-fidelity-assets";

const STATUS_COLOR: Record<string, number> = {
  working: 0x55b98a,
  blocked: 0xd76f59,
  awaiting_owner: 0xd5a74f,
  queued: 0x6d92ad,
  completed: 0x7e9b87,
};

export function LivingHQPhotorealCanvas({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const modelRef = useRef(renderModel);
  const statusMaterialsRef = useRef<Map<string, any>>(new Map());
  const semanticRevisionRef = useRef(0);
  modelRef.current = renderModel;

  const employeeSignature = useMemo(
    () => renderModel.departmentZones.flatMap((zone) => zone.employeeSlots.map((slot) => slot.employee.position_key)).join("|"),
    [renderModel],
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const saveData = Boolean((navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData);
    if (saveData) {
      canvas.dataset.renderMode = "css-fallback";
      return;
    }

    let disposed = false;
    let cleanup: (() => void) | null = null;

    void (async () => {
      const THREE = await import("three");
      if (disposed) return;

      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "high-performance" });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumDevicePixelRatio));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.12;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x9fb7c0);
      scene.fog = new THREE.FogExp2(0x9faead, 0.012);
      const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 140);
      camera.position.set(12.8, 4.65, 17.8);
      camera.lookAt(0.4, 1.55, -0.8);

      scene.add(new THREE.HemisphereLight(0xfff4df, 0x26383d, 1.95));
      const sun = new THREE.DirectionalLight(0xffebc4, 3.9);
      sun.position.set(-8, 12, 9);
      sun.castShadow = true;
      sun.shadow.mapSize.set(1024, 1024);
      scene.add(sun);
      const warm = new THREE.PointLight(0xffc878, 14, 28, 2);
      warm.position.set(-3.5, 5.2, 1.5);
      scene.add(warm);
      const boardWarm = new THREE.PointLight(0xffd39b, 8, 18, 2);
      boardWarm.position.set(6.8, 4.8, -4.5);
      scene.add(boardWarm);

      const resources: Array<{ dispose?: () => void }> = [];
      const addBox = (size: [number, number, number], position: [number, number, number], material: any, cast = true) => {
        const geometry = new THREE.BoxGeometry(...size);
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(...position);
        mesh.castShadow = cast;
        mesh.receiveShadow = true;
        scene.add(mesh);
        resources.push(geometry);
        return mesh;
      };
      const addCylinder = (
        radiusTop: number,
        radiusBottom: number,
        height: number,
        position: [number, number, number],
        material: any,
        segments = 12,
      ) => {
        const geometry = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, segments);
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(...position);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        scene.add(mesh);
        resources.push(geometry);
        return mesh;
      };

      const wood = new THREE.MeshStandardMaterial({ color: 0x9d714d, roughness: 0.61, metalness: 0.015 });
      const woodDark = new THREE.MeshStandardMaterial({ color: 0x5b4030, roughness: 0.65, metalness: 0.02 });
      const blackMetal = new THREE.MeshStandardMaterial({ color: 0x171d20, roughness: 0.42, metalness: 0.42 });
      const stone = new THREE.MeshStandardMaterial({ color: 0x9b9890, roughness: 0.84, metalness: 0.01 });
      const carpet = new THREE.MeshStandardMaterial({ color: 0x3f4948, roughness: 0.98 });
      const lounge = new THREE.MeshStandardMaterial({ color: 0xb8b0a5, roughness: 0.88 });
      const accent = new THREE.MeshStandardMaterial({ color: 0xa8653f, roughness: 0.78 });
      const glass = new THREE.MeshPhysicalMaterial({ color: 0xd8e7e9, roughness: 0.08, transmission: 0.78, transparent: true, opacity: 0.25, thickness: 0.1 });
      const screen = new THREE.MeshStandardMaterial({ color: 0x0b1519, roughness: 0.25, metalness: 0.28, emissive: 0x15353e, emissiveIntensity: 0.72 });
      const outside = new THREE.MeshStandardMaterial({ color: 0x86aab9, roughness: 0.95, emissive: 0x618b9d, emissiveIntensity: 0.33 });
      const lightMat = new THREE.MeshStandardMaterial({ color: 0xffefd0, roughness: 0.2, emissive: 0xffd49a, emissiveIntensity: 2.3 });
      resources.push(wood, woodDark, blackMetal, stone, carpet, lounge, accent, glass, screen, outside, lightMat);

      addBox([24, 0.24, 18], [0, -0.14, 0], wood, false);
      addBox([12.5, 0.055, 9.2], [-4.1, 0.03, 1.0], carpet, false);
      addBox([24, 0.18, 0.12], [0, 0.08, -8.78], blackMetal, false);
      addBox([24, 7.5, 0.12], [0, 3.75, -8.9], outside, false);
      for (let x = -10.5; x <= 10.5; x += 3.5) addBox([0.09, 7.0, 0.18], [x, 3.5, -8.72], blackMetal, false);
      addBox([0.16, 5.8, 8.7], [3.0, 2.9, -3.9], glass, false);
      addBox([0.16, 5.8, 7.8], [8.0, 2.9, -4.0], glass, false);
      for (let z = -7.0; z <= 7.0; z += 3.5) addBox([24, 0.16, 0.16], [0, 7.0, z], blackMetal, false);
      for (let i = 0; i < 5; i += 1) addBox([4.0, 0.045, 0.13], [-8 + i * 4.0, 6.78, -1.4 + (i % 2) * 3.2], lightMat, false);

      const workstation = (x: number, z: number, rotation = 0) => {
        const top = addBox([2.45, 0.13, 1.05], [x, 0.98, z], wood);
        top.rotation.y = rotation;
        const legA = addBox([0.10, 0.9, 0.10], [x - 0.95, 0.46, z], blackMetal);
        const legB = addBox([0.10, 0.9, 0.10], [x + 0.95, 0.46, z], blackMetal);
        legA.rotation.y = legB.rotation.y = rotation;
        const monitor = addBox([0.82, 0.53, 0.07], [x, 1.42, z - 0.34], screen);
        monitor.rotation.y = rotation;
        addBox([0.74, 0.83, 0.72], [x, 0.47, z + 0.88], blackMetal);
      };
      [-7.1, -4.0, -0.9].forEach((x, idx) => workstation(x, 1.0 + (idx % 2) * 2.6));
      [-5.6, -2.5].forEach((x) => workstation(x, 4.9));
      [0.2, 2.65].forEach((x) => workstation(x, 2.4));

      workstation(5.15, -1.7, 0.03);
      workstation(5.15, -4.5, -0.03);
      addBox([3.9, 1.55, 0.14], [5.15, 2.1, -6.9], blackMetal);
      for (let i = 0; i < 3; i += 1) addBox([0.92, 0.56, 0.08], [4.0 + i * 1.15, 2.2, -6.78], screen);

      addBox([4.8, 0.18, 1.75], [7.55, 1.05, -3.9], woodDark);
      for (let i = 0; i < 8; i += 1) {
        const side = i < 4 ? -1 : 1;
        const slot = i % 4;
        addBox([0.66, 0.86, 0.68], [6.05 + slot * 1.0, 0.48, -3.9 + side * 1.42], blackMetal);
      }

      addBox([3.6, 0.68, 1.12], [6.3, 0.43, 4.7], lounge);
      addBox([1.12, 0.72, 2.75], [8.45, 0.45, 4.1], lounge);
      addCylinder(0.82, 0.82, 0.26, [6.9, 0.32, 2.95], blackMetal, 28);
      addBox([3.6, 1.0, 0.36], [9.8, 0.55, 6.15], blackMetal);
      addBox([3.2, 0.06, 0.14], [9.8, 1.03, 5.95], lightMat, false);

      const plantAt = (x: number, z: number, scale = 1) => {
        addCylinder(0.30 * scale, 0.40 * scale, 0.52 * scale, [x, 0.26 * scale, z], stone, 14);
        const leafMat = new THREE.MeshStandardMaterial({ color: 0x315d3d, roughness: 0.92 });
        resources.push(leafMat);
        const offsets = [[0, 0.98, 0], [-0.28, 0.82, 0.10], [0.25, 0.78, -0.12], [-0.10, 1.20, -0.08], [0.17, 1.09, 0.14]];
        offsets.forEach(([ox, oy, oz], idx) => {
          const geo = new THREE.SphereGeometry((0.34 + (idx % 2) * 0.07) * scale, 9, 6);
          const leaf = new THREE.Mesh(geo, leafMat);
          leaf.scale.set(0.65, 1.35, 0.56);
          leaf.rotation.z = (idx - 2) * 0.18;
          leaf.position.set(x + ox * scale, oy * scale, z + oz * scale);
          leaf.castShadow = true;
          scene.add(leaf);
          resources.push(geo);
        });
      };
      [[-10, -6.9, 1.35], [-8.8, 6.4, 1.2], [-1.0, -6.7, 1.0], [2.25, 6.2, 1.15], [9.4, -6.8, 1.25], [10.4, 1.4, 1.0]].forEach(([x, z, scale]) => plantAt(x, z, scale));

      statusMaterialsRef.current.clear();
      const employees = modelRef.current.departmentZones.flatMap((zone) => zone.employeeSlots.map((slot) => slot));
      const isMobile = window.matchMedia("(max-width: 760px)").matches;
      const humanCap = isMobile
        ? LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumVisibleHumansMobile
        : LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumVisibleHumansDesktop;
      const visibleEmployees = employees.slice(0, humanCap);
      visibleEmployees.forEach(({ employee }, index) => {
        const row = Math.floor(index / 8);
        const col = index % 8;
        const x = -7.0 + col * 2.05;
        const z = 0.95 + row * 2.25;
        const skinMat = new THREE.MeshStandardMaterial({ color: [0xc99372, 0x9f6a4c, 0xd9ac88, 0x84553d, 0xc18461][index % 5], roughness: 0.72 });
        const suitMat = new THREE.MeshStandardMaterial({ color: [0x242d33, 0x343b42, 0x1d2529, 0x3b3937, 0x29333a][index % 5], roughness: 0.73 });
        const trouserMat = new THREE.MeshStandardMaterial({ color: 0x202629, roughness: 0.78 });
        const hairMat = new THREE.MeshStandardMaterial({ color: [0x191716, 0x33241d, 0x181818, 0x503528][index % 4], roughness: 0.86 });
        const headGeo = new THREE.SphereGeometry(0.17, 12, 8);
        const hairGeo = new THREE.SphereGeometry(0.175, 10, 6);
        const torsoGeo = new THREE.CapsuleGeometry(0.21, 0.58, 5, 10);
        const legGeo = new THREE.CylinderGeometry(0.075, 0.085, 0.62, 8);
        const head = new THREE.Mesh(headGeo, skinMat);
        const hair = new THREE.Mesh(hairGeo, hairMat);
        const torso = new THREE.Mesh(torsoGeo, suitMat);
        const legLeft = new THREE.Mesh(legGeo, trouserMat);
        const legRight = new THREE.Mesh(legGeo, trouserMat);
        torso.position.set(x, 1.02, z);
        head.position.set(x, 1.61, z);
        hair.scale.set(1.02, 0.52, 1.03);
        hair.position.set(x, 1.70, z - 0.01);
        legLeft.position.set(x - 0.09, 0.43, z);
        legRight.position.set(x + 0.09, 0.43, z);
        torso.castShadow = head.castShadow = hair.castShadow = legLeft.castShadow = legRight.castShadow = true;
        scene.add(torso, head, hair, legLeft, legRight);

        const statusGeo = new THREE.SphereGeometry(0.045, 8, 6);
        const statusColor = STATUS_COLOR[employee.semantic_state] ?? 0x8b969c;
        const statusMat = new THREE.MeshStandardMaterial({ color: statusColor, emissive: statusColor, emissiveIntensity: 1.25 });
        const status = new THREE.Mesh(statusGeo, statusMat);
        status.position.set(x + 0.30, 1.70, z);
        scene.add(status);
        statusMaterialsRef.current.set(employee.position_key, statusMat);
        resources.push(headGeo, hairGeo, torsoGeo, legGeo, skinMat, suitMat, trouserMat, hairMat, statusGeo, statusMat);
      });

      canvas.dataset.renderMode = "three-procedural-realism";
      canvas.dataset.presentationOnly = "true";
      canvas.dataset.presenceClaimed = "false";
      canvas.dataset.locomotionAllowed = "false";
      canvas.dataset.visibleHumans = String(visibleEmployees.length);
      canvas.dataset.humanBudget = isMobile ? "mobile" : "desktop";

      const resize = () => {
        const rect = canvas.getBoundingClientRect();
        const width = Math.max(320, Math.floor(rect.width || 960));
        const height = Math.max(360, Math.floor(rect.height || 680));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        if (width < 600) {
          camera.position.set(9.4, 5.15, 24.8);
          camera.lookAt(0.15, 1.35, -1.0);
          camera.fov = 52;
        } else {
          camera.position.set(12.8, 4.65, 17.8);
          camera.lookAt(0.4, 1.55, -0.8);
          camera.fov = 48;
        }
        camera.updateProjectionMatrix();
      };
      resize();
      const observer = new ResizeObserver(resize);
      observer.observe(canvas);

      let frame = 0;
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const animate = () => {
        if (disposed) return;
        if (!reducedMotion && canvas.clientWidth >= 600) {
          const t = performance.now() * 0.000035;
          camera.position.x = 12.8 + Math.sin(t) * 0.20;
          camera.lookAt(0.4, 1.55, -0.8);
        }
        renderer.render(scene, camera);
        frame = requestAnimationFrame(animate);
      };
      animate();

      cleanup = () => {
        observer.disconnect();
        cancelAnimationFrame(frame);
        statusMaterialsRef.current.clear();
        resources.forEach((resource) => resource.dispose?.());
        renderer.dispose();
      };
    })();

    return () => {
      disposed = true;
      cleanup?.();
    };
  }, [employeeSignature]);

  useEffect(() => {
    semanticRevisionRef.current += 1;
    const canvas = canvasRef.current;
    if (canvas) canvas.dataset.semanticRevision = String(semanticRevisionRef.current);
    for (const zone of renderModel.departmentZones) {
      for (const { employee } of zone.employeeSlots) {
        const material = statusMaterialsRef.current.get(employee.position_key);
        if (!material) continue;
        const color = STATUS_COLOR[employee.semantic_state] ?? 0x8b969c;
        material.color?.setHex?.(color);
        material.emissive?.setHex?.(color);
        material.emissiveIntensity = employee.semantic_state === "blocked" ? 1.65 : 1.1;
      }
    }
  }, [renderModel]);

  return (
    <canvas
      ref={canvasRef}
      className="living-hq-photoreal-canvas"
      aria-hidden="true"
      data-presentation-only="true"
      data-authority="none"
    />
  );
}
