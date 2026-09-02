import {
  BoxGeometry, Mesh, MeshBasicMaterial, PerspectiveCamera, Raycaster, Scene, Vector2, WebGPURenderer,
} from "three/webgpu";
import type { LivingSceneRenderModel } from "./living-organization-scene-renderer";
import {
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
  for (let index = 0; index < key.length; index += 1) hash = ((hash << 5) - hash + key.charCodeAt(index)) | 0;
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

const ACTIVE_CANVAS_MOUNTS = new WeakSet<HTMLCanvasElement>();

function markRendererMounted(canvas: HTMLCanvasElement) {
  if (ACTIVE_CANVAS_MOUNTS.has(canvas)) {
    throw new Error("Living Organization renderer refuses a duplicate live mount on the same canvas.");
  }
  ACTIVE_CANVAS_MOUNTS.add(canvas);
  const generation = Number.parseInt(canvas.dataset.rendererMountGeneration ?? "0", 10) || 0;
  canvas.dataset.rendererMountGeneration = String(generation + 1);
  canvas.dataset.rendererActiveMounts = "1";
}

function markRendererDisposed(canvas: HTMLCanvasElement) {
  ACTIVE_CANVAS_MOUNTS.delete(canvas);
  canvas.dataset.rendererActiveMounts = "0";
}

export async function mountLivingOrganizationWebGPUScene({ canvas, model, onSelect }: MountLivingSceneRendererOptions): Promise<LivingSceneRendererController> {
  assertLivingSceneRendererModelNonAuthoritative(model);

  const renderer = new WebGPURenderer({ canvas, antialias: true, alpha: true });
  await renderer.init();
  const backend = resolveActualBackend(renderer);
  const scene = new Scene();
  const camera = new PerspectiveCamera(45, 1, 0.1, 160);
  const raycaster = new Raycaster();
  const pointer = new Vector2();
  const pickTargets: any[] = [];
  const disposableResources: Array<{ dispose?: () => void }> = [];

  canvas.dataset.rendererTarget = "three-webgpu";
  canvas.dataset.rendererBackend = backend;
  canvas.dataset.rendererAuthority = "none";
  canvas.dataset.sceneAuthoritative = "false";

  const addBox = ({ size, position, color, opacity = 1, selection }: {
    size: [number, number, number]; position: [number, number, number]; color: number; opacity?: number; selection: LivingSceneSelection;
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

  const zoneSpacing = 5.4;
  const zoneCount = Math.max(1, model.departmentZones.length);
  const zoneStart = -((zoneCount - 1) * zoneSpacing) / 2;
  model.departmentZones.forEach((zone) => {
    const zoneX = zoneStart + zone.zoneIndex * zoneSpacing;
    addBox({
      size: [4.5, 0.18, 4.0], position: [zoneX, 0, 1.1], color: paletteColor(zone.department.department_key), opacity: 0.42,
      selection: createLivingSceneSelection("department", zone.department.department_key, zone.department.label),
    });
    zone.employeeSlots.forEach(({ employee }, employeeIndex) => {
      const column = employeeIndex % 3;
      const row = Math.floor(employeeIndex / 3);
      addBox({
        size: [0.72, 1.15, 0.72],
        position: [zoneX + (column - 1) * 1.05, 0.68, 0.7 + row * 1.05],
        color: 0xe3e5ff,
        selection: createLivingSceneSelection("employee", employee.position_key, employee.title),
      });
    });
  });

  const roomEntries = [model.missionRoom, model.evidenceLab, model.boardRoom]
    .filter(Boolean) as Array<NonNullable<LivingSceneRenderModel["missionRoom"]>>;
  roomEntries.forEach((room, roomIndex) => {
    const roomX = (roomIndex - (roomEntries.length - 1) / 2) * 4.6;
    addBox({
      size: [3.8, 0.22, 2.6], position: [roomX, 0.04, -3.1], color: 0x2f3659, opacity: 0.62,
      selection: createLivingSceneSelection("room", room.room_key, room.label),
    });
  });

  const span = Math.max(12, zoneCount * zoneSpacing);
  camera.position.set(0, Math.max(9, span * 0.62), Math.max(13, span * 0.9));
  camera.lookAt(0, 0, 0);
  const render = () => renderer.render(scene, camera);
  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(320, Math.floor(rect.width || 960));
    const height = Math.max(260, Math.floor(rect.height || 420));
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
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
  resize();
  markRendererMounted(canvas);

  return {
    rendererBackend: backend,
    render,
    dispose: () => {
      canvas.removeEventListener("pointerdown", handlePointer);
      resizeObserver?.disconnect();
      if (!resizeObserver) window.removeEventListener("resize", resize);
      onSelect?.(null);
      for (const resource of disposableResources) resource.dispose?.();
      scene.clear?.();
      renderer.dispose();
      markRendererDisposed(canvas);
    },
  };
}
