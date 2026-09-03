import {
  type BoardPacketSnapshot,
  type ExecutiveDecision,
  type OrganizationActivity,
  type OrganizationBlocker,
  type OrganizationHumanActionRequest,
  getBoardPacket,
  listOrganizationActivities,
  listOrganizationBlockers,
  listOrganizationHumanActionRequests,
} from "../api";
import {
  type LivingOrganizationScene,
  type LivingOrganizationSceneLatest,
  type LivingSceneDepartment,
  type LivingSceneMission,
  getLatestAustriaLivingScene,
} from "../live-organization";

const ACTIVE_HUMAN_REQUEST_STATUSES = new Set(["required", "acknowledged", "in_progress"]);
const ACTIVE_BLOCKER_STATUSES = new Set(["open"]);
const OPEN_RISK_STATUSES = new Set(["open", "active", "escalated"]);

export type V2AttentionKind = "decision" | "human_action" | "blocker" | "risk";
export type V2AttentionUrgency = "authority" | "critical" | "high" | "normal";

export type V2AttentionItem = {
  id: string;
  kind: V2AttentionKind;
  title: string;
  detail: string;
  urgency: V2AttentionUrgency;
  href: string;
  occurredAt: string | null;
  canonicalBasis: string;
};

export type V2MissionSummary = {
  missionKey: string;
  title: string;
  state: string;
  phaseKey: string | null;
  participantCount: number;
  blockerCount: number;
  decisionCount: number;
  rootWorkItemId: string;
  canonicalBasis: string;
};

export type V2RecentChange = {
  id: string;
  title: string;
  summary: string;
  occurredAt: string;
  activityClass: string;
  department: string | null;
  positionKey: string | null;
};

export type V2ArchitectureWingKey =
  | "executive"
  | "regulatory"
  | "technology"
  | "operations"
  | "atrium";

export type V2ArchitectureZone = {
  wingKey: V2ArchitectureWingKey;
  label: string;
  departments: Array<{
    key: string;
    label: string;
    employeeRosterCount: number;
    workItemCount: number;
    activeBlockerCount: number;
    canonicalBasis: string;
  }>;
  employeeRosterCount: number;
  workItemCount: number;
  activeBlockerCount: number;
};

export type V2OrganizationOverview = {
  established: boolean;
  generatedAt: string | null;
  scope: string | null;
  contractVersion: string | null;
  sceneAuthoritative: boolean;
  rendererAuthoritative: boolean;
  mutationsAllowed: boolean;
  canonicalAuthority: string | null;
  missions: V2MissionSummary[];
  zones: V2ArchitectureZone[];
  employeeRosterCount: number;
  departmentCount: number;
  missionCount: number;
  coverage: LivingOrganizationScene["coverage"] | null;
};

export type V2OwnerOrganizationData = {
  loadedAt: string;
  partial: boolean;
  unavailableSources: string[];
  attention: V2AttentionItem[];
  missions: V2MissionSummary[];
  recentChanges: V2RecentChange[];
  organization: V2OrganizationOverview;
  boardGeneratedAt: string | null;
};

function urgencyRank(urgency: V2AttentionUrgency): number {
  if (urgency === "authority") return 4;
  if (urgency === "critical") return 3;
  if (urgency === "high") return 2;
  return 1;
}

function decisionAttention(decision: ExecutiveDecision): V2AttentionItem {
  return {
    id: "decision:" + decision.id,
    kind: "decision",
    title: decision.title,
    detail: decision.decision_owner_position + " authority · " + decision.status,
    urgency: "authority",
    href: "/board-room",
    occurredAt: decision.updated_at || decision.created_at,
    canonicalBasis: "ExecutiveDecision:" + decision.id,
  };
}

function humanActionAttention(request: OrganizationHumanActionRequest): V2AttentionItem {
  const priority = request.priority.toLowerCase();
  const urgency: V2AttentionUrgency =
    priority === "critical" ? "critical" : priority === "high" ? "high" : "normal";
  return {
    id: "human_action:" + request.id,
    kind: "human_action",
    title: request.title,
    detail: request.required_role + " · " + request.status,
    urgency,
    href: "/owner-inbox",
    occurredAt: request.updated_at || request.created_at,
    canonicalBasis: "HumanActionRequest:" + request.id,
  };
}

