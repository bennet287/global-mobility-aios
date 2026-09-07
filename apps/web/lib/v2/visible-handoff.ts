/**
 * AIOS V2 — Phase 7A visible canonical handoff integration.
 *
 * Selects exactly one presentation candidate from the supported canonical
 * Living Organization handoff stream and binds it to exact roster identities.
 * This module never animates, mutates AIOS, infers physical presence, or falls
 * back to an older event merely because the newest event is easier to render.
 */

import type { LivingSceneEmployee, LivingSceneHandoff } from "../live-organization.ts";
import { resolveV2CharacterPresentation } from "./character-mission-presentation.ts";
import {
  buildV2HandoffMotionDescriptor,
  type V2HandoffMotionDescriptor,
  type V2HandoffMotionLimitationCode,
} from "./character-semantic-motion.ts";
import {
  buildV2HandoffVisualization,
  type V2HandoffVisualizationDescriptor,
} from "./handoff-visualization.ts";

const SUPPORTED_HANDOFF_COVERAGE_STATES = Object.freeze([
  "organization_work_assigned_activity_v1",
  // Retained for bounded fixture/backward compatibility only. The current live
  // scene contract uses organization_work_assigned_activity_v1.
  "covered",
] as const);

export type V2VisibleHandoffEndpoint = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
};

export type V2VisibleHandoffLimitation =
  | "sender-employee-unavailable"
  | "receiver-employee-unavailable"
  | "sender-and-receiver-employees-unavailable"
  | V2HandoffMotionLimitationCode;

export type V2VisibleHandoffModel = {
  readonly kind: "visible-canonical-handoff";
  readonly canonicalHandoff: LivingSceneHandoff;
  readonly sender: V2VisibleHandoffEndpoint | null;
  readonly receiver: V2VisibleHandoffEndpoint | null;
  readonly motion: V2HandoffMotionDescriptor | null;
  readonly semanticAnimationSupported: boolean;
  readonly limitation: V2VisibleHandoffLimitation | null;
  readonly truth: Readonly<{
    canonicalEvent: true;
    canonicalCoverageState: string;
    canonicalCoverageSupported: true;
    presentationOnly: true;
    canonicalStateWritable: false;
    physicalPresenceClaimed: false;
    physicalLocationClaimed: false;
    physicalTravelClaimed: false;
    conversationClaimed: false;
    completionClaimed: false;
    latestMeansLatestSupportedEvent: true;
  }>;
};

export type BuildLatestV2VisibleHandoffInput = {
  readonly handoffs: readonly LivingSceneHandoff[];
  readonly employees: readonly LivingSceneEmployee[];
  readonly coverageState: string;
};

function deepFreeze<T>(value: T): T {
  if (value === null || typeof value !== "object" || Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const key of Reflect.ownKeys(value as object)) {
    deepFreeze((value as Record<PropertyKey, unknown>)[key]);
  }
  return value;
}

export function isSupportedV2HandoffCoverage(coverageState: string): boolean {
  return (SUPPORTED_HANDOFF_COVERAGE_STATES as readonly string[]).includes(coverageState);
}

function isOrderableHandoff(value: LivingSceneHandoff | null): value is LivingSceneHandoff {
  return Boolean(
    value &&
      typeof value.activity_id === "string" && value.activity_id.length > 0 &&
      typeof value.occurred_at === "string" && value.occurred_at.length > 0,
  );
}

function isCompleteCanonicalHandoff(value: LivingSceneHandoff | null): value is LivingSceneHandoff {
  return Boolean(
    isOrderableHandoff(value) &&
      typeof value.work_item_id === "string" && value.work_item_id.length > 0 &&
      typeof value.previous_position_key === "string" && value.previous_position_key.length > 0 &&
      typeof value.assigned_position_key === "string" && value.assigned_position_key.length > 0 &&
      typeof value.status === "string" && value.status.length > 0 &&
      (value.causation_activity_id === null || typeof value.causation_activity_id === "string") &&
      typeof value.canonical_basis === "string" && value.canonical_basis.length > 0,
  );
}

function comesAfter(candidate: LivingSceneHandoff, current: LivingSceneHandoff): boolean {
  if (candidate.occurred_at !== current.occurred_at) {
    return candidate.occurred_at > current.occurred_at;
  }
  return candidate.activity_id > current.activity_id;
}

