/**
 * AIOS V2 — Phase 2O
 * Canonical Handoff Visualization Descriptor V1
 *
 * Pure presentation bridge from the sealed Phase 2E governed handoff motion
 * descriptor to a renderer-ready visualization sequence. It never activates
 * animation and never upgrades presentation timing/path into canonical truth.
 *
 * Governing law:
 *   The organization causes the animation. Animation never causes the organization.
 */

import type { V2HandoffMotionDescriptor } from "./character-semantic-motion.ts";

export const HANDOFF_VISUALIZATION_CONTRACT = deepFreeze({
  registryId: "aios-v2.canonical-handoff-visualization",
  contractVersion: "1.0.0",
  presentationOnly: true,
  canonicalStateWritable: false,
  semanticAnimationActive: false,
} as const);

export type V2HandoffVisualizationMode =
  | "bounded-transfer-sequence"
  | "static-relation"
  | "unsupported";

export type V2HandoffVisualizationStepKey =
  | "sender-emphasis"
  | "work-object-activate"
  | "bounded-transfer-path"
  | "receiver-emphasis"
  | "settle"
  | "static-relation";

export type V2HandoffVisualizationTimingToken =
  | "micro"
  | "standard"
  | "spatial-focus";

export type V2HandoffVisualizationStep = {
  readonly key: V2HandoffVisualizationStepKey;
  readonly subject: "sender" | "receiver" | "work-object" | "relation" | "scene";
  readonly presentationAction:
    | "emphasis"
    | "activate"
    | "bounded-transfer"
    | "settle"
    | "static-relation";
  readonly timingToken: V2HandoffVisualizationTimingToken;
  readonly physicalMotionClaimed: false;
};

export type V2HandoffVisualizationTruth = {
  readonly canonicalEvent: boolean;
  readonly canonicalEventSource: "LivingSceneHandoff" | "none";
  readonly canonicalStateWritable: false;
  readonly physicalPresenceClaimed: false;
  readonly physicalLocationClaimed: false;
  readonly physicalTravelClaimed: false;
  readonly physicalTransferDurationClaimed: false;
  readonly roomTraversalClaimed: false;
  readonly conversationClaimed: false;
  readonly transcriptClaimed: false;
  readonly spokenWordsClaimed: false;
  readonly collaborationClaimed: false;
  readonly workCompletionClaimed: false;
  readonly dependencyResolutionClaimed: false;
  readonly authorityChangeClaimed: false;
  readonly approvalOrRejectionClaimed: false;
  readonly presentationTimingIsCanonical: false;
  readonly visualPathIsPhysicalRoute: false;
};

export type V2HandoffVisualizationReplay = {
  readonly mode: "live" | "replay";
  readonly coverageSupported: boolean | null;
  readonly cursorActivityId: string | null;
  readonly cursorMatchesActivity: boolean | null;
  readonly activationAllowedByReplayContext: boolean;
  readonly requiresSupportedCoverage: true;
  readonly requiresMatchingCanonicalEvent: true;
  readonly historicalInferenceAllowed: false;
};

export type V2HandoffVisualizationReducedMotion = {
  readonly enabled: boolean;
  readonly mode: "full-sequence" | "static-relation-brief-emphasis";
  readonly longTravelAnimationAllowed: false;
  readonly semanticInformationPreserved: true;
};

export type V2HandoffVisualizationLimitation =
  | "source-motion-unsupported"
  | "source-motion-truth-invalid"
  | "replay-coverage-unsupported"
  | "replay-cursor-mismatch";

export type V2HandoffVisualizationDescriptor = {
  readonly kind: "canonical-handoff-visualization";
  readonly contract: Readonly<{
    registryId: typeof HANDOFF_VISUALIZATION_CONTRACT.registryId;
    contractVersion: typeof HANDOFF_VISUALIZATION_CONTRACT.contractVersion;
  }>;
  readonly presentationOnly: true;
  readonly semanticAnimationActive: false;
  readonly supported: boolean;
  readonly limitation: V2HandoffVisualizationLimitation | null;
  readonly mode: V2HandoffVisualizationMode;
  readonly activityId: string;
  readonly workItemId: string;
  readonly fromPositionKey: string;
  readonly toPositionKey: string;
  readonly occurredAt: string;
  readonly canonicalBasis: string;
  readonly handoffStatus: string;
  readonly senderPresentationKey: string;
  readonly receiverPresentationKey: string;
  readonly steps: readonly V2HandoffVisualizationStep[];
  readonly truth: V2HandoffVisualizationTruth;
  readonly replay: V2HandoffVisualizationReplay;
  readonly reducedMotion: V2HandoffVisualizationReducedMotion;
};

