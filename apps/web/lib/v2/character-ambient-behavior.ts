/**
 * AIOS V2 — Phase 2K
 * Ambient Character Behavior Contract V1.
 *
 * Presentation-only. This planner may make a character appear quietly alive,
 * but it never establishes organization truth, presence, location, work,
 * conversation, handoff, completion, or any canonical state mutation.
 */

import type { V2CharacterPresentationResolution } from "./character-mission-presentation";

export type V2AmbientActionKey =
  | "blink"
  | "breathing"
  | "micro-posture"
  | "gaze-shift"
  | "focus-glow"
  | "device-idle"
  | "prop-idle"
  | "selection-emphasis";

export type V2AmbientMotionClass = "transform" | "opacity";
export type V2AmbientDensity = "low" | "normal" | "high";
export type V2AmbientBehaviorMode = "standard" | "reduced-motion" | "static";
export type V2AmbientProfileKey =
  | "ceo"
  | "cto"
  | "regulatory-compliance"
  | "operations"
  | "neutral";

export interface V2AmbientAction {
  readonly action: V2AmbientActionKey;
  readonly motionClass: V2AmbientMotionClass;
  readonly durationMs: number;
  readonly minIntervalMs: number;
  readonly weight: number;
  readonly tier: 1 | 2 | 3;
  readonly presentationOnly: true;
}

export interface V2AmbientTimingBlock {
  readonly source: "bounded-presentation-constants";
  readonly independentOfCanonicalTime: true;
  readonly densityAffectsPresentationOnly: true;
  readonly densityMayChangeActionSubset: true;
  readonly densityNeverChangesTruth: true;
  readonly entries: Readonly<
    Record<string, Readonly<{ durationMs: number; minIntervalMs: number }>>
  >;
}

export interface V2AmbientReducedMotionBlock {
  readonly enabled: boolean;
  readonly policy: "brief-opacity-emphasis-only" | "not-applied";
  readonly excludedActionKeys: readonly V2AmbientActionKey[];
  readonly informationLoss: false;
}

export interface V2AmbientCharacterBehaviorDescriptor {
  readonly kind: "ambient-character-behavior";
  readonly contract: Readonly<{ registryId: string; contractVersion: string }>;
  readonly presentationKey: string;
  readonly ambientProfile: V2AmbientProfileKey;
  readonly density: V2AmbientDensity;
  readonly mode: V2AmbientBehaviorMode;
  readonly presentationBasis: "character-presentation-registry";
  readonly presentationOnly: true;
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
  readonly actions: readonly V2AmbientAction[];
  readonly timing: V2AmbientTimingBlock;
  readonly reducedMotion: V2AmbientReducedMotionBlock;
  readonly limitations: readonly string[];
}

export interface V2AmbientCharacterBehaviorInput {
  readonly presentation: V2CharacterPresentationResolution;
  readonly reducedMotion: boolean;
  readonly density: V2AmbientDensity;
}

function deepFreeze<T>(value: T): T {
  if (value === null || typeof value !== "object" || Object.isFrozen(value)) {
    return value;
  }
  Object.freeze(value);
  for (const key of Reflect.ownKeys(value as object)) {
    deepFreeze((value as Record<PropertyKey, unknown>)[key]);
  }
  return value;
}

export const AMBIENT_CHARACTER_BEHAVIOR_CONTRACT = deepFreeze({
  registryId: "aios-v2.character-ambient-behavior",
  contractVersion: "1.0.0",
  presentationOnly: true,
  presenceClaimed: false,
  semanticAnimationActive: false,
  canonicalStateWritable: false,
} as const);

export const ALLOWED_AMBIENT_ACTION_KEYS: readonly V2AmbientActionKey[] = deepFreeze([
  "blink",
  "breathing",
  "micro-posture",
  "gaze-shift",
  "focus-glow",
  "device-idle",
  "prop-idle",
  "selection-emphasis",
] as const);

