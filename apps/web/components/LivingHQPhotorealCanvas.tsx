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
  const renderFrameRef = useRef<(() => void) | null>(null);
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
      renderer.toneMappingExposure = 1.08;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x93a9b2);
      scene.fog = new THREE.Fog(0xa5b3b2, 28, 70);
      const camera = new THREE.PerspectiveCamera(44, 1, 0.1, 140);

      const renderFrame = () => {
        if (!disposed && document.visibilityState === "visible") renderer.render(scene, camera);
      };
      renderFrameRef.current = renderFrame;

      scene.add(new THREE.HemisphereLight(0xfff5e7, 0x263136, 1.65));
      const sun = new THREE.DirectionalLight(0xffead1, 3.1);
      sun.position.set(-10, 13, 8);
      sun.castShadow = true;
      sun.shadow.mapSize.set(1024, 1024);
      sun.shadow.camera.near = 1;
      sun.shadow.camera.far = 45;
      scene.add(sun);
      const interiorWarm = new THREE.PointLight(0xffc98a, 8.5, 26, 2);
      interiorWarm.position.set(-4.0, 4.6, 2.4);
      scene.add(interiorWarm);
      const boardWarm = new THREE.PointLight(0xffd7a5, 5.5, 18, 2);
      boardWarm.position.set(7.0, 4.1, -4.8);
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

      const timber = new THREE.MeshStandardMaterial({ color: 0x9d724f, roughness: 0.68, metalness: 0.01 });
      const timberDark = new THREE.MeshStandardMaterial({ color: 0x553b2d, roughness: 0.7, metalness: 0.01 });
      const blackMetal = new THREE.MeshStandardMaterial({ color: 0x151a1d, roughness: 0.38, metalness: 0.48 });
      const charcoal = new THREE.MeshStandardMaterial({ color: 0x242a2c, roughness: 0.82, metalness: 0.08 });
      const stone = new THREE.MeshStandardMaterial({ color: 0x918d86, roughness: 0.88 });
      const carpet = new THREE.MeshStandardMaterial({ color: 0x4b514f, roughness: 0.99 });
      const lounge = new THREE.MeshStandardMaterial({ color: 0xc0b8ad, roughness: 0.91 });
      const glass = new THREE.MeshPhysicalMaterial({ color: 0xe5eff0, roughness: 0.06, transmission: 0.86, transparent: true, opacity: 0.18, thickness: 0.08 });
      const screen = new THREE.MeshStandardMaterial({ color: 0x081216, roughness: 0.2, metalness: 0.34, emissive: 0x14323a, emissiveIntensity: 0.8 });
      const outside = new THREE.MeshStandardMaterial({ color: 0x7e9eab, roughness: 1, emissive: 0x4a6974, emissiveIntensity: 0.22 });
      const lightMat = new THREE.MeshStandardMaterial({ color: 0xfff0d4, roughness: 0.18, emissive: 0xffd6a0, emissiveIntensity: 2.2 });
      const planter = new THREE.MeshStandardMaterial({ color: 0x303638, roughness: 0.78, metalness: 0.1 });
      const green = new THREE.MeshStandardMaterial({ color: 0x315c3c, roughness: 0.95 });
      resources.push(timber, timberDark, blackMetal, charcoal, stone, carpet, lounge, glass, screen, outside, lightMat, planter, green);

      /* One continuous office shell: timber circulation, carpet workfield, glazed rooms, skyline and exposed ceiling. */
      addBox([26, 0.22, 20], [0, -0.13, 0], timber, false);
      addBox([13.6, 0.045, 10.4], [-4.0, 0.025, 1.1], carpet, false);
      addBox([26, 7.6, 0.10], [0, 3.8, -9.65], outside, false);
      for (let x = -11.6; x <= 11.6; x += 2.9) addBox([0.065, 7.1, 0.15], [x, 3.55, -9.51], blackMetal, false);
      for (let x = -10.5; x <= 11.0; x += 2.35) {
        const h = 1.1 + ((Math.abs(x * 7) % 5) * 0.35);
        addBox([1.18, h, 0.38], [x, h / 2, -9.15], charcoal, false);
      }
      addBox([0.12, 5.9, 9.2], [3.3, 2.95, -4.0], glass, false);
      addBox([0.12, 5.9, 8.0], [8.35, 2.95, -4.2], glass, false);
      addBox([5.0, 0.10, 0.12], [5.82, 5.85, -8.0], blackMetal, false);
      for (let z = -7.2; z <= 7.2; z += 3.2) addBox([26, 0.13, 0.13], [0, 7.0, z], blackMetal, false);
      for (let x = -10.5; x <= 10.5; x += 4.2) addBox([0.12, 7.0, 20], [x, 7.06, 0], charcoal, false);
      for (let i = 0; i < 7; i += 1) addBox([3.4, 0.035, 0.09], [-10 + i * 3.3, 6.72, -2.3 + (i % 2) * 4.6], lightMat, false);

      const workstation = (x: number, z: number, rotation = 0) => {
        const top = addBox([2.5, 0.12, 1.0], [x, 0.98, z], timber);
        top.rotation.y = rotation;
        const rail = addBox([2.15, 0.08, 0.08], [x, 0.58, z], blackMetal);
        rail.rotation.y = rotation;
        const monitor = addBox([0.82, 0.52, 0.055], [x, 1.43, z - 0.33], screen);
        monitor.rotation.y = rotation;
        addBox([0.68, 0.72, 0.64], [x, 0.44, z + 0.86], charcoal);
      };
      [-7.4, -4.4, -1.4].forEach((x, index) => workstation(x, 0.6 + (index % 2) * 2.5));
      [-6.0, -3.0, 0.0].forEach((x) => workstation(x, 5.1));
      [0.5, 2.9].forEach((x) => workstation(x, 2.55));
      workstation(5.35, -1.7);
      workstation(5.35, -4.7);
      addBox([4.2, 1.52, 0.13], [5.25, 2.05, -7.15], charcoal);
      for (let i = 0; i < 3; i += 1) addBox([0.98, 0.58, 0.06], [4.0 + i * 1.22, 2.18, -7.05], screen);

      /* Board room and lounge read as real furniture groups, not room cards. */
      addBox([5.05, 0.17, 1.8], [7.65, 1.05, -4.15], timberDark);
      for (let i = 0; i < 8; i += 1) {
        const side = i < 4 ? -1 : 1;
        const slot = i % 4;
        addBox([0.62, 0.82, 0.63], [6.05 + slot * 1.05, 0.48, -4.15 + side * 1.42], charcoal);
      }
      addBox([3.75, 0.64, 1.16], [6.4, 0.43, 4.8], lounge);
      addBox([1.15, 0.70, 2.9], [8.55, 0.45, 4.15], lounge);
      addCylinder(0.86, 0.86, 0.25, [6.95, 0.31, 3.0], blackMetal, 28);
      addBox([3.9, 0.96, 0.35], [10.0, 0.52, 6.3], charcoal);
      addBox([3.45, 0.05, 0.10], [10.0, 1.01, 6.08], lightMat, false);

      const plantAt = (x: number, z: number, scale = 1) => {
        addCylinder(0.30 * scale, 0.38 * scale, 0.50 * scale, [x, 0.25 * scale, z], planter, 14);
        const offsets = [[0, 0.96, 0], [-0.27, 0.80, 0.10], [0.24, 0.77, -0.12], [-0.10, 1.18, -0.08], [0.18, 1.07, 0.14]];
        offsets.forEach(([ox, oy, oz], index) => {
          const geo = new THREE.SphereGeometry((0.34 + (index % 2) * 0.06) * scale, 8, 6);
          const leaf = new THREE.Mesh(geo, green);
          leaf.scale.set(0.58, 1.48, 0.46);
          leaf.rotation.z = (index - 2) * 0.18;
          leaf.position.set(x + ox * scale, oy * scale, z + oz * scale);
          leaf.castShadow = true;
          scene.add(leaf);
          resources.push(geo);
        });
      };
      [[-10.2, -7.2, 1.4], [-9.4, 6.6, 1.25], [-1.3, -6.8, 1.05], [2.25, 6.4, 1.15], [9.7, -7.0, 1.3], [10.6, 1.6, 1.0]].forEach(([x, z, scale]) => plantAt(x, z, scale));

      /* Shared human geometry/materials keep the procedural fallback cheap while improving adult proportions. */
      const headGeo = new THREE.SphereGeometry(0.15, 12, 8);
      const hairGeo = new THREE.SphereGeometry(0.154, 10, 6);
      const torsoGeo = new THREE.CapsuleGeometry(0.19, 0.58, 4, 10);
      const upperArmGeo = new THREE.CylinderGeometry(0.047, 0.055, 0.43, 7);
      const legGeo = new THREE.CylinderGeometry(0.068, 0.078, 0.61, 7);
      const skinPalette = [0xc99372, 0xa46d4d, 0xddb08d, 0x85563e, 0xc28461].map((color) => new THREE.MeshStandardMaterial({ color, roughness: 0.74 }));
      const suitPalette = [0x242d33, 0x343b42, 0x1d2529, 0x3b3937, 0x29333a].map((color) => new THREE.MeshStandardMaterial({ color, roughness: 0.74 }));
      const hairPalette = [0x191716, 0x33241d, 0x181818, 0x503528].map((color) => new THREE.MeshStandardMaterial({ color, roughness: 0.88 }));
      const trouserMat = new THREE.MeshStandardMaterial({ color: 0x202629, roughness: 0.8 });
      resources.push(headGeo, hairGeo, torsoGeo, upperArmGeo, legGeo, trouserMat, ...skinPalette, ...suitPalette, ...hairPalette);

      statusMaterialsRef.current.clear();
      const employees = modelRef.current.departmentZones.flatMap((zone) => zone.employeeSlots.map((slot) => slot));
      const isMobile = window.matchMedia("(max-width: 760px)").matches;
      const humanCap = isMobile
        ? LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumVisibleHumansMobile
        : LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumVisibleHumansDesktop;
      const visibleEmployees = employees.slice(0, humanCap);
      const deskAnchors = [
        [-7.35, 1.42], [-4.35, 3.92], [-1.35, 1.42], [-5.95, 5.92], [-2.95, 5.92], [0.05, 5.92], [0.55, 3.35], [2.95, 3.35],
        [5.35, -0.85], [5.35, -3.85], [6.10, -2.75], [7.15, -2.75], [8.20, -2.75], [9.20, -2.75], [6.10, -5.55], [7.15, -5.55],
      ] as const;

      visibleEmployees.forEach(({ employee }, index) => {
        const anchor = deskAnchors[index % deskAnchors.length];
        const overflowRow = Math.floor(index / deskAnchors.length);
        const x = anchor[0] + overflowRow * 0.55;
        const z = anchor[1] + overflowRow * 0.65;
        const skinMat = skinPalette[index % skinPalette.length];
        const suitMat = suitPalette[index % suitPalette.length];
        const hairMat = hairPalette[index % hairPalette.length];
        const seated = index % 4 !== 3;

        const torso = new THREE.Mesh(torsoGeo, suitMat);
        const head = new THREE.Mesh(headGeo, skinMat);
        const hair = new THREE.Mesh(hairGeo, hairMat);
        const legLeft = new THREE.Mesh(legGeo, trouserMat);
        const legRight = new THREE.Mesh(legGeo, trouserMat);
        const armLeft = new THREE.Mesh(upperArmGeo, suitMat);
        const armRight = new THREE.Mesh(upperArmGeo, suitMat);

        const baseY = seated ? 0.77 : 1.02;
        torso.position.set(x, baseY + 0.36, z);
        torso.rotation.x = seated ? -0.12 : 0;
        head.position.set(x, baseY + 0.98, z - (seated ? 0.05 : 0));
        hair.scale.set(1.03, 0.48, 1.04);
        hair.position.set(x, baseY + 1.06, z - 0.01);
        legLeft.position.set(x - 0.08, seated ? 0.39 : 0.43, z + (seated ? 0.17 : 0));
        legRight.position.set(x + 0.08, seated ? 0.39 : 0.43, z + (seated ? 0.17 : 0));
        if (seated) {
          legLeft.rotation.x = legRight.rotation.x = 1.02;
          armLeft.rotation.x = armRight.rotation.x = 1.10;
          armLeft.rotation.z = 0.18;
          armRight.rotation.z = -0.18;
          armLeft.position.set(x - 0.22, baseY + 0.44, z - 0.15);
          armRight.position.set(x + 0.22, baseY + 0.44, z - 0.15);
        } else {
          armLeft.rotation.z = 0.08;
          armRight.rotation.z = -0.08;
          armLeft.position.set(x - 0.22, baseY + 0.44, z);
          armRight.position.set(x + 0.22, baseY + 0.44, z);
        }
        [torso, head, hair, legLeft, legRight, armLeft, armRight].forEach((mesh) => {
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          scene.add(mesh);
        });

        const statusGeo = new THREE.SphereGeometry(0.038, 8, 6);
        const statusColor = STATUS_COLOR[employee.semantic_state] ?? 0x8b969c;
        const statusMat = new THREE.MeshStandardMaterial({ color: statusColor, emissive: statusColor, emissiveIntensity: 1.15 });
        const status = new THREE.Mesh(statusGeo, statusMat);
        status.position.set(x + 0.25, baseY + 1.08, z);
        scene.add(status);
        statusMaterialsRef.current.set(employee.position_key, statusMat);
        resources.push(statusGeo, statusMat);
      });

      canvas.dataset.renderMode = "three-procedural-realism";
      canvas.dataset.presentationOnly = "true";
      canvas.dataset.presenceClaimed = "false";
      canvas.dataset.locomotionAllowed = "false";
      canvas.dataset.visibleHumans = String(visibleEmployees.length);
      canvas.dataset.humanBudget = isMobile ? "mobile" : "desktop";
      canvas.dataset.renderCadence = "on-demand";
      canvas.dataset.geometryReuse = "shared-human-primitives";

      const resize = () => {
        const rect = canvas.getBoundingClientRect();
        const width = Math.max(320, Math.floor(rect.width || 960));
        const height = Math.max(360, Math.floor(rect.height || 680));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        if (width < 600) {
          camera.position.set(8.7, 4.9, 24.6);
          camera.lookAt(0.2, 1.25, -1.2);
          camera.fov = 50;
        } else {
          camera.position.set(13.2, 4.25, 18.8);
          camera.lookAt(0.65, 1.45, -1.0);
          camera.fov = 44;
        }
        camera.updateProjectionMatrix();
        renderFrame();
      };
      resize();
      const observer = new ResizeObserver(resize);
      observer.observe(canvas);
      const handleVisibility = () => {
        if (document.visibilityState === "visible") renderFrame();
      };
      document.addEventListener("visibilitychange", handleVisibility);
      renderFrame();

      cleanup = () => {
        observer.disconnect();
        document.removeEventListener("visibilitychange", handleVisibility);
        renderFrameRef.current = null;
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
        material.emissiveIntensity = employee.semantic_state === "blocked" ? 1.55 : 1.05;
      }
    }
    renderFrameRef.current?.();
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
