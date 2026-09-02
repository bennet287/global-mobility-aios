import {
  BoxGeometry, Group, Mesh, MeshBasicMaterial, PerspectiveCamera, Raycaster, Scene, SphereGeometry, Vector2, WebGPURenderer,
} from "three/webgpu";
import type { LivingSceneRenderModel } from "./living-organization-scene-renderer";
import {
  acquireLivingSceneRendererCanvasLease,
  assertLivingSceneRendererModelNonAuthoritative,
  createLivingSceneSelection,
  isLivingSceneSelection,
  type LivingSceneSelection,
} from "./living-organization-renderer-policy";

export type { LivingSceneSelection } from "./living-organization-renderer-policy";
export type LivingSceneRendererBackend = "webgpu" | "webgl2" | "unknown";
export type LivingSceneRendererController = {
  rendererBackend: LivingSceneRendererBackend;
  render: () => void;
  updateModel: (model: LivingSceneRenderModel) => void;
  dispose: () => void;
};
type MountLivingSceneRendererOptions = {
  canvas: HTMLCanvasElement;
  model: LivingSceneRenderModel;
  onSelect?: (selection: LivingSceneSelection | null) => void;
};

const DEPARTMENT_PALETTE = [0x5966c7, 0x4f7a8d, 0x6d5f9e, 0x49765f, 0x8a6647];

function paletteColor(key: string): number {
  let hash = 0;
  for (let index = 0; index < key.length; index += 1) {
    hash = ((hash << 5) - hash + key.charCodeAt(index)) | 0;
  }
  return DEPARTMENT_PALETTE[Math.abs(hash) % DEPARTMENT_PALETTE.length] ?? DEPARTMENT_PALETTE[0];
}

function resolveActualBackend(renderer: any): LivingSceneRendererBackend {
  const backend = renderer?.backend;
  if (backend?.isWebGPUBackend === true) return "webgpu";
  if (backend?.isWebGLBackend === true) return "webgl2";
  const constructorName = String(backend?.constructor?.name ?? "").toLowerCase();
  if (constructorName.includes("webgpubackend")) return "webgpu";
  if (constructorName.includes("webglbackend")) return "webgl2";
  return "unknown";
}

function markRendererMounted(canvas: HTMLCanvasElement) {
  const lease = acquireLivingSceneRendererCanvasLease(canvas);
  const generation = Number.parseInt(canvas.dataset.rendererMountGeneration ?? "0", 10) || 0;
  canvas.dataset.rendererMountGeneration = String(generation + 1);
  canvas.dataset.rendererActiveMounts = "1";
  return lease;
}