export const FORBIDDEN_AMBIENT_ACTION_KEYS: readonly string[] = deepFreeze([
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
  "celebrate",
  "blocker-resolved",
] as const);

export const AMBIENT_DENSITY_MODES: readonly V2AmbientDensity[] = deepFreeze([
  "low",
  "normal",
  "high",
] as const);

export const AMBIENT_BEHAVIOR_MODES: readonly V2AmbientBehaviorMode[] = deepFreeze([
  "standard",
  "reduced-motion",
  "static",
] as const);

export const AMBIENT_ACTION_TIMING = deepFreeze({
  blink: { durationMs: 120, minIntervalMs: 2400 },
  breathing: { durationMs: 4200, minIntervalMs: 4200 },
  "micro-posture": { durationMs: 380, minIntervalMs: 9000 },
  "gaze-shift": { durationMs: 260, minIntervalMs: 7000 },
  "focus-glow": { durationMs: 900, minIntervalMs: 12000 },
  "device-idle": { durationMs: 700, minIntervalMs: 11000 },
  "prop-idle": { durationMs: 640, minIntervalMs: 15000 },
  "selection-emphasis": { durationMs: 320, minIntervalMs: 5000 },
} satisfies Readonly<
  Record<V2AmbientActionKey, Readonly<{ durationMs: number; minIntervalMs: number }>>
>);

const ACTION_MOTION_CLASS = deepFreeze({
  blink: "opacity",
  breathing: "transform",
  "micro-posture": "transform",
  "gaze-shift": "transform",
  "focus-glow": "opacity",
  "device-idle": "opacity",
  "prop-idle": "opacity",
  "selection-emphasis": "opacity",
} satisfies Readonly<Record<V2AmbientActionKey, V2AmbientMotionClass>>);

type ProfileAction = Readonly<{
  action: V2AmbientActionKey;
  tier: 1 | 2 | 3;
  baseWeight: number;
  durationMs?: number;
  minIntervalMs?: number;
}>;

type Profile = Readonly<{
  profileKey: V2AmbientProfileKey;
  actions: readonly ProfileAction[];
}>;

const PROFILES: Readonly<Record<V2AmbientProfileKey, Profile>> = deepFreeze({
  ceo: {
    profileKey: "ceo",
    actions: [
      { action: "blink", tier: 1, baseWeight: 2 },
      { action: "breathing", tier: 1, baseWeight: 2, durationMs: 5200 },
      { action: "gaze-shift", tier: 2, baseWeight: 1, minIntervalMs: 11000 },
      { action: "device-idle", tier: 2, baseWeight: 1 },
    ],
  },
  cto: {
    profileKey: "cto",
    actions: [
      { action: "blink", tier: 1, baseWeight: 2 },
      { action: "breathing", tier: 1, baseWeight: 2 },
      { action: "device-idle", tier: 2, baseWeight: 2 },
      { action: "focus-glow", tier: 2, baseWeight: 2 },
      { action: "micro-posture", tier: 2, baseWeight: 1 },
    ],
  },
  "regulatory-compliance": {
    profileKey: "regulatory-compliance",
    actions: [
      { action: "blink", tier: 1, baseWeight: 2 },
      { action: "breathing", tier: 1, baseWeight: 2 },
      { action: "device-idle", tier: 2, baseWeight: 2 },
      { action: "gaze-shift", tier: 2, baseWeight: 1 },
      { action: "focus-glow", tier: 2, baseWeight: 1 },
    ],
  },
  operations: {
    profileKey: "operations",
    actions: [
      { action: "blink", tier: 1, baseWeight: 2 },
      { action: "breathing", tier: 1, baseWeight: 2 },
      { action: "micro-posture", tier: 2, baseWeight: 2 },
      { action: "device-idle", tier: 2, baseWeight: 2 },
    ],
  },
  neutral: {
    profileKey: "neutral",
    actions: [
      { action: "blink", tier: 1, baseWeight: 2 },
      { action: "breathing", tier: 1, baseWeight: 2 },
    ],
  },
});