function blockerAttention(blocker: OrganizationBlocker): V2AttentionItem {
  const urgency: V2AttentionUrgency =
    blocker.severity === "critical" ? "critical" : blocker.severity === "high" ? "high" : "normal";
  return {
    id: "blocker:" + blocker.id,
    kind: "blocker",
    title: blocker.title,
    detail: blocker.severity + " blocker · human action required",
    urgency,
    href: "/cross-department-friction",
    occurredAt: blocker.updated_at || blocker.created_at,
    canonicalBasis: "OrganizationBlocker:" + blocker.id,
  };
}

function buildAttention(
  packet: BoardPacketSnapshot | null,
  humanRequests: OrganizationHumanActionRequest[],
  blockers: OrganizationBlocker[],
): V2AttentionItem[] {
  const items: V2AttentionItem[] = [];

  for (const decision of packet?.pending_decisions || []) {
    if (decision.is_current) items.push(decisionAttention(decision));
  }

  for (const risk of packet?.open_risks || []) {
    if (!risk.requires_board_attention || !OPEN_RISK_STATUSES.has(risk.status.toLowerCase())) continue;
    items.push({
      id: "risk:" + risk.id,
      kind: "risk",
      title: risk.title,
      detail: risk.severity + " risk · Board attention required",
      urgency: risk.severity.toLowerCase() === "critical" ? "critical" : "authority",
      href: "/board-room",
      occurredAt: risk.created_at,
      canonicalBasis: "RiskEscalation:" + risk.id,
    });
  }

  for (const request of humanRequests) {
    if (ACTIVE_HUMAN_REQUEST_STATUSES.has(request.status.toLowerCase())) {
      items.push(humanActionAttention(request));
    }
  }

  for (const blocker of blockers) {
    if (blocker.requires_human_action && ACTIVE_BLOCKER_STATUSES.has(blocker.status.toLowerCase())) {
      items.push(blockerAttention(blocker));
    }
  }

  const seen = new Set<string>();
  return items
    .sort((a, b) => {
      const urgencyDelta = urgencyRank(b.urgency) - urgencyRank(a.urgency);
      if (urgencyDelta !== 0) return urgencyDelta;
      return (b.occurredAt || "").localeCompare(a.occurredAt || "");
    })
    .filter((item) => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    })
    .slice(0, 8);
}

function missionSummary(mission: LivingSceneMission): V2MissionSummary {
  return {
    missionKey: mission.mission_key,
    title: mission.title,
    state: mission.state,
    phaseKey: mission.phase_key,
    participantCount: mission.participant_position_keys.length,
    blockerCount: mission.blocker_count,
    decisionCount: mission.decision_count,
    rootWorkItemId: mission.root_work_item_id,
    canonicalBasis: mission.canonical_basis,
  };
}

function missionStateRank(state: string): number {
  const value = state.toLowerCase();
  if (value.includes("active") || value.includes("running")) return 3;
  if (value.includes("queued") || value.includes("waiting")) return 2;
  if (value.includes("complete")) return 0;
  return 1;
}

function missionSort(a: V2MissionSummary, b: V2MissionSummary): number {
  const blockerDelta = Number(b.blockerCount > 0) - Number(a.blockerCount > 0);
  if (blockerDelta !== 0) return blockerDelta;
  const stateDelta = missionStateRank(b.state) - missionStateRank(a.state);
  if (stateDelta !== 0) return stateDelta;
  return a.title.localeCompare(b.title);
}

function wingForDepartment(department: LivingSceneDepartment): V2ArchitectureWingKey {
  const value = (department.department_key + " " + department.label).toLowerCase();
  if (/(board|executive|strategy|ceo|chief)/.test(value)) return "executive";
  if (/(regulat|evidence|legal|policy|compliance|document|eligibility|visa)/.test(value)) return "regulatory";
  if (/(technology|engineering|security|platform|systems|product|technical|soc)/.test(value)) return "technology";
  if (/(operations|operation|mobility|client|case|service|delivery|recruit)/.test(value)) return "operations";
  return "atrium";
}

const WING_LABELS: Record<V2ArchitectureWingKey, string> = {
  executive: "Executive Terrace",
  regulatory: "Regulatory & Evidence",
  technology: "Technology & Security",
  operations: "Operations Studio",
  atrium: "Central Atrium",
};