function copyHandoff(handoff: LivingSceneHandoff): LivingSceneHandoff {
  return deepFreeze({
    activity_id: handoff.activity_id,
    work_item_id: handoff.work_item_id,
    previous_position_key: handoff.previous_position_key,
    assigned_position_key: handoff.assigned_position_key,
    status: handoff.status,
    occurred_at: handoff.occurred_at,
    causation_activity_id: handoff.causation_activity_id,
    canonical_basis: handoff.canonical_basis,
  });
}

function endpointFor(
  employees: readonly LivingSceneEmployee[],
  positionKey: string,
): V2VisibleHandoffEndpoint | null {
  const matches = employees.filter((candidate) => candidate.position_key === positionKey);
  if (matches.length !== 1) return null;
  const employee = matches[0];
  return deepFreeze({
    positionKey: employee.position_key,
    title: employee.title,
    department: employee.department,
  });
}

/**
 * Returns the latest complete handoff only when handoff coverage is one of the
 * explicitly supported canonical adapter states.
 *
 * To make the word "latest" truthful, every supplied handoff must provide the
 * canonical ordering identity (`occurred_at` + `activity_id`). If even one
 * record cannot participate in that ordering, this selector fails closed.
 * After the newest event is selected, it must itself satisfy the complete
 * canonical handoff contract. The selector never searches backward for an
 * older, easier-to-render event.
 */
export function buildLatestV2VisibleHandoff(
  input: BuildLatestV2VisibleHandoffInput,
): V2VisibleHandoffModel | null {
  if (!isSupportedV2HandoffCoverage(input.coverageState)) return null;
  if (input.handoffs.length === 0) return null;
  if (input.handoffs.some((candidate) => !isOrderableHandoff(candidate))) return null;

  let latest: LivingSceneHandoff | null = null;
  for (const candidate of input.handoffs) {
    if (!latest || comesAfter(candidate, latest)) latest = candidate;
  }
  if (!isCompleteCanonicalHandoff(latest)) return null;

  const canonicalHandoff = copyHandoff(latest);
  const sender = endpointFor(input.employees, canonicalHandoff.previous_position_key);
  const receiver = endpointFor(input.employees, canonicalHandoff.assigned_position_key);

  let limitation: V2VisibleHandoffLimitation | null = null;
  if (!sender && !receiver) limitation = "sender-and-receiver-employees-unavailable";
  else if (!sender) limitation = "sender-employee-unavailable";
  else if (!receiver) limitation = "receiver-employee-unavailable";

  let motion: V2HandoffMotionDescriptor | null = null;
  if (sender && receiver) {
    motion = buildV2HandoffMotionDescriptor({
      handoff: canonicalHandoff,
      sender: resolveV2CharacterPresentation({
        positionKey: sender.positionKey,
        title: sender.title,
        department: sender.department,
      }),
      receiver: resolveV2CharacterPresentation({
        positionKey: receiver.positionKey,
        title: receiver.title,
        department: receiver.department,
      }),
    });
    if (!motion.supported) limitation = motion.limitation;
  }

  return deepFreeze({
    kind: "visible-canonical-handoff",
    canonicalHandoff,
    sender,
    receiver,
    motion,
    semanticAnimationSupported: motion?.supported === true,
    limitation,
    truth: {
      canonicalEvent: true,
      canonicalCoverageState: input.coverageState,
      canonicalCoverageSupported: true,
      presentationOnly: true,
      canonicalStateWritable: false,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      physicalTravelClaimed: false,
      conversationClaimed: false,
      completionClaimed: false,
      latestMeansLatestSupportedEvent: true,
    },
  });
}

/**
 * Converts the already-governed Phase 2E descriptor into the sealed Phase 2O
 * renderer sequence. Reduced motion is an explicit input; canonical event time
 * never controls presentation timing.
 */
export function buildV2VisibleHandoffVisualization(
  model: V2VisibleHandoffModel,
  reducedMotion: boolean,
): V2HandoffVisualizationDescriptor | null {
  if (!model.motion) return null;
  return buildV2HandoffVisualization({
    motion: model.motion,
    reducedMotion,
    context: { mode: "live" },
  });
}