export type V2HandoffVisualizationContext =
  | { readonly mode: "live" }
  | {
      readonly mode: "replay";
      readonly coverageSupported: boolean;
      readonly cursorActivityId: string | null;
    };

export type V2HandoffVisualizationInput = {
  readonly motion: V2HandoffMotionDescriptor;
  readonly reducedMotion: boolean;
  readonly context?: V2HandoffVisualizationContext;
};

function deepFreeze<T>(value: T): T {
  if (value === null || typeof value !== "object" || Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const key of Reflect.ownKeys(value as object)) {
    deepFreeze((value as Record<PropertyKey, unknown>)[key]);
  }
  return value;
}

function sourceTruthIsSafe(motion: V2HandoffMotionDescriptor | null): motion is V2HandoffMotionDescriptor {
  if (!motion || typeof motion !== "object" || motion.kind !== "handoff") return false;
  const truth = motion.truth;
  if (!truth || typeof truth !== "object") return false;
  return (
    motion.semanticAnimationActive === false &&
    truth.canonicalEvent === true &&
    truth.canonicalEventSource === "LivingSceneHandoff" &&
    truth.canonicalStateWritable === false &&
    truth.physicalTransferDurationClaimed === false &&
    truth.physicalTravelClaimed === false &&
    truth.roomTraversalClaimed === false &&
    truth.physicalPresenceClaimed === false &&
    truth.conversationClaimed === false &&
    truth.transcriptClaimed === false &&
    truth.spokenWordsClaimed === false &&
    truth.workCompletionClaimed === false &&
    truth.dependencyResolutionClaimed === false &&
    truth.authorityChangeClaimed === false &&
    truth.approvalOrRejectionClaimed === false &&
    typeof motion.activityId === "string" && motion.activityId.length > 0 &&
    typeof motion.workItemId === "string" && motion.workItemId.length > 0 &&
    typeof motion.fromPositionKey === "string" && motion.fromPositionKey.length > 0 &&
    typeof motion.toPositionKey === "string" && motion.toPositionKey.length > 0 &&
    typeof motion.occurredAt === "string" && motion.occurredAt.length > 0 &&
    typeof motion.canonicalBasis === "string" && motion.canonicalBasis.length > 0
  );
}

const FULL_SEQUENCE: readonly V2HandoffVisualizationStep[] = deepFreeze([
  {
    key: "sender-emphasis",
    subject: "sender",
    presentationAction: "emphasis",
    timingToken: "micro",
    physicalMotionClaimed: false,
  },
  {
    key: "work-object-activate",
    subject: "work-object",
    presentationAction: "activate",
    timingToken: "standard",
    physicalMotionClaimed: false,
  },
  {
    key: "bounded-transfer-path",
    subject: "relation",
    presentationAction: "bounded-transfer",
    timingToken: "spatial-focus",
    physicalMotionClaimed: false,
  },
  {
    key: "receiver-emphasis",
    subject: "receiver",
    presentationAction: "emphasis",
    timingToken: "standard",
    physicalMotionClaimed: false,
  },
  {
    key: "settle",
    subject: "scene",
    presentationAction: "settle",
    timingToken: "standard",
    physicalMotionClaimed: false,
  },
]);

const REDUCED_SEQUENCE: readonly V2HandoffVisualizationStep[] = deepFreeze([
  {
    key: "sender-emphasis",
    subject: "sender",
    presentationAction: "emphasis",
    timingToken: "micro",
    physicalMotionClaimed: false,
  },
  {
    key: "static-relation",
    subject: "relation",
    presentationAction: "static-relation",
    timingToken: "standard",
    physicalMotionClaimed: false,
  },
  {
    key: "receiver-emphasis",
    subject: "receiver",
    presentationAction: "emphasis",
    timingToken: "micro",
    physicalMotionClaimed: false,
  },
]);

