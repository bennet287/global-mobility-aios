/**
 * AIOS V2 — Phase 2M
 * Ambient Character Renderer Adapter V1 (presentation-only)
 *
 * Consumes only an already-built Phase 2K ambient behavior descriptor and
 * translates it into a frozen renderer descriptor. It never derives identity,
 * reads organization state, or mutates canonical state.
 */

import type { V2AmbientCharacterBehaviorDescriptor } from "./character-ambient-behavior";

export type V2AmbientRendererMode = "ambient" | "reduced-motion" | "static";
export type V2AmbientRendererPhaseSlot = 0 | 1 | 2 | 3;
export type V2AmbientRendererActionKey =
  | "blink"
  | "breathing"
  | "micro-posture"
  | "gaze-shift"
  | "focus-glow"
  | "device-idle"
  | "prop-idle"
  | "selection-emphasis";

export interface V2AmbientRendererAction {
  readonly key: V2AmbientRendererActionKey;
  readonly cssClass: string;
  readonly durationMs: number;
  readonly minIntervalMs: number;
  readonly phaseOffsetMs: number;
  readonly transformAllowed: boolean;
}

export interface V2AmbientRendererTruth {
  readonly semanticAnimationActive: false;
  readonly canonicalStateWritable: false;
  readonly physicalPresenceClaimed: false;
  readonly physicalLocationClaimed: false;
  readonly physicalTravelClaimed: false;
  readonly conversationClaimed: false;
  readonly collaborationClaimed: false;
  readonly workActivityClaimed: false;
  readonly completionClaimed: false;
  readonly handoffClaimed: false;
  readonly blockerResolutionClaimed: false;
}

export interface V2AmbientRendererReducedMotion {
  readonly enabled: boolean;
  readonly transformActionsRemoved: boolean;
  readonly staticEquivalentsOnly: boolean;
  readonly informationLoss: false;
}

export interface V2AmbientCharacterRendererDescriptor {
  readonly kind: "ambient-character-renderer";
  readonly contract: Readonly<{ registryId: string; contractVersion: string }>;
  readonly presentationKey: string;
  readonly mode: V2AmbientRendererMode;
  readonly phaseSlot: V2AmbientRendererPhaseSlot;
  readonly presentationOnly: true;
  readonly truth: V2AmbientRendererTruth;
  readonly actions: readonly V2AmbientRendererAction[];
  readonly reducedMotion: V2AmbientRendererReducedMotion;
  readonly limitations: readonly string[];
}

export interface V2AmbientCharacterRendererInput {
  readonly ambientBehavior: V2AmbientCharacterBehaviorDescriptor;
  readonly phaseSlot?: V2AmbientRendererPhaseSlot;
}

function deepFreeze<T>(value: T): T {
  if (value === null || typeof value !== "object" || Object.isFrozen(value)) return value;
  Object.freeze(value);
  const container = value as unknown as Record<PropertyKey, unknown>;
  for (const key of Reflect.ownKeys(container)) deepFreeze(container[key]);
  return value;
}

export const AMBIENT_RENDERER_CONTRACT = deepFreeze({
  registryId: "aios-v2.ambient-character-renderer",
  contractVersion: "1.0.0",
  presentationOnly: true,
  canonicalStateWritable: false,
  semanticAnimationActive: false,
} as const);

export const ALLOWED_AMBIENT_RENDERER_ACTION_KEYS: readonly V2AmbientRendererActionKey[] =
  deepFreeze([
    "blink",
    "breathing",
    "micro-posture",
    "gaze-shift",
    "focus-glow",
    "device-idle",
    "prop-idle",
    "selection-emphasis",
  ] as const);

export const FORBIDDEN_AMBIENT_RENDERER_ACTION_KEYS: readonly string[] = deepFreeze([
  "walk",
  "walking",
  "travel",
  "room-entry",
  "conversation",
  "talk",
  "coffee-drink",
  "handoff",
  "work",
  "complete",
  "completion",
  "celebrate",
  "blocker-resolved",
] as const);

export const PHASE_SLOT_OFFSETS_MS: readonly number[] = deepFreeze([0, 140, 280, 420] as const);

const ACTION_CSS_CLASSES: Readonly<Record<V2AmbientRendererActionKey, string>> = deepFreeze({
  blink: "ambientBlink",
  breathing: "ambientBreathing",
  "micro-posture": "ambientMicroPosture",
  "gaze-shift": "ambientGazeShift",
  "focus-glow": "ambientFocusGlow",
  "device-idle": "ambientDeviceIdle",
  "prop-idle": "ambientPropIdle",
  "selection-emphasis": "ambientSelectionEmphasis",
});

const EXPECTED_MOTION_CLASS: Readonly<
  Record<V2AmbientRendererActionKey, "transform" | "opacity">
