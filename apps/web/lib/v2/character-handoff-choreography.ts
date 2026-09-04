/**
 * AIOS V2 — Phase 2H Governed Handoff Choreography Planner.
 *
 * The organization causes the animation. Animation never causes the organization.
 * Pure, deterministic, read-only and renderer-independent.
 */
import type { V2HandoffMotionDescriptor } from "./character-semantic-motion.ts";

export type V2HandoffChoreographyMode = "standard" | "reduced-motion" | "unsupported";
export type V2HandoffChoreographyLimitationCode =
  | "phase2e-descriptor-missing-or-malformed"
  | "phase2e-descriptor-unsupported"
  | "phase2e-canonical-event-not-established"
  | "phase2e-sender-identity-mismatch"
  | "phase2e-receiver-identity-mismatch"
  | "phase2e-sender-capability-unsupported"
  | "phase2e-receiver-capability-unsupported"
  | "phase2e-descriptor-animation-already-active";

export type V2HandoffChoreographyStage = {
  readonly key:
    | "sender-emphasis"
    | "transfer-emphasis"
    | "receiver-emphasis"
    | "settle"
    | "static-relation"
    | "brief-target-emphasis";
  readonly durationMs: number;
  readonly target: "sender" | "relation" | "receiver" | "both";
  readonly visualIntent: "emphasize" | "transfer-relation" | "static-relation" | "settle";
  readonly semanticMeaning: "presentation-only";
  readonly canonicalStateWritable: false;
  readonly physicalTravelClaimed: false;
  readonly physicalPresenceClaimed: false;
  readonly conversationClaimed: false;
};

export type V2HandoffChoreography = {
  readonly kind: "handoff-choreography";
  readonly mode: V2HandoffChoreographyMode;
  readonly supported: boolean;
  readonly handoff: {
    readonly activityId: string;
    readonly workItemId: string;
    readonly fromPositionKey: string;
    readonly toPositionKey: string;
    readonly occurredAt: string;
    readonly canonicalBasis: string;
  };
  readonly presentation: {
    readonly senderPresentationKey: string;
    readonly receiverPresentationKey: string;
  };
  readonly semanticAnimationActive: false;
  readonly canonicalStateWritable: false;
  readonly physicalPresenceClaimed: false;
  readonly physicalTravelClaimed: false;
  readonly conversationClaimed: false;
  readonly workCompletionClaimed: false;
  readonly dependencyResolutionClaimed: false;
  readonly roomTraversalClaimed: false;
  readonly pathfindingRequired: false;
  readonly truth: {
    readonly canonicalEvent: boolean;
    readonly canonicalEventSource: "V2HandoffMotionDescriptor" | "none";
    readonly canonicalStateWritable: false;
    readonly physicalPresenceClaimed: false;
    readonly physicalTravelClaimed: false;
    readonly roomTraversalClaimed: false;
    readonly pathfindingRequired: false;
    readonly conversationClaimed: false;
    readonly spokenWordsClaimed: false;
    readonly transcriptClaimed: false;
    readonly physicalObjectTransferClaimed: false;
    readonly workCompletionClaimed: false;
    readonly dependencyResolutionClaimed: false;
    readonly authorityChangeClaimed: false;
    readonly approvalOrRejectionClaimed: false;
  };
  readonly timing: {
    readonly basis: "bounded-presentation-constants" | "none";
    readonly totalDurationMs: number;
    readonly maxTotalDurationMs: 900;
    readonly withinBoundedBudget: boolean;
    readonly timingCanonical: false;
    readonly occurredAtControlsDuration: false;
    readonly derivesFromCanonicalTimestamp: false;
  };
  readonly stages: readonly V2HandoffChoreographyStage[];
  readonly limitation: V2HandoffChoreographyLimitationCode | null;
  readonly phase2eLimitation: string | null;
  readonly reducedMotion: {
    readonly requested: boolean;
    readonly honored: boolean;
    readonly form: "static-relation-brief-emphasis" | "standard-bounded-emphasis" | "none";
    readonly relation: string;
    readonly briefEmphasisOnly: true;
    readonly forbidsLongTravelAnimation: true;
    readonly preservesCanonicalIdentity: boolean;
  };
};

export type V2HandoffChoreographyInput = {
  readonly descriptor: V2HandoffMotionDescriptor;
  readonly reducedMotion?: boolean;
};

const MAX_TOTAL_DURATION_MS = 900 as const;
const STANDARD = Object.freeze([
  Object.freeze({ key: "sender-emphasis", durationMs: 180, target: "sender", visualIntent: "emphasize" }),
  Object.freeze({ key: "transfer-emphasis", durationMs: 260, target: "relation", visualIntent: "transfer-relation" }),
  Object.freeze({ key: "receiver-emphasis", durationMs: 180, target: "receiver", visualIntent: "emphasize" }),
  Object.freeze({ key: "settle", durationMs: 160, target: "both", visualIntent: "settle" }),
] as const);
const REDUCED = Object.freeze([
  Object.freeze({ key: "static-relation", durationMs: 240, target: "relation", visualIntent: "static-relation" }),
  Object.freeze({ key: "brief-target-emphasis", durationMs: 180, target: "both", visualIntent: "emphasize" }),
  Object.freeze({ key: "settle", durationMs: 160, target: "both", visualIntent: "settle" }),
] as const);

