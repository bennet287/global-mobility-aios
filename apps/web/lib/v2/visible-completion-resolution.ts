import type { LivingSceneBlocker, LivingSceneDecision, LivingSceneWorkItem } from "../live-organization";

export const V2_EXPLICIT_COMPLETION_RESOLUTION_CONTRACT =
  "canonical_completion_resolution_evidence_v1" as const;

export type V2BlockerTransitionEvidence = LivingSceneBlocker & {
  resolved_at?: string | null;
  resolution_summary?: string | null;
  resolving_actor_type?: string | null;
  resolving_actor_id?: string | null;
  waived_at?: string | null;
  waived_by_human_id?: string | null;
  waiver_reason?: string | null;
};

export type V2VisibleWorkCompletion = {
  kind: "work_completed";
  workItemId: string;
  title: string;
  assignedPositionKey: string;
  completedAt: string;
  canonicalBasis: "OrganizationalWorkItem.status+completed_at";
};

export type V2VisibleBlockerResolution = {
  kind: "blocker_resolved" | "blocker_waived";
  blockerId: string;
  workItemId: string | null;
  title: string;
  occurredAt: string;
  outcomeSummary: string;
  resolverLabel: string;
  canonicalBasis: "OrganizationBlocker canonical transition fields";
};

export type V2VisibleDecisionOutcome = {
  kind: "decision_outcome";
  decisionId: string;
  workItemId: string | null;
  title: string;
  status: "approved" | "rejected";
  decidedAt: string;
  canonicalBasis: "ExecutiveDecision.status+decided_at";
};

export type V2VisibleCompletionResolution =
  | V2VisibleWorkCompletion
  | V2VisibleBlockerResolution
  | V2VisibleDecisionOutcome;

function isCanonicalTimestamp(value: string | null | undefined): value is string {
  if (!value || !value.trim()) return false;
  return Number.isFinite(Date.parse(value));
}

function nonEmpty(value: string | null | undefined): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function eventTime(item: V2VisibleCompletionResolution): string {
  if (item.kind === "work_completed") return item.completedAt;
  if (item.kind === "decision_outcome") return item.decidedAt;
  return item.occurredAt;
}

export function buildV2VisibleWorkCompletions(
  workItems: readonly LivingSceneWorkItem[],
): V2VisibleWorkCompletion[] {
  return workItems.flatMap((workItem): V2VisibleWorkCompletion[] => {
    if (workItem.status !== "completed" || !isCanonicalTimestamp(workItem.completed_at)) {
      return [];
    }
    return [{
      kind: "work_completed",
      workItemId: workItem.work_item_id,
      title: workItem.title,
      assignedPositionKey: workItem.assigned_position_key,
      completedAt: workItem.completed_at,
      canonicalBasis: "OrganizationalWorkItem.status+completed_at",
    }];
  });
}

export function buildV2VisibleBlockerResolutions(
  blockers: readonly V2BlockerTransitionEvidence[],
): V2VisibleBlockerResolution[] {
  return blockers.flatMap((blocker): V2VisibleBlockerResolution[] => {
    if (
      blocker.status === "resolved" &&
      isCanonicalTimestamp(blocker.resolved_at) &&
      nonEmpty(blocker.resolution_summary) &&
      nonEmpty(blocker.resolving_actor_type) &&
      nonEmpty(blocker.resolving_actor_id)
    ) {
      return [{
        kind: "blocker_resolved",
        blockerId: blocker.blocker_id,
        workItemId: blocker.work_item_id,
        title: blocker.title,
        occurredAt: blocker.resolved_at,
        outcomeSummary: blocker.resolution_summary.trim(),
        resolverLabel: `${blocker.resolving_actor_type.trim()}:${blocker.resolving_actor_id.trim()}`,
        canonicalBasis: "OrganizationBlocker canonical transition fields",
      }];
    }

    if (
      blocker.status === "waived" &&
      isCanonicalTimestamp(blocker.waived_at) &&
      nonEmpty(blocker.waived_by_human_id) &&
      nonEmpty(blocker.waiver_reason)
    ) {
      return [{
        kind: "blocker_waived",
        blockerId: blocker.blocker_id,
        workItemId: blocker.work_item_id,
        title: blocker.title,
        occurredAt: blocker.waived_at,
        outcomeSummary: blocker.waiver_reason.trim(),
        resolverLabel: `human:${blocker.waived_by_human_id.trim()}`,
        canonicalBasis: "OrganizationBlocker canonical transition fields",
      }];
    }

    return [];
  });
}

export function buildV2VisibleDecisionOutcomes(
  decisions: readonly LivingSceneDecision[],
): V2VisibleDecisionOutcome[] {
  return decisions.flatMap((decision): V2VisibleDecisionOutcome[] => {
    if (
      (decision.status !== "approved" && decision.status !== "rejected") ||
      !isCanonicalTimestamp(decision.decided_at)
    ) {
      return [];
    }
    return [{
      kind: "decision_outcome",
      decisionId: decision.decision_id,
      workItemId: decision.work_item_id,
      title: decision.title,
      status: decision.status,
      decidedAt: decision.decided_at,
      canonicalBasis: "ExecutiveDecision.status+decided_at",
    }];
  });
}

export function buildV2VisibleCompletionResolution(input: {
  workItems: readonly LivingSceneWorkItem[];
  blockers: readonly V2BlockerTransitionEvidence[];
  decisions: readonly LivingSceneDecision[];
}): V2VisibleCompletionResolution[] {
  return [
    ...buildV2VisibleWorkCompletions(input.workItems),
    ...buildV2VisibleBlockerResolutions(input.blockers),
    ...buildV2VisibleDecisionOutcomes(input.decisions),
  ].sort((left, right) => {
    const byTime = Date.parse(eventTime(right)) - Date.parse(eventTime(left));
    if (byTime !== 0) return byTime;
    const leftKey = left.kind === "work_completed"
      ? `work:${left.workItemId}`
      : left.kind === "decision_outcome"
        ? `decision:${left.decisionId}`
        : `blocker:${left.blockerId}`;
    const rightKey = right.kind === "work_completed"
      ? `work:${right.workItemId}`
      : right.kind === "decision_outcome"
        ? `decision:${right.decisionId}`
        : `blocker:${right.blockerId}`;
    return leftKey.localeCompare(rightKey);
  });
}

export function visibleCompletionResolutionForWorkItems(
  items: readonly V2VisibleCompletionResolution[],
  workItemIds: ReadonlySet<string>,
): V2VisibleCompletionResolution[] {
  return items.filter((item) => {
    const workItemId = item.workItemId;
    return workItemId !== null && workItemIds.has(workItemId);
  });
}

export function visibleCompletionResolutionForPosition(input: {
  items: readonly V2VisibleCompletionResolution[];
  positionKey: string;
  workItemIds: ReadonlySet<string>;
}): V2VisibleCompletionResolution[] {
  return input.items.filter((item) => {
    if (item.kind === "work_completed") {
      return item.assignedPositionKey === input.positionKey;
    }
    return item.workItemId !== null && input.workItemIds.has(item.workItemId);
  });
}

export const V2_COMPLETION_RESOLUTION_TRUTH = Object.freeze({
  presentationOnly: true,
  physicalCelebrationClaimed: false,
  physicalPresenceClaimed: false,
  locomotionClaimed: false,
  canonicalMutationAllowed: false,
  inferredFromAnimation: false,
  inferredFromElapsedTime: false,
});