type RegistrationView = {
  readonly kind?: unknown;
  readonly canonicalPositionKey?: unknown;
  readonly presentationPositionKey?: unknown;
  readonly roleFamily?: unknown;
};

type ResolutionView = {
  readonly presentationKey?: unknown;
  readonly resolutionKind?: unknown;
  readonly presentationOnly?: unknown;
  readonly presenceClaimed?: unknown;
  readonly canonicalStateWritable?: unknown;
  readonly semanticAnimationActive?: unknown;
  readonly presentation?: {
    readonly registration?: RegistrationView;
    readonly presentationOnly?: unknown;
    readonly presenceClaimed?: unknown;
    readonly canonicalStateWritable?: unknown;
  };
};

type TrustedIdentity = Readonly<{
  presentationKey: string;
  ambientProfile: V2AmbientProfileKey;
}>;

function resolveTrustedIdentity(candidate: unknown): TrustedIdentity | null {
  if (candidate === null || typeof candidate !== "object") return null;
  const view = candidate as ResolutionView;
  const key = typeof view.presentationKey === "string" && view.presentationKey.length > 0
    ? view.presentationKey
    : null;
  const record = view.presentation;
  const registration = record?.registration;

  if (
    key === null ||
    registration === null ||
    typeof registration !== "object" ||
    view.presentationOnly !== true ||
    view.presenceClaimed !== false ||
    view.canonicalStateWritable !== false ||
    view.semanticAnimationActive !== false ||
    record?.presentationOnly !== true ||
    record.presenceClaimed !== false ||
    record.canonicalStateWritable !== false ||
    view.resolutionKind !== registration.kind
  ) {
    return null;
  }

  if (registration.kind === "exact-position") {
    if (
      typeof registration.canonicalPositionKey !== "string" ||
      registration.canonicalPositionKey !== key
    ) {
      return null;
    }
    if (key === "ceo") return { presentationKey: key, ambientProfile: "ceo" };
    if (key === "cto") return { presentationKey: key, ambientProfile: "cto" };
    return { presentationKey: key, ambientProfile: "neutral" };
  }

  if (registration.kind === "role-family-fallback") {
    if (
      typeof registration.presentationPositionKey !== "string" ||
      registration.presentationPositionKey !== key
    ) {
      return null;
    }
    if (
      registration.roleFamily === "regulatory-compliance" &&
      key === "role-family:regulatory-compliance"
    ) {
      return { presentationKey: key, ambientProfile: "regulatory-compliance" };
    }
    if (registration.roleFamily === "operations" && key === "role-family:operations") {
      return { presentationKey: key, ambientProfile: "operations" };
    }
    return { presentationKey: key, ambientProfile: "neutral" };
  }

  if (registration.kind === "neutral-fallback") {
    return key === "neutral-professional"
      ? { presentationKey: key, ambientProfile: "neutral" }
      : null;
  }

  return null;
}

function maxTier(density: V2AmbientDensity): 1 | 2 | 3 {
  return density === "low" ? 1 : density === "high" ? 3 : 2;
}

function densityWeight(baseWeight: number, density: V2AmbientDensity): number {
  if (density === "low") return Math.max(1, baseWeight - 1);
  if (density === "high") return Math.min(4, baseWeight + 1);
  return baseWeight;
}

function buildFallback(
  reducedMotion: boolean,
  density: V2AmbientDensity,
  limitations: readonly string[],
): V2AmbientCharacterBehaviorDescriptor {
  return deepFreeze({
    kind: "ambient-character-behavior",
    contract: {
      registryId: AMBIENT_CHARACTER_BEHAVIOR_CONTRACT.registryId,
      contractVersion: AMBIENT_CHARACTER_BEHAVIOR_CONTRACT.contractVersion,
    },
    presentationKey: "unavailable",
    ambientProfile: "neutral",
    density,
    mode: "static",
    presentationBasis: "character-presentation-registry",
    presentationOnly: true,
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
    actions: [],
    timing: {
      source: "bounded-presentation-constants",
      independentOfCanonicalTime: true,
      densityAffectsPresentationOnly: true,
      densityMayChangeActionSubset: true,
      densityNeverChangesTruth: true,
      entries: {},
    },
    reducedMotion: {
      enabled: reducedMotion,
      policy: reducedMotion ? "brief-opacity-emphasis-only" : "not-applied",
      excludedActionKeys: [],
      informationLoss: false,
    },
    limitations: [...limitations],
  } satisfies V2AmbientCharacterBehaviorDescriptor);
}

