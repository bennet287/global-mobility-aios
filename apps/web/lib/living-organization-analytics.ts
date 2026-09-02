import type { LivingOrganizationScene } from "./live-organization";
import type { LivingOrganizationLensKey } from "./living-organization-lenses";

export type StructuredFlowNode = {
  workItemId: string;
  title: string;
  status: string;
  priority: string;
  riskLevel: string;
  assignedPositionKey: string;
  department: string;
  elapsedSeconds: number | null;
  overdue: boolean;
  blockerCount: number;
  oldestBlockerSeconds: number | null;
  handoffCount: number;
  riskEscalationCount: number;
  ownerAttentionCount: number;
  attentionSignalCount: number;
  specialistEvidenceValid: boolean | null;
  specialistEvidenceReason: string | null;
  canonicalBasis: string;
};

export type StructuredFlowEdge = {
  edgeKey: string;
  edgeType: "parent_topology";
  sourceWorkItemId: string;
  targetWorkItemId: string;
  canonicalBasis: string;
};

export type StructuredFlowHandoff = {
  activityId: string;
  workItemId: string;
  previousPositionKey: string;
  assignedPositionKey: string;
  occurredAt: string;
  canonicalBasis: string;
};

export type StructuredFlowBaseline = {
  authoritative: false;
  projectionOnly: true;
  workItemCount: number;
  activeWorkItemCount: number;
  blockedWorkItemCount: number;
  ownerAttentionWorkItemCount: number;
  overdueWorkItemCount: number;
  parentEdgeCount: number;
  handoffCount: number;
  nodes: StructuredFlowNode[];
  edges: StructuredFlowEdge[];
  handoffs: StructuredFlowHandoff[];
  canonicalBasis: string;
};

export const OWNER_ANALYTICAL_QUERIES = [
  { key: "blocked_over_20_minutes", label: "Show missions blocked >20m", lens: "blockers" },
  { key: "owner_authority", label: "Show work requiring my authority", lens: "decisions" },
  { key: "r4_r5_work", label: "Show R4/R5 work", lens: "risk" },
  { key: "overdue_work", label: "Show overdue work", lens: "flow" },
  { key: "incomplete_evidence", label: "Show incomplete evidence on Austria missions", lens: "evidence" },
  { key: "superseded_this_week", label: "Show decisions superseded this week", lens: "decisions" },
  { key: "model_cost_concentration", label: "Where is model cost concentrated?", lens: "cost" },
] as const satisfies readonly {
  key: string;
  label: string;
  lens: LivingOrganizationLensKey;
}[];

export type OwnerAnalyticalQueryKey = (typeof OWNER_ANALYTICAL_QUERIES)[number]["key"];
export type OwnerAnalyticalQueryStatus = "available" | "partial" | "unavailable";

export type OwnerAnalyticalQueryItem = {
  kind: "mission" | "work_item" | "decision";
  id: string;
  label: string;
  detail: string;
};

export type OwnerAnalyticalQueryResult = {
  key: OwnerAnalyticalQueryKey;
  label: string;
  lens: LivingOrganizationLensKey;
  status: OwnerAnalyticalQueryStatus;
  count: number | null;
  summary: string;
  items: OwnerAnalyticalQueryItem[];
  canonicalBasis: string;
  limitation: string | null;
};

const TERMINAL_WORK_STATUSES = new Set(["completed", "cancelled"]);
const OWNER_ROLES = new Set(["board", "owner", "human_owner", "human owner"]);

function ownerRole(value: string): boolean {
  return OWNER_ROLES.has(value.trim().toLowerCase());
}

function increment(map: Map<string, number>, key: string | null): void {
  if (!key) return;
  map.set(key, (map.get(key) ?? 0) + 1);
}

function resolveHumanActionWorkItemId(
  scene: LivingOrganizationScene,
  request: LivingOrganizationScene["deterministic"]["human_actions"][number],
): string | null {
  if (request.work_item_id) return request.work_item_id;
  if (request.decision_id) {
    return scene.deterministic.decisions.find((item) => item.decision_id === request.decision_id)?.work_item_id ?? null;
  }
  if (request.blocker_id) {
    return scene.deterministic.blockers.find((item) => item.blocker_id === request.blocker_id)?.work_item_id ?? null;
  }
  return null;
}