function truthBlock(canonicalEvent: boolean): V2HandoffVisualizationTruth {
  return deepFreeze({
    canonicalEvent,
    canonicalEventSource: canonicalEvent ? "LivingSceneHandoff" : "none",
    canonicalStateWritable: false,
    physicalPresenceClaimed: false,
    physicalLocationClaimed: false,
    physicalTravelClaimed: false,
    physicalTransferDurationClaimed: false,
    roomTraversalClaimed: false,
    conversationClaimed: false,
    transcriptClaimed: false,
    spokenWordsClaimed: false,
    collaborationClaimed: false,
    workCompletionClaimed: false,
    dependencyResolutionClaimed: false,
    authorityChangeClaimed: false,
    approvalOrRejectionClaimed: false,
    presentationTimingIsCanonical: false,
    visualPathIsPhysicalRoute: false,
  });
}

export function buildV2HandoffVisualization(
  input: V2HandoffVisualizationInput,
): V2HandoffVisualizationDescriptor {
  const motion = input?.motion ?? null;
  const reducedMotion = input?.reducedMotion === true;
  const context: V2HandoffVisualizationContext = input?.context ?? { mode: "live" };

  const truthSafe = sourceTruthIsSafe(motion);
  const sourceSupported = truthSafe && motion.supported === true;

  const replayCoverageSupported =
    context.mode === "replay" ? context.coverageSupported === true : null;
  const replayCursorActivityId =
    context.mode === "replay" ? context.cursorActivityId : null;
  const replayCursorMatches =
    context.mode === "replay" && truthSafe
      ? replayCursorActivityId === motion.activityId
      : context.mode === "replay"
        ? false
        : null;
  const replayAllowsActivation =
    context.mode === "live" ||
    (replayCoverageSupported === true && replayCursorMatches === true);

  let limitation: V2HandoffVisualizationLimitation | null = null;
  if (!truthSafe) {
    limitation = "source-motion-truth-invalid";
  } else if (!motion.supported) {
    limitation = "source-motion-unsupported";
  } else if (context.mode === "replay" && !replayCoverageSupported) {
    limitation = "replay-coverage-unsupported";
  } else if (context.mode === "replay" && !replayCursorMatches) {
    limitation = "replay-cursor-mismatch";
  }

  const supported = sourceSupported && replayAllowsActivation;
  const mode: V2HandoffVisualizationMode = !supported
    ? "unsupported"
    : reducedMotion
      ? "static-relation"
      : "bounded-transfer-sequence";

  const descriptor: V2HandoffVisualizationDescriptor = {
    kind: "canonical-handoff-visualization",
    contract: {
      registryId: HANDOFF_VISUALIZATION_CONTRACT.registryId,
      contractVersion: HANDOFF_VISUALIZATION_CONTRACT.contractVersion,
    },
    presentationOnly: true,
    semanticAnimationActive: false,
    supported,
    limitation,
    mode,
    activityId: truthSafe ? motion.activityId : "",
    workItemId: truthSafe ? motion.workItemId : "",
    fromPositionKey: truthSafe ? motion.fromPositionKey : "",
    toPositionKey: truthSafe ? motion.toPositionKey : "",
    occurredAt: truthSafe ? motion.occurredAt : "",
    canonicalBasis: truthSafe ? motion.canonicalBasis : "",
    handoffStatus: truthSafe ? motion.handoffStatus : "",
    senderPresentationKey: truthSafe ? motion.senderPresentationKey : "unresolved",
    receiverPresentationKey: truthSafe ? motion.receiverPresentationKey : "unresolved",
    steps: supported ? (reducedMotion ? REDUCED_SEQUENCE : FULL_SEQUENCE) : [],
    truth: truthBlock(truthSafe),
    replay: {
      mode: context.mode,
      coverageSupported: replayCoverageSupported,
      cursorActivityId: replayCursorActivityId,
      cursorMatchesActivity: replayCursorMatches,
      activationAllowedByReplayContext: replayAllowsActivation,
      requiresSupportedCoverage: true,
      requiresMatchingCanonicalEvent: true,
      historicalInferenceAllowed: false,
    },
    reducedMotion: {
      enabled: reducedMotion,
      mode: reducedMotion ? "static-relation-brief-emphasis" : "full-sequence",
      longTravelAnimationAllowed: false,
      semanticInformationPreserved: true,
    },
  };

  return deepFreeze(descriptor);
}