export function buildV2AmbientCharacterBehavior(
  input: V2AmbientCharacterBehaviorInput,
): V2AmbientCharacterBehaviorDescriptor {
  const request = input as unknown as
    | Readonly<{ presentation?: unknown; reducedMotion?: unknown; density?: unknown }>
    | null
    | undefined;
  const reducedMotion = request?.reducedMotion === true;
  const requestedDensity = request?.density;
  const density: V2AmbientDensity =
    requestedDensity === "low" || requestedDensity === "normal" || requestedDensity === "high"
      ? requestedDensity
      : "normal";
  const densityLimitations =
    requestedDensity === "low" || requestedDensity === "normal" || requestedDensity === "high"
      ? []
      : ["unknown-density-treated-as-normal"];

  const identity = resolveTrustedIdentity(request?.presentation);
  if (identity === null) {
    return buildFallback(reducedMotion, density, [
      ...densityLimitations,
      "presentation-resolution-missing-or-inconsistent",
    ]);
  }

  const profile = PROFILES[identity.ambientProfile];
  const candidates = profile.actions.filter((spec) => spec.tier <= maxTier(density));
  const excludedActionKeys = reducedMotion
    ? candidates
        .filter((spec) => ACTION_MOTION_CLASS[spec.action] === "transform")
        .map((spec) => spec.action)
    : [];
  const activeSpecs = reducedMotion
    ? candidates.filter((spec) => ACTION_MOTION_CLASS[spec.action] !== "transform")
    : candidates;
  const actions = activeSpecs.map((spec): V2AmbientAction => {
    const timing = AMBIENT_ACTION_TIMING[spec.action];
    return {
      action: spec.action,
      motionClass: ACTION_MOTION_CLASS[spec.action],
      durationMs: spec.durationMs ?? timing.durationMs,
      minIntervalMs: spec.minIntervalMs ?? timing.minIntervalMs,
      weight: densityWeight(spec.baseWeight, density),
      tier: spec.tier,
      presentationOnly: true,
    };
  });
  const entries = Object.fromEntries(
    actions.map((action) => [
      action.action,
      { durationMs: action.durationMs, minIntervalMs: action.minIntervalMs },
    ]),
  );

  return deepFreeze({
    kind: "ambient-character-behavior",
    contract: {
      registryId: AMBIENT_CHARACTER_BEHAVIOR_CONTRACT.registryId,
      contractVersion: AMBIENT_CHARACTER_BEHAVIOR_CONTRACT.contractVersion,
    },
    presentationKey: identity.presentationKey,
    ambientProfile: identity.ambientProfile,
    density,
    mode: reducedMotion ? (actions.length > 0 ? "reduced-motion" : "static") : "standard",
    presentationBasis: "character-presentation-registry",
    presentationOnly: true,
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
    actions,
    timing: {
      source: "bounded-presentation-constants",
      independentOfCanonicalTime: true,
      densityAffectsPresentationOnly: true,
      densityMayChangeActionSubset: true,
      densityNeverChangesTruth: true,
      entries,
    },
    reducedMotion: {
      enabled: reducedMotion,
      policy: reducedMotion ? "brief-opacity-emphasis-only" : "not-applied",
      excludedActionKeys,
      informationLoss: false,
    },
    limitations: densityLimitations,
  } satisfies V2AmbientCharacterBehaviorDescriptor);
}
