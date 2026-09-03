/**
 * AIOS V2 - Phase 2E Governed Handoff Motion Descriptor
 * =====================================================
 *
 * Pure, deterministic, read-only translation of a canonical
 * `LivingSceneHandoff` plus already-resolved sender/receiver character
 * presentations into a bounded, truth-preserving handoff motion descriptor.
 *
 * Core invariant (skills/aios-design/governance/semantic-animation-contract.md):
 *
 *   > The organization causes the animation. Animation never causes the
 *   > organization.
 *
 * The canonical handoff record is the ONLY authority that a handoff occurred.
 * Character presentation metadata may only decide whether/how that event can
 * be visually expressed. This module never starts animation; it describes
 * what a renderer MAY render later (`semanticAnimationActive` is always
 * false at creation time).
 *
 * References:
 *   - apps/web/lib/live-organization.ts          (canonical LivingSceneHandoff)
 *   - apps/web/lib/v2/character-presentation.ts  (capability declarations)
 *   - apps/web/lib/v2/character-mission-presentation.ts (resolution shape)
 *   - skills/aios-design/characters/CHARACTER_BIBLE.md
 *   - skills/aios-design/characters/animation-states.md
 *   - skills/aios-design/governance/semantic-animation-contract.md
 *
 * Determinism: no random sources, no clocks, no scheduling primitives, no
 * platform/event/renderer/network/backend access, no mutable module state.
 * Identical inputs always produce a deeply identical, deeply frozen result.
 */

import type { LivingSceneHandoff } from "../live-organization.ts";
import type { V2CharacterPresentationResolution } from "./character-mission-presentation.ts";

/* ------------------------------------------------------------------ */
/* Descriptor vocabulary                                               */
/* ------------------------------------------------------------------ */

export type V2HandoffMotionVisualMode = "bounded-transfer-emphasis";

/** Truth flags. Never-claims are literal `false` so the compiler itself forbids them drifting to true. */
export type V2HandoffMotionTruth = {
  /** True only when a complete canonical handoff record is present. The record is the sole authority. */
  readonly canonicalEvent: boolean;
  /** Where the canonical event authority comes from (never from presentation data). */
  readonly canonicalEventSource: "LivingSceneHandoff" | "none";
  /** occurred_at is canonical event time; it must never become animation duration. */
  readonly occurredAtIsEventTimeOnly: boolean;
  readonly occurredAtIsAnimationDuration: false;
  /** Canonical status is echoed verbatim; it is never converted into completion. */
  readonly handoffStatusIsVerbatimEcho: boolean;
  readonly handoffStatusIsCompletionClaim: false;
  readonly physicalTransferDurationClaimed: false;
  readonly physicalTravelClaimed: false;
  readonly roomTraversalClaimed: false;
  readonly physicalPresenceClaimed: false;
  readonly conversationClaimed: false;
  readonly transcriptClaimed: false;
  readonly spokenWordsClaimed: false;
  readonly workCompletionClaimed: false;
  readonly dependencyResolutionClaimed: false;
  readonly authorityChangeClaimed: false;
  readonly approvalOrRejectionClaimed: false;
  readonly canonicalStateWritable: false;
};

/** First-class reduced-motion form: static sender -> receiver relation with brief emphasis only. */
export type V2HandoffReducedMotion = {
  readonly mode: "static-relation-brief-emphasis";
  /** Static relation label with concrete canonical position keys. */
  readonly relation: string;
  readonly fromPositionKey: string;
  readonly toPositionKey: string;
  readonly direction: "sender-to-receiver";
  readonly briefEmphasisOnly: true;
  readonly forbidsLongTravelAnimation: true;
  readonly preservesCanonicalIdentity: true;
};