function nonEmpty(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

function canonicalIdentityAvailable(descriptor: V2HandoffMotionDescriptor | null): boolean {
  return !!descriptor &&
    nonEmpty(descriptor.activityId) &&
    nonEmpty(descriptor.workItemId) &&
    nonEmpty(descriptor.fromPositionKey) &&
    nonEmpty(descriptor.toPositionKey) &&
    nonEmpty(descriptor.occurredAt) &&
    nonEmpty(descriptor.canonicalBasis);
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function stage(source: (typeof STANDARD)[number] | (typeof REDUCED)[number]): V2HandoffChoreographyStage {
  return {
    ...source,
    semanticMeaning: "presentation-only",
    canonicalStateWritable: false,
    physicalTravelClaimed: false,
    physicalPresenceClaimed: false,
    conversationClaimed: false,
  };
}

function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === "object") {
    for (const child of Object.values(value as Record<string, unknown>)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

export function buildV2HandoffChoreography(input: V2HandoffChoreographyInput): V2HandoffChoreography {
  const descriptor: V2HandoffMotionDescriptor | null = input?.descriptor ?? null;
  const reducedRequested = input?.reducedMotion === true;
  const hasIdentity = canonicalIdentityAvailable(descriptor);

  let limitation: V2HandoffChoreographyLimitationCode | null = null;
  if (!descriptor || typeof descriptor !== "object" || descriptor.kind !== "handoff") {
    limitation = "phase2e-descriptor-missing-or-malformed";
  } else if (descriptor.supported !== true) {
    limitation = "phase2e-descriptor-unsupported";
  } else if (!hasIdentity) {
    limitation = "phase2e-descriptor-missing-or-malformed";
  } else if (descriptor.truth?.canonicalEvent !== true) {
    limitation = "phase2e-canonical-event-not-established";
  } else if (descriptor.senderIdentityMatchesCanonicalHandoff !== true) {
    limitation = "phase2e-sender-identity-mismatch";
  } else if (descriptor.receiverIdentityMatchesCanonicalHandoff !== true) {
    limitation = "phase2e-receiver-identity-mismatch";
  } else if (descriptor.senderCapabilitySupported !== true) {
    limitation = "phase2e-sender-capability-unsupported";
  } else if (descriptor.receiverCapabilitySupported !== true) {
    limitation = "phase2e-receiver-capability-unsupported";
  } else if (descriptor.semanticAnimationActive !== false) {
    limitation = "phase2e-descriptor-animation-already-active";
  }

  const supported = limitation === null;
  const mode: V2HandoffChoreographyMode = !supported ? "unsupported" : reducedRequested ? "reduced-motion" : "standard";
  const stages = supported ? (reducedRequested ? REDUCED : STANDARD).map(stage) : [];
  const totalDurationMs = stages.reduce((sum, item) => sum + item.durationMs, 0);
  const canonicalEvent = hasIdentity && descriptor?.truth?.canonicalEvent === true;
  const from = asString(descriptor?.fromPositionKey);
  const to = asString(descriptor?.toPositionKey);

  return deepFreeze({
    kind: "handoff-choreography",
    mode,
    supported,
    handoff: {
      activityId: asString(descriptor?.activityId),
      workItemId: asString(descriptor?.workItemId),
      fromPositionKey: from,
      toPositionKey: to,
      occurredAt: asString(descriptor?.occurredAt),
      canonicalBasis: asString(descriptor?.canonicalBasis),
    },
    presentation: {
      senderPresentationKey: asString(descriptor?.senderPresentationKey),
      receiverPresentationKey: asString(descriptor?.receiverPresentationKey),
    },
    semanticAnimationActive: false,
    canonicalStateWritable: false,
    physicalPresenceClaimed: false,
    physicalTravelClaimed: false,
    conversationClaimed: false,
    workCompletionClaimed: false,
    dependencyResolutionClaimed: false,
    roomTraversalClaimed: false,
    pathfindingRequired: false,
    truth: {
      canonicalEvent,
      canonicalEventSource: canonicalEvent ? "V2HandoffMotionDescriptor" : "none",
      canonicalStateWritable: false,
      physicalPresenceClaimed: false,
      physicalTravelClaimed: false,
      roomTraversalClaimed: false,
      pathfindingRequired: false,
      conversationClaimed: false,
      spokenWordsClaimed: false,
      transcriptClaimed: false,
      physicalObjectTransferClaimed: false,
      workCompletionClaimed: false,
      dependencyResolutionClaimed: false,
      authorityChangeClaimed: false,
      approvalOrRejectionClaimed: false,
    },
    timing: {
      basis: supported ? "bounded-presentation-constants" : "none",
      totalDurationMs,
      maxTotalDurationMs: MAX_TOTAL_DURATION_MS,
      withinBoundedBudget: totalDurationMs <= MAX_TOTAL_DURATION_MS,
      timingCanonical: false,
      occurredAtControlsDuration: false,
      derivesFromCanonicalTimestamp: false,
    },
    stages,
    limitation,
    phase2eLimitation: nonEmpty(descriptor?.limitation) ? descriptor.limitation : null,
    reducedMotion: {
      requested: reducedRequested,
      honored: supported && reducedRequested,
      form: !supported ? "none" : reducedRequested ? "static-relation-brief-emphasis" : "standard-bounded-emphasis",
      relation: hasIdentity ? `${from} -> ${to}` : "",
      briefEmphasisOnly: true,
      forbidsLongTravelAnimation: true,
      preservesCanonicalIdentity: hasIdentity,
    },
  });
}