> = deepFreeze({
  blink: "opacity",
  breathing: "transform",
  "micro-posture": "transform",
  "gaze-shift": "transform",
  "focus-glow": "opacity",
  "device-idle": "opacity",
  "prop-idle": "opacity",
  "selection-emphasis": "opacity",
});

const EXPECTED_FALSE_FLAGS = deepFreeze([
  "semanticAnimationActive",
  "canonicalStateWritable",
  "physicalPresenceClaimed",
  "physicalLocationClaimed",
  "physicalTravelClaimed",
  "conversationClaimed",
  "collaborationClaimed",
  "workActivityClaimed",
  "completionClaimed",
  "handoffClaimed",
  "blockerResolutionClaimed",
] as const);

type AmbientBehaviorView = {
  readonly kind?: unknown;
  readonly contract?: { readonly registryId?: unknown; readonly contractVersion?: unknown };
  readonly presentationKey?: unknown;
  readonly presentationBasis?: unknown;
  readonly mode?: unknown;
  readonly actions?: unknown;
  readonly reducedMotion?: {
    readonly enabled?: unknown;
    readonly informationLoss?: unknown;
  };
  readonly presentationOnly?: unknown;
  readonly semanticAnimationActive?: unknown;
  readonly canonicalStateWritable?: unknown;
  readonly physicalPresenceClaimed?: unknown;
  readonly physicalLocationClaimed?: unknown;
  readonly physicalTravelClaimed?: unknown;
  readonly conversationClaimed?: unknown;
  readonly collaborationClaimed?: unknown;
  readonly workActivityClaimed?: unknown;
  readonly completionClaimed?: unknown;
  readonly handoffClaimed?: unknown;
  readonly blockerResolutionClaimed?: unknown;
};

function validateBehaviorEnvelope(candidate: unknown): string[] {
  if (candidate === null || typeof candidate !== "object") {
    return ["fail-closed-descriptor-not-an-object"];
  }
  const failures: string[] = [];
  const view = candidate as AmbientBehaviorView;
  if (view.kind !== "ambient-character-behavior") {
    failures.push("fail-closed-invalid-descriptor-kind");
  }
  if (
    view.contract?.registryId !== "aios-v2.character-ambient-behavior" ||
    view.contract?.contractVersion !== "1.0.0"
  ) {
    failures.push("fail-closed-invalid-source-contract");
  }
  if (view.presentationBasis !== "character-presentation-registry") {
    failures.push("fail-closed-invalid-presentation-basis");
  }
  if (typeof view.presentationKey !== "string" || view.presentationKey.length === 0) {
    failures.push("fail-closed-invalid-presentation-key");
  }
  if (!Array.isArray(view.actions)) {
    failures.push("fail-closed-invalid-actions");
  }
  if (
    view.mode !== "standard" &&
    view.mode !== "reduced-motion" &&
    view.mode !== "static"
  ) {
    failures.push("fail-closed-invalid-behavior-mode");
  }
  if (view.presentationOnly !== true) {
    failures.push("fail-closed-truth-presentationOnly");
  }
  for (const flag of EXPECTED_FALSE_FLAGS) {
    if (view[flag] !== false) failures.push(`fail-closed-truth-${flag}`);
  }
  if (view.reducedMotion?.informationLoss !== false) {
    failures.push("fail-closed-invalid-reduced-motion-envelope");
  }
  if (view.mode === "reduced-motion" && view.reducedMotion?.enabled !== true) {
    failures.push("fail-closed-reduced-motion-mode-mismatch");
  }
  if (view.mode === "standard" && view.reducedMotion?.enabled !== false) {
    failures.push("fail-closed-reduced-motion-mode-mismatch");
  }
  return failures;
}

function normalizePhaseSlot(
  value: unknown,
  limitations: string[],
): V2AmbientRendererPhaseSlot {
  if (value === undefined || value === null) return 0;
  if (typeof value === "number" && Number.isInteger(value) && value >= 0 && value <= 3) {
    return value as V2AmbientRendererPhaseSlot;
  }
  limitations.push("invalid-phase-slot-normalized-to-zero");
  return 0;
}

function isSafeTiming(value: unknown, upperBoundMs: number): value is number {
  return (
    typeof value === "number" &&
    Number.isFinite(value) &&
    value > 0 &&
    value <= upperBoundMs
  );
}

function rendererTruth(): V2AmbientRendererTruth {
  return deepFreeze({
    semanticAnimationActive: false,
    canonicalStateWritable: false,
    physicalPresenceClaimed: false,
    physicalLocationClaimed: false,
    physicalTravelClaimed: false,
    conversationClaimed: false,
    collaborationClaimed: false,
    workActivityClaimed: false,
    completionClaimed: false,
    handoffClaimed: false,
    blockerResolutionClaimed: false,
  });
}