function buildArchitectureZones(departments: LivingSceneDepartment[]): V2ArchitectureZone[] {
  const order: V2ArchitectureWingKey[] = ["executive", "regulatory", "atrium", "technology", "operations"];
  const map = new Map<V2ArchitectureWingKey, V2ArchitectureZone>();

  for (const wingKey of order) {
    map.set(wingKey, {
      wingKey,
      label: WING_LABELS[wingKey],
      departments: [],
      employeeRosterCount: 0,
      workItemCount: 0,
      activeBlockerCount: 0,
    });
  }

  for (const department of departments) {
    const wingKey = wingForDepartment(department);
    const zone = map.get(wingKey)!;
    zone.departments.push({
      key: department.department_key,
      label: department.label,
      employeeRosterCount: department.employee_count,
      workItemCount: department.work_item_count,
      activeBlockerCount: department.active_blocker_count,
      canonicalBasis: department.canonical_basis,
    });
    zone.employeeRosterCount += department.employee_count;
    zone.workItemCount += department.work_item_count;
    zone.activeBlockerCount += department.active_blocker_count;
  }

  return order.map((key) => map.get(key)!);
}

function buildOrganization(sceneLatest: LivingOrganizationSceneLatest | null): V2OrganizationOverview {
  const scene = sceneLatest?.established ? sceneLatest.scene : null;
  if (!scene) {
    return {
      established: false,
      generatedAt: null,
      scope: null,
      contractVersion: null,
      sceneAuthoritative: false,
      rendererAuthoritative: false,
      mutationsAllowed: false,
      canonicalAuthority: null,
      missions: [],
      zones: buildArchitectureZones([]),
      employeeRosterCount: 0,
      departmentCount: 0,
      missionCount: 0,
      coverage: null,
    };
  }

  const missions = scene.deterministic.missions.map(missionSummary).sort(missionSort);
  const departments = scene.deterministic.departments;

  return {
    established: true,
    generatedAt: scene.generated_at,
    scope: scene.scope,
    contractVersion: scene.contract_version,
    sceneAuthoritative: scene.truth.scene_authoritative,
    rendererAuthoritative: scene.truth.renderer_authoritative,
    mutationsAllowed: scene.truth.scene_mutations_allowed,
    canonicalAuthority: scene.truth.canonical_authority,
    missions,
    zones: buildArchitectureZones(departments),
    employeeRosterCount: scene.deterministic.employees.length,
    departmentCount: departments.length,
    missionCount: missions.length,
    coverage: scene.coverage,
  };
}

function recentChange(activity: OrganizationActivity): V2RecentChange {
  return {
    id: activity.id,
    title: activity.title,
    summary: activity.summary,
    occurredAt: activity.occurred_at,
    activityClass: activity.activity_class,
    department: activity.department,
    positionKey: activity.position_key,
  };
}

export async function loadV2OwnerOrganization(): Promise<V2OwnerOrganizationData> {
  const results = await Promise.allSettled([
    getBoardPacket(),
    listOrganizationHumanActionRequests({ page_size: 50 }),
    listOrganizationBlockers({ status: "open", page_size: 50 }),
    listOrganizationActivities({ page_size: 12 }),
    getLatestAustriaLivingScene(),
  ]);

  const unavailableSources: string[] = [];

  const packet = results[0].status === "fulfilled" ? results[0].value : null;
  if (!packet) unavailableSources.push("Board packet");

  const humanRequests = results[1].status === "fulfilled" ? results[1].value.data : [];
  if (results[1].status === "rejected") unavailableSources.push("Human action requests");

  const blockers = results[2].status === "fulfilled" ? results[2].value.data : [];
  if (results[2].status === "rejected") unavailableSources.push("Blockers");

  const activities = results[3].status === "fulfilled" ? results[3].value.data : [];
  if (results[3].status === "rejected") unavailableSources.push("Activity");

  const sceneLatest = results[4].status === "fulfilled" ? results[4].value : null;
  if (results[4].status === "rejected") unavailableSources.push("Living Organization scene");

  const organization = buildOrganization(sceneLatest);

  return {
    loadedAt: new Date().toISOString(),
    partial: unavailableSources.length > 0,
    unavailableSources,
    attention: buildAttention(packet, humanRequests, blockers),
    missions: organization.missions.slice(0, 5),
    recentChanges: activities.map(recentChange).slice(0, 6),
    organization,
    boardGeneratedAt: packet?.generated_at || null,
  };
}
