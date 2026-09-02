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
  setFlowTrialEnabled: (enabled: boolean) => void;
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
  let flowTrialEnabled = false;
  let flowTrialGroup: Group | null = null;
  let flowActors: Array<{
    root: any;
    sourceX: number;
    sourceZ: number;
    targetX: number;
    targetZ: number;
    phase: number;
    speed: number;
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
  canvas.dataset.flowTrialEnabled = "false";
  canvas.dataset.flowTrialVersion = model.flowTrial.trialVersion;
  canvas.dataset.flowTrialPromotionStatus = model.flowTrial.promotionStatus;
  canvas.dataset.flowTrialPresentationOnly = "true";
  canvas.dataset.flowTrialMutatesWork = "false";
  canvas.dataset.flowTrialThroughputClaimed = "false";
  canvas.dataset.flowTrialDependencyClaimed = "false";
  canvas.dataset.flowTrialComputeGate = "unmeasured";
  canvas.dataset.flowTrialNodeCount = "0";
  canvas.dataset.flowTrialPathCount = "0";
  canvas.dataset.flowTrialParticleCount = "0";

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
    flowTrialGroup = null;
    flowActors = [];
    canvas.dataset.rendererProjectionResources = "0";
    canvas.dataset.presentationModes = "";
    canvas.dataset.animationProof = "pending";
    canvas.dataset.flowTrialNodeCount = "0";
    canvas.dataset.flowTrialPathCount = "0";
    canvas.dataset.flowTrialParticleCount = "0";
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

  const addFlowTrialProjection = (nextModel: LivingSceneRenderModel) => {
    const trial = nextModel.flowTrial;
    const group = new Group();
    group.visible = flowTrialEnabled;
    scene.add(group);
    flowTrialGroup = group;
    flowActors = [];

    trial.nodes.forEach((node) => {
      const geometry = new SphereGeometry(0.11 + node.fieldStrength * 0.15, 12, 8);
      const material = new MeshBasicMaterial({
        color: node.stalledCue ? 0xffa06e : 0x74c8ff,
        transparent: true,
        opacity: 0.24 + node.fieldStrength * 0.48,
      });
      const mesh = new Mesh(geometry, material);
      mesh.position.set(node.x, 0.3 + node.fieldStrength * 0.08, node.z);
      group.add(mesh);
      disposableResources.push(geometry, material);
    });

    let particleCount = 0;
    trial.paths.forEach((path, pathIndex) => {
      const dx = path.targetX - path.sourceX;
      const dz = path.targetZ - path.sourceZ;
      const length = Math.max(0.15, Math.hypot(dx, dz));
      const corridorGeometry = new BoxGeometry(
        length,
        0.035 + path.fieldStrength * 0.025,
        0.055 + path.fieldStrength * 0.08,
      );
      const corridorMaterial = new MeshBasicMaterial({
        color: path.stalledCue ? 0xffa06e : 0x74c8ff,
        transparent: true,
        opacity: 0.12 + path.fieldStrength * 0.24,
      });
      const corridor = new Mesh(corridorGeometry, corridorMaterial);
      corridor.position.set(
        (path.sourceX + path.targetX) / 2,
        0.2,
        (path.sourceZ + path.targetZ) / 2,
      );
      corridor.rotation.y = -Math.atan2(dz, dx);
      group.add(corridor);
      disposableResources.push(corridorGeometry, corridorMaterial);

      const particlesForPath = 4;
      for (let particleIndex = 0; particleIndex < particlesForPath; particleIndex += 1) {
        const particleGeometry = new SphereGeometry(0.045 + path.fieldStrength * 0.025, 8, 6);
        const particleMaterial = new MeshBasicMaterial({
          color: path.stalledCue ? 0xffc089 : 0xa6e2ff,
          transparent: true,
          opacity: 0.58 + path.fieldStrength * 0.32,
        });
        const particle = new Mesh(particleGeometry, particleMaterial);
        group.add(particle);
        disposableResources.push(particleGeometry, particleMaterial);
        flowActors.push({
          root: particle,
          sourceX: path.sourceX,
          sourceZ: path.sourceZ,
          targetX: path.targetX,
          targetZ: path.targetZ,
          phase: (particleIndex / particlesForPath + pathIndex * 0.173) % 1,
          speed: 0.08 + path.fieldStrength * 0.16,
        });
        particleCount += 1;
      }
    });

    canvas.dataset.flowTrialVersion = trial.trialVersion;
    canvas.dataset.flowTrialPromotionStatus = trial.promotionStatus;
    canvas.dataset.flowTrialPresentationOnly = String(trial.projectionOnly);
    canvas.dataset.flowTrialMutatesWork = String(trial.fieldStateCanMutateWork);
    canvas.dataset.flowTrialThroughputClaimed = String(trial.throughputClaimed);
    canvas.dataset.flowTrialDependencyClaimed = String(trial.dependencyClaimed);
    canvas.dataset.flowTrialNodeCount = String(trial.nodes.length);
    canvas.dataset.flowTrialPathCount = String(trial.paths.length);
    canvas.dataset.flowTrialParticleCount = String(particleCount);
    canvas.dataset.flowTrialDominantDerivedPath = trial.dominantDerivedPathKey ?? "none";
    canvas.dataset.flowTrialEnabled = String(flowTrialEnabled);
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

    nextModel.smartObjects.forEach((object, objectIndex) => {
      const column = objectIndex % 4;
      const row = Math.floor(objectIndex / 4);
      addBox({
        size: [1.45, 0.34, 0.84],
        position: [(column - 1.5) * 2.0, 0.24, -5.1 - row * 1.15],
        color: paletteColor(object.object_type),
        opacity: object.state === "unavailable" ? 0.24 : 0.68,
        selection: createLivingSceneSelection("smart_object", object.object_key, object.label),
      });
    });
    canvas.dataset.smartObjectCount = String(nextModel.smartObjects.length);

    addFlowTrialProjection(nextModel);

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
    if (flowTrialEnabled) {
      for (const actor of flowActors) {
        const progress = (seconds * actor.speed + actor.phase) % 1;
        actor.root.position.set(
          actor.sourceX + (actor.targetX - actor.sourceX) * progress,
          0.28 + Math.sin((progress + actor.phase) * Math.PI * 2) * 0.035,
          actor.sourceZ + (actor.targetZ - actor.sourceZ) * progress,
        );
      }
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
    setFlowTrialEnabled: (enabled: boolean) => {
      if (disposed) return;
      flowTrialEnabled = enabled;
      if (flowTrialGroup) flowTrialGroup.visible = enabled;
      canvas.dataset.flowTrialEnabled = String(enabled);
      render();
    },
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