export type V2HandoffMotionDescriptor = {
  readonly kind: "handoff";
  /* Canonical evidence, preserved exactly (never reinterpreted). */
  readonly activityId: string;
  readonly workItemId: string;
  readonly fromPositionKey: string;
  readonly toPositionKey: string;
  readonly causationActivityId: string | null;
  readonly occurredAt: string;
  readonly canonicalBasis: string;
  /** Verbatim echo of `LivingSceneHandoff.status`; carries no completion semantics. */
  readonly handoffStatus: string;
  /* Capability gate outcome. */
  readonly supported: boolean;
  /** Deterministic machine-stable limitation code; null when supported. */
  readonly limitation: V2HandoffMotionLimitationCode | null;
  readonly senderPresentationKey: string;
  readonly receiverPresentationKey: string;
  readonly senderCapabilitySupported: boolean;
  readonly receiverCapabilitySupported: boolean;
  readonly senderIdentityMatchesCanonicalHandoff: boolean;
  readonly receiverIdentityMatchesCanonicalHandoff: boolean;
  /* Rendering contract. */
  readonly visualMode: V2HandoffMotionVisualMode;
  /** Descriptor creation NEVER activates animation. A renderer may do so later, governed by this descriptor. */
  readonly semanticAnimationActive: false;
  readonly truth: V2HandoffMotionTruth;
  readonly reducedMotion: V2HandoffReducedMotion;
};

export type V2HandoffMotionLimitationCode =
  | "canonical-handoff-record-missing-or-incomplete"
  | "sender-presentation-identity-mismatch"
  | "receiver-presentation-identity-mismatch"
  | "sender-and-receiver-presentation-identities-mismatch"
  | "sender-presentation-lacks-handoff-capability"
  | "receiver-presentation-lacks-handoff-capability"
  | "sender-and-receiver-presentations-lack-handoff-capability";

export type V2HandoffMotionDescriptorInput = {
  handoff: LivingSceneHandoff;
  sender: V2CharacterPresentationResolution;
  receiver: V2CharacterPresentationResolution;
};

/* ------------------------------------------------------------------ */
/* Internal pure helpers                                               */
/* ------------------------------------------------------------------ */

const REQUIRED_CAPABILITY = "handoff" as const;

function declaresHandoffCapability(resolution: V2CharacterPresentationResolution | null): boolean {
  return (
    resolution !== null &&
    Array.isArray(resolution.presentation.supportedSemanticAnimationCapabilities) &&
    resolution.presentation.supportedSemanticAnimationCapabilities.includes(REQUIRED_CAPABILITY)
  );
}

function resolutionMatchesCanonicalPosition(
  resolution: V2CharacterPresentationResolution | null,
  expectedPositionKey: string,
): boolean {
  return resolution !== null && resolution.identity.positionKey === expectedPositionKey;
}

function presentationKeyOf(resolution: V2CharacterPresentationResolution | null): string {
  return resolution === null ? "unresolved" : String(resolution.presentationKey);
}

function hasCompleteCanonicalHandoff(handoff: LivingSceneHandoff | null): handoff is LivingSceneHandoff {
  if (handoff === null || typeof handoff !== "object") return false;
  return (
    typeof handoff.activity_id === "string" && handoff.activity_id.length > 0 &&
    typeof handoff.work_item_id === "string" && handoff.work_item_id.length > 0 &&
    typeof handoff.previous_position_key === "string" && handoff.previous_position_key.length > 0 &&
    typeof handoff.assigned_position_key === "string" && handoff.assigned_position_key.length > 0 &&
    typeof handoff.occurred_at === "string" && handoff.occurred_at.length > 0 &&
    typeof handoff.canonical_basis === "string" && handoff.canonical_basis.length > 0 &&
    typeof handoff.status === "string" && handoff.status.length > 0 &&
    (handoff.causation_activity_id === null || typeof handoff.causation_activity_id === "string")
  );
}

/**
 * Deep-freeze the descriptor and every nested object/array so the exported
 * result exposes no mutation surface. Purely local; no global state.
 */
function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === "object") {
    for (const key of Object.getOwnPropertyNames(value as object)) {
      deepFreeze((value as Record<string, unknown>)[key]);
    }
    Object.freeze(value);
  }
  return value;
}

/* ------------------------------------------------------------------ */
/* Public API (single pure function)                                   */
/* ------------------------------------------------------------------ */

/**
 * Build the governed handoff motion descriptor.
 *
 * - Visual support requires BOTH presentations to declare the "handoff"
 *   semantic capability. Neutral fallbacks declare none, so neutral
 *   sender/receiver normally yields an unsupported descriptor.
 * - Canonical identifiers, positions, occurred_at and canonical_basis are
 *   preserved exactly, whether supported or not.
 * - The result never claims physical duration/travel/traversal/presence,
 *   conversation, transcript, spoken words, work completion, dependency
 *   resolution, authority change, approval/rejection, or canonical mutation.
 * - occurred_at is event time, never animation duration.
 */
