import type { LivingSceneEmployee } from "../live-organization.ts";
import {
  deriveLivingEmployeePresentation,
  type LivingEmployeeMotionMode,
  type LivingEmployeePresentationState,
} from "../living-organization-employee-presentation.ts";

export type V2VisibleWorkStateKind =
  | "working"
  | "blocked"
  | "awaiting_owner"
  | "queued"
  | "completed";

export type V2VisibleWorkStateTruth = {
  readonly canonicalStateSource: "LivingSceneEmployee.semantic_state";
  readonly canonicalSemanticStateEchoed: true;
  readonly canonicalPresenceStateEchoed: true;
  readonly workItemRelationPresent: boolean;
  readonly presentationOnly: true;
  readonly canonicalStateWritable: false;
  readonly physicalPresenceClaimed: false;
  readonly physicalLocationClaimed: false;
  readonly physicalTravelClaimed: false;
  readonly locomotionAllowed: false;
  readonly conversationClaimed: false;
  readonly collaborationClaimed: false;
  readonly handoffClaimed: false;
  readonly blockerDetailsClaimed: false;
  readonly blockerResolutionClaimed: false;
  readonly completionEventClaimed: false;
};

export type V2VisibleWorkStateModel = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
  readonly workItemId: string | null;
  readonly canonicalSemanticState: string;
  readonly canonicalPresenceState: string;
  readonly stateReason: string;
  readonly supported: boolean;
  readonly kind: V2VisibleWorkStateKind | null;
  readonly presentationState: LivingEmployeePresentationState;
  readonly motion: LivingEmployeeMotionMode;
  readonly label: string;
  readonly shortLabel: string;
  readonly reducedMotionMode: "static-posture-and-label";
  readonly truth: V2VisibleWorkStateTruth;
};

const STATE_META: Readonly<
  Record<V2VisibleWorkStateKind, { readonly label: string; readonly shortLabel: string }>
> = Object.freeze({
  working: Object.freeze({ label: "Working", shortLabel: "WORK" }),
  blocked: Object.freeze({ label: "Blocked", shortLabel: "BLOCKED" }),
  awaiting_owner: Object.freeze({ label: "Awaiting Owner", shortLabel: "OWNER" }),
  queued: Object.freeze({ label: "Queued", shortLabel: "QUEUED" }),
  completed: Object.freeze({ label: "Completed state", shortLabel: "DONE" }),
});

function canonicalKind(value: string): V2VisibleWorkStateKind | null {
  return Object.hasOwn(STATE_META, value)
    ? (value as V2VisibleWorkStateKind)
    : null;
}

function nonEmpty(value: string | null | undefined): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === "object") {
    for (const key of Object.getOwnPropertyNames(value as object)) {
      deepFreeze((value as Record<string, unknown>)[key]);
    }
    Object.freeze(value);
  }
  return value;
}

/**
 * Translate the already-canonical employee semantic state into the V2 character
 * presentation contract. This function does not infer work, blockers, presence,
 * completion events or movement from visual metadata.
 */
export function buildV2VisibleWorkState(
  employee: LivingSceneEmployee,
): V2VisibleWorkStateModel {
  const positionKey = nonEmpty(employee?.position_key) ?? "";
  const semanticState = nonEmpty(employee?.semantic_state) ?? "unknown";
  const presenceState = nonEmpty(employee?.presence_state) ?? "not_asserted";
  const workItemId = nonEmpty(employee?.work_item_id);
  const kind = canonicalKind(semanticState);
  const basePresentation = deriveLivingEmployeePresentation({
    semantic_state: semanticState,
    presence_state: presenceState,
  });
  const supported = positionKey.length > 0 && kind !== null;
  const meta = kind === null ? null : STATE_META[kind];

  return deepFreeze({
    positionKey,
    title: nonEmpty(employee?.title) ?? positionKey,
    department: nonEmpty(employee?.department) ?? "Department unavailable",
    workItemId,
    canonicalSemanticState: semanticState,
    canonicalPresenceState: presenceState,
    stateReason: nonEmpty(employee?.state_reason) ?? "Canonical employee semantic state",
    supported,
    kind,
    presentationState: basePresentation.state,
    motion: supported ? basePresentation.motion : "none",
    label: meta?.label ?? "Unsupported state",
    shortLabel: meta?.shortLabel ?? "STATIC",
    reducedMotionMode: "static-posture-and-label",
    truth: {
      canonicalStateSource: "LivingSceneEmployee.semantic_state",
      canonicalSemanticStateEchoed: true,
      canonicalPresenceStateEchoed: true,
      workItemRelationPresent: workItemId !== null,
      presentationOnly: true,
      canonicalStateWritable: false,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      physicalTravelClaimed: false,
      locomotionAllowed: false,
      conversationClaimed: false,
      collaborationClaimed: false,
      handoffClaimed: false,
      blockerDetailsClaimed: false,
      blockerResolutionClaimed: false,
      completionEventClaimed: false,
    },
  });
}

export function buildV2VisibleWorkStates(
  employees: readonly LivingSceneEmployee[],
): readonly V2VisibleWorkStateModel[] {
  return Object.freeze(
    [...employees]
      .sort((a, b) => a.position_key.localeCompare(b.position_key))
      .map(buildV2VisibleWorkState),
  );
}

export function findV2VisibleWorkState(
  models: readonly V2VisibleWorkStateModel[],
  positionKey: string,
): V2VisibleWorkStateModel | null {
  return models.find((model) => model.positionKey === positionKey) ?? null;
}
