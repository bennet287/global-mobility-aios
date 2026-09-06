import type { LivingOrganizationScene, LivingOrganizationSceneLatest, LivingSceneMission } from "../live-organization";

/** Q5 read model: exact-key joins over one governed snapshot. No mutation authority. */
export function missionDestination(missionKey: string) {
  return `/cockpit/v2/missions?mission=${encodeURIComponent(missionKey)}`;
}

export function missionCoverageUnavailable(scene: LivingOrganizationScene) {
  return !scene.coverage?.missions || /unavailable|unsupported|not_established/i.test(scene.coverage.missions);
}

export function validateMissionScene(latest: LivingOrganizationSceneLatest): LivingOrganizationScene | null {
  if (latest.established === false && latest.scene === null) return null;
  const scene = latest.scene;
  if (!latest.established || !scene || scene.truth?.scene_mutations_allowed !== false || scene.truth.scene_authoritative !== false || scene.truth.renderer_authoritative !== false || scene.deterministic?.authoritative !== false || scene.deterministic.canonical_projection !== true) {
    throw new Error("The Mission source did not provide a supported read-only projection.");
  }
  for (const key of ["missions", "employees", "work_items", "blockers", "decisions", "handoffs", "conversations", "human_actions", "relationships"] as const) {
    if (!Array.isArray(scene.deterministic[key])) throw new Error(`The Mission source omitted ${key}.`);
  }
  const keys = scene.deterministic.missions.map((mission) => mission.mission_key);
  if (keys.some((key) => typeof key !== "string" || !key) || new Set(keys).size !== keys.length) throw new Error("The Mission source returned ambiguous Mission identities.");
  return scene;
}

export function filterMissions(missions: readonly LivingSceneMission[], query: string, state: string) {
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return missions.filter((item) => (!state || item.state === state) && words.every((word) => `${item.title} ${item.mission_key} ${item.objective_key}`.toLowerCase().includes(word)))
    .slice().sort((a, b) => a.title < b.title ? -1 : a.title > b.title ? 1 : a.mission_key < b.mission_key ? -1 : a.mission_key > b.mission_key ? 1 : 0);
}

export function selectMission(scene: LivingOrganizationScene, missionKey: string) {
  const plane = scene.deterministic;
  const mission = plane.missions.find((item) => item.mission_key === missionKey);
  if (!mission) return null;
  const workIds = new Set(mission.work_item_ids);
  const participantKeys = new Set(mission.participant_position_keys);
  const workItems = plane.work_items.filter((item) => workIds.has(item.work_item_id));
  const participants = plane.employees.filter((item) => participantKeys.has(item.position_key));
  const blockers = plane.blockers.filter((item) => item.work_item_id !== null && workIds.has(item.work_item_id));
  const decisions = plane.decisions.filter((item) => item.work_item_id !== null && workIds.has(item.work_item_id));
  const conversations = plane.conversations.filter((item) => workIds.has(item.work_item_id));
  const handoffs = plane.handoffs.filter((item) => workIds.has(item.work_item_id));
  const humanRequests = plane.human_actions.filter((item) => item.work_item_id !== null && workIds.has(item.work_item_id));
  const missingWorkIds = [...workIds].filter((id) => !workItems.some((item) => item.work_item_id === id));
  const missingParticipantKeys = [...participantKeys].filter((key) => !participants.some((item) => item.position_key === key));
  const relationships = plane.relationships.filter((item) => (item.source_type === "work_item" && workIds.has(item.source_id)) || (item.target_type === "work_item" && workIds.has(item.target_id)));
  const unavailable = ["missions", "blockers", "conversations", "handoffs", "human_actions"].filter((key) => {
    const value = scene.coverage?.[key as keyof typeof scene.coverage];
    return !value || /unavailable|unsupported|not_established/i.test(value);
  });
  if (missingWorkIds.length) unavailable.push("linked work items");
  if (missingParticipantKeys.length) unavailable.push("linked participants");
  if (blockers.length < mission.blocker_count) unavailable.push("complete blocker detail");
  if (decisions.length < mission.decision_count) unavailable.push("complete decision detail");
  return { mission, participants, workItems, blockers, decisions, conversations, handoffs, humanRequests, relationships, missingWorkIds, missingParticipantKeys, unavailable };
}

export type V2MissionDetail = NonNullable<ReturnType<typeof selectMission>>;
