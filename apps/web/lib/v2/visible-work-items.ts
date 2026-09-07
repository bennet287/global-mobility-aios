/**
 * AIOS V2 — Phase 7B visible canonical WorkItem integration.
 *
 * This module adapts the deterministic Living Organization WorkItem projection
 * into read-only presentation semantics. It never changes canonical state,
 * invents WorkItem coverage, infers physical location/presence, converts
 * timestamps into progress, or reinterprets legacy lifecycle states.
 */

import type { LivingSceneEmployee, LivingSceneWorkItem } from "../live-organization.ts";

export type V2CanonicalWorkStatusKind =
  | "queued"
  | "running"
  | "blocked"
  | "awaiting-human"
  | "completed"
  | "cancelled"
  | "legacy-attention"
  | "terminal-exception"
  | "unsupported";

export type V2CanonicalWorkMotion = "current-running-cycle" | "static";

export type V2VisibleWorkAssignee = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
};

export type V2VisibleWorkItemLimitation =
  | "assignee-unavailable"
  | "assignee-ambiguous"
  | "parent-work-item-unavailable"
  | "unsupported-status";

export type V2VisibleWorkItem = {
  readonly canonicalWorkItem: LivingSceneWorkItem;
  readonly root: boolean;
  readonly assignee: V2VisibleWorkAssignee | null;
  readonly statusKind: V2CanonicalWorkStatusKind;
  readonly statusLabel: string;
  readonly motion: V2CanonicalWorkMotion;
  readonly limitations: readonly V2VisibleWorkItemLimitation[];
  readonly truth: Readonly<{
    canonicalRecord: true;
    presentationOnly: true;
    canonicalStateWritable: false;
    physicalPresenceClaimed: false;
    physicalLocationClaimed: false;
    locomotionClaimed: false;
    elapsedProgressClaimed: false;
    blockerCauseInferred: false;
    completionClaimed: boolean;
  }>;
};

export type V2VisibleWorkCollectionLimitation =
  | "canonical-projection-unavailable"
  | "root-work-item-unavailable"
  | "duplicate-work-item-identity"
  | "malformed-work-item";

export type V2VisibleWorkCollection = {
  readonly kind: "visible-canonical-work-items";
  readonly supported: boolean;
  readonly rootWorkItemId: string | null;
  readonly items: readonly V2VisibleWorkItem[];
  readonly limitation: V2VisibleWorkCollectionLimitation | null;
  readonly truth: Readonly<{
    canonicalProjection: boolean;
    canonicalSource: "LivingSceneDeterministicPlane.work_items";
    presentationOnly: true;
    canonicalStateWritable: false;
    sceneMutationsAllowed: boolean;
    physicalPresenceClaimed: false;
    physicalLocationClaimed: false;
    physicalTravelClaimed: false;
    statusClaimsAreExact: true;
    workCoverageInvented: false;
  }>;
};

export type BuildV2VisibleWorkCollectionInput = {
  readonly workItems: readonly LivingSceneWorkItem[];
  readonly employees: readonly LivingSceneEmployee[];
  readonly rootWorkItemId: string | null;
  readonly canonicalProjection: boolean;
  readonly sceneMutationsAllowed: boolean;
};

type StatusPresentation = Readonly<{
  kind: V2CanonicalWorkStatusKind;
  label: string;
  motion: V2CanonicalWorkMotion;
}>;

const LEGACY_ATTENTION_STATES = new Set([
  "held",
  "retry_wait",
  "pending_ceo",
  "pending_board",
]);

const TERMINAL_EXCEPTION_STATES = new Set([
  "failed",
  "rejected",
  "returned",
]);