export async function mountLivingOrganizationWebGPUScene({
  canvas,
  model,
  onSelect,
}: MountLivingSceneRendererOptions): Promise<LivingSceneRendererController> {
  assertLivingSceneRendererModelNonAuthoritative(model);

  const renderer = new WebGPURenderer({ canvas, antialias: true, alpha: true });
  await renderer.init();
  const backend = resolveActualBackend(renderer);
  const scene = new Scene();
  const camera = new PerspectiveCamera(45, 1, 0.1, 160);
  const raycaster = new Raycaster();
  const pointer = new Vector2();
  let pickTargets: any[] = [];
  let disposableResources: Array<{ dispose?: () => void }> = [];
  let employeeActors: Array<{
    root: any;
    baseY: number;
    motion: string;
    phase: number;
    previousOffset: number;
  }> = [];
  let modelRevision = 0;
  let disposed = false;

  canvas.dataset.rendererTarget = "three-webgpu";
  canvas.dataset.rendererBackend = backend;
  canvas.dataset.rendererAuthority = "none";
  canvas.dataset.sceneAuthoritative = "false";
  canvas.dataset.rendererModelRevision = "0";
  canvas.dataset.rendererProjectionResources = "0";
  canvas.dataset.animationScope = "workspace-representation";
  canvas.dataset.locomotionEnabled = "false";
  canvas.dataset.presenceClaimed = "false";
  canvas.dataset.presentationModes = "";
  canvas.dataset.animationProof = "pending";

  const render = () => {
    if (disposed) return;
    renderer.render(scene, camera);
  };

  const resize = () => {
    if (disposed) return;
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(320, Math.floor(rect.width || 960));
    const height = Math.max(260, Math.floor(rect.height || 420));
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    render();
  };

  const clearProjection = () => {
    onSelect?.(null);
    scene.clear?.();
    for (const resource of disposableResources) {
      try {
        resource.dispose?.();
      } catch (error) {
        console.warn("Living Organization renderer resource disposal failed.", error);
      }
    }
    disposableResources = [];
    pickTargets = [];
    employeeActors = [];
    canvas.dataset.rendererProjectionResources = "0";
    canvas.dataset.presentationModes = "";
    canvas.dataset.animationProof = "pending";
  };

  const addBox = ({
    size,
    position,
    color,
    opacity = 1,
    selection,
  }: {
    size: [number, number, number];
    position: [number, number, number];
    color: number;
    opacity?: number;
    selection: LivingSceneSelection;
  }) => {
    const geometry = new BoxGeometry(size[0], size[1], size[2]);
    const material = new MeshBasicMaterial({ color, transparent: opacity < 1, opacity });
    const mesh = new Mesh(geometry, material);
    mesh.position.set(position[0], position[1], position[2]);
    mesh.userData.selection = selection;
    scene.add(mesh);
    pickTargets.push(mesh);
    disposableResources.push(geometry, material);
  };

  const updateModel = (nextModel: LivingSceneRenderModel) => {
    if (disposed) throw new Error("Living Organization renderer cannot update after disposal.");
    assertLivingSceneRendererModelNonAuthoritative(nextModel);
    clearProjection();

    const zoneSpacing = 5.4;
    const zoneCount = Math.max(1, nextModel.departmentZones.length);
    const zoneStart = -((zoneCount - 1) * zoneSpacing) / 2;

    nextModel.departmentZones.forEach((zone) => {
      const zoneX = zoneStart + zone.zoneIndex * zoneSpacing;
      addBox({
        size: [4.5, 0.18, 4.0],
        position: [zoneX, 0, 1.1],
        color: paletteColor(zone.department.department_key),
        opacity: 0.42,
        selection: createLivingSceneSelection(
          "department",
          zone.department.department_key,
          zone.department.label,
        ),
      });

      zone.employeeSlots.forEach(({ employee, presentation }, employeeIndex) => {
        const column = employeeIndex % 3;
        const row = Math.floor(employeeIndex / 3);
        const root = new Group();
        const baseY = 0.62;
        root.position.set(zoneX + (column - 1) * 1.05, baseY, 0.7 + row * 1.05);

        const employeeColor: Record<string, number> = {
          focused_work: 0xaac8ff,
          blocked_wait: 0xffa4a4,
          awaiting_attention: 0xf1cf77,
          queued_wait: 0xc8b8ff,
          settled_idle: 0xa9dfba,
          neutral_static: 0xc6cad6,
        };
        const selection = createLivingSceneSelection("employee", employee.position_key, employee.title);

        const torsoGeometry = new BoxGeometry(0.48, 0.68, 0.34);
        const torsoMaterial = new MeshBasicMaterial({
          color: employeeColor[presentation.state] ?? employeeColor.neutral_static,
        });
        const torso = new Mesh(torsoGeometry, torsoMaterial);
        torso.position.set(0, 0.18, 0);
        torso.userData.selection = selection;

        const headGeometry = new SphereGeometry(0.22, 12, 8);
        const headMaterial = new MeshBasicMaterial({ color: 0xf0dfcf });
        const head = new Mesh(headGeometry, headMaterial);
        head.position.set(0, 0.72, 0);
        head.userData.selection = selection;

        root.add(torso);
        root.add(head);
        scene.add(root);
        pickTargets.push(torso, head);
        disposableResources.push(torsoGeometry, torsoMaterial, headGeometry, headMaterial);
        employeeActors.push({
          root,
          baseY,
          motion: presentation.motion,
          phase: employeeIndex * 0.73 + zone.zoneIndex * 0.41,
          previousOffset: 0,
        });
      });
    });

    const roomEntries = [nextModel.missionRoom, nextModel.evidenceLab, nextModel.boardRoom]
      .filter(Boolean) as Array<NonNullable<LivingSceneRenderModel["missionRoom"]>>;
    roomEntries.forEach((room, roomIndex) => {
      const roomX = (roomIndex - (roomEntries.length - 1) / 2) * 4.6;
      addBox({
        size: [3.8, 0.22, 2.6],
        position: [roomX, 0.04, -3.1],
        color: 0x2f3659,
        opacity: 0.62,
        selection: createLivingSceneSelection("room", room.room_key, room.label),
      });
    });

    const span = Math.max(12, zoneCount * zoneSpacing);
    camera.position.set(0, Math.max(9, span * 0.62), Math.max(13, span * 0.9));
    camera.lookAt(0, 0, 0);

    const presentationModes = [...new Set(
      nextModel.employeeSlots.map(({ presentation }) => presentation.state),
    )].sort();
    canvas.dataset.presentationModes = presentationModes.join(",");
    canvas.dataset.animationProof = employeeActors.some(({ motion }) => motion !== "none")
      ? "pending"
      : "static-only";

    modelRevision += 1;
    canvas.dataset.rendererModelRevision = String(modelRevision);
    canvas.dataset.rendererProjectionResources = String(disposableResources.length);
    resize();
  };

  const motionOffset = (motion: string, seconds: number, phase: number): number => {
    if (motion === "work_pulse") return Math.sin(seconds * 4.8 + phase) * 0.035;
    if (motion === "blocked_pulse") return Math.abs(Math.sin(seconds * 4.2 + phase)) * 0.07;
    if (motion === "waiting_breathe") return Math.sin(seconds * 2.1 + phase) * 0.022;
    if (motion === "settled_breathe") return Math.sin(seconds * 1.45 + phase) * 0.012;
    return 0;
  };

  const animate = (time: number) => {
    if (disposed) return;
    const seconds = time * 0.001;
    let motionObserved = false;
    for (const actor of employeeActors) {
      const offset = motionOffset(actor.motion, seconds, actor.phase);
      actor.root.position.y = actor.baseY + offset;
      if (Math.abs(offset - actor.previousOffset) > 0.0005) motionObserved = true;
      actor.previousOffset = offset;
    }
    if (motionObserved) canvas.dataset.animationProof = "motion-observed";
    render();
  };

  const handlePointer = (event: PointerEvent) => {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const [hit] = raycaster.intersectObjects(pickTargets, false);
    const selection = hit?.object?.userData?.selection;
    onSelect?.(isLivingSceneSelection(selection) ? selection : null);
  };

  canvas.addEventListener("pointerdown", handlePointer);
  const resizeObserver = typeof ResizeObserver !== "undefined" ? new ResizeObserver(resize) : null;
  resizeObserver?.observe(canvas);
  if (!resizeObserver) window.addEventListener("resize", resize);

  const canvasLease = markRendererMounted(canvas);
  renderer.setAnimationLoop(animate);
  try {
    updateModel(model);
  } catch (error) {
    canvas.removeEventListener("pointerdown", handlePointer);
    resizeObserver?.disconnect();
    if (!resizeObserver) window.removeEventListener("resize", resize);
    renderer.setAnimationLoop(null);
    clearProjection();
    try {
      renderer.dispose();
    } catch (disposeError) {
      console.warn("Living Organization renderer initialization cleanup failed.", disposeError);
    } finally {
      canvasLease.release();
      canvas.dataset.rendererActiveMounts = "0";
    }
    throw error;
  }

  return {
    rendererBackend: backend,
    render,
    updateModel,
    dispose: () => {
      if (disposed) return;
      disposed = true;
      canvas.removeEventListener("pointerdown", handlePointer);
      resizeObserver?.disconnect();
      if (!resizeObserver) window.removeEventListener("resize", resize);
      renderer.setAnimationLoop(null);
      clearProjection();
      try {
        renderer.dispose();
      } catch (error) {
        console.warn("Living Organization renderer disposal failed.", error);
      } finally {
        canvasLease.release();
        canvas.dataset.rendererActiveMounts = "0";
      }
    },
  };
}
