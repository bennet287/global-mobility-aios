import type {
  LivingOrganizationScene,
  LivingSceneBlocker,
  LivingSceneDecision,
  LivingSceneEmployee,
  LivingSceneHandoff,
  LivingSceneMission,
} from "../live-organization";
import {
  V2_CANONICAL_BLOCKER_COVERAGE,
  selectV2CanonicalBlockersForPosition,
} from "./visible-blocker";
import {
  buildV2VisibleConversations,
  visibleConversationsForPosition,
  type V2VisibleConversationItem,
} from "./visible-conversation";
import {
  buildV2VisibleMissionCollaborations,
  visibleMissionCollaborationsForMission,
  visibleMissionCollaborationsForPosition,
  type V2VisibleMissionCollaborationItem,
} from "./visible-mission-collaboration";

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
  blockerCoverageSupported: boolean;
  blockerCoverageState: string;
  conversations: readonly V2VisibleConversationItem[];
  conversationCoverageSupported: boolean;
  conversationCoverageState: string;
  collaborations: readonly V2VisibleMissionCollaborationItem[];
  collaborationCoverageSupported: boolean;
  missionCoverageState: string;
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
  blockers: LivingSceneBlocker[];
  blockerIds: string[];
  blockerCoverageSupported: boolean;
  blockerCoverageState: string;
  conversations: readonly V2VisibleConversationItem[];
  conversationCoverageSupported: boolean;
  conversationCoverageState: string;
  collaborations: readonly V2VisibleMissionCollaborationItem[];
  collaborationCoverageSupported: boolean;
  missionCoverageState: string;
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

function blockerCoverage(scene: LivingOrganizationScene) {
  const state = scene.coverage.blockers || "unavailable";
  return {
    state,
    supported: state === V2_CANONICAL_BLOCKER_COVERAGE,
  } as const;
}

function conversationProjection(scene: LivingOrganizationScene) {
  return buildV2VisibleConversations({
    conversations: scene.deterministic.conversations,
    employees: scene.deterministic.employees,
    workItems: scene.deterministic.work_items,
    coverageState: scene.coverage.conversations,
  });
}

function collaborationProjection(scene: LivingOrganizationScene) {
  const conversations = conversationProjection(scene);
  return buildV2VisibleMissionCollaborations({
    missions: scene.deterministic.missions,
    conversations,
    missionCoverageState: scene.coverage.missions,
  });
}

export function buildV2MissionRoomModel(
  scene: LivingOrganizationScene,
  missionKey: string,
): V2MissionRoomModel {
  const blockerTruth = blockerCoverage(scene);
  const conversationTruth = conversationProjection(scene);
  const collaborationTruth = buildV2VisibleMissionCollaborations({
    missions: scene.deterministic.missions,
    conversations: conversationTruth,
    missionCoverageState: scene.coverage.missions,
  });
  const mission = scene.deterministic.missions.find((item) => item.mission_key === missionKey) || null;

  if (!mission) {
    return {
      established: false,
      mission: null,
      participants: [],
      blockers: [],
      blockerCoverageSupported: blockerTruth.supported,
      blockerCoverageState: blockerTruth.state,
      conversations: [],
      conversationCoverageSupported: conversationTruth.supported,
      conversationCoverageState: conversationTruth.coverageState,
      collaborations: [],
      collaborationCoverageSupported: collaborationTruth.supported,
      missionCoverageState: collaborationTruth.missionCoverageState,
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
  const conversations = conversationTruth.supported
    ? conversationTruth.items.filter((conversation) => workIds.has(conversation.workItemId))
    : [];
  const collaborations = visibleMissionCollaborationsForMission(
    collaborationTruth,
    mission.mission_key,
  );

  return {
    established: true,
    mission,
    participants: scene.deterministic.employees
      .filter((employee) => participantKeys.has(employee.position_key))
      .map(participantFromEmployee),
    blockers: blockerTruth.supported
      ? scene.deterministic.blockers.filter(
          (blocker) => blocker.work_item_id !== null && workIds.has(blocker.work_item_id),
        )
      : [],
    blockerCoverageSupported: blockerTruth.supported,
    blockerCoverageState: blockerTruth.state,
    conversations,
    conversationCoverageSupported: conversationTruth.supported,
    conversationCoverageState: conversationTruth.coverageState,
    collaborations,
    collaborationCoverageSupported: collaborationTruth.supported,
    missionCoverageState: collaborationTruth.missionCoverageState,
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
      "Mission Room content is a read-only projection of canonical Living Organization entities. Mission topology scopes work; governed coordination evidence uses exact conversation participants and does not establish live teamwork, physical presence or live speech.",
  };
}

export function buildV2EmployeeInspectorModel(
  scene: LivingOrganizationScene,
  positionKey: string,
): V2EmployeeInspectorModel {
  const blockerTruth = blockerCoverage(scene);
  const conversationTruth = conversationProjection(scene);
  const collaborationTruth = collaborationProjection(scene);
  const employee = scene.deterministic.employees.find((item) => item.position_key === positionKey) || null;

  if (!employee) {
    return {
      established: false,
      employee: null,
      activeMissionKeys: [],
      blockers: [],
      blockerIds: [],
      blockerCoverageSupported: blockerTruth.supported,
      blockerCoverageState: blockerTruth.state,
      conversations: [],
      conversationCoverageSupported: conversationTruth.supported,
      conversationCoverageState: conversationTruth.coverageState,
      collaborations: [],
      collaborationCoverageSupported: collaborationTruth.supported,
      missionCoverageState: collaborationTruth.missionCoverageState,
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

  const blockerSelection = selectV2CanonicalBlockersForPosition({
    blockers: scene.deterministic.blockers,
    employees: scene.deterministic.employees,
    coverageState: scene.coverage.blockers,
    positionKey,
  });
  const blockers = [...blockerSelection.blockers];
  const blockerIds = [...blockerSelection.blockerIds];
  const conversations = visibleConversationsForPosition(conversationTruth, positionKey);
  const collaborations = visibleMissionCollaborationsForPosition(collaborationTruth, positionKey);

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
    blockers,
    blockerIds,
    blockerCoverageSupported: blockerSelection.supported,
    blockerCoverageState: blockerSelection.coverageState,
    conversations,
    conversationCoverageSupported: conversationTruth.supported,
    conversationCoverageState: conversationTruth.coverageState,
    collaborations,
    collaborationCoverageSupported: collaborationTruth.supported,
    missionCoverageState: collaborationTruth.missionCoverageState,
    decisionIds,
    handoffActivityIds,
    presenceClaimed: false,
    locomotionClaimed: false,
    canonicalProjection: scene.deterministic.canonical_projection,
    mutationsAllowed: scene.truth.scene_mutations_allowed,
    limitation:
      "Employee Inspector is read-only. Mission membership is topology scope only; governed coordination evidence requires exact canonical conversation participation and does not assert active collaboration, physical presence, locomotion or live speech.",
  };
}
