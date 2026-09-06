// AIOS V2 Q5 — Missions experience presentation model.
//
// Pure presentation mapping over the canonical Living Organization scene
// contract. This module never fetches, never mutates, and never invents Mission
// content: every entry is derived from LivingSceneMission and its linked
// canonical scene entities. A mission with no canonical match produces an
// explicit unestablished state — never a fabricated workspace.
//
// Boundaries (permanent):
// - participant inclusion is roster projection, not physical presence;
// - conversation summaries carry their canonical authority_effect and
//   transcript_persisted flags; no transcript content exists here;
// - no progress percentage is computed or implied;
// - work/blocker/decision/conversation linkage follows mission.work_item_ids
//   and canonical scene membership only — no proximity or timing inference.

import type {
  LivingOrganizationScene,
  LivingSceneBlocker,
  LivingSceneConversation,
  LivingSceneDecision,
  LivingSceneEmployee,
  LivingSceneHandoff,
  LivingSceneMission,
  LivingSceneWorkItem,
} from "../live-organization";

export type V2MissionParticipant = {
  positionKey: string;
  title: string;
  department: string;
  authorityLevel: string;
  semanticState: string;
  workItemId: string | null;
  workStatus: string | null;
  presenceClaimed: false;
};

export type V2MissionWorkEntry = {
  workItemId: string;
  title: string;
  status: string;
  priority: string;
  riskLevel: string;
  assignedPositionKey: string;
  department: string;
  authorityLevel: string;
  overdue: boolean;
  dueAt: string | null;
  completedAt: string | null;
};

export type V2MissionBlockerEntry = {
  blockerId: string;
  title: string;
  severity: string;
  status: string;
  blockerType: string;
  accountablePositionKey: string | null;
  workItemId: string | null;
  requiresHumanAction: boolean;
};

export type V2MissionDecisionEntry = {
  decisionId: string;
  title: string;
  status: string;
  authorityLevel: string;
  decisionOwnerPosition: string;
  workItemId: string | null;
};

export type V2MissionConversationEntry = {
  conversationId: string;
  summary: string;
  status: string;
  participantPositionKeys: string[];
  workItemId: string;
  openedAt: string;
  lifecycleAt: string;
  authorityEffect: string;
  transcriptPersisted: boolean;
};

export type V2MissionHandoffEntry = {
  activityId: string;
  previousPositionKey: string;
  assignedPositionKey: string;
  status: string;
  occurredAt: string;
};

export type V2MissionExperienceEntry = {
  missionKey: string;
  objectiveKey: string;
  rootWorkItemId: string;
  title: string;
  state: string;
  phaseKey: string | null;
  participants: V2MissionParticipant[];
  work: V2MissionWorkEntry[];
  blockers: V2MissionBlockerEntry[];
  decisions: V2MissionDecisionEntry[];
  conversations: V2MissionConversationEntry[];
  handoffs: V2MissionHandoffEntry[];
  canonicalBasis: string;
};

export type V2MissionsExperienceModel = {
  established: boolean;
  missions: V2MissionExperienceEntry[];
  missionCount: number;
  canonicalProjection: boolean;
  sceneAuthoritative: boolean;
  rendererAuthoritative: boolean;
  mutationsAllowed: boolean;
  canonicalAuthority: string | null;
  limitation: string;
};

export const MISSIONS_PROJECTION_LIMITATION =
  "Missions experience is a read-only projection of canonical Living Organization entities. Participant inclusion is not a physical-presence claim; conversation summaries carry their recorded authority effect and never transcript content.";

const NO_SCENE_LIMITATION =
  "No canonical Living Organization scene is established. V2 must not fabricate Mission content.";

function participantFromEmployee(employee: LivingSceneEmployee): V2MissionParticipant {
  return {
    positionKey: employee.position_key,
    title: employee.title,
    department: employee.department,
    authorityLevel: employee.authority_level,
    semanticState: employee.semantic_state,
    workItemId: employee.work_item_id,
    workStatus: employee.work_status,
    presenceClaimed: false,
  };
}

function workEntry(workItem: LivingSceneWorkItem): V2MissionWorkEntry {
  return {
    workItemId: workItem.work_item_id,
    title: workItem.title,
    status: workItem.status,
    priority: workItem.priority,
    riskLevel: workItem.risk_level,
    assignedPositionKey: workItem.assigned_position_key,
    department: workItem.department,
    authorityLevel: workItem.authority_level,
    overdue: workItem.overdue,
    dueAt: workItem.due_at,
    completedAt: workItem.completed_at,
  };
}