export function buildStructuredFlowBaseline(
  scene: LivingOrganizationScene,
): StructuredFlowBaseline {
  const blockerCount = new Map<string, number>();
  const oldestBlockerSeconds = new Map<string, number>();
  const handoffCount = new Map<string, number>();
  const riskCount = new Map<string, number>();
  const ownerAttentionCount = new Map<string, number>();

  for (const blocker of scene.deterministic.blockers) {
    if (!blocker.work_item_id) continue;
    increment(blockerCount, blocker.work_item_id);
    oldestBlockerSeconds.set(
      blocker.work_item_id,
      Math.max(oldestBlockerSeconds.get(blocker.work_item_id) ?? 0, blocker.open_elapsed_seconds),
    );
  }
  for (const handoff of scene.deterministic.handoffs) increment(handoffCount, handoff.work_item_id);
  for (const risk of scene.deterministic.risk_escalations) {
    increment(riskCount, risk.work_item_id);
    if (risk.requires_board_attention) increment(ownerAttentionCount, risk.work_item_id);
  }
  for (const decision of scene.deterministic.decisions) {
    if (decision.required_owner_action) increment(ownerAttentionCount, decision.work_item_id);
  }
  for (const request of scene.deterministic.human_actions) {
    if (!ownerRole(request.required_role)) continue;
    increment(ownerAttentionCount, resolveHumanActionWorkItemId(scene, request));
  }

  const nodes = scene.deterministic.work_items.map((work): StructuredFlowNode => {
    const blockers = blockerCount.get(work.work_item_id) ?? 0;
    const risks = riskCount.get(work.work_item_id) ?? 0;
    const ownerAttention = ownerAttentionCount.get(work.work_item_id) ?? 0;
    const handoffs = handoffCount.get(work.work_item_id) ?? 0;
    return {
      workItemId: work.work_item_id,
      title: work.title,
      status: work.status,
      priority: work.priority,
      riskLevel: work.risk_level,
      assignedPositionKey: work.assigned_position_key,
      department: work.department,
      elapsedSeconds: work.elapsed_seconds,
      overdue: work.overdue,
      blockerCount: blockers,
      oldestBlockerSeconds: blockers ? oldestBlockerSeconds.get(work.work_item_id) ?? 0 : null,
      handoffCount: handoffs,
      riskEscalationCount: risks,
      ownerAttentionCount: ownerAttention,
      attentionSignalCount: blockers + risks + ownerAttention,
      specialistEvidenceValid: work.specialist_evidence_valid,
      specialistEvidenceReason: work.specialist_evidence_reason,
      canonicalBasis: "OrganizationalWorkItem + linked canonical blocker/risk/decision/human-action/handoff projections + bounded K.1 specialist evidence validity",
    };
  });

  const edges = scene.deterministic.work_items
    .filter((work) => work.parent_work_item_id !== null)
    .map((work): StructuredFlowEdge => ({
      edgeKey: `parent:${work.parent_work_item_id}:${work.work_item_id}`,
      edgeType: "parent_topology",
      sourceWorkItemId: work.parent_work_item_id as string,
      targetWorkItemId: work.work_item_id,
      canonicalBasis: "OrganizationalWorkItem.parent_work_item_id; topology is not promoted to dependency truth",
    }));

  const handoffs = scene.deterministic.handoffs.map((handoff): StructuredFlowHandoff => ({
    activityId: handoff.activity_id,
    workItemId: handoff.work_item_id,
    previousPositionKey: handoff.previous_position_key,
    assignedPositionKey: handoff.assigned_position_key,
    occurredAt: handoff.occurred_at,
    canonicalBasis: handoff.canonical_basis,
  }));

  return {
    authoritative: false,
    projectionOnly: true,
    workItemCount: nodes.length,
    activeWorkItemCount: nodes.filter((node) => !TERMINAL_WORK_STATUSES.has(node.status)).length,
    blockedWorkItemCount: nodes.filter((node) => node.blockerCount > 0).length,
    ownerAttentionWorkItemCount: nodes.filter((node) => node.ownerAttentionCount > 0).length,
    overdueWorkItemCount: nodes.filter((node) => node.overdue).length,
    parentEdgeCount: edges.length,
    handoffCount: handoffs.length,
    nodes,
    edges,
    handoffs,
    canonicalBasis: "Derived read-only structured FLOW baseline over living-organization-scene.v5 canonical projections",
  };
}