export function buildV2HandoffMotionDescriptor(
  input: V2HandoffMotionDescriptorInput,
): V2HandoffMotionDescriptor {
  const handoff: LivingSceneHandoff | null = input?.handoff ?? null;
  const sender = input?.sender ?? null;
  const receiver = input?.receiver ?? null;

  const complete = hasCompleteCanonicalHandoff(handoff);
  const senderCapabilitySupported = declaresHandoffCapability(sender);
  const receiverCapabilitySupported = declaresHandoffCapability(receiver);
  const senderIdentityMatchesCanonicalHandoff =
    complete && resolutionMatchesCanonicalPosition(sender, handoff.previous_position_key);
  const receiverIdentityMatchesCanonicalHandoff =
    complete && resolutionMatchesCanonicalPosition(receiver, handoff.assigned_position_key);

  const activityId = complete ? handoff.activity_id : "";
  const workItemId = complete ? handoff.work_item_id : "";
  const fromPositionKey = complete ? handoff.previous_position_key : "";
  const toPositionKey = complete ? handoff.assigned_position_key : "";
  const causationActivityId = complete ? handoff.causation_activity_id : null;
  const occurredAt = complete ? handoff.occurred_at : "";
  const canonicalBasis = complete ? handoff.canonical_basis : "";
  const handoffStatus = complete ? handoff.status : "";

  let limitation: V2HandoffMotionLimitationCode | null = null;
  if (!complete) {
    limitation = "canonical-handoff-record-missing-or-incomplete";
  } else if (!senderIdentityMatchesCanonicalHandoff && !receiverIdentityMatchesCanonicalHandoff) {
    limitation = "sender-and-receiver-presentation-identities-mismatch";
  } else if (!senderIdentityMatchesCanonicalHandoff) {
    limitation = "sender-presentation-identity-mismatch";
  } else if (!receiverIdentityMatchesCanonicalHandoff) {
    limitation = "receiver-presentation-identity-mismatch";
  } else if (!senderCapabilitySupported && !receiverCapabilitySupported) {
    limitation = "sender-and-receiver-presentations-lack-handoff-capability";
  } else if (!senderCapabilitySupported) {
    limitation = "sender-presentation-lacks-handoff-capability";
  } else if (!receiverCapabilitySupported) {
    limitation = "receiver-presentation-lacks-handoff-capability";
  }

  const descriptor: V2HandoffMotionDescriptor = {
    kind: "handoff",
    activityId,
    workItemId,
    fromPositionKey,
    toPositionKey,
    causationActivityId,
    occurredAt,
    canonicalBasis,
    handoffStatus,
    supported:
      complete &&
      senderIdentityMatchesCanonicalHandoff &&
      receiverIdentityMatchesCanonicalHandoff &&
      senderCapabilitySupported &&
      receiverCapabilitySupported,
    limitation,
    senderPresentationKey: presentationKeyOf(sender),
    receiverPresentationKey: presentationKeyOf(receiver),
    senderCapabilitySupported,
    receiverCapabilitySupported,
    senderIdentityMatchesCanonicalHandoff,
    receiverIdentityMatchesCanonicalHandoff,
    visualMode: "bounded-transfer-emphasis",
    semanticAnimationActive: false,
    truth: {
      canonicalEvent: complete,
      canonicalEventSource: complete ? "LivingSceneHandoff" : "none",
      occurredAtIsEventTimeOnly: complete,
      occurredAtIsAnimationDuration: false,
      handoffStatusIsVerbatimEcho: complete,
      handoffStatusIsCompletionClaim: false,
      physicalTransferDurationClaimed: false,
      physicalTravelClaimed: false,
      roomTraversalClaimed: false,
      physicalPresenceClaimed: false,
      conversationClaimed: false,
      transcriptClaimed: false,
      spokenWordsClaimed: false,
      workCompletionClaimed: false,
      dependencyResolutionClaimed: false,
      authorityChangeClaimed: false,
      approvalOrRejectionClaimed: false,
      canonicalStateWritable: false,
    },
    reducedMotion: {
      mode: "static-relation-brief-emphasis",
      relation: `${fromPositionKey} -> ${toPositionKey}`,
      fromPositionKey,
      toPositionKey,
      direction: "sender-to-receiver",
      briefEmphasisOnly: true,
      forbidsLongTravelAnimation: true,
      preservesCanonicalIdentity: true,
    },
  };

  return deepFreeze(descriptor);
}
