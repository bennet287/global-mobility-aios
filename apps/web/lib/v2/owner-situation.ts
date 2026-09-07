import type { V2OwnerOrganizationData } from "./owner-organization";
import {
  buildV2CountTruth,
  deriveV2OwnerSourceCoverage,
  type V2CountTruth,
} from "./truth-state.ts";

export type V2OwnerSituationSummary = {
  readonly attentionTotal: V2CountTruth;
  readonly authorityAttentionCount: V2CountTruth;
  readonly criticalAttentionCount: V2CountTruth;
  readonly decisionAttentionCount: V2CountTruth;
  readonly humanActionAttentionCount: V2CountTruth;
  readonly blockerAttentionCount: V2CountTruth;
  readonly riskAttentionCount: V2CountTruth;
  readonly missionCount: V2CountTruth;
  readonly blockedMissionCount: V2CountTruth;
  readonly missionWithoutLinkedBlockerCount: V2CountTruth;
  readonly decisionLinkedMissionCount: V2CountTruth;
  readonly departmentCount: V2CountTruth;
  readonly rosteredEmployeeCount: V2CountTruth;
  readonly organizationActiveBlockerCount: V2CountTruth;
  readonly recentChangeCount: V2CountTruth;
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
  const coverage = deriveV2OwnerSourceCoverage(data);
  const attentionSources = ["board", "humanActions", "blockers"] as const;
  const organizationSources = ["livingOrganization"] as const;

  return Object.freeze({
    attentionTotal: buildV2CountTruth(attention.length, coverage, attentionSources),
    authorityAttentionCount: buildV2CountTruth(
      attention.filter((item) => item.urgency === "authority").length,
      coverage,
      ["board"],
    ),
    criticalAttentionCount: buildV2CountTruth(
      attention.filter((item) => item.urgency === "critical").length,
      coverage,
      attentionSources,
    ),
    decisionAttentionCount: buildV2CountTruth(
      attention.filter((item) => item.kind === "decision").length,
      coverage,
      ["board"],
    ),
    humanActionAttentionCount: buildV2CountTruth(
      attention.filter((item) => item.kind === "human_action").length,
      coverage,
      ["humanActions"],
    ),
    blockerAttentionCount: buildV2CountTruth(
      attention.filter((item) => item.kind === "blocker").length,
      coverage,
      ["blockers"],
    ),
    riskAttentionCount: buildV2CountTruth(
      attention.filter((item) => item.kind === "risk").length,
      coverage,
      ["board"],
    ),
    missionCount: buildV2CountTruth(missions.length, coverage, organizationSources),
    blockedMissionCount: buildV2CountTruth(blockedMissionCount, coverage, organizationSources),
    missionWithoutLinkedBlockerCount: buildV2CountTruth(
      missions.length - blockedMissionCount,
      coverage,
      organizationSources,
    ),
    decisionLinkedMissionCount: buildV2CountTruth(
      missions.filter((mission) => mission.decisionCount > 0).length,
      coverage,
      organizationSources,
    ),
    departmentCount: buildV2CountTruth(data.organization.departmentCount, coverage, organizationSources),
    rosteredEmployeeCount: buildV2CountTruth(data.organization.employeeRosterCount, coverage, organizationSources),
    organizationActiveBlockerCount: buildV2CountTruth(
      data.organization.zones.reduce((total, zone) => total + zone.activeBlockerCount, 0),
      coverage,
      organizationSources,
    ),
    recentChangeCount: buildV2CountTruth(data.recentChanges.length, coverage, ["activity"]),
    latestChangeAt,
    partial: data.partial,
    unavailableSourceCount: data.unavailableSources.length,
    loadedAt: data.loadedAt,
    boardGeneratedAt: data.boardGeneratedAt,
  });
}
