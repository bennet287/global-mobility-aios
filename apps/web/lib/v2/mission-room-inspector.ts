import type {
  LivingOrganizationScene,
  LivingSceneBlocker,
  LivingSceneDecision,
  LivingSceneEmployee,
  LivingSceneHandoff,
  LivingSceneMission,
} from "../live-organization";

export type V2MissionRoomParticipant = {
  positionKey: string;
  title: string;
  department: string;
  authorityLevel: string;
  semanticState: string;
  workItemId: string | null;
  workStatus: string | null;
  stateReason: string;
  presenceClaimed: false;
};

export type V2MissionRoomModel = {
  established: boolean;
  mission: LivingSceneMission | null;
  participants: V2MissionRoomParticipant[];
  blockers: LivingSceneBlocker[];
  decisions: LivingSceneDecision[];
  handoffs: LivingSceneHandoff[];
  canonicalProjection: boolean;
  sceneAuthoritative: boolean;
  rendererAuthoritative: boolean;
  mutationsAllowed: boolean;
  canonicalAuthority: string | null;
  limitation: string;
};

export type V2EmployeeInspectorModel = {
  established: boolean;
  employee: LivingSceneEmployee | null;
  activeMissionKeys: string[];
  blockerIds: string[];
  decisionIds: string[];
  handoffActivityIds: string[];
  presenceClaimed: false;
  locomotionClaimed: false;
  canonicalProjection: boolean;
  mutationsAllowed: boolean;
  limitation: string;
};

const NO_MISSION_LIMITATION =
  "No canonical LivingSceneMission matched the requested mission key. V2 must not fabricate a Mission Room.";

const NO_EMPLOYEE_LIMITATION =
  "No canonical LivingSceneEmployee matched the requested position key. V2 must not fabricate an employee.";

function participantFromEmployee(employee: LivingSceneEmployee): V2MissionRoomParticipant {
  return {
    positionKey: employee.position_key,
    title: employee.title,
    department: employee.department,
    authorityLevel: employee.authority_level,
    semanticState: employee.semantic_state,
    workItemId: employee.work_item_id,
    workStatus: employee.work_status,
    stateReason: employee.state_reason,
    presenceClaimed: false,
  };
}

export function buildV2MissionRoomModel(
  scene: LivingOrganizationScene,
  missionKey: string,
): V2MissionRoomModel {
  const mission = scene.deterministic.missions.find((item) => item.mission_key === missionKey) || null;

  if (!mission) {
    return {
      established: false,
      mission: null,
      participants: [],
      blockers: [],
      decisions: [],
      handoffs: [],
      canonicalProjection: scene.deterministic.canonical_projection,
      sceneAuthoritative: scene.truth.scene_authoritative,
      rendererAuthoritative: scene.truth.renderer_authoritative,
      mutationsAllowed: scene.truth.scene_mutations_allowed,
      canonicalAuthority: scene.truth.canonical_authority,
      limitation: NO_MISSION_LIMITATION,
    };
  }

  const workIds = new Set(mission.work_item_ids);
  const participantKeys = new Set(mission.participant_position_keys);

  return {
    established: true,
    mission,
    participants: scene.deterministic.employees
      .filter((employee) => participantKeys.has(employee.position_key))
      .map(participantFromEmployee),
    blockers: scene.deterministic.blockers.filter(
      (blocker) => blocker.work_item_id !== null && workIds.has(blocker.work_item_id),
    ),
    decisions: scene.deterministic.decisions.filter(
      (decision) => decision.work_item_id !== null && workIds.has(decision.work_item_id),
    ),
    handoffs: scene.deterministic.handoffs.filter((handoff) => workIds.has(handoff.work_item_id)),
    canonicalProjection: scene.deterministic.canonical_projection,
    sceneAuthoritative: scene.truth.scene_authoritative,
    rendererAuthoritative: scene.truth.renderer_authoritative,
    mutationsAllowed: scene.truth.scene_mutations_allowed,
    canonicalAuthority: scene.truth.canonical_authority,
    limitation:
      "Mission Room content is a read-only projection of canonical Living Organization entities. Participant inclusion is not a physical-presence claim.",
  };
}

export function buildV2EmployeeInspectorModel(
  scene: LivingOrganizationScene,
  positionKey: string,
): V2EmployeeInspectorModel {
  const employee = scene.deterministic.employees.find((item) => item.position_key === positionKey) || null;

  if (!employee) {
    return {
      established: false,
      employee: null,
      activeMissionKeys: [],
      blockerIds: [],
      decisionIds: [],
      handoffActivityIds: [],
      presenceClaimed: false,
      locomotionClaimed: false,
      canonicalProjection: scene.deterministic.canonical_projection,
      mutationsAllowed: scene.truth.scene_mutations_allowed,
      limitation: NO_EMPLOYEE_LIMITATION,
    };
  }

  const missionKeys = scene.deterministic.missions
    .filter((mission) => mission.participant_position_keys.includes(positionKey))
    .map((mission) => mission.mission_key);

  const blockerIds = scene.deterministic.blockers
    .filter(
      (blocker) =>
        blocker.accountable_position_key === positionKey ||
        (employee.work_item_id !== null && blocker.work_item_id === employee.work_item_id),
    )
    .map((blocker) => blocker.blocker_id);

  const decisionIds = scene.deterministic.decisions
    .filter(
      (decision) =>
        decision.decision_owner_position === positionKey ||
        (employee.work_item_id !== null && decision.work_item_id === employee.work_item_id),
    )
    .map((decision) => decision.decision_id);

  const handoffActivityIds = scene.deterministic.handoffs
    .filter(
      (handoff) =>
        handoff.previous_position_key === positionKey ||
        handoff.assigned_position_key === positionKey,
    )
    .map((handoff) => handoff.activity_id);

  return {
    established: true,
    employee,
    activeMissionKeys: missionKeys,
    blockerIds,
    decisionIds,
    handoffActivityIds,
    presenceClaimed: false,
    locomotionClaimed: false,
    canonicalProjection: scene.deterministic.canonical_projection,
    mutationsAllowed: scene.truth.scene_mutations_allowed,
    limitation:
      "Employee Inspector is read-only. Roster identity and semantic state do not assert physical presence or locomotion.",
  };
}
