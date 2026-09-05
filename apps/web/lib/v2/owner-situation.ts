import type { V2OwnerOrganizationData } from "./owner-organization";

export type V2OwnerSituationSummary = {
  readonly attentionTotal: number;
  readonly authorityAttentionCount: number;
  readonly criticalAttentionCount: number;
  readonly decisionAttentionCount: number;
  readonly humanActionAttentionCount: number;
  readonly blockerAttentionCount: number;
  readonly riskAttentionCount: number;
  readonly missionCount: number;
  readonly blockedMissionCount: number;
  readonly missionWithoutLinkedBlockerCount: number;
  readonly decisionLinkedMissionCount: number;
  readonly departmentCount: number;
  readonly rosteredEmployeeCount: number;
  readonly organizationActiveBlockerCount: number;
  readonly recentChangeCount: number;
  readonly latestChangeAt: string | null;
  readonly partial: boolean;
  readonly unavailableSourceCount: number;
  readonly loadedAt: string;
  readonly boardGeneratedAt: string | null;
};

export function buildV2OwnerSituationSummary(
  data: V2OwnerOrganizationData,
): V2OwnerSituationSummary {
  const attention = data.attention;
  const missions = data.missions;
  const blockedMissionCount = missions.filter((mission) => mission.blockerCount > 0).length;
  const latestChangeAt = data.recentChanges.reduce<string | null>((latest, change) => {
    if (!latest || change.occurredAt > latest) return change.occurredAt;
    return latest;
  }, null);

  return Object.freeze({
    attentionTotal: attention.length,
    authorityAttentionCount: attention.filter((item) => item.urgency === "authority").length,
    criticalAttentionCount: attention.filter((item) => item.urgency === "critical").length,
    decisionAttentionCount: attention.filter((item) => item.kind === "decision").length,
    humanActionAttentionCount: attention.filter((item) => item.kind === "human_action").length,
    blockerAttentionCount: attention.filter((item) => item.kind === "blocker").length,
    riskAttentionCount: attention.filter((item) => item.kind === "risk").length,
    missionCount: missions.length,
    blockedMissionCount,
    missionWithoutLinkedBlockerCount: missions.length - blockedMissionCount,
    decisionLinkedMissionCount: missions.filter((mission) => mission.decisionCount > 0).length,
    departmentCount: data.organization.departmentCount,
    rosteredEmployeeCount: data.organization.employeeRosterCount,
    organizationActiveBlockerCount: data.organization.zones.reduce(
      (total, zone) => total + zone.activeBlockerCount,
      0,
    ),
    recentChangeCount: data.recentChanges.length,
    latestChangeAt,
    partial: data.partial,
    unavailableSourceCount: data.unavailableSources.length,
    loadedAt: data.loadedAt,
    boardGeneratedAt: data.boardGeneratedAt,
  });
}