function buildStaticDescriptor(
  presentationKey: string,
  phaseSlot: V2AmbientRendererPhaseSlot,
  limitations: readonly string[],
): V2AmbientCharacterRendererDescriptor {
  return deepFreeze({
    kind: "ambient-character-renderer",
    contract: {
      registryId: AMBIENT_RENDERER_CONTRACT.registryId,
      contractVersion: AMBIENT_RENDERER_CONTRACT.contractVersion,
    },
    presentationKey,
    mode: "static",
    phaseSlot,
    presentationOnly: true,
    truth: rendererTruth(),
    actions: [],
    reducedMotion: {
      enabled: false,
      transformActionsRemoved: false,
      staticEquivalentsOnly: false,
      informationLoss: false,
    },
    limitations: [...limitations],
  });
}

export function buildV2AmbientCharacterRenderer(
  input: V2AmbientCharacterRendererInput,
): V2AmbientCharacterRendererDescriptor {
  const request = input as unknown as
    | Readonly<{ ambientBehavior?: unknown; phaseSlot?: unknown }>
    | null
    | undefined;

  const limitations: string[] = [];
  const phaseSlot = normalizePhaseSlot(request?.phaseSlot, limitations);
  const candidate = request?.ambientBehavior;
  const failures = validateBehaviorEnvelope(candidate);
  const view = (candidate ?? null) as AmbientBehaviorView | null;
  const presentationKey =
    view && typeof view.presentationKey === "string" && view.presentationKey.length > 0
      ? view.presentationKey
      : "unavailable";

  if (failures.length > 0) {
    return buildStaticDescriptor(presentationKey, phaseSlot, [...limitations, ...failures]);
  }

  const behaviorMode = view!.mode as "standard" | "reduced-motion" | "static";
  const mode: V2AmbientRendererMode =
    behaviorMode === "standard"
      ? "ambient"
      : behaviorMode === "reduced-motion"
        ? "reduced-motion"
        : "static";

  if (mode === "static") {
    const rawActions = Array.isArray(view!.actions) ? view!.actions : [];
    if (rawActions.length > 0) limitations.push("static-mode-actions-omitted");
    return buildStaticDescriptor(presentationKey, phaseSlot, limitations);
  }

  const allowedKeys = new Set<string>(ALLOWED_AMBIENT_RENDERER_ACTION_KEYS);
  const phaseOffsetMs = PHASE_SLOT_OFFSETS_MS[phaseSlot];
  const seen = new Set<string>();
  const actions: V2AmbientRendererAction[] = [];
  const rawActions = Array.isArray(view!.actions) ? view!.actions : [];

  for (const raw of rawActions) {
    if (raw === null || typeof raw !== "object") {
      limitations.push("unsupported-ambient-action-ignored");
      continue;
    }

    const entry = raw as {
      readonly action?: unknown;
      readonly motionClass?: unknown;
      readonly durationMs?: unknown;
      readonly minIntervalMs?: unknown;
      readonly presentationOnly?: unknown;
    };

    if (typeof entry.action !== "string" || !allowedKeys.has(entry.action)) {
      limitations.push("unsupported-ambient-action-ignored");
      continue;
    }

    const key = entry.action as V2AmbientRendererActionKey;
    if (seen.has(key)) {
      limitations.push("duplicate-ambient-action-ignored");
      continue;
    }
    if (
      entry.presentationOnly !== true ||
      entry.motionClass !== EXPECTED_MOTION_CLASS[key] ||
      !isSafeTiming(entry.durationMs, 20_000) ||
      !isSafeTiming(entry.minIntervalMs, 60_000)
    ) {
      limitations.push("malformed-ambient-action-ignored");
      continue;
    }
    if (entry.motionClass === "transform" && mode !== "ambient") {
      limitations.push("transform-action-omitted-outside-ambient-mode");
      continue;
    }

    seen.add(key);
    actions.push({
      key,
      cssClass: ACTION_CSS_CLASSES[key],
      durationMs: entry.durationMs,
      minIntervalMs: entry.minIntervalMs,
      phaseOffsetMs,
      transformAllowed: entry.motionClass === "transform" && mode === "ambient",
    });
  }

  return deepFreeze({
    kind: "ambient-character-renderer",
    contract: {
      registryId: AMBIENT_RENDERER_CONTRACT.registryId,
      contractVersion: AMBIENT_RENDERER_CONTRACT.contractVersion,
    },
    presentationKey,
    mode,
    phaseSlot,
    presentationOnly: true,
    truth: rendererTruth(),
    actions,
    reducedMotion: {
      enabled: mode === "reduced-motion",
      transformActionsRemoved: mode === "reduced-motion",
      staticEquivalentsOnly: mode === "reduced-motion",
      informationLoss: false,
    },
    limitations,
  });
}