function blockerEntry(blocker: LivingSceneBlocker): V2MissionBlockerEntry {
  return {
    blockerId: blocker.blocker_id,
    title: blocker.title,
    severity: blocker.severity,
    status: blocker.status,
    blockerType: blocker.blocker_type,
    accountablePositionKey: blocker.accountable_position_key,
    workItemId: blocker.work_item_id,
    requiresHumanAction: blocker.requires_human_action,
  };
}

function decisionEntry(decision: LivingSceneDecision): V2MissionDecisionEntry {
  return {
    decisionId: decision.decision_id,
    title: decision.title,
    status: decision.status,
    authorityLevel: decision.authority_level,
    decisionOwnerPosition: decision.decision_owner_position,
    workItemId: decision.work_item_id,
  };
}

function conversationEntry(conversation: LivingSceneConversation): V2MissionConversationEntry {
  return {
    conversationId: conversation.conversation_id,
    summary: conversation.summary,
    status: conversation.status,
    participantPositionKeys: conversation.participant_position_keys,
    workItemId: conversation.work_item_id,
    openedAt: conversation.opened_at,
    lifecycleAt: conversation.lifecycle_at,
    authorityEffect: conversation.authority_effect,
    transcriptPersisted: conversation.transcript_persisted,
  };
}

function handoffEntry(handoff: LivingSceneHandoff): V2MissionHandoffEntry {
  return {
    activityId: handoff.activity_id,
    previousPositionKey: handoff.previous_position_key,
    assignedPositionKey: handoff.assigned_position_key,
    status: handoff.status,
    occurredAt: handoff.occurred_at,
  };
}

export function buildV2MissionExperienceEntry(
  scene: LivingOrganizationScene,
  mission: LivingSceneMission,
): V2MissionExperienceEntry {
  const workIds = new Set(mission.work_item_ids);
  const participantKeys = new Set(mission.participant_position_keys);

  return {
    missionKey: mission.mission_key,
    objectiveKey: mission.objective_key,
    rootWorkItemId: mission.root_work_item_id,
    title: mission.title,
    state: mission.state,
    phaseKey: mission.phase_key,
    participants: scene.deterministic.employees
      .filter((employee) => participantKeys.has(employee.position_key))
      .map(participantFromEmployee),
    work: scene.deterministic.work_items
      .filter((workItem) => workIds.has(workItem.work_item_id))
      .map(workEntry),
    blockers: scene.deterministic.blockers
      .filter((blocker) => blocker.work_item_id !== null && workIds.has(blocker.work_item_id))
      .map(blockerEntry),
    decisions: scene.deterministic.decisions
      .filter((decision) => decision.work_item_id !== null && workIds.has(decision.work_item_id))
      .map(decisionEntry),
    conversations: scene.deterministic.conversations
      .filter((conversation) => workIds.has(conversation.work_item_id))
      .map(conversationEntry),
    handoffs: scene.deterministic.handoffs
      .filter((handoff) => workIds.has(handoff.work_item_id))
      .map(handoffEntry),
    canonicalBasis: mission.canonical_basis,
  };
}

export function buildV2MissionsExperience(
  scene: LivingOrganizationScene | null | undefined,
): V2MissionsExperienceModel {
  const truth = scene?.truth;
  const shared = {
    canonicalProjection: scene?.deterministic.canonical_projection === true,
    sceneAuthoritative: truth?.scene_authoritative === true,
    rendererAuthoritative: truth?.renderer_authoritative === true,
    mutationsAllowed: truth?.scene_mutations_allowed === true,
    canonicalAuthority: truth?.canonical_authority ?? null,
  };

  if (!scene || !scene.deterministic || !Array.isArray(scene.deterministic.missions)) {
    return {
      established: false,
      missions: [],
      missionCount: 0,
      ...shared,
      limitation: NO_SCENE_LIMITATION,
    };
  }

  const missions = scene.deterministic.missions.map((mission) =>
    buildV2MissionExperienceEntry(scene, mission),
  );

  return {
    established: true,
    missions,
    missionCount: missions.length,
    ...shared,
    limitation: MISSIONS_PROJECTION_LIMITATION,
  };
}