function queryDescriptor(key: OwnerAnalyticalQueryKey) {
  const descriptor = OWNER_ANALYTICAL_QUERIES.find((item) => item.key === key);
  if (!descriptor) throw new Error(`Unknown Owner analytical query: ${key}`);
  return descriptor;
}

function workItems(
  scene: LivingOrganizationScene,
  ids: Set<string>,
  detail: (work: LivingOrganizationScene["deterministic"]["work_items"][number]) => string,
): OwnerAnalyticalQueryItem[] {
  return scene.deterministic.work_items
    .filter((work) => ids.has(work.work_item_id))
    .map((work) => ({
      kind: "work_item" as const,
      id: work.work_item_id,
      label: work.title,
      detail: detail(work),
    }));
}

export function evaluateOwnerAnalyticalQuery(
  scene: LivingOrganizationScene,
  key: OwnerAnalyticalQueryKey,
): OwnerAnalyticalQueryResult {
  const descriptor = queryDescriptor(key);

  if (key === "blocked_over_20_minutes") {
    const thresholdSeconds = 20 * 60;
    const blockers = scene.deterministic.blockers.filter(
      (blocker) => blocker.open_elapsed_seconds >= thresholdSeconds,
    );
    const blockedWorkIds = new Set(
      blockers.flatMap((blocker) => blocker.work_item_id ? [blocker.work_item_id] : []),
    );
    const missions = scene.deterministic.missions.filter((mission) =>
      mission.work_item_ids.some((workItemId) => blockedWorkIds.has(workItemId)),
    );
    return {
      ...descriptor,
      status: "available",
      count: missions.length,
      summary: missions.length
        ? `${missions.length} mission${missions.length === 1 ? "" : "s"} contain canonical blockers open for at least 20 minutes.`
        : "No projected mission has a canonical blocker open for at least 20 minutes.",
      items: missions.map((mission) => ({
        kind: "mission",
        id: mission.mission_key,
        label: mission.title,
        detail: `${blockers.filter((blocker) => blocker.work_item_id && mission.work_item_ids.includes(blocker.work_item_id)).length} blocker(s) over threshold`,
      })),
      canonicalBasis: "OrganizationBlocker.open_elapsed_seconds derived by the backend scene projection clock + Mission WorkItem membership",
      limitation: null,
    };
  }

  if (key === "owner_authority") {
    const ids = new Set<string>();
    for (const decision of scene.deterministic.decisions) {
      if (decision.required_owner_action && decision.work_item_id) ids.add(decision.work_item_id);
    }
    for (const request of scene.deterministic.human_actions) {
      if (!ownerRole(request.required_role)) continue;
      const workItemId = resolveHumanActionWorkItemId(scene, request);
      if (workItemId) ids.add(workItemId);
    }
    const items = workItems(
      scene,
      ids,
      (work) => `${work.authority_level} · explicit Board/Owner action record; authority is not inferred from the lens`,
    );
    return {
      ...descriptor,
      status: "available",
      count: items.length,
      summary: items.length
        ? `${items.length} WorkItem${items.length === 1 ? "" : "s"} have explicit Owner/Board action requirements.`
        : "No projected WorkItem has an explicit Owner/Board action requirement.",
      items,
      canonicalBasis: "ExecutiveDecision.required_owner_action + OrganizationHumanActionRequest.required_role",
      limitation: "Risk attention alone is not treated as Owner authority.",
    };
  }

  if (key === "r4_r5_work") {
    const ids = new Set(
      scene.deterministic.work_items
        .filter((work) => ["R4", "R5"].includes(work.risk_level.trim().toUpperCase()))
        .map((work) => work.work_item_id),
    );
    const items = workItems(scene, ids, (work) => `Canonical risk_level ${work.risk_level}`);
    return {
      ...descriptor,
      status: "available",
      count: items.length,
      summary: items.length
        ? `${items.length} WorkItem${items.length === 1 ? "" : "s"} match canonical R4/R5 risk levels.`
        : "No projected WorkItem has canonical risk_level R4 or R5.",
      items,
      canonicalBasis: "Exact OrganizationalWorkItem.risk_level match only",
      limitation: "High/critical labels are not silently remapped to R4/R5.",
    };
  }

  if (key === "overdue_work") {
    const ids = new Set(
      scene.deterministic.work_items.filter((work) => work.overdue).map((work) => work.work_item_id),
    );
    const items = workItems(scene, ids, (work) => `Due ${work.due_at ?? "not recorded"} · ${work.status}`);
    return {
      ...descriptor,
      status: "available",
      count: items.length,
      summary: items.length
        ? `${items.length} WorkItem${items.length === 1 ? "" : "s"} are overdue at the scene projection clock.`
        : "No projected WorkItem is overdue at the scene projection clock.",
      items,
      canonicalBasis: "Backend-derived WorkItem.overdue against LivingOrganizationScene.generated_at",
      limitation: null,
    };
  }

  if (key === "incomplete_evidence") {
    const gaps = scene.deterministic.work_items.filter(
      (work) => work.specialist_evidence_valid === false,
    );
    return {
      ...descriptor,
      status: "partial",
      count: gaps.length,
      summary: gaps.length
        ? `${gaps.length} specialist WorkItem${gaps.length === 1 ? "" : "s"} have a persisted K.1 evidence-validity gap.`
        : "No K.1 specialist evidence-validity gap is projected; full mission evidence completeness is not asserted.",
      items: gaps.map((work) => ({
        kind: "work_item",
        id: work.work_item_id,
        label: work.title,
        detail: work.specialist_evidence_reason ?? "Specialist evidence validity is false without a recorded reason.",
      })),
      canonicalBasis: "AustriaLiveSpecialistSnapshot.evidence_valid/evidence_reason projected onto its exact specialist WorkItem",
      limitation: "This covers K.1 specialist execution evidence only; aggregate Evidence/VerifiedRule/SourceSnapshot counts are not promoted to full mission completeness.",
    };
  }

  if (key === "superseded_this_week") {
    const decisions = scene.deterministic.decisions.filter(
      (decision) => decision.superseded_in_projection_week,
    );
    return {
      ...descriptor,
      status: "available",
      count: decisions.length,
      summary: decisions.length
        ? `${decisions.length} decision${decisions.length === 1 ? "" : "s"} were superseded in the UTC week containing the scene projection clock.`
        : "No projected decision was superseded in the UTC week containing the scene projection clock.",
      items: decisions.map((decision) => ({
        kind: "decision",
        id: decision.decision_id,
        label: decision.title,
        detail: `Successor ${decision.superseded_by_decision_id ?? "unknown"} created ${decision.superseded_by_created_at ?? "timestamp unavailable"}`,
      })),
      canonicalBasis: "Backend-derived ExecutiveDecision.superseded_in_projection_week using successor record created_at against LivingOrganizationScene.generated_at",
      limitation: "The bounded timestamp is successor decision creation; complete historical replay across scene gaps remains M.8.",
    };
  }

  return {
    ...descriptor,
    status: "unavailable",
    count: null,
    summary: "Canonical organization cost concentration is unavailable.",
    items: [],
    canonicalBasis: scene.coverage.runtime_costs,
    limitation: "Specialist runtime estimates remain telemetry and are not promoted to an organization cost ledger.",
  };
}
