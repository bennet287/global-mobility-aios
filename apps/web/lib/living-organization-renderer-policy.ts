export type LivingSceneSelection = Readonly<{
  entityType: "department" | "employee" | "room" | "smart_object";
  entityKey: string;
  label: string;
}>;

const SELECTION_KEYS = new Set(["entityType", "entityKey", "label"]);

export function assertLivingSceneRendererModelNonAuthoritative(
  model: { sceneAuthoritative?: unknown },
): asserts model is { sceneAuthoritative: false } {
  if (model.sceneAuthoritative !== false) {
    throw new Error("Living Organization renderer refuses an authoritative scene model.");
  }
}

export function createLivingSceneSelection(
  entityType: LivingSceneSelection["entityType"],
  entityKey: string,
  label: string,
): LivingSceneSelection {
  return Object.freeze({ entityType, entityKey, label });
}

export function isLivingSceneSelection(value: unknown): value is LivingSceneSelection {
  if (!value || typeof value !== "object") return false;
  const keys = Object.keys(value);
  if (keys.length !== 3 || keys.some((key) => !SELECTION_KEYS.has(key))) return false;
  const selection = value as Partial<LivingSceneSelection>;
  return (
    (selection.entityType === "department" || selection.entityType === "employee" || selection.entityType === "room" || selection.entityType === "smart_object")
    && typeof selection.entityKey === "string"
    && typeof selection.label === "string"
  );
}


const ACTIVE_RENDERER_CANVASES = new WeakSet<object>();

export type LivingSceneRendererCanvasLease = {
  release: () => void;
};

export function acquireLivingSceneRendererCanvasLease(canvas: object): LivingSceneRendererCanvasLease {
  if (ACTIVE_RENDERER_CANVASES.has(canvas)) {
    throw new Error("Living Organization renderer refuses a duplicate live mount on the same canvas.");
  }
  ACTIVE_RENDERER_CANVASES.add(canvas);
  let released = false;
  return {
    release: () => {
      if (released) return;
      released = true;
      ACTIVE_RENDERER_CANVASES.delete(canvas);
    },
  };
}
