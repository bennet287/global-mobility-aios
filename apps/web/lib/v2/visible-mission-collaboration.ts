import type { LivingSceneMission } from "../live-organization";
import type {
  V2VisibleConversationCollection,
  V2VisibleConversationItem,
  V2VisibleConversationParticipant,
} from "./visible-conversation";

export const V2_CANONICAL_MISSION_COVERAGE =
  "workitem_objective_topology_projection" as const;

export type V2VisibleMissionCollaborationItem = {
  readonly missionKey: string;
  readonly missionTitle: string;
  readonly objectiveKey: string;
  readonly missionState: string;
  readonly workItemId: string;
  readonly conversationId: string;
  readonly conversationStatus: string;
  readonly summary: string;
  readonly lifecycleAt: string;
  readonly participantPositionKeys: readonly string[];
  readonly participants: readonly V2VisibleConversationParticipant[];
  readonly canonicalBasis: {
    readonly mission: string;
    readonly coordination: "OrganizationActivity conversation work_item_id";
  };
  readonly truth: {
    readonly missionProjectionOnly: true;
    readonly governedCoordinationClaimed: true;
    readonly activeCollaborationClaimed: false;
    readonly liveSpeechClaimed: false;
    readonly physicalPresenceClaimed: false;
    readonly physicalLocationClaimed: false;
    readonly authorityOutcomeClaimed: false;
    readonly completionClaimed: false;
    readonly canonicalMutationAllowed: false;
  };
};

export type V2VisibleMissionCollaborationCollection = {
  readonly supported: boolean;
  readonly missionCoverageState: string;
  readonly conversationCoverageState: string;
  readonly items: readonly V2VisibleMissionCollaborationItem[];
  readonly limitation: string | null;
};

function normalized(value: string | null | undefined): string {
  return typeof value === "string" ? value.trim() : "";
}

function validMission(mission: LivingSceneMission): boolean {
  const workIds = mission.work_item_ids.map(normalized);
  const participantKeys = mission.participant_position_keys.map(normalized);
  return Boolean(
    mission.projection_only === true &&
      normalized(mission.mission_key) &&
      normalized(mission.title) &&
      normalized(mission.objective_key) &&
      normalized(mission.canonical_basis) &&
      workIds.length > 0 &&
      workIds.every(Boolean) &&
      new Set(workIds).size === workIds.length &&
      participantKeys.length > 0 &&
      participantKeys.every(Boolean) &&
      new Set(participantKeys).size === participantKeys.length,
  );
}

function collaborationItem(
  mission: LivingSceneMission,
  conversation: V2VisibleConversationItem,
): V2VisibleMissionCollaborationItem | null {
  if (!validMission(mission)) return null;
  const missionParticipants = new Set(mission.participant_position_keys.map(normalized));
  if (
    !mission.work_item_ids.map(normalized).includes(conversation.workItemId) ||
    conversation.participantPositionKeys.some((positionKey) => !missionParticipants.has(positionKey))
  ) {
    return null;
  }

  return {
    missionKey: normalized(mission.mission_key),
    missionTitle: normalized(mission.title),
    objectiveKey: normalized(mission.objective_key),
    missionState: normalized(mission.state) || "unknown",
    workItemId: conversation.workItemId,
    conversationId: conversation.conversationId,
    conversationStatus: conversation.status,
    summary: conversation.summary,
    lifecycleAt: conversation.lifecycleAt,
    participantPositionKeys: conversation.participantPositionKeys,
    participants: conversation.participants,
    canonicalBasis: {
      mission: normalized(mission.canonical_basis),
      coordination: "OrganizationActivity conversation work_item_id",
    },
    truth: {
      missionProjectionOnly: true,
      governedCoordinationClaimed: true,
      activeCollaborationClaimed: false,
      liveSpeechClaimed: false,
      physicalPresenceClaimed: false,
      physicalLocationClaimed: false,
      authorityOutcomeClaimed: false,
      completionClaimed: false,
      canonicalMutationAllowed: false,
    },
  };
}

export function buildV2VisibleMissionCollaborations({
  missions,
  conversations,
  missionCoverageState,
}: {
  readonly missions: readonly LivingSceneMission[];
  readonly conversations: V2VisibleConversationCollection;
  readonly missionCoverageState: string | null | undefined;
}): V2VisibleMissionCollaborationCollection {
  const missionCoverage = normalized(missionCoverageState) || "unavailable";
  if (missionCoverage !== V2_CANONICAL_MISSION_COVERAGE) {
    return {
      supported: false,
      missionCoverageState: missionCoverage,
      conversationCoverageState: conversations.coverageState,
      items: [],
      limitation:
        "Mission coordination evidence is unavailable for this Mission coverage state. AIOS will not infer collaboration from roster membership, room placement or shared work topology.",
    };
  }
  if (!conversations.supported) {
    return {
      supported: false,
      missionCoverageState: missionCoverage,
      conversationCoverageState: conversations.coverageState,
      items: [],
      limitation:
        "Mission coordination evidence is unavailable because governed conversation lifecycle coverage is unavailable. AIOS will not infer collaboration from Mission topology alone.",
    };
  }

  const validMissions = missions.filter(validMission);
  const items: V2VisibleMissionCollaborationItem[] = [];
  for (const conversation of conversations.items) {
    const matches = validMissions.filter((mission) =>
      mission.work_item_ids.map(normalized).includes(conversation.workItemId),
    );
    if (matches.length !== 1) continue;
    const item = collaborationItem(matches[0], conversation);
    if (item) items.push(item);
  }

  items.sort((left, right) => {
    const lifecycleOrder = right.lifecycleAt.localeCompare(left.lifecycleAt);
    if (lifecycleOrder !== 0) return lifecycleOrder;
    const missionOrder = left.missionKey.localeCompare(right.missionKey);
    return missionOrder !== 0
      ? missionOrder
      : left.conversationId.localeCompare(right.conversationId, undefined, {
          numeric: true,
          sensitivity: "base",
        });
  });

  return {
    supported: true,
    missionCoverageState: missionCoverage,
    conversationCoverageState: conversations.coverageState,
    items,
    limitation: null,
  };
}

export function visibleMissionCollaborationsForMission(
  collection: V2VisibleMissionCollaborationCollection,
  missionKey: string,
): readonly V2VisibleMissionCollaborationItem[] {
  if (!collection.supported) return [];
  const key = normalized(missionKey);
  if (!key) return [];
  return collection.items.filter((item) => item.missionKey === key);
}

export function visibleMissionCollaborationsForPosition(
  collection: V2VisibleMissionCollaborationCollection,
  positionKey: string,
): readonly V2VisibleMissionCollaborationItem[] {
  if (!collection.supported) return [];
  const key = normalized(positionKey);
  if (!key) return [];
  return collection.items.filter((item) => item.participantPositionKeys.includes(key));
}
