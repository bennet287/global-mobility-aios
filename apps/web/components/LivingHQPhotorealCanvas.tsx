"use client";

import { useEffect, useRef } from "react";
import type { LivingSceneRenderModel } from "../lib/living-organization-scene-renderer";
import { LIVING_HQ_HIGH_FIDELITY_BUDGET } from "../lib/living-hq-high-fidelity-assets";

export function LivingHQPhotorealCanvas({ renderModel }: { renderModel: LivingSceneRenderModel }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const modelRef = useRef(renderModel);
  modelRef.current = renderModel;

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
      renderer.toneMappingExposure = 1.06;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0xb9c6c7);
      scene.fog = new THREE.FogExp2(0xc6ceca, 0.017);
      const camera = new THREE.PerspectiveCamera(43, 1, 0.1, 120);
      camera.position.set(12.5, 7.4, 14.8);
      camera.lookAt(0, 1.4, 0);

      scene.add(new THREE.HemisphereLight(0xf7f1e4, 0x354348, 2.1));
      const sun = new THREE.DirectionalLight(0xffefd2, 3.2);
      sun.position.set(-7, 11, 8);
      sun.castShadow = true;
      sun.shadow.mapSize.set(1024, 1024);
      scene.add(sun);
      const warm = new THREE.PointLight(0xffd7a2, 12, 24, 2);
      warm.position.set(-3, 5.8, -2);
      scene.add(warm);

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

      const wood = new THREE.MeshStandardMaterial({ color: 0x9d7450, roughness: 0.66, metalness: 0.02 });
      const dark = new THREE.MeshStandardMaterial({ color: 0x20282b, roughness: 0.58, metalness: 0.18 });
      const stone = new THREE.MeshStandardMaterial({ color: 0xaaa59c, roughness: 0.82, metalness: 0.01 });
      const carpet = new THREE.MeshStandardMaterial({ color: 0x4b514f, roughness: 0.96 });
      const glass = new THREE.MeshPhysicalMaterial({ color: 0xdce9e9, roughness: 0.12, transmission: 0.7, transparent: true, opacity: 0.32, thickness: 0.12 });
      const screen = new THREE.MeshStandardMaterial({ color: 0x112126, roughness: 0.28, metalness: 0.25, emissive: 0x17333a, emissiveIntensity: 0.42 });
      resources.push(wood, dark, stone, carpet, glass, screen);

      addBox([22, 0.25, 16], [0, -0.12, 0], wood, false);
      addBox([11, 0.05, 8], [-4.4, 0.04, 1.2], carpet, false);
      addBox([22, 0.38, 2.1], [0, 6.7, -7.2], dark, false);
      addBox([0.18, 5.6, 8.8], [3.1, 2.8, -2.7], glass, false);
      addBox([0.18, 5.6, 7.7], [7.9, 2.8, -2.8], glass, false);

      for (let i = 0; i < 5; i += 1) {
        const x = -7 + i * 3.2;
        addBox([2.3, 0.16, 1.15], [x, 1.05, 1.4 + (i % 2) * 2.2], wood);
        addBox([0.9, 0.58, 0.08], [x, 1.52, 1.08 + (i % 2) * 2.2], screen);
        addBox([0.75, 0.9, 0.75], [x, 0.55, 2.25 + (i % 2) * 2.2], dark);
      }

      addBox([4.3, 0.18, 1.75], [5.55, 1.02, -2.7], wood);
      for (let i = 0; i < 6; i += 1) {
        const angle = (i / 6) * Math.PI * 2;
        addBox([0.7, 0.85, 0.7], [5.55 + Math.cos(angle) * 2.25, 0.5, -2.7 + Math.sin(angle) * 1.3], dark);
      }

      for (let i = 0; i < 7; i += 1) {
        const geometry = new THREE.CylinderGeometry(0.28, 0.38, 0.5, 12);
        const pot = new THREE.Mesh(geometry, stone);
        pot.position.set(-9 + i * 3, 0.25, -5.8 + (i % 2) * 10.7);
        pot.castShadow = true;
        scene.add(pot);
        resources.push(geometry);
        const leafGeo = new THREE.SphereGeometry(0.7, 10, 7);
        const leafMat = new THREE.MeshStandardMaterial({ color: i % 2 ? 0x315e40 : 0x426f4d, roughness: 0.9 });
        const leaf = new THREE.Mesh(leafGeo, leafMat);
        leaf.scale.set(0.65, 1.3, 0.65);
        leaf.position.set(pot.position.x, 1.1, pot.position.z);
        leaf.castShadow = true;
        scene.add(leaf);
        resources.push(leafGeo, leafMat);
      }

      const employees = modelRef.current.departmentZones.flatMap((zone) => zone.employeeSlots.map((slot) => slot));
      const visibleEmployees = employees.slice(0, LIVING_HQ_HIGH_FIDELITY_BUDGET.maximumVisibleHumansDesktop);
      const stateColor: Record<string, number> = {
        working: 0x5bb88c,
        blocked: 0xd46b57,
        awaiting_owner: 0xd6aa51,
        queued: 0x6e92ad,
        completed: 0x7e9b87,
      };

      visibleEmployees.forEach(({ employee }, index) => {
        const row = Math.floor(index / 8);
        const col = index % 8;
        const x = -8.2 + col * 2.15;
        const z = 0.1 + row * 2.3;
        const skinMat = new THREE.MeshStandardMaterial({ color: [0xc99372, 0x9f6a4c, 0xd9ac88, 0x84553d][index % 4], roughness: 0.72 });
        const suitMat = new THREE.MeshStandardMaterial({ color: [0x293138, 0x343b42, 0x22282c, 0x3b3937][index % 4], roughness: 0.76 });
        const headGeo = new THREE.SphereGeometry(0.18, 12, 8);
        const torsoGeo = new THREE.CapsuleGeometry(0.22, 0.52, 5, 10);
        const head = new THREE.Mesh(headGeo, skinMat);
        const torso = new THREE.Mesh(torsoGeo, suitMat);
        torso.position.set(x, 1.02, z);
        head.position.set(x, 1.58, z);
        torso.castShadow = head.castShadow = true;
        scene.add(torso, head);
        const statusGeo = new THREE.SphereGeometry(0.055, 8, 6);
        const statusMat = new THREE.MeshStandardMaterial({ color: stateColor[employee.semantic_state] ?? 0x8b969c, emissive: stateColor[employee.semantic_state] ?? 0x8b969c, emissiveIntensity: 0.8 });
        const status = new THREE.Mesh(statusGeo, statusMat);
        status.position.set(x + 0.34, 1.65, z);
        scene.add(status);
        resources.push(headGeo, torsoGeo, skinMat, suitMat, statusGeo, statusMat);
      });

      canvas.dataset.renderMode = "three-procedural-realism";
      canvas.dataset.presentationOnly = "true";
      canvas.dataset.presenceClaimed = "false";
      canvas.dataset.locomotionAllowed = "false";
      canvas.dataset.visibleHumans = String(visibleEmployees.length);

      const resize = () => {
        const rect = canvas.getBoundingClientRect();
        const width = Math.max(320, Math.floor(rect.width || 960));
        const height = Math.max(320, Math.floor(rect.height || 560));
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      };
      resize();
      const observer = new ResizeObserver(resize);
      observer.observe(canvas);

      let frame = 0;
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const animate = () => {
        if (disposed) return;
        if (!reducedMotion) {
          const t = performance.now() * 0.00005;
          camera.position.x = 12.5 + Math.sin(t) * 0.28;
          camera.lookAt(0, 1.4, 0);
        }
        renderer.render(scene, camera);
        frame = requestAnimationFrame(animate);
      };
      animate();

      cleanup = () => {
        observer.disconnect();
        cancelAnimationFrame(frame);
        resources.forEach((resource) => resource.dispose?.());
        renderer.dispose();
      };
    })();

    return () => {
      disposed = true;
      cleanup?.();
    };
  }, []);

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
