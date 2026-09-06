import type { V2MissionSummary, V2OwnerOrganizationData } from "./owner-organization";

export type V2MissionPortfolio = {
  readonly missions: readonly V2MissionSummary[];
  readonly returnedMissionCount: number;
  readonly missionsWithBlockers: number;
  readonly missionsWithDecisions: number;
  readonly rosteredParticipants: number;
};

export function buildV2MissionPortfolio(data: V2OwnerOrganizationData): V2MissionPortfolio {
  const missions = data.organization.missions;
  return {
    missions,
    returnedMissionCount: missions.length,
    missionsWithBlockers: missions.filter((mission) => mission.blockerCount > 0).length,
    missionsWithDecisions: missions.filter((mission) => mission.decisionCount > 0).length,
    rosteredParticipants: missions.reduce((total, mission) => total + mission.participantCount, 0),
  };
}

export function missionSourceUnavailable(data: V2OwnerOrganizationData): boolean {
  return data.unavailableSources.includes("Living Organization scene");
}

export function filterMissionSummaries(
  missions: readonly V2MissionSummary[],
  query: string,
  state: string,
): V2MissionSummary[] {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return missions.filter((mission) => {
    if (state && mission.state !== state) return false;
    const text = `${mission.title} ${mission.missionKey} ${mission.state} ${mission.phaseKey ?? ""}`.toLocaleLowerCase();
    return words.every((word) => text.includes(word));
  });
}

export function selectMissionSummary(
  missions: readonly V2MissionSummary[],
  missionKey: string | null,
): V2MissionSummary | null {
  if (!missionKey) return null;
  return missions.find((mission) => mission.missionKey === missionKey) ?? null;
}

export function missionDestination(missionKey: string): string {
  return `/cockpit/v2/missions?mission=${encodeURIComponent(missionKey)}`;
}