function deepFreeze<T>(value: T): T {
  if (value === null || typeof value !== "object" || Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const key of Reflect.ownKeys(value as object)) {
    deepFreeze((value as Record<PropertyKey, unknown>)[key]);
  }
  return value;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isOptionalString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isCompleteCanonicalWorkItem(value: LivingSceneWorkItem): boolean {
  return Boolean(
    isNonEmptyString(value.work_item_id) &&
      (value.parent_work_item_id === null || isNonEmptyString(value.parent_work_item_id)) &&
      isNonEmptyString(value.title) &&
      isOptionalString(value.objective_key) &&
      isOptionalString(value.phase_key) &&
      isNonEmptyString(value.status) &&
      isNonEmptyString(value.priority) &&
      isNonEmptyString(value.risk_level) &&
      isNonEmptyString(value.assigned_position_key) &&
      isNonEmptyString(value.department) &&
      isNonEmptyString(value.authority_level) &&
      isNonEmptyString(value.created_at) &&
      isNonEmptyString(value.updated_at) &&
      isOptionalString(value.due_at) &&
      isOptionalString(value.completed_at) &&
      (value.elapsed_seconds === null ||
        (typeof value.elapsed_seconds === "number" &&
          Number.isFinite(value.elapsed_seconds) &&
          value.elapsed_seconds >= 0)) &&
      typeof value.overdue === "boolean" &&
      (value.specialist_evidence_valid === null ||
        typeof value.specialist_evidence_valid === "boolean") &&
      isOptionalString(value.specialist_evidence_reason),
  );
}

function copyWorkItem(workItem: LivingSceneWorkItem): LivingSceneWorkItem {
  return deepFreeze({
    work_item_id: workItem.work_item_id,
    parent_work_item_id: workItem.parent_work_item_id,
    title: workItem.title,
    objective_key: workItem.objective_key,
    phase_key: workItem.phase_key,
    status: workItem.status,
    priority: workItem.priority,
    risk_level: workItem.risk_level,
    assigned_position_key: workItem.assigned_position_key,
    department: workItem.department,
    authority_level: workItem.authority_level,
    created_at: workItem.created_at,
    updated_at: workItem.updated_at,
    due_at: workItem.due_at,
    completed_at: workItem.completed_at,
    elapsed_seconds: workItem.elapsed_seconds,
    overdue: workItem.overdue,
    specialist_evidence_valid: workItem.specialist_evidence_valid,
    specialist_evidence_reason: workItem.specialist_evidence_reason,
  });
}

function readableRawStatus(status: string): string {
  return status
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function resolveV2CanonicalWorkStatus(status: string): StatusPresentation {
  switch (status) {
    case "queued":
      return deepFreeze({ kind: "queued", label: "Queued", motion: "static" });
    case "running":
      return deepFreeze({
        kind: "running",
        label: "Running",
        motion: "current-running-cycle",
      });
    case "blocked":
      return deepFreeze({ kind: "blocked", label: "Blocked", motion: "static" });
    case "awaiting_human":
      return deepFreeze({
        kind: "awaiting-human",
        label: "Awaiting human",
        motion: "static",
      });
    case "completed":
      return deepFreeze({ kind: "completed", label: "Completed", motion: "static" });
    case "cancelled":
      return deepFreeze({ kind: "cancelled", label: "Cancelled", motion: "static" });
    default:
      if (LEGACY_ATTENTION_STATES.has(status)) {
        return deepFreeze({
          kind: "legacy-attention",
          label: readableRawStatus(status),
          motion: "static",
        });
      }
      if (TERMINAL_EXCEPTION_STATES.has(status)) {
        return deepFreeze({
          kind: "terminal-exception",
          label: readableRawStatus(status),
          motion: "static",
        });
      }
      return deepFreeze({
        kind: "unsupported",
        label: readableRawStatus(status) || status,
        motion: "static",
      });
  }
}

function resolveAssignee(
  employees: readonly LivingSceneEmployee[],
  positionKey: string,
): Readonly<{
  assignee: V2VisibleWorkAssignee | null;
  limitation: V2VisibleWorkItemLimitation | null;
}> {
  const matches = employees.filter((employee) => employee.position_key === positionKey);
  if (matches.length === 0) {
    return deepFreeze({ assignee: null, limitation: "assignee-unavailable" });
  }

  const identities = new Map<string, LivingSceneEmployee>();
  for (const employee of matches) {
    const identityKey = `${employee.title}\u0000${employee.department}`;
    identities.set(identityKey, employee);
  }
  if (identities.size !== 1) {
    return deepFreeze({ assignee: null, limitation: "assignee-ambiguous" });
  }

  const employee = identities.values().next().value as LivingSceneEmployee;
  return deepFreeze({
    assignee: {
      positionKey: employee.position_key,
      title: employee.title,
      department: employee.department,
    },
    limitation: null,
  });
}

function unsupportedCollection(
  input: BuildV2VisibleWorkCollectionInput,
  limitation: V2VisibleWorkCollectionLimitation,
): V2VisibleWorkCollection {
  return deepFreeze({
    kind: "visible-canonical-work-items",
    supported: false,
    rootWorkItemId: input.rootWorkItemId,
    items: [],
    limitation,
    truth: {
      canonicalProjection: input.canonicalProjection,
      canonicalSource: "LivingSceneDeterministicPlane.work_items",
      presentationOnly: true,
      canonicalStateWritable: false,
      sceneMutationsAllowed: input.sceneMutationsAllowed,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      physicalTravelClaimed: false,
      statusClaimsAreExact: true,
      workCoverageInvented: false,
    },
  });
}

/**
 * Build the WorkItem presentation from the deterministic scene projection.
 *
 * There is intentionally no WorkItem coverage-state argument: LivingSceneCoverage
 * does not define one. An established canonical deterministic plane is the source
 * contract for this slice. Duplicate/malformed WorkItem identity fails the entire
 * presentation closed rather than presenting a partially trustworthy topology.
 */
export function buildV2VisibleWorkCollection(
  input: BuildV2VisibleWorkCollectionInput,
): V2VisibleWorkCollection {
  if (!input.canonicalProjection) {
    return unsupportedCollection(input, "canonical-projection-unavailable");
  }
  if (!isNonEmptyString(input.rootWorkItemId)) {
    return unsupportedCollection(input, "root-work-item-unavailable");
  }

  const workById = new Map<string, LivingSceneWorkItem>();
  for (const candidate of input.workItems) {
    if (!isCompleteCanonicalWorkItem(candidate)) {
      return unsupportedCollection(input, "malformed-work-item");
    }
    if (workById.has(candidate.work_item_id)) {
      return unsupportedCollection(input, "duplicate-work-item-identity");
    }
    workById.set(candidate.work_item_id, candidate);
  }
  if (!workById.has(input.rootWorkItemId)) {
    return unsupportedCollection(input, "root-work-item-unavailable");
  }

  const items = [...input.workItems]
    .sort((left, right) => {
      if (left.work_item_id === input.rootWorkItemId) return -1;
      if (right.work_item_id === input.rootWorkItemId) return 1;
      if (left.created_at !== right.created_at) {
        return left.created_at.localeCompare(right.created_at);
      }
      return left.work_item_id.localeCompare(right.work_item_id);
    })
    .map((candidate): V2VisibleWorkItem => {
      const canonicalWorkItem = copyWorkItem(candidate);
      const status = resolveV2CanonicalWorkStatus(canonicalWorkItem.status);
      const assigneeResolution = resolveAssignee(
        input.employees,
        canonicalWorkItem.assigned_position_key,
      );
      const limitations: V2VisibleWorkItemLimitation[] = [];
      if (assigneeResolution.limitation) limitations.push(assigneeResolution.limitation);
      if (
        canonicalWorkItem.parent_work_item_id !== null &&
        !workById.has(canonicalWorkItem.parent_work_item_id)
      ) {
        limitations.push("parent-work-item-unavailable");
      }
      if (status.kind === "unsupported") limitations.push("unsupported-status");

      return deepFreeze({
        canonicalWorkItem,
        root: canonicalWorkItem.work_item_id === input.rootWorkItemId,
        assignee: assigneeResolution.assignee,
        statusKind: status.kind,
        statusLabel: status.label,
        motion: status.motion,
        limitations,
        truth: {
          canonicalRecord: true,
          presentationOnly: true,
          canonicalStateWritable: false,
          physicalPresenceClaimed: false,
          physicalLocationClaimed: false,
          locomotionClaimed: false,
          elapsedProgressClaimed: false,
          blockerCauseInferred: false,
          completionClaimed: canonicalWorkItem.status === "completed",
        },
      });
    });

  return deepFreeze({
    kind: "visible-canonical-work-items",
    supported: true,
    rootWorkItemId: input.rootWorkItemId,
    items,
    limitation: null,
    truth: {
      canonicalProjection: true,
      canonicalSource: "LivingSceneDeterministicPlane.work_items",
      presentationOnly: true,
      canonicalStateWritable: false,
      sceneMutationsAllowed: input.sceneMutationsAllowed,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      physicalTravelClaimed: false,
      statusClaimsAreExact: true,
      workCoverageInvented: false,
    },
  });
}
